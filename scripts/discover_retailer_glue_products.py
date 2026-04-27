#!/usr/bin/env python3
"""Discover glue and adhesive product pages sold by major retailers."""

from __future__ import annotations

import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse
import xml.etree.ElementTree as ET

import requests


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "retailer-discovery-config.json"
SEEDS_PATH = ROOT / "data" / "autonomous-research-seeds.json"
OUTPUT_PATH = ROOT / "data" / "retailer-discovered-products.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
SEARCH_URL = "https://www.bing.com/search"
TIMEOUT = 20


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_space(value).lower())


def load_seed_queries() -> dict[str, list[str]]:
    payload = json.loads(SEEDS_PATH.read_text())
    retailer_makers = {
        "Henkel Loctite",
        "DAP",
        "Gorilla Glue",
        "J-B Weld",
        "3M",
        "Oatey / IPS Weld-On",
    }
    queries: dict[str, list[str]] = {}
    for maker in retailer_makers:
        queries[maker] = []
    for manufacturer in payload.get("manufacturers", []):
        maker = manufacturer.get("name", "")
        if maker not in retailer_makers:
            continue
        for product in manufacturer.get("products", [])[:8]:
            name = normalize_space(product.get("name"))
            if name:
                queries[maker].append(name)
    return queries


def build_queries(config: dict) -> list[dict]:
    dynamic = load_seed_queries()
    rows = []
    for maker_query in config.get("makerQueries", []):
        maker = maker_query["maker"]
        terms = list(dict.fromkeys([*maker_query.get("terms", []), *dynamic.get(maker, [])]))
        for term in terms:
            rows.append({"maker": maker, "term": term})
    return rows


def clean_title(title: str, retailer: str) -> str:
    cleaned = html.unescape(title)
    suffixes = {
        "Home Depot": [
            " - The Home Depot",
            " | The Home Depot",
        ],
        "Lowe's": [
            " at Lowes.com",
            " - Lowes.com",
            " | Lowes.com",
        ],
    }
    for suffix in suffixes.get(retailer, []):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    return normalize_space(cleaned)


def search(query: str, limit: int = 8) -> list[dict]:
    response = requests.get(
        SEARCH_URL,
        params={"format": "rss", "q": query},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    root = ET.fromstring(response.text)
    results = []
    for item in root.findall("./channel/item"):
        title = normalize_space(item.findtext("title"))
        href = normalize_space(item.findtext("link"))
        if not title or not href:
            continue
        results.append(
            {
                "url": html.unescape(href),
                "title": title,
            }
        )
        if len(results) >= limit:
            break
    return results


def allowed_result(result_url: str, retailer_domain: str) -> bool:
    parsed = urlparse(result_url)
    if retailer_domain not in parsed.netloc:
        return False
    if retailer_domain == "homedepot.com":
        return "/p/" in parsed.path
    if retailer_domain == "lowes.com":
        return "/pd/" in parsed.path
    return True


def discover() -> dict:
    config = json.loads(CONFIG_PATH.read_text())
    query_rows = build_queries(config)

    entries = []
    seen: set[tuple[str, str, str]] = set()
    retailer_summaries = []

    for retailer in config.get("retailers", []):
        retailer_hits = []
        maker_counts: dict[str, int] = {}
        for row in query_rows:
            query = f'{retailer["siteQuery"]} "{row["term"]}"'
            try:
                results = search(query)
            except Exception as exc:  # noqa: BLE001
                retailer_hits.append(
                    {
                        "maker": row["maker"],
                        "query": query,
                        "hits": 0,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                time.sleep(0.25)
                continue

            accepted = 0
            for result in results:
                if not allowed_result(result["url"], retailer["domain"]):
                    continue
                title = clean_title(result["title"], retailer["name"])
                if not title:
                    continue
                key = (retailer["name"], normalize_text(row["maker"]), normalize_text(title))
                if key in seen:
                    continue
                seen.add(key)
                accepted += 1
                maker_counts[row["maker"]] = maker_counts.get(row["maker"], 0) + 1
                entries.append(
                    {
                        "retailer": retailer["name"],
                        "maker": row["maker"],
                        "name": title,
                        "retailerUrl": result["url"],
                        "sourceQuery": query,
                        "sourceType": "search-engine-assisted-retailer",
                    }
                )
            retailer_hits.append({"maker": row["maker"], "query": query, "hits": accepted})
            time.sleep(0.25)

        retailer_summaries.append(
            {
                "name": retailer["name"],
                "domain": retailer["domain"],
                "queries": len(query_rows),
                "discoveredEntries": sum(hit.get("hits", 0) for hit in retailer_hits),
                "makers": [
                    {"maker": maker, "discoveredEntries": count}
                    for maker, count in sorted(
                        maker_counts.items(),
                        key=lambda item: (-item[1], normalize_text(item[0])),
                    )
                ],
                "queryLog": retailer_hits,
            }
        )

    entries.sort(key=lambda row: (normalize_text(row["retailer"]), normalize_text(row["maker"]), normalize_text(row["name"])))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "retailersConfigured": len(config.get("retailers", [])),
            "searchQueries": len(query_rows) * len(config.get("retailers", [])),
            "discoveredEntries": len(entries),
        },
        "retailers": retailer_summaries,
        "entries": entries,
    }


def main() -> None:
    payload = discover()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
