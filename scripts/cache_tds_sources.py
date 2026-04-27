#!/usr/bin/env python3
"""Download and extract local text copies of Glueguy reference sources."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "tds-manual-source.json"
CACHE_DIR = ROOT / "data" / "tds-cache"
MANIFEST_PATH = ROOT / "data" / "tds-cache-manifest.json"
OVERRIDES_PATH = ROOT / "data" / "tds-cache-overrides.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
FETCH_TIMEOUT = int(os.environ.get("GLUEBOY_TDS_FETCH_TIMEOUT", "20"))
REFRESH_CACHE = os.environ.get("GLUEBOY_REFRESH_TDS_CACHE", "").lower() in {"1", "true", "yes"}
PREFER_MISTRAL_OCR = os.environ.get("GLUEBOY_PREFER_MISTRAL_OCR", "1").lower() not in {"0", "false", "no"}


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?>.*?</style>", " ", html)
    html = re.sub(r"(?i)<br\\s*/?>", "\n", html)
    html = re.sub(r"(?i)</p>", "\n\n", html)
    html = re.sub(r"(?i)</div>", "\n", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    html = (
        html.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#8211;", "-")
        .replace("&#8217;", "'")
    )
    return normalize_space(html)


def looks_like_html(raw_bytes: bytes) -> bool:
    sample = raw_bytes[:512].lstrip().lower()
    return sample.startswith(b"<!doctype html") or sample.startswith(b"<html") or b"<html" in sample


def looks_like_block_text(text: str) -> bool:
    normalized = text.lower()
    return (
        "incapsula incident" in normalized
        or "request unsuccessful" in normalized
        or "access denied" in normalized
        or "akamai" in normalized and "reference" in normalized and "denied" in normalized
    )


def looks_like_block_page(raw_bytes: bytes) -> bool:
    return looks_like_block_text(raw_bytes[:4096].decode("utf-8", "ignore"))


def extract_pdf_text(raw_path: Path, text_path: Path) -> None:
    subprocess.run(
        ["pdftotext", str(raw_path), str(text_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def mistral_paths(entry_id: str) -> tuple[Path, Path]:
    stem = CACHE_DIR / entry_id
    return stem.with_suffix(".mistral.json"), stem.with_suffix(".mistral.md")


def usable_mistral_markdown(entry_id: str) -> Path | None:
    _, markdown_path = mistral_paths(entry_id)
    if markdown_path.exists() and markdown_path.stat().st_size > 0:
        text = markdown_path.read_text(encoding="utf-8", errors="ignore")
        if not looks_like_block_text(text):
            return markdown_path
    return None


def write_text_from_mistral_if_available(entry_id: str, text_path: Path) -> dict | None:
    markdown_path = usable_mistral_markdown(entry_id)
    if markdown_path is None:
        return None
    markdown = markdown_path.read_text(encoding="utf-8", errors="ignore")
    text_path.write_text(markdown, encoding="utf-8")
    return {
        "ocrEngine": "mistral-ocr",
        "mistralMarkdownPath": str(markdown_path.relative_to(ROOT)),
        "textExtraction": "mistral-ocr-markdown",
    }


def fetch_reference(url: str) -> tuple[bytes, str]:
    response = requests.get(url, headers=HEADERS, timeout=FETCH_TIMEOUT)
    response.raise_for_status()
    return response.content, normalize_space(response.headers.get("content-type", ""))


def fetch_reference_with_curl(url: str) -> tuple[bytes, str]:
    """Fallback for vendor CDNs that block Python TLS/client fingerprints but allow curl."""
    if not shutil.which("curl"):
        raise RuntimeError("curl is not available for fallback fetch")
    attempts = [HEADERS["User-Agent"], "Mozilla/5.0"]
    last_result: tuple[bytes, str] | None = None
    for user_agent in attempts:
        with tempfile.NamedTemporaryFile() as body_file, tempfile.NamedTemporaryFile() as header_file:
            subprocess.run(
                [
                    "curl",
                    "-L",
                    "--fail",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    str(FETCH_TIMEOUT),
                    "-A",
                    user_agent,
                    "-H",
                    "Accept: application/pdf,*/*",
                    "-D",
                    header_file.name,
                    "-o",
                    body_file.name,
                    url,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            raw_bytes = Path(body_file.name).read_bytes()
            headers = Path(header_file.name).read_text(encoding="utf-8", errors="ignore")
        content_types = re.findall(r"(?im)^content-type:\s*([^\r\n]+)", headers)
        content_type = normalize_space(content_types[-1] if content_types else "")
        last_result = (raw_bytes, content_type)
        if raw_bytes and not looks_like_block_page(raw_bytes):
            return raw_bytes, content_type
    assert last_result is not None
    return last_result


def should_retry_with_curl(url: str, raw_bytes: bytes, content_type: str) -> bool:
    expected_pdf = url.lower().split("?", 1)[0].endswith(".pdf") or "application/pdf" in content_type
    html_or_block = looks_like_html(raw_bytes) or looks_like_block_page(raw_bytes)
    return expected_pdf and (raw_bytes[:4] != b"%PDF" or html_or_block)


def fetch_reference_for_entry(entry: dict) -> tuple[bytes, str]:
    """Fetch normal URL references plus official portals that require a form POST."""
    download = entry.get("tdsDownload") or {}
    if download.get("method") == "shinetsu-tds-post":
        preflight_url = download["preflightUrl"]
        session = requests.Session()
        preflight = session.get(preflight_url, headers=HEADERS, timeout=FETCH_TIMEOUT)
        preflight.raise_for_status()
        action_match = re.search(
            r'id="sdsTdsDownload"[^>]*method="post"[^>]*action="([^"]+)"',
            preflight.text,
        )
        action = action_match.group(1) if action_match else "/sdstds/downloadSdsTds.do"
        form_data = {
            "downloadTargetCategory": "2",
            "deviceInfo": HEADERS["User-Agent"],
            "timezoneInfo": "UTC",
            "dlDatetime": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            **{key: str(value) for key, value in (download.get("formData") or {}).items()},
        }
        response = session.post(
            urljoin(preflight_url, action),
            data=form_data,
            headers={**HEADERS, "Referer": preflight_url},
            timeout=FETCH_TIMEOUT,
        )
        response.raise_for_status()
        return response.content, normalize_space(response.headers.get("content-type", ""))

    raw_bytes, content_type = fetch_reference(entry["referenceUrl"])
    if should_retry_with_curl(entry["referenceUrl"], raw_bytes, content_type):
        try:
            curl_bytes, curl_content_type = fetch_reference_with_curl(entry["referenceUrl"])
        except Exception:
            return raw_bytes, content_type
        if curl_bytes and not looks_like_block_page(curl_bytes):
            return curl_bytes, curl_content_type
    return raw_bytes, content_type


def load_existing_manifest() -> dict[str, dict]:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {entry.get("id"): entry for entry in payload.get("entries", []) if entry.get("id")}


def reusable_cache_entry(entry: dict, existing: dict[str, dict]) -> dict | None:
    if REFRESH_CACHE:
        return None
    entry_id = entry.get("id") or slugify(entry["name"])
    prior = dict(existing.get(entry_id) or {})
    prior_url = normalize_space(prior.get("referenceUrl"))
    entry_url = normalize_space(entry.get("referenceUrl"))
    if prior and prior_url and entry_url and prior_url != entry_url:
        return None
    if PREFER_MISTRAL_OCR:
        markdown_path = usable_mistral_markdown(entry_id)
        text_path = CACHE_DIR / f"{entry_id}.txt"
        if markdown_path and text_path.exists() and text_path.stat().st_size > 0:
            cached_text = markdown_path.read_text(encoding="utf-8", errors="ignore")
            if not looks_like_block_text(cached_text):
                prior.update(
                    {
                        "id": entry_id,
                        "maker": entry.get("maker"),
                        "name": entry.get("name"),
                        "referenceUrl": entry.get("referenceUrl"),
                        "textPath": str(text_path.relative_to(ROOT)),
                        "textBytes": text_path.stat().st_size,
                        "textPreview": cached_text[:400],
                        "mistralMarkdownPath": str(markdown_path.relative_to(ROOT)),
                        "textExtraction": "mistral-ocr-markdown",
                        "ocrEngine": "mistral-ocr",
                        "cacheReused": True,
                    }
                )
                return prior
    text_path_value = prior.get("textPath")
    if text_path_value:
        text_path = ROOT / text_path_value
        if text_path.exists() and text_path.stat().st_size > 0 and not prior.get("error"):
            cached_text = text_path.read_text(encoding="utf-8", errors="ignore")
            if looks_like_block_text(cached_text):
                return None
            prior.update(
                {
                    "id": entry_id,
                    "maker": entry.get("maker"),
                    "name": entry.get("name"),
                    "referenceUrl": entry.get("referenceUrl"),
                    "textBytes": text_path.stat().st_size,
                    "textPreview": cached_text[:400],
                    "cacheReused": True,
                }
            )
            return prior

    text_path = CACHE_DIR / f"{entry_id}.txt"
    if text_path.exists() and text_path.stat().st_size > 0:
        cached_text = text_path.read_text(encoding="utf-8", errors="ignore")
        if looks_like_block_text(cached_text):
            return None
        raw_path = None
        for suffix in [".pdf", ".html", ".txt"]:
            candidate = CACHE_DIR / f"{entry_id}{suffix}"
            if candidate.exists():
                raw_path = candidate
                break
        result = {
            "id": entry_id,
            "maker": entry.get("maker"),
            "name": entry.get("name"),
            "referenceUrl": entry.get("referenceUrl"),
            "contentType": prior.get("contentType", "local-cache"),
            "rawPath": str((raw_path or text_path).relative_to(ROOT)),
            "textPath": str(text_path.relative_to(ROOT)),
            "textBytes": text_path.stat().st_size,
            "textPreview": cached_text[:400],
            "cacheReused": True,
        }
        markdown_path = usable_mistral_markdown(entry_id)
        if markdown_path:
            result.update(
                {
                    "mistralMarkdownPath": str(markdown_path.relative_to(ROOT)),
                    "textExtraction": "mistral-ocr-markdown",
                    "ocrEngine": "mistral-ocr",
                }
            )
        return result
    return None


def load_overrides() -> dict[str, dict]:
    if not OVERRIDES_PATH.exists():
        return {}
    payload = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    return {entry["id"]: entry for entry in entries if entry.get("id")}


def cache_override(entry: dict, override: dict, fallback_error: Exception | None = None) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entry_id = entry.get("id") or slugify(entry["name"])
    stem = CACHE_DIR / entry_id
    extension = override.get("rawExtension", ".txt")
    if not extension.startswith("."):
        extension = "." + extension
    raw_path = stem.with_suffix(extension)
    text_path = stem.with_suffix(".txt")
    raw_text = override.get("rawText") or override.get("text") or ""
    text_content = override.get("text") or raw_text
    raw_path.write_text(raw_text, encoding="utf-8")
    text_path.write_text(text_content, encoding="utf-8")
    extracted_text = text_path.read_text(encoding="utf-8", errors="ignore")
    result = {
        "id": entry_id,
        "maker": entry.get("maker"),
        "name": entry.get("name"),
        "referenceUrl": override.get("sourceUrl") or entry.get("referenceUrl"),
        "contentType": override.get("contentType", "text/plain"),
        "rawPath": str(raw_path.relative_to(ROOT)),
        "textPath": str(text_path.relative_to(ROOT)),
        "textBytes": text_path.stat().st_size,
        "textPreview": extracted_text[:400],
        "override": True,
    }
    if fallback_error is not None:
        result["overrideReason"] = f"{type(fallback_error).__name__}: {fallback_error}"
    return result


def cache_entry(entry: dict, overrides: dict[str, dict], existing: dict[str, dict]) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entry_id = entry.get("id") or slugify(entry["name"])
    url = entry["referenceUrl"]
    override = overrides.get(entry_id)
    if override and override.get("force"):
        return cache_override(entry, override)
    cached = reusable_cache_entry(entry, existing)
    if cached:
        return cached
    try:
        raw_bytes, content_type = fetch_reference_for_entry(entry)
    except Exception as exc:
        if override:
            return cache_override(entry, override, fallback_error=exc)
        stale_cache = reusable_cache_entry(entry, existing)
        if stale_cache:
            stale_cache["cacheReusedAfterFetchError"] = f"{type(exc).__name__}: {exc}"
            return stale_cache
        raise

    is_pdf = (
        "application/pdf" in content_type
        or url.lower().endswith(".pdf")
        or raw_bytes[:4] == b"%PDF"
    )
    stem = CACHE_DIR / entry_id

    if is_pdf:
        raw_path = stem.with_suffix(".pdf")
        text_path = stem.with_suffix(".txt")
        raw_path.write_bytes(raw_bytes)
        mistral_meta = write_text_from_mistral_if_available(entry_id, text_path) if PREFER_MISTRAL_OCR else None
        if mistral_meta is None:
            try:
                extract_pdf_text(raw_path, text_path)
            except subprocess.CalledProcessError:
                if looks_like_html(raw_bytes):
                    raw_path.unlink(missing_ok=True)
                    raw_path = stem.with_suffix(".html")
                    raw_path.write_bytes(raw_bytes)
                    text_path.write_text(html_to_text(raw_bytes.decode("utf-8", "ignore")), encoding="utf-8")
                else:
                    raise
            mistral_meta = {"textExtraction": "pdftotext-fallback"}
        else:
            pass
        if text_path.exists() and text_path.stat().st_size > 0:
            pass
        else:
            if looks_like_html(raw_bytes):
                raw_path.unlink(missing_ok=True)
                raw_path = stem.with_suffix(".html")
                raw_path.write_bytes(raw_bytes)
                text_path.write_text(html_to_text(raw_bytes.decode("utf-8", "ignore")), encoding="utf-8")
            else:
                raise RuntimeError(f"No text extracted for {entry_id}")
    else:
        raw_path = stem.with_suffix(".html")
        text_path = stem.with_suffix(".txt")
        raw_path.write_bytes(raw_bytes)
        text_path.write_text(html_to_text(raw_bytes.decode("utf-8", "ignore")), encoding="utf-8")
        mistral_meta = {"textExtraction": "html-to-text"}

    extracted_text = text_path.read_text(encoding="utf-8", errors="ignore")
    result = {
        "id": entry_id,
        "maker": entry.get("maker"),
        "name": entry.get("name"),
        "referenceUrl": url,
        "contentType": content_type,
        "rawPath": str(raw_path.relative_to(ROOT)),
        "textPath": str(text_path.relative_to(ROOT)),
        "textBytes": text_path.stat().st_size,
        "textPreview": extracted_text[:400],
    }
    result.update(mistral_meta)
    return result


def main() -> None:
    payload = json.loads(SOURCE_PATH.read_text())
    overrides = load_overrides()
    existing = load_existing_manifest()
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entries": [],
        "stats": {"attempted": 0, "cached": 0, "reused": 0, "errors": 0},
    }

    for entry in payload.get("entries", []):
        url = entry.get("referenceUrl")
        if not url:
            continue
        manifest["stats"]["attempted"] += 1
        try:
            cached = cache_entry(entry, overrides, existing)
            manifest["entries"].append(cached)
            manifest["stats"]["cached"] += 1
            if cached.get("cacheReused"):
                manifest["stats"]["reused"] += 1
            else:
                time.sleep(0.15)
        except Exception as exc:  # noqa: BLE001
            manifest["entries"].append(
                {
                    "id": entry.get("id"),
                    "maker": entry.get("maker"),
                    "name": entry.get("name"),
                    "referenceUrl": url,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            manifest["stats"]["errors"] += 1
            time.sleep(0.15)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
