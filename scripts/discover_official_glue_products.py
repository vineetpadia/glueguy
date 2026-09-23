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
from urllib.parse import urljoin, urlparse
from typing import Iterable

try:
    import requests
except ImportError:  # Use pip's bundled requests in the managed Python runtime.
    from pip._vendor import requests

if not hasattr(requests, "get"):  # tolerate incomplete local dependency caches
    from pip._vendor import requests as requests


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "autonomous-discovery-config.json"
OUTPUT_PATH = ROOT / "data" / "autonomous-discovered-products.json"
VERIFIED_LEADS_PATH = ROOT / "data" / "verified-major-glue-products.json"

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
            text = response.text
            if "\ufffd" in text and response.apparent_encoding:
                text = response.content.decode(response.apparent_encoding, errors="replace")
            return text
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
    pattern = re.compile(r"""<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>""", re.I | re.S)
    records = []
    for href, inner in pattern.findall(text):
        label = html.unescape(re.sub(r"<[^>]+>", " ", inner))
        records.append({"url": urljoin(url, href), "label": normalize_space(label)})
    return records


def collect_html_link_records_from_text(base_url: str, page: str) -> list[dict]:
    pattern = re.compile(r"""<a\b[^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>""", re.I | re.S)
    records = []
    for href, inner in pattern.findall(page):
        label = html.unescape(re.sub(r"<[^>]+>", " ", inner))
        records.append({"url": urljoin(base_url, html.unescape(href)), "label": normalize_space(label)})
    return records


def extract_tds_links(product_url: str, allowed_domains: list[str] | None = None, timeout: int = TIMEOUT, transport: str = "requests") -> list[dict]:
    """Find official TDS/document PDF links exposed by a product detail page."""
    page = fetch_text(product_url, timeout=timeout, transport=transport)
    results = []
    seen = set()
    for record in collect_html_link_records_from_text(product_url, page):
        label = normalize_space(record.get("label", ""))
        url = record["url"].split("#", 1)[0]
        host = (urlparse(url).hostname or "").lower()
        domains = [domain.lower().lstrip(".") for domain in (allowed_domains or [])]
        if domains and not any(host == domain or host.endswith("." + domain) for domain in domains):
            continue
        searchable = f"{label} {url}".lower()
        if not re.search(r"technical data|technical documentation|\btds\b", searchable):
            continue
        if not (url.lower().split("?", 1)[0].endswith(".pdf") or "getmedia/" in url.lower() or "document" in url.lower()):
            continue
        if url in seen:
            continue
        seen.add(url)
        results.append({"url": url, "label": label or "Technical data sheet"})
    return results


def extract_tds_and_sds_links(product_url: str, allowed_domains: list[str] | None = None, timeout: int = TIMEOUT, transport: str = "requests") -> list[dict]:
    """Find manufacturer-hosted TDS and SDS links while retaining document type."""
    page = fetch_text(product_url, timeout=timeout, transport=transport)
    if "eclecticproducts.com" in (urlparse(product_url).hostname or ""):
        # Eclectic lists sheet names as link text and stores the PDF URL in a
        # separate data attribute, outside ordinary hrefs.
        product_slug = urlparse(product_url).path.rstrip("/").split("/")[-1]
        labels = {
            "e6000-fabri-fuse": "https://eclecticproducts.com/downloads/tds/tds-e6000-fabri-fuse-us-ca-eu-me-arabic-au-nz-mex.pdf",
            "e6000-fray-lock": "https://eclecticproducts.com/downloads/tds/tds-e6000-fray-lock-us-ca-eu-me-arabic-au-nz-mex.pdf",
            "e6000-jewelry-bead": "https://eclecticproducts.com/downloads/tds/tds-e6000-jewelry-and-bead-us-ca-eu-me-au-nz-mex.pdf",
            "e6000-spray-adhesive": "https://eclecticproducts.com/downloads/tds/tds-e6000-sprayadhesive-us-ca-eu-me-au-nz.pdf",
            "e6000-premium": "https://eclecticproducts.com/datasheet/e6000-premium-tds-usa_can_eu_aus-rev-9/",
            "e6000-premium-automotive": "https://eclecticproducts.com/datasheet/e6000-premium-tds-usa_can_eu_aus-rev-9/",
            "e6000-premium-jewelry-and-bead": "https://eclecticproducts.com/datasheet/e6000-premium-tds-usa_can_eu_aus-rev-9/",
            "e6000-premium-with-precision-tips": "https://eclecticproducts.com/datasheet/e6000-premium-tds-usa_can_eu_aus-rev-9/",
            "e6000-jewelry-and-bead": "https://eclecticproducts.com/downloads/tds/tds-e6000-jewelry-and-bead-us-ca-eu-me-au-nz-mex.pdf",
            "e6000-industrial-adhesive": "https://eclecticproducts.com/downloads/tds/e6000-industrial-clear-black-us-can-mex-tds-rev-3.pdf",
            "e6100-industrial-adhesive": "https://eclecticproducts.com/downloads/tds/e6100-industrial-black-gray-white-us-can-mex-tds-5-23-19.pdf",
            "e6800-industrial-adhesive": "https://eclecticproducts.com/downloads/tds/e6800-industrial-clear-usa-tds-rev-2.pdf",
            "e6000-precision-tip-adhesive": "https://eclecticproducts.com/downloads/tds/e6000-industrial-clear-black-us-can-mex-tds-rev-3.pdf",
        }
        manual_url = labels.get(product_slug)
        if manual_url:
            return [{"url": manual_url, "label": f"{product_slug.replace('-', ' ').title()} Technical Data Sheet"}]
    results = []
    seen = set()
    domains = [domain.lower().lstrip(".") for domain in (allowed_domains or [])]
    for record in collect_html_link_records_from_text(product_url, page):
        label = normalize_space(record.get("label", ""))
        url = record["url"].split("#", 1)[0]
        host = (urlparse(url).hostname or "").lower()
        if domains and not any(host == domain or host.endswith("." + domain) for domain in domains):
            continue
        searchable = f"{label} {url}".lower()
        doc_type = "SDS" if re.search(r"\bsds\b|safety data|msds", searchable) else "TDS" if re.search(r"technical data|technical documentation|\btds\b", searchable) else None
        if not doc_type or not (url.lower().split("?", 1)[0].endswith(".pdf") or "getmedia/" in url.lower() or "document" in url.lower()):
            continue
        if url in seen:
            continue
        seen.add(url)
        results.append({"url": url, "label": label or f"{doc_type} document", "documentType": doc_type})
    return results


def extract_titebond_print_tds(product_url: str, timeout: int = TIMEOUT, transport: str = "requests") -> list[dict]:
    """Resolve Titebond's explicit 'Get TDS' link to its printable technical sheet."""
    match = re.search(r"/product/(?:glues|adhesives)/([0-9a-f-]+)", product_url, re.I)
    if not match:
        return []
    print_url = f"https://www.titebond.com/print/product/{match.group(1)}"
    # The manufacturer's product page exposes this route as its Get TDS action.
    return [{"url": print_url, "label": "Titebond Technical Data Sheet", "documentType": "TDS"}]


def extract_tds_catalog_links(source: dict, allowed_domains: list[str], manufacturer_name: str) -> list[dict]:
    """Discover TDS PDFs from explicitly configured official document-library pages.

    A separate catalog is only useful when the PDF's own filename or link label
    identifies a known product. This avoids attaching generic safety PDFs or
    unrelated brand documents to arbitrary products.
    """
    results = []
    seen = set()
    for page_url in source.get("urls", []):
        try:
            if page_url.lower().split("?", 1)[0].endswith(".pdf"):
                records = [{"url": page_url, "label": source.get("labels", {}).get(page_url, "")}]
            else:
                page = fetch_text(page_url, timeout=source.get("requestTimeout", TIMEOUT))
                records = collect_html_link_records_from_text(page_url, page)
        except Exception:
            continue
        for record in records:
            url = record["url"].split("#", 1)[0]
            host = (urlparse(url).hostname or "").lower()
            if not any(host == domain.lower().lstrip(".") or host.endswith("." + domain.lower().lstrip(".")) for domain in allowed_domains):
                continue
            label = normalize_space(record.get("label", ""))
            searchable = f"{label} {url}".lower()
            if not (url.lower().split("?", 1)[0].endswith(".pdf") or "getmedia/" in url.lower()):
                continue
            if not re.search(r"technical data|technical documentation|\btds\b", searchable):
                continue
            identity = url.lower()
            if identity in seen:
                continue
            seen.add(identity)
            results.append({"url": url, "label": label or f"{manufacturer_name} Technical Data Sheet"})
    return results


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
    if strategy == "pidiliteBrandSlug":
        slug = url.rstrip("/").split("/")[-1].lower()
        names = {
            "fevikwik": "Fevikwik",
            "araldite": "Araldite",
            "fevistik-and-fevicolmr": "Fevistik & Fevicol MR",
        }
        return names.get(slug)
    if strategy == "slugTitleCase":
        slug = url.rstrip("/").split("/")[-1].lower()
        words = [word for word in re.split(r"[-_]+", slug) if word]
        if not words:
            return None
        titled = []
        for word in words:
            if re.fullmatch(r"[a-z]{1,4}", word) and word not in {"glue", "bond", "tack", "fast", "foam"}:
                titled.append(word.upper())
            elif re.fullmatch(r"\d+[a-z]*", word):
                titled.append(word.upper())
            else:
                titled.append(word.capitalize())
        return normalize_space(" ".join(titled))
    if strategy == "tamiyaItemSlug":
        match = re.search(r"/products/(\d+)/index\.html", url, re.I)
        return f"Tamiya item {match.group(1)}" if match else None
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

    pattern = re.compile(r'<a[^>]+href=["\']([^"\']+/3M/en_US/p/d(?:c)?/[^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
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


def product_url_identity(value: str | None) -> tuple[str, str] | None:
    if not value:
        return None
    parsed = urlparse(value)
    if not parsed.hostname:
        return None
    path = parsed.path.rstrip("/") or "/"
    return parsed.hostname.lower(), path


def dedupe_entries(entries: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen_names: set[tuple[str, str]] = set()
    seen_urls: set[tuple[str, str]] = set()
    for entry in entries:
        name = entry.get("name")
        if not name:
            continue
        key = (normalize_text(entry.get("maker")), normalize_text(name))
        url_key = product_url_identity(entry.get("officialUrl"))
        if key in seen_names or (url_key and url_key in seen_urls and not entry.get("allowSharedSourceUrl")):
            continue
        seen_names.add(key)
        if url_key:
            seen_urls.add(url_key)
        deduped.append(entry)
    return deduped


def discover() -> dict:
    config = json.loads(CONFIG_PATH.read_text())
    verified_leads = json.loads(VERIFIED_LEADS_PATH.read_text(encoding="utf-8")).get("entries", []) if VERIFIED_LEADS_PATH.exists() else []
    previous = json.loads(OUTPUT_PATH.read_text()) if OUTPUT_PATH.exists() else {}
    previous_entries = previous.get("entries", [])
    previous_tds = {
        (normalize_text(entry.get("maker")), normalize_text(entry.get("name"))): entry
        for entry in previous_entries
        if entry.get("maker") and entry.get("name") and entry.get("tdsDocuments")
    }
    previous_tds_by_url = {
        product_url_identity(entry.get("officialUrl")): entry
        for entry in previous_entries
        if entry.get("officialUrl") and entry.get("tdsDocuments")
    }
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
        manufacturer_entries.extend(entry for entry in verified_leads if normalize_text(entry.get("maker")) == normalize_text(manufacturer.get("name")))
        source_summaries = []
        verified_count = sum(1 for entry in verified_leads if normalize_text(entry.get("maker")) == normalize_text(manufacturer.get("name")))
        if verified_count:
            source_summaries.append({"label": "verified major product and TDS seed", "url": "data/verified-major-glue-products.json", "matchedUrls": verified_count, "discoveredEntries": verified_count})
        for source in manufacturer.get("sources", []):
            include_patterns = compile_patterns(source.get("includeRegex"))
            exclude_patterns = compile_patterns(source.get("excludeRegex"))
            require_patterns = compile_patterns(source.get("requireRegex"))
            name_require_patterns = compile_patterns(source.get("nameRequireRegex"))
            name_exclude_patterns = compile_patterns(source.get("nameExcludeRegex"))
            try:
                manual_products = source.get("manualProducts", [])
                if manual_products:
                    manual_entries = []
                    for product in manual_products:
                        name = normalize_space(product.get("name"))
                        if not name:
                            continue
                        record = {
                            "maker": manufacturer["name"],
                            "name": name,
                            "officialUrl": product.get("officialUrl") or source["url"],
                            "kind": product.get("kind", source.get("kind", "product")),
                            "sourceLabel": source.get("label"),
                            "allowSharedSourceUrl": True,
                        }
                        if product.get("technicalDocuments"):
                            record["technicalDocuments"] = product["technicalDocuments"]
                        if product.get("tdsDocuments"):
                            record["tdsDocuments"] = product["tdsDocuments"]
                        manual_entries.append(record)
                    manufacturer_entries.extend(manual_entries)
                    source_summaries.append({
                        "label": source.get("label"),
                        "url": source["url"],
                        "matchedUrls": len(manual_entries),
                        "discoveredEntries": len(manual_entries),
                    })
                    continue
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
                    records = []
                    for page_url in [source["url"], *source.get("additionalUrls", [])]:
                        page_timeout = timeout
                        if "eclecticproducts.com" in page_url:
                            # Eclectic's E6000 brand page needs longer than the
                            # general adhesive catalog on its WordPress host.
                            page_timeout = max(timeout, 30)
                        records.extend(
                            collect_html_link_records(
                                page_url,
                                timeout=page_timeout,
                                transport=transport,
                                stream=stream,
                                extra_headers=extra_headers,
                            )
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
                        if source.get("nameStrategy") == "loctiteCentralPdpSlug" and "central-pdp.html" not in record["url"].lower():
                            name = clean_title(record["label"], manufacturer["name"])
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
                if source.get("extractor") == "liquid_nails_catalog":
                    records = collect_html_link_records(source["url"], timeout=timeout, transport=transport, stream=stream, extra_headers=extra_headers)
                    source_entries = []
                    for record in records:
                        if not re.search(r"liquid-nails-products/|/products/adhesives-sealants/", record["url"], re.I):
                            continue
                        name = derive_name_from_label(record.get("label", ""), "Liquid Nails")
                        if not name or re.search(r"caulk|sealant|remover|accessory|roof repair", name, re.I):
                            continue
                        source_entries.append({"maker": manufacturer["name"], "name": name, "officialUrl": record["url"], "kind": source.get("kind", "product"), "sourceLabel": source.get("label")})
                    manufacturer_entries.extend(source_entries[:int(source.get("maxUrls", 150))])
                    source_summaries.append({"label": source.get("label"), "url": source["url"], "matchedUrls": len(source_entries), "discoveredEntries": len(source_entries[:int(source.get("maxUrls", 150))])})
                    continue
                if source.get("extractor") == "dap_adhesives_catalog":
                    page = fetch_text(source["url"], timeout=timeout, transport=transport, stream=stream, extra_headers=extra_headers)
                    records = collect_html_link_records_from_text(source["url"], page)
                    if not records:
                        pattern = re.compile(r'<a[^>]+href=["\']([^"\']*/products/adhesives/[^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
                        records = [{"url": urljoin(source["url"], href), "label": normalize_space(html.unescape(re.sub(r"<[^>]+>", " ", label)))} for href, label in pattern.findall(page)]
                    if not records:
                        labels = re.findall(r"(?:<h[1-6][^>]*>|data-title=[\"'])([^<\"']*(?:RapidFuse|Weldwood|DAP Adhesive)[^<\"']*)", page, re.I)
                        records = [{"url": source["url"], "label": label, "allowSharedSourceUrl": True} for label in labels]
                    source_entries = []
                    for record in records:
                        if not allowed_url(record["url"], include_patterns, exclude_patterns, require_patterns):
                            continue
                        name = derive_name_from_label(record.get("label", ""), manufacturer["name"])
                        if not name or not allowed_name(name, name_require_patterns, name_exclude_patterns):
                            continue
                        source_entries.append({"maker": manufacturer["name"], "name": name, "officialUrl": record["url"], "kind": source.get("kind", "product"), "sourceLabel": source.get("label"), "allowSharedSourceUrl": record.get("allowSharedSourceUrl", False)})
                    manufacturer_entries.extend(source_entries[:int(source.get("maxUrls", 150))])
                    source_summaries.append({"label": source.get("label"), "url": source["url"], "matchedUrls": len(records), "discoveredEntries": len(source_entries[:int(source.get("maxUrls", 150))])})
                    continue
                if source.get("extractor") == "3m_search_products":
                    page = fetch_text(source["url"], timeout=timeout, transport=transport, stream=stream, extra_headers=extra_headers)
                    records = collect_html_link_records_from_text(source["url"], page)
                    if not records:
                        pattern = re.compile(r'<a[^>]+href="([^"]*/3M/en_US/p/d(?:c)?/[^\"]+)"[^>]*>(.*?)</a>', re.I | re.S)
                        records = [{"url": urljoin(source["url"], href), "label": normalize_space(html.unescape(re.sub(r"<[^>]+>", " ", label)))} for href, label in pattern.findall(page)]
                    source_entries = []
                    for record in records:
                        if not allowed_url(record["url"], include_patterns, exclude_patterns, require_patterns):
                            continue
                        name = derive_name_from_label(record.get("label", ""), manufacturer["name"])
                        if not name or not allowed_name(name, name_require_patterns, name_exclude_patterns):
                            continue
                        source_entries.append({"maker": manufacturer["name"], "name": name, "officialUrl": record["url"], "kind": source.get("kind", "product"), "sourceLabel": source.get("label")})
                    manufacturer_entries.extend(source_entries[:int(source.get("maxUrls", 100))])
                    source_summaries.append({"label": source.get("label"), "url": source["url"], "matchedUrls": len(records), "discoveredEntries": len(source_entries[:int(source.get("maxUrls", 100))])})
                    continue
                if source.get("extractor") == "loctite_products":
                    records = collect_html_link_records(source["url"], timeout=timeout, transport=transport, stream=stream, extra_headers=extra_headers)
                    source_entries = []
                    for record in records:
                        if not allowed_url(record["url"], include_patterns, exclude_patterns, require_patterns):
                            continue
                        name = derive_name_from_url(record["url"], "loctiteCentralPdpSlug")
                        if not name:
                            name = derive_name_from_label(record.get("label", ""), manufacturer["name"])
                        if name and allowed_name(name, name_require_patterns, name_exclude_patterns):
                            source_entries.append({"maker": manufacturer["name"], "name": name, "officialUrl": record["url"], "kind": source.get("kind", "product"), "sourceLabel": source.get("label")})
                    manufacturer_entries.extend(source_entries[:int(source.get("maxUrls", 100))])
                    source_summaries.append({"label": source.get("label"), "url": source["url"], "matchedUrls": len(records), "discoveredEntries": len(source_entries[:int(source.get("maxUrls", 100))])})
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
        tds_catalog_documents = []
        tds_catalog = manufacturer.get("tdsCatalog")
        if tds_catalog:
            tds_catalog_documents = extract_tds_catalog_links(tds_catalog, manufacturer.get("officialDomains", []), manufacturer["name"])
            for entry in deduped:
                product_tokens = [normalize_text(token) for token in re.findall(r"[A-Za-z0-9]+", entry.get("name", "")) if len(token) >= 4]
                matched = []
                for document in tds_catalog_documents:
                    document_text = normalize_text(f"{document['label']} {document['url']}")
                    meaningful_tokens = [token for token in product_tokens if token not in {"pritt", "glue", "adhesive", "technical", "datasheet", "tds"}]
                    exact_candidates = [token for token in meaningful_tokens if token in {"stick", "pads"}]
                    if exact_candidates and any(token in document_text for token in exact_candidates):
                        matched.append(document)
                    elif not exact_candidates and meaningful_tokens and any(token in document_text for token in meaningful_tokens):
                        matched.append(document)
                if matched:
                    existing = {document.get("url") for document in entry.get("tdsDocuments", [])}
                    entry.setdefault("tdsDocuments", []).extend(document for document in matched if document.get("url") not in existing)
        tds_documents_found = 0
        if any(source.get("extractTdsLinks") for source in manufacturer.get("sources", [])):
            tds_source = next(source for source in manufacturer["sources"] if source.get("extractTdsLinks"))
            max_pages = int(tds_source.get("tdsMaxPages", 20))
            for entry in deduped[:max_pages]:
                try:
                    link_extractor = extract_tds_and_sds_links if tds_source.get("includeSds") else extract_tds_links
                    found_documents = link_extractor(
                        entry["officialUrl"],
                        allowed_domains=manufacturer.get("officialDomains", []),
                        timeout=tds_source.get("requestTimeout", TIMEOUT),
                        transport=tds_source.get("transport", "requests"),
                    )
                    existing_tds_documents = list(entry.get("tdsDocuments", []))
                    discovered_tds_documents = [document for document in found_documents if document.get("documentType") != "SDS"]
                    if tds_source.get("extractTitebondPrintTds"):
                        discovered_tds_documents.extend(extract_titebond_print_tds(
                            entry["officialUrl"],
                            timeout=tds_source.get("requestTimeout", TIMEOUT),
                            transport=tds_source.get("transport", "requests"),
                        ))
                    entry["tdsDocuments"] = list({
                        document.get("url"): document
                        for document in [*existing_tds_documents, *discovered_tds_documents]
                        if document.get("url")
                    }.values())
                    safety_documents = [document for document in found_documents if document.get("documentType") == "SDS"]
                    if safety_documents:
                        entry["technicalDocuments"] = safety_documents
                    tds_documents_found += len(entry["tdsDocuments"])
                except Exception as exc:  # noqa: BLE001
                    entry["tdsDiscoveryError"] = f"{type(exc).__name__}: {exc}"
                time.sleep(float(tds_source.get("tdsRequestIntervalSeconds", 0.15)))
        for entry in deduped:
            key = (normalize_text(entry.get("maker")), normalize_text(entry.get("name")))
            previous_entry = previous_tds.get(key) or previous_tds_by_url.get(
                product_url_identity(entry.get("officialUrl"))
            )
            if previous_entry:
                documents = [
                    *entry.get("tdsDocuments", []),
                    *previous_entry.get("tdsDocuments", []),
                ]
                seen_documents = set()
                merged_documents = []
                for document in documents:
                    url = document.get("url")
                    if url and url not in seen_documents:
                        seen_documents.add(url)
                        merged_documents.append(document)
                entry["tdsDocuments"] = merged_documents
            entry["priority"] = manufacturer.get("priority", "medium")
            entry["officialDomains"] = manufacturer.get("officialDomains", [])
        discovered.extend(deduped)
        manufacturers_summary.append(
            {
                "name": manufacturer["name"],
                "priority": manufacturer.get("priority", "medium"),
                "officialDomains": manufacturer.get("officialDomains", []),
                "discoveredEntries": len(deduped),
                "tdsDocumentsDiscovered": tds_documents_found,
                "tdsCatalogDocumentsFound": len(tds_catalog_documents),
                "sources": source_summaries,
            }
        )

    discovered_by_key = {
        (normalize_text(entry.get("maker")), normalize_text(entry.get("name"))): entry
        for entry in discovered
    }
    discovered_by_url = {
        product_url_identity(entry.get("officialUrl")): entry
        for entry in discovered
        if entry.get("officialUrl")
    }
    preserved_previous_entries = 0
    preserved_tds_entries = 0
    for entry in previous_entries:
        key = (normalize_text(entry.get("maker")), normalize_text(entry.get("name")))
        url_key = product_url_identity(entry.get("officialUrl"))
        current = discovered_by_key.get(key) or (discovered_by_url.get(url_key) if url_key else None)
        if current is None:
            discovered.append(entry)
            discovered_by_key[key] = entry
            if url_key:
                discovered_by_url[url_key] = entry
            preserved_previous_entries += 1
            if entry.get("tdsDocuments"):
                preserved_tds_entries += 1
            continue
        if entry.get("tdsDocuments") or entry.get("technicalDocuments"):
            documents = [*current.get("tdsDocuments", []), *entry.get("tdsDocuments", [])]
            seen_documents = set()
            current["tdsDocuments"] = []
            for document in documents:
                document_url = document.get("url")
                if document_url and document_url not in seen_documents:
                    seen_documents.add(document_url)
                    current["tdsDocuments"].append(document)
        if entry.get("technicalDocuments"):
            documents = [*current.get("technicalDocuments", []), *entry.get("technicalDocuments", [])]
            current["technicalDocuments"] = list({doc.get("url"): doc for doc in documents if doc.get("url")}.values())

    discovered.sort(key=lambda entry: (normalize_text(entry["maker"]), normalize_text(entry["name"])))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "manufacturersConfigured": len(config.get("manufacturers", [])),
            "discoveredEntries": len(discovered),
            "tdsDocumentsDiscovered": sum(item.get("tdsDocumentsDiscovered", 0) for item in manufacturers_summary),
            "tdsDocumentsLinked": sum(len(entry.get("tdsDocuments", [])) for entry in discovered),
            "technicalDocumentsLinked": sum(len(entry.get("technicalDocuments", [])) for entry in discovered),
            "previousEntriesPreserved": preserved_previous_entries,
            "previousTdsEntriesPreserved": preserved_tds_entries,
        },
        "manufacturers": manufacturers_summary,
        "entries": discovered,
    }


def main() -> None:
    payload = discover()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
