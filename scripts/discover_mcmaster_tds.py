#!/usr/bin/env python3
"""Discover official TDS links for McMaster adhesive families.

The raw McMaster crawl gives reliable commercial package data, while this
script resolves official manufacturer technical datasheets wherever possible.
It records a family-level lookup keyed by McMaster ``family_key`` so the site
build can prefer manufacturer documentation over search-engine fallbacks.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "mcmaster-glues.json"
DETAILS_PATH = ROOT / "data" / "mcmaster-product-details.json"
OUTPUT_PATH = ROOT / "data" / "mcmaster-tds-links.json"
OVERRIDES_PATH = ROOT / "data" / "official-tds-overrides.json"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
REQUEST_TIMEOUT = 12
HENKEL_GRAPHQL_URL = "https://s-weu-prd-raqnsp-apim.azure-api.net/raqnsearch/raqnsearch"
HENKEL_SUBSCRIPTION_KEY = "b39cabbd48aa44139b319eba6674a36d"

CANONICAL_MAKERS = {
    "Loctite": ["loctite", "loctite superflex silicone", "loctite retaining compounds"],
    "3M": ["3m", "3m scotch-weld", "3m polyurethane", "3m hybrid polymer"],
    "Permabond": ["permabond"],
    "Sika": ["sika", "sikaflex"],
    "Plexus": ["plexus"],
    "Devcon": ["devcon"],
    "Momentive": ["momentive", "ge silicone"],
    "Dow": ["dow corning", "dowsil"],
    "Vibra-Tite": ["vibra-tite"],
    "J-B Weld": ["j-b weld", "jb weld", "kwikweld"],
    "Gorilla": ["gorilla"],
    "SciGrip": ["scigrip", "weld-on"],
    "Pliobond": ["pliobond"],
    "Liquid Nails": ["liquid nails"],
    "Permatex": ["permatex"],
    "Elmer's": ["elmer"],
}

MAKER_CONFIG = {
    "Loctite": {
        "strategy": "henkel",
        "domains": ["datasheets.tdx.henkel.com", "henkel-adhesives.com", "next.henkel-adhesives.com"],
    },
    "3M": {
        "strategy": "3m-search",
        "domains": ["3m.com", "multimedia.3m.com", "3mcanada.ca", "3m.co.uk"],
    },
    "Permabond": {
        "strategy": "permabond",
        "domains": ["permabond.com"],
    },
    "Sika": {
        "strategy": "sika-direct",
        "domains": ["sika.com", "usa.sika.com", "industry.sika.com"],
    },
    "Plexus": {
        "strategy": "itw-search",
        "domains": ["itwperformancepolymers.com"],
    },
    "Devcon": {
        "strategy": "itw-search",
        "domains": ["itwperformancepolymers.com"],
    },
    "Momentive": {
        "strategy": "momentive-sitemap",
        "domains": ["momentive.com"],
    },
    "Dow": {
        "strategy": "bing",
        "domains": ["dow.com"],
    },
    "Vibra-Tite": {
        "strategy": "bing",
        "domains": ["vibra-tite.com"],
    },
    "J-B Weld": {
        "strategy": "jbweld-products",
        "domains": ["jbweld.com"],
    },
    "Gorilla": {
        "strategy": "gorilla-sitemap",
        "domains": ["gorillatough.com"],
    },
    "SciGrip": {
        "strategy": "scigrip-sitemap",
        "domains": ["scigrip.com", "scigripadhesives.com", "ipsadhesives.com"],
    },
    "Pliobond": {
        "strategy": "bing",
        "domains": ["pliobondadhesives.com"],
    },
    "Liquid Nails": {
        "strategy": "liquid-nails-algolia",
        "domains": ["liquidnails.com", "ppgpaints.com"],
    },
    "Permatex": {
        "strategy": "permatex-sitemap",
        "domains": ["permatex.com"],
    },
    "Elmer's": {
        "strategy": "bing",
        "domains": ["elmers.com"],
    },
}

GENERIC_MAKER_TOKENS = {
    "",
    "<none>",
    "adhesives with ten mixing sticks",
    "ceramic",
    "epoxy",
    "polyether",
    "polymer",
    "hybrid polymer",
    "silicone",
    "other hot glue",
    "other threadlockers",
    "wood glue",
    "each",
    "buna-n",
    "calcium carbonate",
    "viton fluoroelastomer",
    "acrylic",
}

PERMABOND_ARCHIVE_URL = "https://permabond.com/tds/"
SCIGRIP_SITEMAP_URL = "https://scigripadhesives.com/page-sitemap.xml"
PERMATEX_SITEMAP_URL = "https://www.permatex.com/product-sitemap.xml"
GORILLA_SITEMAP_URL = "https://gorillatough.com/sitemap.xml"
MOMENTIVE_SITEMAP_URL = "https://www.momentive.com/sitemap.xml"
LIQUID_NAILS_ALGOLIA_APP_ID = "RG6LZNMOGC"
LIQUID_NAILS_ALGOLIA_KEY = "ef45d97ef63234f4c54db0c45d3578a8"
LIQUID_NAILS_ALGOLIA_INDEX = "prd_MBProducts"

MOMENTIVE_DIRECT_PDFS = {
    "frv1106": "https://www.momentive.com/content/dam/momentive/en-us/products/tds/snapsil/SNAPSIL%20FRV1106%20Adhesive%20Sealant.pdf",
    "rtv230": "https://www.momentive.com/content/dam/momentive/en-us/products/tds/snapsil/SNAPSIL%E2%84%A2%20RTV230.pdf",
    "rtv157": "https://www.momentive.com/content/dam/momentive/en-us/products/tds/snapsil/snapsil-rtv157-rtv159.pdf",
    "rtv159": "https://www.momentive.com/content/dam/momentive/en-us/products/tds/snapsil/snapsil-rtv157-rtv159.pdf",
}
MOMENTIVE_RTV100_TOKENS = {
    "rtv102",
    "rtv103",
    "rtv106",
    "rtv108",
    "rtv109",
    "rtv116",
    "rtv118",
}
MOMENTIVE_RTV100_PDF = "https://www.momentive.com/content/dam/momentive/global/docs/default-source/tds/snapsil/snapsil-rtv100-series-tds.pdf"

JBWELD_SLUG_HINTS = {
    "clearweld": "/product/clearweld-syringe",
    "kwikweld": "/product/kwikweld-syringe",
    "marineweld": "/product/marineweld-syringe",
    "plastic bonder": "/product/plastic-bonder-syringe",
    "plasticweld": "/product/plasticweld-syringe",
    "waterweld": "/product/waterweld-epoxy-putty",
    "highheat": "/product/highheat-epoxy-putty",
    "steelstik": "/product/steelstik-epoxy-putty-stick",
    "steelstik structural": "/product/steelstik-epoxy-putty-stick",
    "original": "/product/j-b-weld-twin-tube",
    "cold-weld": "/product/j-b-weld-twin-tube",
}
HENKEL_SITE = {
    "tenant": "adhesive/pro-now",
    "country": "us",
    "language": "en",
    "tabConfigs": [
        {"name": "Products", "types": [{"type": "PAGE_TYPE", "values": ["product"]}]},
        {
            "name": "Technical documents",
            "types": [
                {"type": "PRODUCT_DOCUMENT", "values": ["tds", "sds", "rohs", "rds"]},
                {"type": "DAM_DOCUMENT", "values": ["damDocument"]},
            ],
        },
        {
            "name": "Resources",
            "types": [
                {
                    "type": "PAGE_TYPE",
                    "values": [
                        "article",
                        "articlesWithComments",
                        "brochure",
                        "caseStudies",
                        "eBook",
                        "events",
                        "researchReport",
                        "webinars",
                        "whitePapers",
                    ],
                }
            ],
        },
        {
            "name": "All",
            "types": [
                {
                    "type": "PAGE_TYPE",
                    "values": [
                        "article",
                        "brochure",
                        "caseStudies",
                        "content",
                        "eBook",
                        "product",
                        "researchReport",
                        "webinars",
                        "whitePapers",
                    ],
                },
                {"type": "PRODUCT_DOCUMENT", "values": ["tds", "sds", "rohs", "rds"]},
                {"type": "DAM_DOCUMENT", "values": ["damDocument"]},
            ],
        },
    ],
    "damFilter": {"language": "en"},
}

HENKEL_QUERY = """
query Search(
  $term: String
  $offset: Int!
  $size: Int
  $sort: RaqnwebSort
  $site: RaqnwebSite!
  $tab: String
) {
  raqnwebSearch(
    term: $term
    offset: $offset
    size: $size
    sort: $sort
    site: $site
    tab: $tab
  ) {
    resultCount
    results {
      __typename
      ... on ProductTdsSearchResult {
        title
        url
        documentLanguage
        snippet
        productFields {
          productName
          productKnownAs
        }
      }
      ... on ProductVariantDocumentSearchResult {
        productVariantDocumentType
        title
        url
        snippet
        documentLanguage
        variantIdh
        variantSku
        variantDescription
        variantSize
        productFields {
          productName
          productKnownAs
        }
      }
      ... on ProductSearchResult {
        title
        url
        productFields {
          productName
          productKnownAs
        }
      }
    }
  }
}
""".strip()


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def detail_field(detail: dict | None, key: str) -> str | None:
    if not detail:
        return None
    return normalize_space(detail.get("fields", {}).get(key)) or None


def choose_representative_offer(offers: list[dict]) -> dict:
    return sorted(
        offers,
        key=lambda offer: (
            offer.get("price_usd") is None,
            offer.get("package_ml") is None,
            offer.get("package_ml") or 10**9,
            offer.get("price_usd") or 10**9,
        ),
    )[0]


def offer_part_no(offer: dict) -> str | None:
    fields = offer.get("fields", {})
    part_no = normalize_space(fields.get("mcmaster_part_no"))
    if part_no:
        return part_no
    for link in offer.get("row_links", []):
        href = link.get("href") or ""
        path = urlparse(href).path.strip("/")
        if re.fullmatch(r"[0-9]{3,}[A-Z]?[0-9A-Z]*", path):
            return path
    return None


def load_detail_lookup() -> dict[str, dict]:
    if not DETAILS_PATH.exists():
        return {}
    return json.loads(DETAILS_PATH.read_text()).get("detailsByPartNo", {})


def load_existing_cache() -> tuple[dict[str, dict], dict]:
    if not OUTPUT_PATH.exists():
        return {}, {}
    payload = json.loads(OUTPUT_PATH.read_text())
    return payload.get("entriesByFamilyKey", {}), payload.get("stats", {})


def load_official_overrides() -> dict[str, dict]:
    if not OVERRIDES_PATH.exists():
        return {}
    payload = json.loads(OVERRIDES_PATH.read_text())
    return payload if isinstance(payload, dict) else {}


def clean_brand_text(value: str | None) -> str:
    text = normalize_space(value)
    text = text.replace("®", "").replace("™", "").replace("©", "")
    return normalize_space(text)


def canonical_maker(*values: str | None) -> str | None:
    cleaned_values = [clean_brand_text(value) for value in values if normalize_space(value)]
    for candidate in cleaned_values:
        lowered = candidate.lower()
        if lowered in GENERIC_MAKER_TOKENS:
            continue
        for canonical, aliases in CANONICAL_MAKERS.items():
            if any(alias in lowered for alias in aliases):
                return canonical
    for candidate in cleaned_values:
        lowered = candidate.lower()
        if lowered in GENERIC_MAKER_TOKENS:
            continue
        if re.fullmatch(r"[0-9]{3,}[A-Z]?[0-9A-Z]*|__", candidate):
            continue
        if re.search(r"[A-Za-z]", candidate):
            return candidate
    return None


def family_display_name(family: dict, detail: dict | None, maker: str | None) -> str:
    model_name = clean_brand_text(detail_field(detail, "manufacturer_model_name"))
    model_number = clean_brand_text(detail_field(detail, "manufacturer_model_number"))
    title_name = clean_brand_text(detail.get("name")) if detail else ""
    raw_name = clean_brand_text(family.get("family_name"))

    if model_name or model_number:
        parts = [part for part in (maker, model_name, model_number) if part]
        name = " ".join(parts)
        if name:
            return normalize_space(name)

    for candidate in (raw_name, title_name):
        if not candidate:
            continue
        if re.fullmatch(r"[0-9]{3,}[A-Z]?[0-9A-Z]*|__", candidate):
            continue
        if maker and not candidate.lower().startswith(maker.lower()):
            return f"{maker} {candidate}"
        return candidate

    if maker and model_number:
        return f"{maker} {model_number}"
    return raw_name or title_name or family.get("family_key")


def extract_model_tokens(name: str, maker: str | None) -> list[str]:
    text = name
    if maker and text.lower().startswith(maker.lower()):
        text = text[len(maker) :].strip()
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", text) if part]
    return parts[:4]


def build_search_name(family: dict, detail: dict | None, maker: str | None) -> str:
    model_number = clean_brand_text(detail_field(detail, "manufacturer_model_number"))
    display_name = family_display_name(family, detail, maker)
    if maker == "3M":
        if model_number:
            return f"3M {model_number}"
        return display_name
    if maker == "Loctite" and model_number:
        return f"LOCTITE {model_number}"
    return display_name


def is_generic_candidate(maker: str | None, search_name: str) -> bool:
    lowered_maker = (maker or "").strip().lower()
    if lowered_maker in GENERIC_MAKER_TOKENS:
        return True
    lowered_name = search_name.lower()
    generic_fragments = (
        "quick-set epoxy structural adhesive",
        "slow-set epoxy structural adhesive",
        "glue hardens in",
        "adhesives with ten mixing sticks",
    )
    return any(fragment in lowered_name for fragment in generic_fragments)


def session() -> requests.Session:
    client = requests.Session()
    client.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
        }
    )
    return client


def url_matches_domains(url: str, domains: list[str]) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


def normalize_compact(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def search_variants(search_name: str, tokens: list[str]) -> list[str]:
    variants = {normalize_compact(search_name)}
    for token in tokens:
        variants.add(normalize_compact(token))
    return [value for value in variants if len(value) >= 2]


def candidate_url_score(url: str, search_name: str, tokens: list[str]) -> int:
    compact_url = normalize_compact(url)
    score = url_text_score(url, url, tokens)
    variants = search_variants(search_name, tokens)
    for variant in variants:
        if variant and variant in compact_url:
            score += min(12, max(4, len(variant)))
    if variants:
        longer = [variant for variant in variants if len(variant) >= 4]
        if longer and all(variant in compact_url for variant in longer[:3]):
            score += 12
    return score


def extract_xml_locs(text: str) -> list[str]:
    return [unescape(match) for match in re.findall(r"<loc>(.*?)</loc>", text, re.IGNORECASE)]


def load_sitemap_url_list(
    client: requests.Session,
    sitemap_url: str,
    cache: dict[str, list[str]],
    max_sitemaps: int = 24,
    max_urls: int = 6000,
) -> list[str]:
    if sitemap_url in cache:
        return cache[sitemap_url]

    queue = [sitemap_url]
    seen_sitemaps: set[str] = set()
    seen_urls: set[str] = set()
    urls: list[str] = []

    while queue and len(seen_sitemaps) < max_sitemaps and len(urls) < max_urls:
        current = queue.pop(0)
        if current in seen_sitemaps:
            continue
        seen_sitemaps.add(current)
        response = client.get(current, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        text = response.text
        locs = extract_xml_locs(text)
        if not locs:
            continue
        lowered = text[:400].lower()
        is_index = "<sitemapindex" in lowered
        for loc in locs:
            if is_index or (loc.endswith(".xml") and "sitemap" in loc):
                if loc not in seen_sitemaps:
                    queue.append(loc)
                continue
            if loc not in seen_urls:
                seen_urls.add(loc)
                urls.append(loc)

    cache[sitemap_url] = urls
    return urls


def load_sitemap_blocks(
    client: requests.Session,
    sitemap_url: str,
    cache: dict[str, list[dict]],
) -> list[dict]:
    if sitemap_url in cache:
        return cache[sitemap_url]
    response = client.get(sitemap_url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    blocks: list[dict] = []
    for match in re.finditer(r"<url>(.*?)</url>", response.text, re.IGNORECASE | re.DOTALL):
        block = match.group(1)
        loc_match = re.search(r"<loc>(.*?)</loc>", block, re.IGNORECASE)
        if not loc_match:
            continue
        loc = unescape(loc_match.group(1))
        blocks.append(
            {
                "loc": loc,
                "text": normalize_space(re.sub(r"<[^>]+>", " ", block)),
            }
        )
    cache[sitemap_url] = blocks
    return blocks


def discover_from_candidate_urls(
    client: requests.Session,
    candidate_urls: list[str],
    search_name: str,
    tokens: list[str],
    domains: list[str],
    source: str,
    limit: int = 8,
) -> dict | None:
    scored: list[tuple[int, str]] = []
    for candidate_url in candidate_urls:
        if not url_matches_domains(candidate_url, domains):
            continue
        score = candidate_url_score(candidate_url, search_name, tokens)
        if score > 0:
            scored.append((score, candidate_url))

    if not scored:
        return None

    best: dict | None = None
    for _, candidate_url in sorted(scored, reverse=True)[:limit]:
        try:
            tds_url, product_url = maybe_extract_pdf_link(client, candidate_url, tokens, domains)
        except Exception:
            tds_url, product_url = None, candidate_url
        chosen_url = tds_url or product_url or candidate_url
        if not chosen_url:
            continue
        score = candidate_url_score(chosen_url, search_name, tokens)
        if tds_url:
            score += 8
        result = {
            "score": score,
            "status": "found" if tds_url else "product-page",
            "tdsUrl": tds_url,
            "productUrl": product_url or candidate_url,
            "source": source,
            "domain": urlparse(chosen_url).netloc.lower(),
        }
        if best is None or result["score"] > best["score"]:
            best = result

    if not best:
        return None
    best.pop("score", None)
    return best


def discover_from_explicit_urls(
    client: requests.Session,
    candidate_urls: list[str],
    tokens: list[str],
    domains: list[str],
    source: str,
) -> dict | None:
    seen: set[str] = set()
    for candidate_url in candidate_urls:
        if not candidate_url or candidate_url in seen:
            continue
        seen.add(candidate_url)
        if not url_matches_domains(candidate_url, domains):
            continue
        try:
            tds_url, product_url = maybe_extract_pdf_link(client, candidate_url, tokens, domains)
        except Exception:
            tds_url, product_url = None, candidate_url
        chosen_url = tds_url or product_url or candidate_url
        if not chosen_url:
            continue
        return {
            "status": "found" if tds_url else "product-page",
            "tdsUrl": tds_url,
            "productUrl": product_url or candidate_url,
            "source": source,
            "domain": urlparse(chosen_url).netloc.lower(),
        }
    return None


def decode_search_click_url(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    uddg = params.get("uddg", [""])
    if uddg and uddg[0]:
        return unquote(uddg[0])
    encoded = params.get("u", [""])
    if encoded and encoded[0].startswith("a1"):
        payload = encoded[0][2:]
        payload += "=" * (-len(payload) % 4)
        try:
            return base64.urlsafe_b64decode(payload).decode("utf-8", "ignore")
        except Exception:
            return url
    return url


def bing_search(client: requests.Session, query: str, limit: int = 10) -> list[dict]:
    results: list[dict] = []
    try:
        response = client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.select("a.result__a"):
            href = normalize_space(anchor.get("href"))
            if not href:
                continue
            resolved = decode_search_click_url(href)
            results.append(
                {
                    "title": normalize_space(anchor.get_text(" ", strip=True)),
                    "url": resolved,
                }
            )
            if len(results) >= limit:
                break
    except requests.RequestException:
        results = []
    if results:
        return results

    try:
        response = client.get(
            f"https://www.bing.com/search?q={quote_plus(query)}",
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.select("li.b_algo h2 a"):
            href = normalize_space(anchor.get("href"))
            if not href:
                continue
            results.append(
                {
                    "title": normalize_space(anchor.get_text(" ", strip=True)),
                    "url": decode_search_click_url(href),
                }
            )
            if len(results) >= limit:
                break
    except requests.RequestException:
        return []
    return results


def url_text_score(url: str, text: str, tokens: list[str]) -> int:
    haystack = f"{url} {text}".lower()
    score = 0
    if url.lower().endswith(".pdf"):
        score += 10
    if any(token in haystack for token in ("technical data sheet", "tech data sheet", "product data sheet", "download tds", " tds")):
        score += 8
    if "sds" in haystack or "safety data sheet" in haystack:
        score -= 12
    for token in tokens:
        if token.lower() in haystack:
            score += 4
    return score


def maybe_extract_pdf_link(
    client: requests.Session,
    url: str,
    tokens: list[str],
    domains: list[str],
) -> tuple[str | None, str | None]:
    if url.lower().endswith(".pdf"):
        return url, None

    response = client.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "").lower()
    if "pdf" in content_type:
        return url, None

    soup = BeautifulSoup(response.text, "html.parser")
    candidates: list[tuple[int, str]] = []
    for anchor in soup.select("a[href]"):
        href = normalize_space(anchor.get("href"))
        text = normalize_space(anchor.get_text(" ", strip=True))
        if not href:
            continue
        resolved = urljoin(response.url, href)
        if not url_matches_domains(resolved, domains):
            continue
        score = url_text_score(resolved, text, tokens)
        if score > 0:
            candidates.append((score, resolved))

    if not candidates:
        return None, response.url
    candidates.sort(reverse=True)
    return candidates[0][1], response.url


def load_permabond_archive(client: requests.Session) -> dict[str, str]:
    response = client.get(PERMABOND_ARCHIVE_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    mapping: dict[str, str] = {}
    pattern = re.compile(
        r"<td>([A-Za-z0-9-]+)_TDS(?:[^<]*)</td>.*?(https://permabond\.com/tds/[^<]+?\?pdf=1)",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(response.text):
        model = match.group(1).strip().lower()
        pdf_url = unescape(match.group(2).strip())
        if model and model not in mapping:
            mapping[model] = pdf_url
    return mapping


def discover_permabond(
    archive: dict[str, str],
    search_name: str,
    tokens: list[str],
) -> dict | None:
    for token in tokens:
        lowered = token.lower()
        if lowered in archive:
            return {
                "status": "found",
                "tdsUrl": archive[lowered],
                "productUrl": None,
                "source": "permabond-archive",
                "domain": urlparse(archive[lowered]).netloc.lower(),
            }
    model = slugify(search_name).replace("-", "")
    if model in archive:
        return {
            "status": "found",
            "tdsUrl": archive[model],
            "productUrl": None,
            "source": "permabond-archive",
            "domain": urlparse(archive[model]).netloc.lower(),
        }
    return None


def henkel_search(client: requests.Session, search_name: str, tab: str) -> list[dict]:
    body = {
        "query": HENKEL_QUERY,
        "variables": {
            "site": HENKEL_SITE,
            "size": 12,
            "offset": 0,
            "term": search_name,
            "tab": tab,
            "sort": "RELEVANT",
        },
    }
    response = client.post(
        HENKEL_GRAPHQL_URL,
        json=body,
        timeout=REQUEST_TIMEOUT,
        headers={
            "Subscription-Key": HENKEL_SUBSCRIPTION_KEY,
            "Content-Type": "application/json",
        },
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", {}).get("raqnwebSearch", {}).get("results", [])


def discover_henkel(client: requests.Session, search_name: str, tokens: list[str]) -> dict | None:
    results = henkel_search(client, search_name, "Technical documents")
    scored: list[tuple[int, dict]] = []
    for item in results:
        url = normalize_space(item.get("url"))
        title = normalize_space(item.get("title"))
        if not url:
            continue
        score = url_text_score(url, title, tokens)
        if item.get("__typename") == "ProductTdsSearchResult":
            score += 12
        if item.get("__typename") == "ProductVariantDocumentSearchResult":
            document_type = normalize_space(item.get("productVariantDocumentType")).lower()
            if document_type == "tds":
                score += 10
        if score > 0:
            scored.append((score, item))

    if not scored:
        product_results = henkel_search(client, search_name, "Products")
        product_scored: list[tuple[int, dict]] = []
        for item in product_results:
            url = normalize_space(item.get("url"))
            title = normalize_space(item.get("title"))
            if not url:
                continue
            score = url_text_score(url, title, tokens)
            if any(token.lower() in f"{url} {title}".lower() for token in tokens):
                score += 8
            if score > 0:
                product_scored.append((score, item))
        if not product_scored:
            return None
        product_scored.sort(key=lambda item: item[0], reverse=True)
        best = product_scored[0][1]
        product_url = normalize_space(best.get("url"))
        return {
            "status": "product-page",
            "tdsUrl": None,
            "productUrl": product_url,
            "source": "henkel-product",
            "domain": urlparse(product_url).netloc.lower(),
        }
    scored.sort(key=lambda item: item[0], reverse=True)
    best = scored[0][1]
    return {
        "status": "found",
        "tdsUrl": normalize_space(best.get("url")),
        "productUrl": None,
        "source": "henkel-graphql",
        "domain": urlparse(best.get("url") or "").netloc.lower(),
    }


def build_bing_queries(maker: str, search_name: str, tokens: list[str]) -> list[str]:
    model = next((token for token in reversed(tokens) if re.search(r"\d", token)), tokens[-1] if tokens else "")
    if maker == "3M":
        return [
            f'site:multimedia.3m.com "{model}" "technical data sheet"' if model else f'site:multimedia.3m.com "{search_name}" "technical data sheet"',
            f'{model} technical data sheet 3M' if model else f"{search_name} technical data sheet",
            f'"{search_name}" "technical data sheet"',
            f"{search_name} pdf",
        ]
    if maker == "Momentive":
        return [
            f"{search_name} momentive technical data sheet",
            f"{search_name} momentive pdf",
            f"{search_name} technical data sheet",
        ]
    return [
        f"{search_name} technical data sheet",
        f"{search_name} tds",
        f"{maker} {model or search_name} technical data sheet",
    ]


def discover_via_bing(
    client: requests.Session,
    maker: str,
    search_name: str,
    tokens: list[str],
    domains: list[str],
) -> dict | None:
    queries = build_bing_queries(maker, search_name, tokens)
    seen_urls: set[str] = set()
    best: dict | None = None

    for query in queries:
        results = bing_search(client, query)
        for result in results:
            url = result["url"]
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            if not url_matches_domains(url, domains):
                continue
            try:
                tds_url, product_url = maybe_extract_pdf_link(client, url, tokens, domains)
            except Exception:
                continue
            chosen_url = tds_url or product_url or url
            if not chosen_url:
                continue
            score = url_text_score(chosen_url, result["title"], tokens)
            if best is None or score > best["score"]:
                best = {
                    "score": score,
                    "status": "found" if tds_url else "product-page",
                    "tdsUrl": tds_url,
                    "productUrl": product_url or url,
                    "source": "search-official",
                    "domain": urlparse(chosen_url).netloc.lower(),
                    "searchQuery": query,
                }
        if best and best["status"] == "found":
            break

    if not best:
        return None
    best.pop("score", None)
    return best


def discover_sika_direct(
    client: requests.Session,
    search_name: str,
    domains: list[str],
) -> dict | None:
    slug = slugify(search_name)
    if slug.startswith("sika-"):
        slug = slug[len("sika-") :]
    candidates = [
        f"https://industry.sika.com/en/products/{slug}.html",
        f"https://usa.sika.com/en/industry/products-solutions/adhesives-and-sealants/{slug}.html",
    ]
    for url in candidates:
        try:
            tds_url, product_url = maybe_extract_pdf_link(client, url, search_name.split(), domains)
        except Exception:
            continue
        if tds_url or product_url:
            return {
                "status": "found" if tds_url else "product-page",
                "tdsUrl": tds_url,
                "productUrl": product_url or url,
                "source": "sika-direct",
                "domain": urlparse(tds_url or product_url or url).netloc.lower(),
            }
    return None


def discover_itw_search(
    client: requests.Session,
    search_name: str,
    tokens: list[str],
    domains: list[str],
) -> dict | None:
    response = client.get(
        "https://itwperformancepolymers.com/",
        params={"s": search_name},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    product_links: list[str] = []
    for anchor in soup.select("a[href]"):
        href = normalize_space(anchor.get("href"))
        text = normalize_space(anchor.get_text(" ", strip=True))
        if not href or "/products/" not in href:
            continue
        score = url_text_score(href, text, tokens)
        if score > 0:
            product_links.append(href)
    seen: set[str] = set()
    for product_url in product_links:
        if product_url in seen:
            continue
        seen.add(product_url)
        try:
            tds_url, canonical_product_url = maybe_extract_pdf_link(client, product_url, tokens, domains)
        except Exception:
            continue
        if tds_url or canonical_product_url:
            return {
                "status": "found" if tds_url else "product-page",
                "tdsUrl": tds_url,
                "productUrl": canonical_product_url or product_url,
                "source": "itw-search",
                "domain": urlparse(tds_url or canonical_product_url or product_url).netloc.lower(),
            }
    return None


def discover_scigrip_sitemap(
    client: requests.Session,
    search_name: str,
    tokens: list[str],
    domains: list[str],
    sitemap_url_cache: dict[str, list[str]],
) -> dict | None:
    urls = load_sitemap_url_list(client, SCIGRIP_SITEMAP_URL, sitemap_url_cache)
    return discover_from_candidate_urls(
        client,
        urls,
        search_name,
        tokens,
        domains,
        source="scigrip-sitemap",
    )


def discover_permatex_sitemap(
    client: requests.Session,
    search_name: str,
    tokens: list[str],
    domains: list[str],
    sitemap_block_cache: dict[str, list[dict]],
) -> dict | None:
    blocks = load_sitemap_blocks(client, PERMATEX_SITEMAP_URL, sitemap_block_cache)
    exact_variants = search_variants(search_name, tokens)
    candidate_urls: list[str] = []
    for block in blocks:
        haystack = normalize_compact(block["text"])
        if any(variant in haystack for variant in exact_variants):
            candidate_urls.append(block["loc"])
    return discover_from_explicit_urls(
        client,
        candidate_urls,
        tokens,
        domains,
        source="permatex-sitemap",
    )


def discover_gorilla_sitemap(
    client: requests.Session,
    search_name: str,
    tokens: list[str],
    domains: list[str],
    sitemap_url_cache: dict[str, list[str]],
) -> dict | None:
    urls = load_sitemap_url_list(client, GORILLA_SITEMAP_URL, sitemap_url_cache)
    return discover_from_candidate_urls(
        client,
        urls,
        search_name,
        tokens,
        domains,
        source="gorilla-sitemap",
    )


def load_jbweld_product_urls(client: requests.Session, cache: dict[str, list[str]]) -> list[str]:
    cache_key = "jbweld-products"
    if cache_key in cache:
        return cache[cache_key]
    response = client.get("https://www.jbweld.com/products", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    urls: list[str] = []
    seen: set[str] = set()
    for href in re.findall(r'"/product/[^"]+"', response.text):
        path = href.strip('"')
        url = urljoin(response.url, path)
        if url not in seen:
            seen.add(url)
            urls.append(url)
    cache[cache_key] = urls
    return urls


def discover_jbweld_products(
    client: requests.Session,
    search_name: str,
    tokens: list[str],
    domains: list[str],
    sitemap_url_cache: dict[str, list[str]],
) -> dict | None:
    candidate_urls = []
    lowered = search_name.lower()
    for hint, path in JBWELD_SLUG_HINTS.items():
        if hint in lowered:
            candidate_urls.append(urljoin("https://www.jbweld.com", path))
    candidate_urls.extend(load_jbweld_product_urls(client, sitemap_url_cache))
    return discover_from_candidate_urls(
        client,
        candidate_urls,
        search_name,
        tokens,
        domains,
        source="jbweld-products",
    )


def normalized_code_values(values: list[str] | None) -> list[str]:
    output: list[str] = []
    for value in values or []:
        compact = normalize_compact(value)
        if compact:
            output.append(compact)
    return output


def discover_liquid_nails_algolia(
    client: requests.Session,
    search_name: str,
    tokens: list[str],
    domains: list[str],
) -> dict | None:
    query_terms = [search_name]
    query_terms.extend(token for token in tokens if re.search(r"\d", token))
    exact_variants = search_variants(search_name, tokens)
    best: dict | None = None

    for query in query_terms[:4]:
        response = client.post(
            f"https://{LIQUID_NAILS_ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/{LIQUID_NAILS_ALGOLIA_INDEX}/query",
            headers={
                "X-Algolia-Application-Id": LIQUID_NAILS_ALGOLIA_APP_ID,
                "X-Algolia-API-Key": LIQUID_NAILS_ALGOLIA_KEY,
                "Content-Type": "application/json",
            },
            json={"params": f"query={quote_plus(query)}&hitsPerPage=8"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        for hit in response.json().get("hits", []):
            page_url = normalize_space(hit.get("page_url"))
            title = normalize_space(hit.get("title"))
            if not page_url or not url_matches_domains(page_url, domains):
                continue
            codes = normalized_code_values(hit.get("product_codes"))
            exact_match = any(
                variant == code or variant in code or code in variant
                for variant in exact_variants
                for code in codes
            )
            score = candidate_url_score(page_url, search_name, tokens) + url_text_score(page_url, title, tokens)
            if exact_match:
                score += 24
            if "liquid nails" in title.lower():
                score += 8
            if best is None or score > best["score"]:
                best = {
                    "score": score,
                    "status": "product-page",
                    "tdsUrl": None,
                    "productUrl": page_url,
                    "source": "liquid-nails-algolia",
                    "domain": urlparse(page_url).netloc.lower(),
                }
        if best and best["score"] >= 30:
            break

    if not best:
        return None
    best.pop("score", None)
    return best


def discover_momentive_sitemap(
    client: requests.Session,
    search_name: str,
    tokens: list[str],
    domains: list[str],
    sitemap_url_cache: dict[str, list[str]],
) -> dict | None:
    compact_tokens = {normalize_compact(token) for token in tokens}
    if compact_tokens & MOMENTIVE_RTV100_TOKENS:
        return {
            "status": "found",
            "tdsUrl": MOMENTIVE_RTV100_PDF,
            "productUrl": None,
            "source": "momentive-direct",
            "domain": urlparse(MOMENTIVE_RTV100_PDF).netloc.lower(),
        }
    for token, pdf_url in MOMENTIVE_DIRECT_PDFS.items():
        if token in compact_tokens:
            return {
                "status": "found",
                "tdsUrl": pdf_url,
                "productUrl": None,
                "source": "momentive-direct",
                "domain": urlparse(pdf_url).netloc.lower(),
            }

    urls = load_sitemap_url_list(client, MOMENTIVE_SITEMAP_URL, sitemap_url_cache)
    return discover_from_candidate_urls(
        client,
        urls,
        search_name,
        tokens,
        domains,
        source="momentive-sitemap",
    )


def extract_json_array_after_marker(text: str, marker: str) -> list[dict]:
    marker_index = text.find(marker)
    if marker_index < 0:
        return []
    start = text.find("[", marker_index)
    if start < 0:
        return []

    depth = 0
    in_string = False
    escaped = False
    end = None
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                end = index + 1
                break

    if end is None:
        return []
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return []


def discover_3m_search(
    client: requests.Session,
    search_name: str,
    tokens: list[str],
    domains: list[str],
) -> dict | None:
    response = client.get(
        "https://www.3m.com/3M/en_US/p/search/",
        params={"Ntt": search_name},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    items = extract_json_array_after_marker(response.text, '"items":[')
    candidates: list[tuple[int, str, str]] = []
    for item in items:
        url = normalize_space(item.get("url"))
        title = normalize_space(re.sub(r"<[^>]+>", " ", item.get("name") or ""))
        if not url or not url_matches_domains(url, domains):
            continue
        if "/p/d/" not in url:
            continue
        score = url_text_score(url, title, tokens)
        if any(token.lower() in f"{url} {title}".lower() for token in tokens):
            score += 6
        if score > 0:
            candidates.append((score, url, title))

    candidates.sort(reverse=True)
    seen: set[str] = set()
    best: dict | None = None
    for _, product_url, title in candidates[:8]:
        if product_url in seen:
            continue
        seen.add(product_url)
        try:
            tds_url, canonical_product_url = maybe_extract_pdf_link(client, product_url, tokens, domains)
        except Exception:
            continue
        chosen_url = tds_url or canonical_product_url or product_url
        if not chosen_url:
            continue
        score = url_text_score(chosen_url, title, tokens)
        if tds_url:
            score += 6
        if best is None or score > best["score"]:
            best = {
                "score": score,
                "status": "found" if tds_url else "product-page",
                "tdsUrl": tds_url,
                "productUrl": canonical_product_url or product_url,
                "source": "3m-site-search",
                "domain": urlparse(chosen_url).netloc.lower(),
            }

    if not best:
        return None
    best.pop("score", None)
    return best


def build_candidate(
    family: dict,
    representative: dict,
    detail: dict | None,
) -> dict:
    maker = canonical_maker(
        detail_field(detail, "manufacturer"),
        family.get("manufacturer"),
        family.get("family_name"),
    )
    search_name = build_search_name(family, detail, maker)
    tokens = extract_model_tokens(search_name, maker)
    return {
        "maker": maker,
        "familyName": family_display_name(family, detail, maker),
        "searchName": search_name,
        "tokens": tokens,
        "partNo": offer_part_no(representative),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Re-run discovery for cached families.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N family candidates after sorting by family key.",
    )
    parser.add_argument(
        "--family-key",
        action="append",
        default=[],
        help="Restrict discovery to specific McMaster family keys. Repeatable.",
    )
    parser.add_argument(
        "--sleep-ms",
        type=int,
        default=150,
        help="Small delay between families to reduce burstiness against upstream sources.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw = json.loads(RAW_PATH.read_text())
    detail_lookup = load_detail_lookup()
    existing_entries, existing_stats = load_existing_cache()
    official_overrides = load_official_overrides()

    family_filter = {normalize_space(value) for value in args.family_key if normalize_space(value)}
    offers_by_family: dict[str, list[dict]] = defaultdict(list)
    for offer in raw.get("offers", []):
        offers_by_family[offer["family_key"]].append(offer)

    families = sorted(raw.get("families", []), key=lambda family: family["family_key"])
    if family_filter:
        families = [family for family in families if family["family_key"] in family_filter]
    if args.limit is not None:
        families = families[: args.limit]

    entries_by_family = dict(existing_entries)
    skipped = 0
    found = 0
    product_only = 0
    not_found = 0
    errors = 0
    strategy_counter: Counter[str] = Counter()

    client = session()
    permabond_archive: dict[str, str] | None = None
    sitemap_url_cache: dict[str, list[str]] = {}
    sitemap_block_cache: dict[str, list[dict]] = {}

    for index, family in enumerate(families, start=1):
        family_key = family["family_key"]
        if not args.refresh and family_key in entries_by_family:
            continue

        offers = offers_by_family.get(family_key, [])
        if not offers:
            continue
        representative = choose_representative_offer(offers)
        detail = detail_lookup.get(offer_part_no(representative) or "")
        candidate = build_candidate(family, representative, detail)
        maker = candidate["maker"]
        search_name = candidate["searchName"]
        tokens = candidate["tokens"]
        base_entry = {
            "familyKey": family_key,
            "maker": maker,
            "familyName": candidate["familyName"],
            "searchName": search_name,
            "partNo": candidate["partNo"],
            "categoryHeadings": family.get("category_headings", []),
        }

        override = official_overrides.get(family_key)
        if override:
            entries_by_family[family_key] = {
                **base_entry,
                **override,
                "strategy": "override",
            }
            if override.get("status") == "found":
                found += 1
            elif override.get("status") == "product-page":
                product_only += 1
            else:
                not_found += 1
            print(f"[tds] {index:03d}/{len(families):03d} override {family_key} {search_name}")
            continue

        if is_generic_candidate(maker, search_name) or not maker or maker not in MAKER_CONFIG:
            skipped += 1
            entries_by_family[family_key] = {
                **base_entry,
                "status": "skipped",
                "skipReason": "no-supported-official-manufacturer-strategy",
            }
            print(f"[tds] {index:03d}/{len(families):03d} skip {family_key} {search_name}")
            continue

        config = MAKER_CONFIG[maker]
        domains = config["domains"]
        print(f"[tds] {index:03d}/{len(families):03d} {maker} {search_name}")

        try:
            result = None
            if config["strategy"] == "henkel":
                result = discover_henkel(client, search_name, tokens)
            elif config["strategy"] == "3m-search":
                result = discover_3m_search(client, search_name, tokens, domains)
            elif config["strategy"] == "permabond":
                if permabond_archive is None:
                    permabond_archive = load_permabond_archive(client)
                result = discover_permabond(permabond_archive, search_name, tokens)
            elif config["strategy"] == "sika-direct":
                result = discover_sika_direct(client, search_name, domains)
            elif config["strategy"] == "itw-search":
                result = discover_itw_search(client, search_name, tokens, domains)
            elif config["strategy"] == "scigrip-sitemap":
                result = discover_scigrip_sitemap(client, search_name, tokens, domains, sitemap_url_cache)
            elif config["strategy"] == "permatex-sitemap":
                result = discover_permatex_sitemap(client, search_name, tokens, domains, sitemap_block_cache)
            elif config["strategy"] == "gorilla-sitemap":
                result = discover_gorilla_sitemap(client, search_name, tokens, domains, sitemap_url_cache)
            elif config["strategy"] == "jbweld-products":
                result = discover_jbweld_products(client, search_name, tokens, domains, sitemap_url_cache)
            elif config["strategy"] == "liquid-nails-algolia":
                result = discover_liquid_nails_algolia(client, search_name, tokens, domains)
            elif config["strategy"] == "momentive-sitemap":
                result = discover_momentive_sitemap(client, search_name, tokens, domains, sitemap_url_cache)
            if result is None:
                result = discover_via_bing(client, maker, search_name, tokens, domains)

            if result is None:
                not_found += 1
                entries_by_family[family_key] = {
                    **base_entry,
                    "status": "not-found",
                    "strategy": config["strategy"],
                }
            else:
                entries_by_family[family_key] = {
                    **base_entry,
                    **result,
                    "strategy": config["strategy"],
                }
                strategy_counter[result["source"]] += 1
                if result["status"] == "found":
                    found += 1
                else:
                    product_only += 1
        except Exception as exc:
            errors += 1
            entries_by_family[family_key] = {
                **base_entry,
                "status": "error",
                "strategy": config["strategy"],
                "error": str(exc)[:300],
            }

        time.sleep(max(args.sleep_ms, 0) / 1000)

    final_status_counts = Counter(entry.get("status") for entry in entries_by_family.values())
    final_source_counts = Counter(
        entry.get("source")
        for entry in entries_by_family.values()
        if normalize_space(entry.get("source"))
    )

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "families": len(raw.get("families", [])),
        "processed_families": len(families),
        "entries": len(entries_by_family),
        "found": final_status_counts.get("found", 0),
        "product_only": final_status_counts.get("product-page", 0),
        "not_found": final_status_counts.get("not-found", 0),
        "skipped": final_status_counts.get("skipped", 0),
        "errors": final_status_counts.get("error", 0),
        "previous_entries": existing_stats.get("entries"),
        "last_run_found": found,
        "last_run_product_only": product_only,
        "last_run_not_found": not_found,
        "last_run_skipped": skipped,
        "last_run_errors": errors,
        "by_source": dict(final_source_counts),
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "generated_at": stats["generated_at"],
                "stats": stats,
                "entriesByFamilyKey": entries_by_family,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
