#!/usr/bin/env python3
"""Normalize the Digi-Key glue/adhesives/applicators CSV into TDS lead data."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "glue__adhesives__applicators.csv"
OUTPUT_PATH = ROOT / "data" / "digikey-electronics-adhesives.json"

ANCILLARY_RE = re.compile(
    r"\b(applicator|primer|activator|hardener|hardner|mixer|mixers|nozzle|dispenser|gun|tips?)\b",
    re.I,
)
NON_ADHESIVE_RE = re.compile(
    r"\b(carbon conductive paste|assembly paste|thermal grease|contact grease|conductive grease|dielectric grease)\b",
    re.I,
)
ELECTRONICS_RE = re.compile(
    r"\b(electronic|electronics|pcb|circuit|conductive|thermally conductive|potting|encapsul|non-corrosive|non corrosive|heat cure|silicone|rtv|die attach|chip)\b",
    re.I,
)
GENERIC_SERIES = {"", "-", "*", "rtv", "scotch-weld", "chipquik"}
PACKAGE_SUFFIX_RE = re.compile(
    r"(\s|-)?\b\d+(?:\.\d+)?\s*(ml|mL|l|liter|liters|litre|litres|g|G|gram|grams|oz|ounce|ounces|fl\.?\s*oz|pint|quart|gal|kg|lb|pack|packs|ct|syr|tube|bottle|cart|cartridge|bulk)\b.*$",
    re.I,
)


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_space(value).lower())


def normalize_url(value: str | None) -> str:
    url = normalize_space(value)
    if url.startswith("//"):
        return "https:" + url
    return url


def parse_int(value: str | None) -> int | None:
    text = normalize_space(value).replace(",", "")
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_float(value: str | None) -> float | None:
    text = normalize_space(value).replace(",", "").replace("$", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def clean_series(value: str | None) -> str:
    text = normalize_space(value)
    text = text.replace("(TM)", "").replace("(R)", "")
    text = re.sub(r"[\u2122\u00ae]", "", text)
    return normalize_space(text)


def base_part_name(value: str | None) -> str:
    part = normalize_space(value)
    part = PACKAGE_SUFFIX_RE.sub("", part)
    part = re.sub(r"\s+\(\d+\s+packs?\).*$", "", part, flags=re.I)
    return normalize_space(part) or normalize_space(value)


def product_name(row: dict) -> str:
    maker = normalize_space(row.get("Mfr"))
    series = clean_series(row.get("Series"))
    part = base_part_name(row.get("Mfr Part #"))
    if normalize_text(series) not in GENERIC_SERIES and len(series) >= 3:
        series_key = normalize_text(series)
        part_key = normalize_text(part)
        if part_key.startswith(series_key) and part_key != series_key:
            suffix = part_key[len(series_key):]
            if suffix and suffix[0].isalpha():
                return part
        if normalize_text(series) not in normalize_text(part) and re.search(r"\d", part):
            return normalize_space(f"{series} ({part})")
        return series
    if maker == "3M" and part and not part.lower().startswith("3m "):
        return normalize_space(f"3M {part}")
    return part


def classify_row(row: dict) -> tuple[bool, bool, int]:
    combined = " ".join(
        normalize_space(row.get(column))
        for column in ["Type", "Description", "Features", "For Use With/Related Products", "Series", "Mfr Part #"]
    )
    is_ancillary = bool(ANCILLARY_RE.search(combined) or NON_ADHESIVE_RE.search(combined))
    adhesive_likely = not is_ancillary and bool(
        re.search(r"\b(adhesive|epoxy|silicone|urethane|acrylic|sealant|potting|threadlocker|cyanoacrylate|resin|rubber|film|cement)\b", combined, re.I)
    )
    electronics_relevant = bool(ELECTRONICS_RE.search(combined))
    score = 0
    if adhesive_likely:
        score += 25
    if electronics_relevant:
        score += 35
    if normalize_url(row.get("Datasheet")):
        score += 20
    if normalize_space(row.get("Product Status")).lower() == "active":
        score += 10
    if parse_int(row.get("Stock") or ""):
        score += 5
    maker = normalize_text(row.get("Mfr"))
    if maker in {"mgchemicals", "loctite", "momentiveperformancematerials", "chemtronics", "epoxytechnology", "dow", "chipquikinc"}:
        score += 10
    return adhesive_likely, electronics_relevant, score


def read_rows() -> list[dict]:
    if not INPUT_PATH.exists():
        return []
    with INPUT_PATH.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_payload() -> dict:
    raw_rows = read_rows()
    normalized_rows = []
    leads_by_key: dict[tuple[str, str], dict] = {}
    datasheet_groups: dict[str, list[dict]] = defaultdict(list)

    for row in raw_rows:
        datasheet_url = normalize_url(row.get("Datasheet"))
        image_url = normalize_url(row.get("Image"))
        adhesive_likely, electronics_relevant, score = classify_row(row)
        lead_name = product_name(row)
        normalized = {
            "distributor": "Digi-Key",
            "maker": normalize_space(row.get("Mfr")),
            "supplier": normalize_space(row.get("Supplier")),
            "name": lead_name,
            "mfrPart": normalize_space(row.get("Mfr Part #")),
            "digikeyPart": normalize_space(row.get("DK Part #")),
            "series": clean_series(row.get("Series")),
            "description": normalize_space(row.get("Description")),
            "type": normalize_space(row.get("Type")),
            "features": normalize_space(row.get("Features")),
            "forUseWith": normalize_space(row.get("For Use With/Related Products")),
            "status": normalize_space(row.get("Product Status")),
            "stock": parse_int(row.get("Stock")),
            "priceUsd": parse_float(row.get("Price")),
            "priceQuantity": parse_int(row.get("@ qty")),
            "minimumQuantity": parse_int(row.get("Min Qty")),
            "package": normalize_space(row.get(" Package")),
            "datasheetUrl": datasheet_url,
            "datasheetHost": urlparse(datasheet_url).netloc,
            "imageUrl": image_url,
            "productUrl": normalize_url(row.get("URL")),
            "adhesiveLikely": adhesive_likely,
            "electronicsRelevant": electronics_relevant,
            "leadScore": score,
        }
        normalized_rows.append(normalized)
        if datasheet_url:
            datasheet_groups[datasheet_url].append(normalized)
        if not adhesive_likely or not lead_name:
            continue
        key = (normalize_text(normalized["maker"]), normalize_text(lead_name))
        existing = leads_by_key.get(key)
        offer = {
            "mfrPart": normalized["mfrPart"],
            "digikeyPart": normalized["digikeyPart"],
            "stock": normalized["stock"],
            "priceUsd": normalized["priceUsd"],
            "productUrl": normalized["productUrl"],
            "features": normalized["features"],
            "package": normalized["package"],
        }
        if existing is None:
            leads_by_key[key] = {
                "maker": normalized["maker"],
                "name": lead_name,
                "supplier": normalized["supplier"],
                "series": normalized["series"],
                "type": normalized["type"],
                "description": normalized["description"],
                "features": normalized["features"],
                "forUseWith": normalized["forUseWith"],
                "status": normalized["status"],
                "datasheetUrl": datasheet_url,
                "datasheetHost": normalized["datasheetHost"],
                "datasheetUrls": [datasheet_url] if datasheet_url else [],
                "primaryDatasheetScore": score,
                "electronicsRelevant": electronics_relevant,
                "leadScore": score,
                "offerCount": 1,
                "totalStock": normalized["stock"] or 0,
                "bestPriceUsd": normalized["priceUsd"],
                "offers": [offer],
            }
        else:
            primary_score = existing.get("primaryDatasheetScore", 0)
            existing["offerCount"] += 1
            existing["totalStock"] += normalized["stock"] or 0
            existing["electronicsRelevant"] = existing["electronicsRelevant"] or electronics_relevant
            if datasheet_url and datasheet_url not in existing["datasheetUrls"]:
                existing["datasheetUrls"].append(datasheet_url)
            if datasheet_url and (not existing.get("datasheetUrl") or score > primary_score):
                existing["datasheetUrl"] = datasheet_url
                existing["datasheetHost"] = normalized["datasheetHost"]
                existing["primaryDatasheetScore"] = score
            existing["leadScore"] = max(existing["leadScore"], score)
            if normalized["priceUsd"] is not None:
                prices = [price for price in [existing.get("bestPriceUsd"), normalized["priceUsd"]] if price is not None]
                existing["bestPriceUsd"] = min(prices) if prices else None
            existing["offers"].append(offer)

    product_leads = sorted(
        leads_by_key.values(),
        key=lambda row: (-row["leadScore"], normalize_text(row["maker"]), normalize_text(row["name"]), row.get("datasheetUrl") or ""),
    )
    datasheet_leads = []
    for url, rows in datasheet_groups.items():
        adhesive_rows = [row for row in rows if row["adhesiveLikely"]]
        datasheet_leads.append(
            {
                "datasheetUrl": url,
                "datasheetHost": urlparse(url).netloc,
                "makerCount": len({normalize_text(row["maker"]) for row in adhesive_rows or rows}),
                "productCount": len({normalize_text(row["name"]) for row in adhesive_rows or rows}),
                "offerCount": len(rows),
                "electronicsRelevant": any(row["electronicsRelevant"] for row in rows),
                "topLeadScore": max(row["leadScore"] for row in rows),
                "products": [
                    {
                        "maker": row["maker"],
                        "name": row["name"],
                        "mfrPart": row["mfrPart"],
                        "type": row["type"],
                    }
                    for row in sorted(rows, key=lambda item: (-item["leadScore"], normalize_text(item["maker"]), normalize_text(item["name"])))[:12]
                ],
            }
        )
    datasheet_leads.sort(key=lambda row: (-row["topLeadScore"], -row["offerCount"], row["datasheetUrl"]))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": str(INPUT_PATH.relative_to(ROOT)),
            "sourceType": "digikey-export",
            "category": "Glue, Adhesives, Applicators",
        },
        "stats": {
            "rows": len(normalized_rows),
            "adhesiveLikelyRows": sum(1 for row in normalized_rows if row["adhesiveLikely"]),
            "electronicsRelevantRows": sum(1 for row in normalized_rows if row["electronicsRelevant"]),
            "uniqueDatasheets": len(datasheet_groups),
            "productLeads": len(product_leads),
            "electronicsProductLeads": sum(1 for row in product_leads if row["electronicsRelevant"]),
        },
        "productLeads": product_leads,
        "datasheetLeads": datasheet_leads,
        "rows": normalized_rows,
    }


def main() -> None:
    payload = build_payload()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
