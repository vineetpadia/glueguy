#!/usr/bin/env python3
"""Enrich McMaster adhesive entries with direct part-page details.

This script reads the raw McMaster category crawl and visits direct McMaster
part pages to extract the richer product-detail spec table exposed on each
product page. It supports two target modes:

- ``representative``: one representative offer per family
- ``all-offers``: every unique McMaster part number found in the crawl

The output is a cached JSON artifact that the site-build step can merge back
into selector and reference entries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "mcmaster-glues.json"
OUTPUT_PATH = ROOT / "data" / "mcmaster-product-details.json"
DEFAULT_TIMEOUT_MS = 30_000
DETAIL_ROW_SELECTOR = "[class*='product-detail-spec-table-row']"
ITEM_TABLE_ROW_SELECTOR = "a.PartNbrLnk"
PART_NO_PATTERN = re.compile(r"[0-9]{3,}[A-Z]?[0-9A-Z]*")


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def parse_price_usd(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"\$([\d,]+(?:\.\d+)?)", text)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


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


def extract_part_no_from_url(url: str | None) -> str | None:
    if not url:
        return None
    path = urlparse(url).path.strip("/")
    if PART_NO_PATTERN.fullmatch(path):
        return path
    return None


def canonical_part_url(part_no: str) -> str:
    return f"https://www.mcmaster.com/{part_no}/"


def detail_key(section: str | None, label: str) -> str:
    section_key = slugify(normalize_space(section))
    label_key = slugify(label)

    if label_key == "type":
        if section_key == "container":
            return "container_type"
        return "item_type"
    if label_key == "size":
        return "size"
    if section_key == "strength" and label_key in {"shear", "peel"}:
        return label_key
    if section_key and label_key in {"type", "size", "value"}:
        return f"{section_key}_{label_key}"
    return label_key


def offer_part_target(offer: dict) -> dict | None:
    part_url = next(
        (
            link.get("href")
            for link in offer.get("row_links", [])
            if "mcmaster.com/" in (link.get("href") or "")
        ),
        None,
    )
    part_no = extract_part_no_from_url(part_url) or normalize_space(
        offer.get("fields", {}).get("mcmaster_part_no")
    )
    if not part_no:
        return None
    if not part_url:
        part_url = canonical_part_url(part_no)
    return {
        "part_no": part_no,
        "url": part_url,
        "family_key": offer.get("family_key"),
        "family_name": offer.get("family_name"),
        "offer_fields": dict(offer.get("fields") or {}),
    }


def build_targets(
    raw_payload: dict,
    requested_parts: set[str] | None = None,
    target_mode: str = "representative",
) -> list[dict]:
    if target_mode == "all-offers":
        targets_by_part: dict[str, dict] = {}
        for offer in raw_payload.get("offers", []):
            target = offer_part_target(offer)
            if not target:
                continue
            part_no = target["part_no"]
            if requested_parts and part_no not in requested_parts:
                continue
            targets_by_part.setdefault(part_no, target)
        return [targets_by_part[key] for key in sorted(targets_by_part)]

    family_keys = {family["family_key"] for family in raw_payload.get("families", [])}
    offers_by_family: dict[str, list[dict]] = defaultdict(list)
    for offer in raw_payload.get("offers", []):
        family_key = offer.get("family_key")
        if family_key in family_keys:
            offers_by_family[family_key].append(offer)

    targets: list[dict] = []
    for family_key, offers in sorted(offers_by_family.items()):
        offer = choose_representative_offer(offers)
        target = offer_part_target(offer)
        if not target:
            continue
        part_no = target["part_no"]
        part_url = target["url"]
        if requested_parts and part_no not in requested_parts:
            continue

        targets.append(
            {
                "family_key": family_key,
                "family_name": offer.get("family_name"),
                "part_no": part_no,
                "url": part_url,
            }
        )

    return targets


def build_offer_fallback_detail(target: dict) -> dict | None:
    offer_fields = dict(target.get("offer_fields") or {})
    if not offer_fields:
        return None

    fields: dict[str, str] = {}
    field_mappings = {
        "mfr_model_no": "manufacturer_model_number",
        "for_joining": "for_joining",
        "reaches_full_strength": "reaches_full_strength",
        "mix_ratio": "mix_ratio",
        "color": "color",
        "cure_type": "cure_type",
    }
    for raw_key, detail_name in field_mappings.items():
        value = normalize_space(offer_fields.get(raw_key))
        if value:
            fields[detail_name] = value

    size_text = normalize_space(offer_fields.get("size"))
    if not size_text:
        size_fl_oz = normalize_space(offer_fields.get("size_fl_oz"))
        if size_fl_oz:
            size_text = f"{size_fl_oz} fl. oz."
    if size_text:
        fields["size"] = size_text

    container_type = normalize_space(offer_fields.get("container")) or normalize_space(
        offer_fields.get("type")
    )
    if container_type:
        fields["container_type"] = container_type

    price_text = normalize_space(offer_fields.get("price_each_usd")) or normalize_space(
        offer_fields.get("pkg_price_usd")
    )
    price_text = f"${price_text}" if price_text else None

    return {
        "partNo": target["part_no"],
        "url": target["url"],
        "title": target.get("family_name") or target["part_no"],
        "name": target.get("family_name") or target["part_no"],
        "subtitle": "",
        "priceText": price_text,
        "priceUsd": parse_price_usd(price_text),
        "fields": fields,
        "copy": [],
        "layout": "offer-fallback",
        "itemTableHeaders": [],
        "itemTableCells": [],
        "itemTableRowText": "",
    }


def load_existing_cache() -> tuple[dict[str, dict], dict]:
    if not OUTPUT_PATH.exists():
        return {}, {}
    payload = json.loads(OUTPUT_PATH.read_text())
    return payload.get("detailsByPartNo", {}), payload.get("stats", {})


def extract_page_detail(page, url: str, part_no: str) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    try:
        page.wait_for_load_state("networkidle", timeout=8_000)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_function(
        """([detailSelector, partNo]) => {
          if (document.querySelector(detailSelector)) return true;
          const byAttr = document.querySelector(`a.PartNbrLnk[data-mcm-partnbr="${partNo}"]`);
          if (byAttr) return true;
          return Array.from(document.querySelectorAll("a.PartNbrLnk")).some(
            (link) => (link.textContent || "").replace(/\\s+/g, " ").trim() === partNo
          );
        }""",
        arg=[DETAIL_ROW_SELECTOR, part_no],
        timeout=DEFAULT_TIMEOUT_MS,
    )
    extracted = page.evaluate(
        """(partNo) => {
          const normalize = (value) => (value || "").replace(/\\s+/g, " ").trim();
          const specTable = document.querySelector("[class*='product-detail-spec-table']");
          const rows = [];
          let section = null;

          if (specTable) {
            for (const row of specTable.querySelectorAll("tr")) {
              const cells = Array.from(row.querySelectorAll("td")).map((cell) =>
                normalize(cell.textContent)
              );
              if (cells.length < 2) continue;
              const [label, value] = cells;
              if (!label) continue;
              if (!value) {
                section = label;
                continue;
              }
              rows.push({
                section,
                label,
                value,
                indented: row.className.includes("row-indented"),
              });
            }
          }

          const copyRoot = document.querySelector("[class*='product-detail-copy']");
          const copy = copyRoot
            ? copyRoot.innerText
                .split(/\\n+/)
                .map((entry) => normalize(entry))
                .filter(Boolean)
            : [];

          const partLink =
            document.querySelector(`a.PartNbrLnk[data-mcm-partnbr="${partNo}"]`) ||
            Array.from(document.querySelectorAll("a.PartNbrLnk")).find(
              (link) => normalize(link.textContent) === partNo
            );
          const itemRow = partLink ? partLink.closest("tr") : null;
          const itemTable = partLink ? partLink.closest(".ItmTblCntnr") : null;
          const itemTableHeaders = itemTable
            ? Array.from(itemTable.querySelectorAll("th"))
                .map((entry) => normalize(entry.textContent))
                .filter(Boolean)
            : [];
          const itemTableCells = itemRow
            ? Array.from(itemRow.querySelectorAll("td")).map((cell) => normalize(cell.textContent))
            : [];

          return {
            url: window.location.href,
            title: document.title,
            name: normalize(document.querySelector("[class*='productDetailHeaderPrimary']")?.textContent),
            subtitle: normalize(document.querySelector("[class*='productDetailHeaderSecondary']")?.textContent),
            priceText: normalize(document.querySelector(".PrceTxt")?.textContent),
            specRows: rows,
            copy,
            layout: specTable ? "product-detail" : itemRow ? "item-table" : "unknown",
            itemTableHeaders,
            itemTableCells,
            itemTableRowText: itemRow ? normalize(itemRow.innerText) : "",
          };
        }""",
        part_no,
    )

    fields: dict[str, str] = {}
    for row in extracted.get("specRows", []):
        key = detail_key(row.get("section"), row.get("label") or "")
        value = normalize_space(row.get("value"))
        if key and value and key not in fields:
            fields[key] = value

    return {
        "partNo": part_no,
        "url": extracted.get("url") or url,
        "title": extracted.get("title"),
        "name": extracted.get("name"),
        "subtitle": extracted.get("subtitle"),
        "priceText": extracted.get("priceText"),
        "priceUsd": parse_price_usd(extracted.get("priceText")),
        "fields": fields,
        "copy": extracted.get("copy") or [],
        "layout": extracted.get("layout") or "product-detail",
        "itemTableHeaders": extracted.get("itemTableHeaders") or [],
        "itemTableCells": extracted.get("itemTableCells") or [],
        "itemTableRowText": extracted.get("itemTableRowText") or "",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only enrich the first N selected McMaster part pages.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh existing cached details instead of only fetching missing parts.",
    )
    parser.add_argument(
        "--part-no",
        action="append",
        default=[],
        help="Restrict enrichment to specific McMaster part numbers. Repeatable.",
    )
    parser.add_argument(
        "--target-mode",
        choices=("representative", "all-offers"),
        default="all-offers",
        help="Select whether to enrich one representative page per family or every offer page.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_payload = json.loads(RAW_PATH.read_text())
    requested_parts = {normalize_space(value) for value in args.part_no if normalize_space(value)}
    targets = build_targets(raw_payload, requested_parts or None, args.target_mode)
    if args.limit is not None:
        targets = targets[: args.limit]

    existing_details, existing_stats = load_existing_cache()
    details_by_part_no = dict(existing_details)
    fetched = 0
    cached = 0
    failed = 0
    fallback_from_offer = 0
    failed_parts: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_navigation_timeout(DEFAULT_TIMEOUT_MS)

        for index, target in enumerate(targets, start=1):
            part_no = target["part_no"]
            if not args.refresh and part_no in details_by_part_no:
                cached += 1
                print(
                    f"[detail] {index:03d}/{len(targets):03d} cache {part_no}",
                    file=sys.stderr,
                )
                continue

            print(
                f"[detail] {index:03d}/{len(targets):03d} fetch {part_no} {target['url']}",
                file=sys.stderr,
            )
            try:
                details_by_part_no[part_no] = extract_page_detail(page, target["url"], part_no)
                fetched += 1
            except PlaywrightTimeoutError:
                failed += 1
                failed_parts.append(part_no)
                fallback_detail = build_offer_fallback_detail(target)
                if fallback_detail:
                    details_by_part_no[part_no] = fallback_detail
                    fallback_from_offer += 1
                    print(f"[warn] timeout on {part_no}; using offer fallback", file=sys.stderr)
                else:
                    print(f"[warn] timeout on {part_no}", file=sys.stderr)
            except Exception as exc:  # pragma: no cover - defensive logging
                failed += 1
                failed_parts.append(part_no)
                fallback_detail = build_offer_fallback_detail(target)
                if fallback_detail:
                    details_by_part_no[part_no] = fallback_detail
                    fallback_from_offer += 1
                    print(
                        f"[warn] failed {part_no}: {exc}; using offer fallback",
                        file=sys.stderr,
                    )
                else:
                    print(f"[warn] failed {part_no}: {exc}", file=sys.stderr)

        browser.close()

    target_parts = {target["part_no"] for target in targets}
    missing_parts = sorted(part_no for part_no in target_parts if part_no not in details_by_part_no)
    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_mode": args.target_mode,
        "targeted_pages": len(targets),
        "targeted_families": len({target.get("family_key") for target in targets if target.get("family_key")}),
        "targeted_parts": len(target_parts),
        "detail_pages": len(details_by_part_no),
        "fetched": fetched,
        "cached": cached,
        "failed": failed,
        "fallback_from_offer": fallback_from_offer,
        "missing_pages": len(missing_parts),
        "previous_detail_pages": existing_stats.get("detail_pages"),
    }
    if failed_parts:
        stats["failed_parts"] = failed_parts[:50]
    if missing_parts:
        stats["missing_parts"] = missing_parts[:50]

    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "generated_at": stats["generated_at"],
                "stats": stats,
                "detailsByPartNo": details_by_part_no,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
