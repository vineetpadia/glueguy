#!/usr/bin/env python3
"""Generate Mistral OCR sidecars for cached TDS PDFs.

Credentials are read from the local Codex MCP config by default and are never
printed. The cache pipeline then prefers the generated `.mistral.md` files over
`pdftotext`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "tds-cache"
MANIFEST_PATH = ROOT / "data" / "tds-cache-manifest.json"
REPORT_PATH = ROOT / "data" / "autonomous-research-report.json"
CONFIG_PATH = Path("/home/scandium/.codex/config.toml")
OCR_MODEL = "mistral-ocr-latest"


def load_mistral_client():
    try:
        from mistralai import Mistral
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "mistralai is not installed in this Python. Run with "
            "/home/scandium/.local/share/mcp-mistral-ocr-venv/bin/python or install mistralai."
        ) from exc

    config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    env = config.get("mcp_servers", {}).get("mistral_ocr", {}).get("env", {})
    api_key = env.get("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY was not found in Codex MCP config")
    return Mistral(api_key=api_key)


def pages_to_markdown(payload: dict) -> str:
    chunks = []
    for page in payload.get("pages", []):
        index = page.get("index")
        markdown = (page.get("markdown") or "").strip()
        if not markdown:
            continue
        chunks.append(f"<!-- page: {index} -->\n\n{markdown}")
    return "\n\n---\n\n".join(chunks).strip() + "\n"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {"entries": []}


def load_report_rank() -> dict[str, tuple[int, bool, float, float]]:
    if not REPORT_PATH.exists():
        return {}
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    rank = {}
    for index, item in enumerate(report.get("manualFieldCoverage", {}).get("weakestEntries", [])):
        rank[item["id"]] = (
            index,
            bool(item.get("electronicsRelevant")),
            float(item.get("electronicsFieldCoverage") or 1),
            float(item.get("decisionFieldCoverage") or 1),
        )
    return rank


def entry_pdf_path(entry: dict) -> Path | None:
    raw_path = entry.get("rawPath")
    if raw_path and raw_path.endswith(".pdf"):
        candidate = ROOT / raw_path
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
    entry_id = entry.get("id")
    if not entry_id:
        return None
    candidate = CACHE_DIR / f"{entry_id}.pdf"
    if candidate.exists() and candidate.stat().st_size > 0:
        return candidate
    return None


def output_paths(entry_id: str) -> tuple[Path, Path, Path]:
    return (
        CACHE_DIR / f"{entry_id}.mistral.json",
        CACHE_DIR / f"{entry_id}.mistral.md",
        CACHE_DIR / f"{entry_id}.txt",
    )


def needs_ocr(entry: dict, refresh: bool) -> bool:
    entry_id = entry.get("id")
    if not entry_id or entry.get("error"):
        return False
    if entry_pdf_path(entry) is None:
        return False
    _, markdown_path, _ = output_paths(entry_id)
    return refresh or not (markdown_path.exists() and markdown_path.stat().st_size > 0)


def candidate_entries(limit: int | None, refresh: bool, electronics_first: bool) -> list[dict]:
    manifest = load_manifest()
    rank = load_report_rank()
    entries = [entry for entry in manifest.get("entries", []) if needs_ocr(entry, refresh)]

    def sort_key(entry: dict):
        fallback = (9999, False, 1.0, 1.0)
        index, electronics, electronics_cov, decision_cov = rank.get(entry.get("id"), fallback)
        return (
            not electronics if electronics_first else False,
            index,
            electronics_cov,
            decision_cov,
            entry.get("maker") or "",
            entry.get("name") or "",
        )

    entries.sort(key=sort_key)
    return entries[:limit] if limit is not None else entries


def ocr_pdf(client, pdf_path: Path) -> dict:
    with pdf_path.open("rb") as handle:
        uploaded_file = client.files.upload(
            file={
                "file_name": pdf_path.name,
                "content": handle,
            },
            purpose="ocr",
        )
    signed_url = client.files.get_signed_url(file_id=uploaded_file.id)
    response = client.ocr.process(
        model=OCR_MODEL,
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
    )
    return response.model_dump()


def is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "status 429" in message or "rate limit" in message or "rate_limited" in message


def ocr_entry(entry: dict, retries: int, retry_base_sleep: float) -> dict:
    pdf_path = entry_pdf_path(entry)
    if pdf_path is None:
        raise RuntimeError("PDF path disappeared before OCR")
    for attempt in range(retries + 1):
        try:
            client = load_mistral_client()
            payload = ocr_pdf(client, pdf_path)
            return write_sidecars(entry, payload)
        except Exception as exc:  # noqa: BLE001
            if attempt >= retries or not is_rate_limit_error(exc):
                raise
            time.sleep(retry_base_sleep * (2**attempt))
    raise RuntimeError("unreachable retry state")


def write_sidecars(entry: dict, payload: dict) -> dict:
    entry_id = entry["id"]
    json_path, markdown_path, text_path = output_paths(entry_id)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = pages_to_markdown(payload)
    markdown_path.write_text(markdown, encoding="utf-8")
    text_path.write_text(markdown, encoding="utf-8")
    return {
        "id": entry_id,
        "jsonPath": str(json_path.relative_to(ROOT)),
        "markdownPath": str(markdown_path.relative_to(ROOT)),
        "textPath": str(text_path.relative_to(ROOT)),
        "pages": len(payload.get("pages") or []),
        "markdownBytes": markdown_path.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--id", action="append", dest="ids", help="OCR a specific cache entry id. Can be repeated.")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.25)
    parser.add_argument("--all", action="store_true", help="Process all remaining PDFs.")
    parser.add_argument("--no-electronics-first", action="store_true")
    parser.add_argument("--workers", type=int, default=3, help="Parallel OCR workers.")
    parser.add_argument("--retries", type=int, default=6, help="Retries per PDF for transient rate limits.")
    parser.add_argument("--retry-base-sleep", type=float, default=20.0, help="Initial backoff seconds for rate limits.")
    args = parser.parse_args()

    manifest = load_manifest()
    if args.ids:
        wanted = set(args.ids)
        entries = [entry for entry in manifest.get("entries", []) if entry.get("id") in wanted and needs_ocr(entry, args.refresh)]
    else:
        entries = candidate_entries(None if args.all else args.limit, args.refresh, not args.no_electronics_first)

    results = []
    errors = []
    started_at = datetime.now(UTC).isoformat()
    if args.workers <= 1:
        for entry in entries:
            try:
                result = ocr_entry(entry, args.retries, args.retry_base_sleep)
                results.append(result)
                print(json.dumps(result, ensure_ascii=False), flush=True)
                time.sleep(args.sleep)
            except Exception as exc:  # noqa: BLE001
                message = f"{type(exc).__name__}: {exc}"
                errors.append({"id": entry.get("id"), "error": re.sub(r"(?i)(api[_-]?key=?)\\S+", r"\\1***", message)})
                print(json.dumps(errors[-1]), file=sys.stderr, flush=True)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(ocr_entry, entry, args.retries, args.retry_base_sleep): entry for entry in entries}
            for future in as_completed(futures):
                entry = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(json.dumps(result, ensure_ascii=False), flush=True)
                except Exception as exc:  # noqa: BLE001
                    message = f"{type(exc).__name__}: {exc}"
                    errors.append({"id": entry.get("id"), "error": re.sub(r"(?i)(api[_-]?key=?)\\S+", r"\\1***", message)})
                    print(json.dumps(errors[-1]), file=sys.stderr, flush=True)
                if args.sleep:
                    time.sleep(args.sleep)

    print(
        json.dumps(
            {
                "startedAt": started_at,
                "processed": len(results),
                "errors": len(errors),
                "remainingSelected": max(0, len(entries) - len(results) - len(errors)),
            },
            indent=2,
        )
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
