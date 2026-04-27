#!/usr/bin/env python3
"""Import a Mistral OCR MCP result into Glueboy TDS cache sidecars."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "tds-cache"


def load_payload(path: str | None) -> dict:
    text = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    payload = json.loads(text)
    if isinstance(payload, dict) and "result" in payload:
        result = payload["result"]
        if isinstance(result, list) and result and isinstance(result[0], dict) and result[0].get("text"):
            return json.loads(result[0]["text"])
    return payload


def pages_to_markdown(payload: dict) -> str:
    pages = payload.get("pages") or []
    chunks = []
    for page in pages:
        index = page.get("index")
        markdown = (page.get("markdown") or "").strip()
        if not markdown:
            continue
        chunks.append(f"<!-- page: {index} -->\n\n{markdown}")
    return "\n\n---\n\n".join(chunks).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry_id")
    parser.add_argument("--input", help="JSON file containing the MCP result. Defaults to stdin.")
    args = parser.parse_args()

    payload = load_payload(args.input)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    json_path = CACHE_DIR / f"{args.entry_id}.mistral.json"
    markdown_path = CACHE_DIR / f"{args.entry_id}.mistral.md"
    text_path = CACHE_DIR / f"{args.entry_id}.txt"

    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    markdown = pages_to_markdown(payload)
    markdown_path.write_text(markdown, encoding="utf-8")
    text_path.write_text(markdown, encoding="utf-8")

    print(
        json.dumps(
            {
                "entryId": args.entry_id,
                "jsonPath": str(json_path.relative_to(ROOT)),
                "markdownPath": str(markdown_path.relative_to(ROOT)),
                "textPath": str(text_path.relative_to(ROOT)),
                "pages": len(payload.get("pages") or []),
                "markdownBytes": markdown_path.stat().st_size,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
