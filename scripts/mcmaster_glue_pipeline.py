#!/usr/bin/env python3
"""Crawl McMaster's glue catalog and extract structured adhesive offers.

The script uses Playwright because McMaster renders the useful product tables
after hydration. It traverses a curated set of adhesive categories, follows
subcategory tiles, and emits both raw offers and deduplicated product families.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT_URL = "https://www.mcmaster.com/products/glue/"
DEFAULT_ROOT_CATEGORY_NAMES = (
    "Instant-Bond Adhesives",
    "Glue",
    "Structural Adhesives",
    "Contact Adhesives",
    "Hot Glue",
    "Adhesive Cement",
    "Construction Adhesives",
    "Threadlockers",
    "Retaining Compounds",
    "Sealants",
    "Gasket Makers",
    "Potting Compounds",
    "Electrically Insulating Adhesives",
    "Conductive Adhesives",
    "Anchoring Adhesives",
)
FALLBACK_SEED_PATHS = (
    "instant-bond-adhesives-1~/",
    "glue-3~/",
    "structural-adhesives-1~/",
    "contact-adhesives-3~/",
    "hot-glue-2~/",
    "adhesive-cement-1~/",
    "construction-adhesives-2~/",
    "threadlockers-4~/",
    "retaining-compounds-2~/",
    "sealants-3~/",
    "gasket-makers-2~/",
    "potting-compounds-2~/",
    "electrically-insulating-adhesives-2~/",
    "conductive-adhesives-2~/",
    "anchoring-adhesives-2~/",
)
DEFAULT_MAX_PAGES = 250
DEFAULT_TIMEOUT_MS = 45_000

SKIP_FAMILY_KEYS = {
    "accelerator",
    "activator",
    "additive",
    "applicator",
    "brush",
    "caps",
    "cleaner",
    "dispensers",
    "dispensing guns",
    "dispensing gun nozzles",
    "holders",
    "mixer nozzles",
    "primer",
    "remover",
    "spacing beads",
    "tube dispensers",
}

HEADER_KEY_MAP = {
    "mfr. model no.": "mfr_model_no",
    "mfr. model": "mfr_model_no",
    "model no.": "model_no",
    "name": "name",
    "type": "type",
    "container": "container",
    "size, fl. oz.": "size_fl_oz",
    "size, oz.": "size_oz",
    "size, mL": "size_ml",
    "size, ml": "size_ml",
    "size": "size",
    "begins to harden": "begins_to_harden",
    "begins to harden, sec.": "begins_to_harden_sec",
    "begins to harden, min.": "begins_to_harden_min",
    "reaches full strength": "reaches_full_strength",
    "reaches full strength, hr.": "reaches_full_strength_hr",
    "heating req. to reach full strength": "heating_req_full_strength",
    "light intensity req. to reach full strength": "light_req_full_strength",
    "cure type": "cure_type",
    "shear, lbs./sq. in.": "shear_psi",
    "peel, lbs./in. wd.": "peel_lb_per_in",
    "viscosity, cP": "viscosity_cp_raw",
    "consistency": "consistency",
    "consistency (viscosity)": "consistency_viscosity",
    "max. gap size filled": "max_gap_filled",
    'max. gap size filled': "max_gap_filled",
    "temp. range, °F": "temp_range_f",
    "max. temp., ° f": "max_temp_f",
    "max., ° f": "max_temp_f",
    "min.": "service_min_f",
    "max.": "service_max_f",
    "mix ratio": "mix_ratio",
    "color": "color",
    "for joining": "for_joining",
    "for use on": "for_use_on",
    "elongation": "elongation",
    "net wt., oz.": "net_wt_oz",
    "specs. met": "specs_met",
    "specs met": "specs_met",
    "includes": "includes",
    "cannot be sold to": "cannot_be_sold_to",
    "pkg. qty.": "pkg_qty",
    "pkg.": "pkg_price_usd",
    "light intensity req. to reach full strength": "light_req_full_strength",
    "heating req. to reach full strength": "heating_req_full_strength",
    "each": "price_each_usd",
}

VOLUME_UNIT_TO_ML = {
    "fl_oz": 29.5735,
    "ml": 1.0,
    "qt": 946.353,
    "pt": 473.176,
    "gal": 3785.41,
}


def normalize_space(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def canonical_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "value"


def normalize_header_text(text: str | None) -> str:
    value = normalize_space(text)
    value = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    value = re.sub(r"(?<=\.)(?=[A-Za-z])", " ", value)
    value = re.sub(r",(?=\S)", ", ", value)
    value = re.sub(r"(?<=\w)\(", " (", value)
    value = re.sub(r"\)(?=\w)", ") ", value)
    return normalize_space(value)


def clean_brand(text: str | None) -> str:
    cleaned = normalize_space(text)
    cleaned = cleaned.replace("®", "").replace("™", "")
    cleaned = re.sub(r"\s+Adhesives?$", "", cleaned, flags=re.I)
    cleaned = cleaned.strip()
    if cleaned.lower() in {"adhesive", "adhesives", "other", "others"}:
        return ""
    return cleaned


def parse_float(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text)
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def parse_price_usd(text: str | None) -> float | None:
    return parse_float(text)


def looks_like_part_number(text: str | None) -> bool:
    value = normalize_space(text)
    return bool(re.fullmatch(r"[0-9]{3,}[A-Z]?[0-9A-Z]*", value))


def looks_like_numeric_label(text: str | None) -> bool:
    value = normalize_space(text)
    return bool(value and re.fullmatch(r"[\d.]+", value))


def parse_temp_range_f(text: str | None) -> tuple[float | None, float | None]:
    if not text:
        return None, None
    values = re.findall(r"-?\d+(?:\.\d+)?", text)
    if len(values) < 2:
        return None, None
    return float(values[0]), float(values[1])


def parse_viscosity_cp(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"\(([\d,]+)\s*cP\)", text, re.I)
    if match:
        return float(match.group(1).replace(",", ""))
    if "cp" in text.lower():
        return parse_float(text)
    return None


def infer_size_unit(header_key: str, raw_header: str) -> str | None:
    raw = raw_header.lower()
    if header_key == "size_fl_oz" or "fl. oz" in raw:
        return "fl_oz"
    if header_key == "size_ml" or re.search(r"\bml\b", raw):
        return "ml"
    if re.search(r"\bqt\b", raw):
        return "qt"
    if re.search(r"\bpt\b", raw):
        return "pt"
    if re.search(r"\bgal\b", raw):
        return "gal"
    return None


def parse_size_text(text: str | None) -> tuple[float | None, str | None]:
    value = parse_float(text)
    if value is None:
        return None, None
    raw = normalize_space(text).lower()
    if "fl. oz" in raw or "fl oz" in raw:
        return value, "fl_oz"
    if re.search(r"\bml\b", raw):
        return value, "ml"
    if re.search(r"\bqt\b", raw):
        return value, "qt"
    if re.search(r"\bpt\b", raw):
        return value, "pt"
    if re.search(r"\bgal\b", raw):
        return value, "gal"
    return None, None


def normalize_header(raw_header: str, position: int, total: int) -> str:
    cleaned = normalize_header_text(raw_header)
    if not cleaned:
        if position == total - 2:
            return "mcmaster_part_no"
        return f"column_{position + 1}"
    lowered = cleaned.lower()
    return HEADER_KEY_MAP.get(lowered, slugify(lowered))


def discover_seed_urls(page) -> list[str]:
    items = page.evaluate(
        """(rootUrl) => {
          const normalize = (value) => (value || "").replace(/\\s+/g, " ").trim();
          return Array.from(document.querySelectorAll("a[href]"))
            .map((anchor) => {
              const href = new URL(anchor.getAttribute("href"), window.location.href).href;
              return {
                href,
                text: normalize(anchor.textContent),
              };
            })
            .filter((item) =>
              item.href.startsWith(rootUrl) &&
              item.href !== rootUrl &&
              /\\b\\d+\\s+products?\\b/i.test(item.text)
            );
        }""",
        ROOT_URL,
    )

    discovered: dict[str, str] = {}
    for item in items:
        text = item["text"]
        for category_name in DEFAULT_ROOT_CATEGORY_NAMES:
            if text.startswith(category_name):
                discovered[category_name] = canonical_url(item["href"])
                break

    seeds = [discovered[name] for name in DEFAULT_ROOT_CATEGORY_NAMES if name in discovered]
    if seeds:
        return seeds
    return [canonical_url(urljoin(ROOT_URL, path)) for path in FALLBACK_SEED_PATHS]


def fetch_snapshot(page, url: str) -> dict:
    page.goto(url, wait_until="networkidle", timeout=DEFAULT_TIMEOUT_MS)
    return page.evaluate(
        """(rootUrl) => {
          const normalize = (value) => (value || "").replace(/\\s+/g, " ").trim();
          const currentUrl = new URL(window.location.href).href;
          const currentPrefix = currentUrl.endsWith("/") ? currentUrl : `${currentUrl}/`;
          const isCatalogChild = (href) => {
            if (!href.startsWith(currentPrefix) || href === currentUrl) {
              return false;
            }
            const relative = href.slice(currentPrefix.length);
            if (!relative) {
              return false;
            }
            return !relative.includes("~") || relative.endsWith("~~/") || relative.endsWith("~~");
          };
          const headings = Array.from(document.querySelectorAll("h1, h2, h3"))
            .map((node) => normalize(node.textContent))
            .filter(Boolean);

          const rootTiles = Array.from(document.querySelectorAll("a[href]"))
            .map((anchor) => {
              const href = new URL(anchor.getAttribute("href"), currentUrl).href;
              return { href, text: normalize(anchor.textContent) };
            })
            .filter((item) =>
              item.href.startsWith(rootUrl) &&
              item.href !== currentUrl &&
              /\\b\\d+\\s+products?\\b/i.test(item.text)
            );

          const presentationTiles = Array.from(
            document.querySelectorAll("a[href][class*='PrsnttnStructure']")
          )
            .map((anchor) => {
              const href = new URL(anchor.getAttribute("href"), currentUrl).href;
              return {
                href,
                text: normalize(anchor.textContent),
              };
            })
            .filter((item) => item.href.startsWith(rootUrl) && isCatalogChild(item.href) && item.text);

          const fallbackTiles = Array.from(document.querySelectorAll("a[href]"))
            .map((anchor) => {
              const href = new URL(anchor.getAttribute("href"), currentUrl).href;
              return {
                href,
                text: normalize(anchor.textContent),
              };
            })
            .filter(
              (item) =>
                isCatalogChild(item.href) &&
                item.text &&
                item.text.length > 20
            );

          const childTiles = (presentationTiles.length ? presentationTiles : fallbackTiles).filter(
            (item, index, items) => items.findIndex((entry) => entry.href === item.href) === index
          );

          const findContextHeading = (container) => {
            let node = container;
            while (node) {
              let sibling = node.previousElementSibling;
              while (sibling) {
                const text = normalize(sibling.textContent);
                if (
                  text &&
                  text.length < 120 &&
                  !/^\\d+[\\d,]*\\s+Products?$/i.test(text) &&
                  !/^About\\b/i.test(text) &&
                  !/Container|Each|For Joining|Strength/i.test(text)
                ) {
                  return text;
                }
                sibling = sibling.previousElementSibling;
              }
              node = node.parentElement;
            }
            return null;
          };

          const tables = Array.from(document.querySelectorAll("table")).map((table, index) => {
            const headerRows = Array.from(table.querySelectorAll("thead tr"));
            const leafHeaderRow = headerRows.length ? headerRows[headerRows.length - 1] : null;
            const headers = leafHeaderRow
              ? Array.from(leafHeaderRow.children).map((cell) => normalize(cell.textContent))
              : [];

            const rows = Array.from(table.querySelectorAll("tbody tr")).map((row) => ({
              cells: Array.from(row.children).map((cell) => normalize(cell.textContent)),
              links: Array.from(row.querySelectorAll("a[href]")).map((anchor) => ({
                href: new URL(anchor.getAttribute("href"), currentUrl).href,
                text: normalize(anchor.textContent),
              })),
            }));

            if (!headers.length || headers.length < 5 || !rows.length) {
              return null;
            }

            const container =
              table.closest(".ItmTblCntnr, [class*='tableContainer']") || table.parentElement;

            return {
              index,
              heading: findContextHeading(container),
              headers,
              rows,
            };
          }).filter(Boolean);

          return {
            url: currentUrl,
            title: document.title,
            headings,
            childTiles,
            rootTiles,
            tables,
          };
        }""",
        ROOT_URL,
    )


def build_offer(
    page_record: dict,
    table_record: dict,
    raw_headers: list[str],
    row: dict,
    group_label: str | None = None,
) -> dict | None:
    normalized_headers = [
        normalize_header(header, index, len(raw_headers)) for index, header in enumerate(raw_headers)
    ]
    cells = list(row["cells"])
    if (
        raw_headers
        and not normalize_space(raw_headers[0])
        and normalized_headers
        and normalized_headers[0].startswith("column_")
        and cells
        and not normalize_space(cells[-1])
    ):
        raw_headers = raw_headers[1:]
        normalized_headers = normalized_headers[1:]
        cells = cells[:-1]

    non_empty_cells = [normalize_space(cell) for cell in cells if normalize_space(cell)]
    if len(non_empty_cells) < 3 and not row["links"]:
        return None
    if len(cells) < len(normalized_headers):
        cells.extend([""] * (len(normalized_headers) - len(cells)))
    if len(cells) > len(normalized_headers):
        normalized_headers.extend(
            f"column_{index + 1}" for index in range(len(normalized_headers), len(cells))
        )
        raw_headers = [*raw_headers, *([""] * (len(cells) - len(raw_headers)))]

    fields = {normalized_headers[index]: cells[index] for index in range(len(cells))}
    raw_field_map = {
        normalize_header(raw_headers[index], index, len(raw_headers)): raw_headers[index]
        for index in range(len(raw_headers))
    }

    part_number = normalize_space(fields.get("mcmaster_part_no"))
    if not part_number:
        for link in row["links"]:
            if looks_like_part_number(link.get("text")):
                part_number = normalize_space(link["text"])
                break
    if not part_number:
        for cell in reversed(cells):
            if looks_like_part_number(cell):
                part_number = normalize_space(cell)
                break
    if part_number:
        fields["mcmaster_part_no"] = part_number

    size_header_key = next((key for key in normalized_headers if key.startswith("size")), None)
    size_header_raw = raw_field_map.get(size_header_key, "") if size_header_key else ""
    size_value = parse_float(fields.get(size_header_key)) if size_header_key else None
    size_unit = infer_size_unit(size_header_key or "", size_header_raw) if size_header_key else None
    if size_value is None or size_unit is None:
        for fallback_key in ("column_1", "mfr_model_no", "size", "net_wt_oz"):
            fallback_value, fallback_unit = parse_size_text(fields.get(fallback_key))
            if fallback_value is not None and fallback_unit is not None:
                size_value = fallback_value
                size_unit = fallback_unit
                break

    price_usd = parse_price_usd(fields.get("price_each_usd"))
    if price_usd is None:
        if part_number:
            for index, cell in enumerate(cells):
                if normalize_space(cell) == part_number:
                    for candidate in cells[index + 1 : index + 3]:
                        price_usd = parse_price_usd(candidate)
                        if price_usd is not None:
                            break
                    if price_usd is not None:
                        break
        for cell in reversed(cells):
            price_candidate = parse_price_usd(cell) if "$" in cell else None
            if price_candidate is not None:
                price_usd = price_candidate
                break

    if part_number is None and price_usd is None and len(non_empty_cells) < 5:
        return None

    package_ml = None
    price_per_ml = None
    if price_usd is not None and size_value is not None and size_unit in VOLUME_UNIT_TO_ML:
        package_ml = round(size_value * VOLUME_UNIT_TO_ML[size_unit], 2)
        if package_ml > 0:
            price_per_ml = round(price_usd / package_ml, 4)

    temp_min_f, temp_max_f = parse_temp_range_f(fields.get("temp_range_f"))
    consistency_text = fields.get("consistency_viscosity") or fields.get("consistency")
    viscosity_cp = parse_viscosity_cp(consistency_text or fields.get("viscosity_cp_raw"))
    manufacturer_heading = table_record.get("heading")
    brand = clean_brand(group_label) or clean_brand(manufacturer_heading)

    family_label = None
    for key in ("mfr_model_no", "model_no", "name"):
        value = normalize_space(fields.get(key))
        if value:
            family_label = value
            break
    if not family_label and group_label and not looks_like_numeric_label(group_label):
        family_label = normalize_space(group_label)
    if not family_label:
        for key in ("column_1", "column_2"):
            value = normalize_space(fields.get(key))
            if value and not looks_like_numeric_label(value) and not looks_like_part_number(value):
                family_label = value
                break
    if not family_label:
        family_label = part_number or None

    family_name = normalize_space(" ".join(part for part in (brand, family_label) if part))
    family_key = slugify(family_name or f"{brand}_{fields.get('mcmaster_part_no', '')}")

    offer = {
        "source_url": page_record["url"],
        "page_title": page_record["title"],
        "page_headings": page_record["headings"],
        "category_heading": next(
            (heading for heading in reversed(page_record["headings"]) if not heading.startswith("About ")),
            None,
        ),
        "table_heading": manufacturer_heading,
        "manufacturer": brand or None,
        "family_name": family_name or None,
        "family_key": family_key,
        "fields": fields,
        "raw_headers": raw_headers,
        "row_links": row["links"],
        "price_usd": price_usd,
        "size_value": size_value,
        "size_unit": size_unit,
        "package_ml": package_ml,
        "price_per_ml": price_per_ml,
        "temp_min_f": temp_min_f,
        "temp_max_f": temp_max_f,
        "consistency": normalize_space(consistency_text) or None,
        "viscosity_cp": viscosity_cp,
    }
    return offer


def extract_offers_from_table(page_record: dict, table_record: dict) -> list[dict]:
    offers: list[dict] = []
    group_label: str | None = None
    for row in table_record["rows"]:
        non_empty = [normalize_space(cell) for cell in row["cells"] if normalize_space(cell)]
        if len(non_empty) == 1 and not row["links"]:
            group_label = non_empty[0]
            continue
        offer = build_offer(page_record, table_record, table_record["headers"], row, group_label)
        if offer is not None:
            offers.append(offer)
    return offers


def should_skip_family(offer: dict) -> bool:
    haystack = " ".join(
        normalize_space(part)
        for part in (
            offer.get("family_name"),
            offer.get("table_heading"),
            offer["fields"].get("type"),
        )
        if part
    ).lower()
    return any(token in haystack for token in SKIP_FAMILY_KEYS)


def aggregate_families(offers: list[dict]) -> list[dict]:
    families: dict[str, dict] = {}
    for offer in offers:
        if should_skip_family(offer):
            continue

        family = families.setdefault(
            offer["family_key"],
            {
                "family_key": offer["family_key"],
                "family_name": offer["family_name"] or offer["table_heading"],
                "manufacturer": offer["manufacturer"],
                "category_headings": set(),
                "source_urls": set(),
                "offers": [],
            },
        )
        if offer.get("category_heading"):
            family["category_headings"].add(offer["category_heading"])
        family["source_urls"].add(offer["source_url"])
        family["offers"].append(offer)

    normalized_families = []
    for family in families.values():
        price_values = [offer["price_per_ml"] for offer in family["offers"] if offer["price_per_ml"]]
        offer_prices = [offer["price_usd"] for offer in family["offers"] if offer["price_usd"]]
        temp_mins = [offer["temp_min_f"] for offer in family["offers"] if offer["temp_min_f"] is not None]
        temp_maxs = [offer["temp_max_f"] for offer in family["offers"] if offer["temp_max_f"] is not None]
        sample_offer = family["offers"][0]
        normalized_families.append(
            {
                "family_key": family["family_key"],
                "family_name": family["family_name"],
                "manufacturer": family["manufacturer"],
                "category_headings": sorted(family["category_headings"]),
                "source_urls": sorted(family["source_urls"]),
                "offer_count": len(family["offers"]),
                "lowest_price_usd": round(min(offer_prices), 2) if offer_prices else None,
                "best_price_per_ml": round(min(price_values), 4) if price_values else None,
                "temp_min_f": min(temp_mins) if temp_mins else None,
                "temp_max_f": max(temp_maxs) if temp_maxs else None,
                "sample_type": sample_offer["fields"].get("type"),
                "sample_mix_ratio": sample_offer["fields"].get("mix_ratio"),
                "sample_consistency": sample_offer.get("consistency"),
                "sample_for_joining": sample_offer["fields"].get("for_joining"),
            }
        )

    normalized_families.sort(key=lambda item: ((item["manufacturer"] or ""), item["family_name"] or ""))
    return normalized_families


def crawl_catalog(seed_urls: list[str], max_pages: int) -> tuple[list[dict], list[dict]]:
    visited: set[str] = set()
    queued: set[str] = set(canonical_url(url) for url in seed_urls)
    queue = deque(canonical_url(url) for url in seed_urls)
    pages: list[dict] = []
    offers: list[dict] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_navigation_timeout(DEFAULT_TIMEOUT_MS)

        while queue and len(visited) < max_pages:
            url = queue.popleft()
            queued.discard(url)
            if url in visited:
                continue

            print(f"[crawl] {len(visited) + 1:03d} {url}", file=sys.stderr)
            try:
                snapshot = fetch_snapshot(page, url)
            except PlaywrightTimeoutError:
                print(f"[warn] timeout loading {url}", file=sys.stderr)
                visited.add(url)
                continue
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"[warn] failed {url}: {exc}", file=sys.stderr)
                visited.add(url)
                continue

            visited.add(url)
            page_record = {
                "url": snapshot["url"],
                "title": snapshot["title"],
                "headings": snapshot["headings"],
                "table_count": len(snapshot["tables"]),
                "child_link_count": len(snapshot["childTiles"]),
            }
            pages.append(page_record)

            for child in snapshot["childTiles"]:
                child_url = canonical_url(child["href"])
                if child_url.startswith(ROOT_URL) and child_url not in visited and child_url not in queued:
                    queued.add(child_url)
                    queue.append(child_url)

            for table_record in snapshot["tables"]:
                offers.extend(extract_offers_from_table(page_record, table_record))

        browser.close()

    return pages, offers


def build_output(seed_urls: list[str], pages: list[dict], offers: list[dict]) -> dict:
    families = aggregate_families(offers)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root_url": ROOT_URL,
        "seed_urls": seed_urls,
        "stats": {
            "pages_crawled": len(pages),
            "leaf_pages": sum(1 for page in pages if page["table_count"]),
            "offers": len(offers),
            "families": len(families),
        },
        "pages": pages,
        "families": families,
        "offers": offers,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/mcmaster-glues.json"),
        help="Output JSON path.",
    )
    parser.add_argument(
        "--seed",
        action="append",
        default=[],
        help="Additional seed URL under https://www.mcmaster.com/products/glue/.",
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Skip root discovery and crawl only the explicit --seed URLs.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f"Maximum number of catalog pages to crawl (default: {DEFAULT_MAX_PAGES}).",
    )
    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Print discovered root seed URLs and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_navigation_timeout(DEFAULT_TIMEOUT_MS)
        page.goto(ROOT_URL, wait_until="networkidle", timeout=DEFAULT_TIMEOUT_MS)
        discovered_seed_urls = discover_seed_urls(page)
        browser.close()

    if args.discover_only:
        print(json.dumps(discovered_seed_urls, indent=2))
        return 0

    explicit_seeds = [canonical_url(urljoin(ROOT_URL, seed)) for seed in args.seed]
    if args.seed_only:
        if not explicit_seeds:
            print("--seed-only requires at least one --seed URL.", file=sys.stderr)
            return 2
        seed_urls = explicit_seeds
    else:
        seed_urls = [*discovered_seed_urls, *explicit_seeds]
    unique_seed_urls = []
    seen = set()
    for seed_url in seed_urls:
        if seed_url not in seen:
            seen.add(seed_url)
            unique_seed_urls.append(seed_url)

    pages, offers = crawl_catalog(unique_seed_urls, args.max_pages)
    payload = build_output(unique_seed_urls, pages, offers)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                **payload["stats"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
