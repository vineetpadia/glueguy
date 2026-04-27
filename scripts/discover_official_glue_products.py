#!/usr/bin/env python3
"""Discover official adhesive product leads from manufacturer sitemap or HTML surfaces."""

from __future__ import annotations

import html
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
from urllib.parse import urljoin
from typing import Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "autonomous-discovery-config.json"
OUTPUT_PATH = ROOT / "data" / "autonomous-discovered-products.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 20
RETRY_STATUSES = {429, 500, 502, 503, 504}


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_space(value).lower())


def compile_patterns(values: Iterable[str] | None) -> list[re.Pattern[str]]:
    return [re.compile(value, re.I) for value in values or []]


def fetch_text(
    url: str,
    timeout: int = TIMEOUT,
    retries: int = 3,
    transport: str = "requests",
    stream: bool = False,
    extra_headers: dict | None = None,
) -> str:
    if transport == "curl":
        for attempt in range(retries):
            result = subprocess.run(
                ["curl", "-L", "--max-time", str(timeout), "-A", HEADERS["User-Agent"], "-s", url],
                capture_output=True,
                text=True,
            )
            if result.stdout:
                return result.stdout
            if attempt + 1 < retries:
                time.sleep(0.75 * (attempt + 1))
                continue
            message = result.stderr.strip() or f"curl exit {result.returncode}"
            raise RuntimeError(f"curl fetch failed for {url}: {message}")

    last_error: Exception | None = None
    for attempt in range(retries):
        response = None
        try:
            headers = {**HEADERS, **(extra_headers or {})}
            response = requests.get(url, headers=headers, timeout=timeout, stream=stream)
            response.raise_for_status()
            if stream:
                chunks = []
                total = 0
                for chunk in response.iter_content(chunk_size=16384, decode_unicode=True):
                    if not chunk:
                        continue
                    chunks.append(chunk)
                    total += len(chunk)
                    if total >= 262144:
                        break
                return "".join(chunks)
            return response.text
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if response is not None and getattr(response, "status_code", None) not in RETRY_STATUSES:
                raise
            if attempt + 1 < retries:
                time.sleep(0.75 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def collect_html_links(
    url: str,
    timeout: int = TIMEOUT,
    transport: str = "requests",
    stream: bool = False,
    extra_headers: dict | None = None,
) -> list[str]:
    text = fetch_text(url, timeout=timeout, transport=transport, stream=stream, extra_headers=extra_headers)
    matches = re.findall(r'href="([^"]+)"', text)
    return [urljoin(url, match) for match in matches]


def collect_html_link_records(
    url: str,
    timeout: int = TIMEOUT,
    transport: str = "requests",
    stream: bool = False,
    extra_headers: dict | None = None,
) -> list[dict]:
    text = fetch_text(url, timeout=timeout, transport=transport, stream=stream, extra_headers=extra_headers)
    pattern = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    records = []
    for href, inner in pattern.findall(text):
        label = html.unescape(re.sub(r"<[^>]+>", " ", inner))
        records.append({"url": urljoin(url, href), "label": normalize_space(label)})
    return records


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def parse_xml_locs(xml_text: str) -> tuple[str, list[str]]:
    root = ET.fromstring(xml_text)
    kind = local_name(root.tag)
    locs = []
    for child in root.iter():
        if local_name(child.tag) == "loc" and child.text:
            locs.append(child.text.strip())
    return kind, locs


def collect_sitemap_urls(url: str, max_sitemaps: int = 24, timeout: int = TIMEOUT, transport: str = "requests") -> list[str]:
    pending = [url]
    seen = set()
    collected: list[str] = []

    while pending and len(seen) < max_sitemaps:
        current = pending.pop(0)
        if current in seen:
            continue
        seen.add(current)
        kind, locs = parse_xml_locs(fetch_text(current, timeout=timeout, transport=transport))
        if kind == "sitemapindex":
            pending.extend(loc for loc in locs if loc not in seen)
        else:
            collected.extend(locs)
    return collected


def html_title(text: str) -> str | None:
    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    if not title:
        return None
    return normalize_space(html.unescape(re.sub(r"<[^>]+>", " ", title.group(1))))


def html_h1(text: str) -> str | None:
    heading = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    if not heading:
        return None
    return normalize_space(html.unescape(re.sub(r"<[^>]+>", " ", heading.group(1))))


def clean_title(value: str, maker: str) -> str:
    cleaned = normalize_space(value)
    suffixes = [
        " | MasterBond.com",
        " - Permabond",
        " | J-B Weld",
        " | 3M United States",
        " | Sika",
        " | Sika USA",
        " | Sika Group",
    ]
    for suffix in suffixes:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    cleaned = re.sub(r"\s*[\-|:]\s*" + re.escape(maker) + r"$", "", cleaned, flags=re.I)
    cleaned = cleaned.replace("&#8211;", "-")
    return normalize_space(cleaned)


def derive_name_from_url(url: str, strategy: str) -> str | None:
    if strategy == "permabondTdsSlug":
        slug = url.rstrip("/").split("/")[-1].lower()
        slug = re.sub(r"_tds.*$", "", slug)
        slug = slug.replace("_", " ").replace("-", " ")
        tokens = [token.upper() for token in slug.split() if token and token not in {"english"}]
        if not tokens:
            return None
        return normalize_space(" ".join(tokens))
    if strategy == "loctiteCentralPdpSlug":
        match = re.search(r"/products/central-pdp\.html/([^/]+)/", url, re.I)
        if not match:
            return None
        slug = match.group(1).strip().lower()
        words = [word for word in slug.split("-") if word]
        if not words:
            return None
        titled = []
        for word in words:
            if word == "loctite":
                titled.append("Loctite")
            elif re.fullmatch(r"\d+[a-z]*", word):
                titled.append(word.upper())
            else:
                titled.append(word.capitalize())
        return normalize_space(" ".join(titled))
    return None


def derive_name_from_label(label: str, maker: str) -> str | None:
    return clean_title(label, maker) or None


def derive_name_from_page(url: str, maker: str, timeout: int = TIMEOUT, transport: str = "requests") -> str | None:
    text = fetch_text(url, timeout=timeout, transport=transport)
    return clean_title(html_h1(text) or html_title(text) or "", maker) or None


def allowed_url(
    url: str,
    include_patterns: list[re.Pattern[str]],
    exclude_patterns: list[re.Pattern[str]],
    require_patterns: list[re.Pattern[str]],
) -> bool:
    if include_patterns and not any(pattern.search(url) for pattern in include_patterns):
        return False
    if any(pattern.search(url) for pattern in exclude_patterns):
        return False
    if require_patterns and not any(pattern.search(url) for pattern in require_patterns):
        return False
    return True


def build_entry(manufacturer: dict, source: dict, url: str) -> dict | None:
    strategy = source.get("nameStrategy", "title")
    timeout = source.get("requestTimeout", TIMEOUT)
    transport = source.get("transport", "requests")
    try:
        if strategy == "title":
            name = derive_name_from_page(url, manufacturer["name"], timeout=timeout, transport=transport)
        else:
            name = derive_name_from_url(url, strategy)
    except Exception as exc:  # noqa: BLE001
        return {
            "maker": manufacturer["name"],
            "name": None,
            "officialUrl": url,
            "kind": source.get("kind", "product"),
            "sourceLabel": source.get("label"),
            "error": f"{type(exc).__name__}: {exc}",
        }

    if not name:
        return None

    return {
        "maker": manufacturer["name"],
        "name": name,
        "officialUrl": url,
        "kind": source.get("kind", "product"),
        "sourceLabel": source.get("label"),
    }


def allowed_name(
    name: str,
    require_patterns: list[re.Pattern[str]],
    exclude_patterns: list[re.Pattern[str]],
) -> bool:
    if require_patterns and not any(pattern.search(name) for pattern in require_patterns):
        return False
    if any(pattern.search(name) for pattern in exclude_patterns):
        return False
    return True


def extract_3m_adhesives_category(source: dict, manufacturer: dict) -> list[dict]:
    headers = {**HEADERS, **(source.get("headers") or {})}
    text = ""
    timeout = source.get("requestTimeout", TIMEOUT)

    # 3M's broad adhesives landing page intermittently stalls or fails HTTP/2
    # negotiation on this host. Prefer fetchable product category pages and
    # accept the first real page body from several transports.
    try:
        response = requests.get(source["url"], headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=16384, decode_unicode=True):
            if not chunk:
                continue
            chunks.append(chunk)
            total += len(chunk)
            if total >= 262144:
                break
        text = "".join(chunks)
    except Exception:  # noqa: BLE001
        text = ""

    if not text:
        try:
            request = urllib.request.Request(source["url"], headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                text = response.read(262144).decode("utf-8", "ignore")
        except Exception:  # noqa: BLE001
            text = ""

    if not text:
        try:
            result = subprocess.run(
                [
                    "curl",
                    "--http1.1",
                    "-L",
                    "--max-time",
                    str(timeout),
                    "-A",
                    HEADERS["User-Agent"],
                    "-H",
                    "Accept-Encoding: identity",
                    "-s",
                    source["url"],
                ],
                capture_output=True,
                text=True,
            )
            text = result.stdout[:262144]
        except Exception:  # noqa: BLE001
            text = ""

    if not text:
        raise TimeoutError("Could not fetch 3M adhesives category with requests, urllib, or curl")

    include_patterns = compile_patterns(source.get("includeRegex"))
    exclude_patterns = compile_patterns(source.get("excludeRegex"))
    require_patterns = compile_patterns(source.get("requireRegex"))
    name_require_patterns = compile_patterns(source.get("nameRequireRegex"))
    name_exclude_patterns = compile_patterns(source.get("nameExcludeRegex"))

    pattern = re.compile(r'<a[^>]+href="([^"]+/3M/en_US/p/d(?:c)?/[^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    entries = []
    seen_urls = set()
    for href, inner in pattern.findall(text):
        url = urljoin(source["url"], href)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        label = html.unescape(re.sub(r"<[^>]+>", " ", inner))
        label = normalize_space(label)
        if not label:
            continue
        if not allowed_url(url, include_patterns, exclude_patterns, require_patterns):
            continue
        if not allowed_name(label, name_require_patterns, name_exclude_patterns):
            continue
        entries.append(
            {
                "maker": manufacturer["name"],
                "name": clean_title(label, manufacturer["name"]),
                "officialUrl": url,
                "kind": source.get("kind", "product"),
                "sourceLabel": source.get("label"),
            }
        )
        if source.get("maxUrls") and len(entries) >= int(source["maxUrls"]):
            break
    return entries


def dedupe_entries(entries: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        name = entry.get("name")
        if not name:
            continue
        key = (normalize_text(entry["maker"]), normalize_text(name))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def discover() -> dict:
    config = json.loads(CONFIG_PATH.read_text())
    discovered: list[dict] = []
    manufacturers_summary = []
    manufacturers = sorted(
        config.get("manufacturers", []),
        key=lambda manufacturer: (
            0 if normalize_text(manufacturer.get("name")) == "3m" else 1,
            manufacturer.get("priority", "medium"),
            manufacturer.get("name", ""),
        ),
    )

    for manufacturer in manufacturers:
        manufacturer_entries: list[dict] = []
        source_summaries = []
        for source in manufacturer.get("sources", []):
            include_patterns = compile_patterns(source.get("includeRegex"))
            exclude_patterns = compile_patterns(source.get("excludeRegex"))
            require_patterns = compile_patterns(source.get("requireRegex"))
            name_require_patterns = compile_patterns(source.get("nameRequireRegex"))
            name_exclude_patterns = compile_patterns(source.get("nameExcludeRegex"))
            try:
                timeout = source.get("requestTimeout", TIMEOUT)
                transport = source.get("transport", "requests")
                stream = bool(source.get("stream"))
                extra_headers = source.get("headers")
                if source.get("extractor") == "3m_adhesives_category":
                    source_entries = extract_3m_adhesives_category(source, manufacturer)
                    manufacturer_entries.extend(source_entries)
                    source_summaries.append(
                        {
                            "label": source.get("label"),
                            "url": source["url"],
                            "matchedUrls": len(source_entries),
                            "discoveredEntries": len(source_entries),
                        }
                    )
                    continue
                if source.get("sourceType") == "html" and source.get("nameStrategy") == "linkText":
                    records = collect_html_link_records(
                        source["url"],
                        timeout=timeout,
                        transport=transport,
                        stream=stream,
                        extra_headers=extra_headers,
                    )
                    filtered_records = [
                        record
                        for record in records
                        if allowed_url(record["url"], include_patterns, exclude_patterns, require_patterns)
                    ]
                    if source.get("maxUrls"):
                        filtered_records = filtered_records[: int(source["maxUrls"])]
                    source_entries = []
                    for record in filtered_records:
                        name = derive_name_from_label(record["label"], manufacturer["name"])
                        if name and allowed_name(name, name_require_patterns, name_exclude_patterns):
                            source_entries.append(
                                {
                                    "maker": manufacturer["name"],
                                    "name": name,
                                    "officialUrl": record["url"],
                                    "kind": source.get("kind", "product"),
                                    "sourceLabel": source.get("label"),
                                }
                            )
                    manufacturer_entries.extend(source_entries)
                    source_summaries.append(
                        {
                            "label": source.get("label"),
                            "url": source["url"],
                            "matchedUrls": len(filtered_records),
                            "discoveredEntries": len(source_entries),
                        }
                    )
                    continue
                if source.get("sourceType") == "html":
                    urls = collect_html_links(
                        source["url"],
                        timeout=timeout,
                        transport=transport,
                        stream=stream,
                        extra_headers=extra_headers,
                    )
                else:
                    urls = collect_sitemap_urls(source["url"], timeout=timeout, transport=transport)
                filtered_urls = [
                    url for url in urls if allowed_url(url, include_patterns, exclude_patterns, require_patterns)
                ]
                if source.get("maxUrls"):
                    filtered_urls = filtered_urls[: int(source["maxUrls"])]
                source_entries = []
                for url in filtered_urls:
                    entry = build_entry(manufacturer, source, url)
                    if entry and allowed_name(entry["name"], name_require_patterns, name_exclude_patterns):
                        source_entries.append(entry)
                manufacturer_entries.extend(source_entries)
                source_summaries.append(
                    {
                        "label": source.get("label"),
                        "url": source["url"],
                        "matchedUrls": len(filtered_urls),
                        "discoveredEntries": len([entry for entry in source_entries if entry.get("name")]),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                source_summaries.append(
                    {
                        "label": source.get("label"),
                        "url": source["url"],
                        "matchedUrls": 0,
                        "discoveredEntries": 0,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

        deduped = dedupe_entries(manufacturer_entries)
        for entry in deduped:
            entry["priority"] = manufacturer.get("priority", "medium")
            entry["officialDomains"] = manufacturer.get("officialDomains", [])
        discovered.extend(deduped)
        manufacturers_summary.append(
            {
                "name": manufacturer["name"],
                "priority": manufacturer.get("priority", "medium"),
                "officialDomains": manufacturer.get("officialDomains", []),
                "discoveredEntries": len(deduped),
                "sources": source_summaries,
            }
        )

    discovered.sort(key=lambda entry: (normalize_text(entry["maker"]), normalize_text(entry["name"])))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "manufacturersConfigured": len(config.get("manufacturers", [])),
            "discoveredEntries": len(discovered),
        },
        "manufacturers": manufacturers_summary,
        "entries": discovered,
    }


def main() -> None:
    payload = discover()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
