#!/usr/bin/env python3
"""Build site-ready manual TDS-backed catalog additions."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "tds-manual-source.json"
OUTPUT_PATH = ROOT / "data" / "tds-manual-catalog.js"

FL_OZ_TO_ML = 29.5735


def round_money(value: float) -> float:
    return round(value + 1e-9, 4)


def package_ml(size: float, unit: str) -> float:
    if unit == "fl-oz":
        return size * FL_OZ_TO_ML
    if unit == "mL":
        return size
    raise ValueError(f"Unsupported price unit: {unit}")


def build_pricing(entry: dict) -> tuple[dict | None, float | None]:
    """Return observed pricing when a distributor price is present, else (None, None).

    Pricing evidence is optional: direct-sale or specialty manufacturers (Master
    Bond, EPO-TEK, DELO, Panacol, etc.) often do not have a public unit price.
    Leaving pricing blank is preferred over inventing a number.
    """
    if entry.get("priceUsd") is None or entry.get("priceSize") is None or not entry.get("priceUnit"):
        return None, None
    size_ml = package_ml(entry["priceSize"], entry["priceUnit"])
    unit_price = round_money(entry["priceUsd"] / size_ml)
    pricing = {
        "basis": "observed",
        "unit": "mL",
        "unitPrice": unit_price,
        "example": entry.get("priceExample"),
        "sourceUrl": entry.get("priceSourceUrl"),
    }
    return pricing, unit_price


def build_selector_product(entry: dict) -> dict:
    pricing, _ = build_pricing(entry)
    product = {
        key: value
        for key, value in entry.items()
        if key
        not in {
            "referenceCategory",
            "referenceSampleType",
            "referenceSampleConsistency",
            "referenceForJoining",
            "priceUsd",
            "priceSize",
            "priceUnit",
            "priceExample",
            "priceSourceUrl",
        }
    }
    if pricing is not None:
        product["pricing"] = pricing
    return product


def build_reference_family(entry: dict) -> dict:
    pricing, unit_price = build_pricing(entry)
    family = {
        "id": entry["id"],
        "manufacturer": entry["maker"],
        "familyName": entry["name"],
        "primaryCategory": entry["referenceCategory"],
        "categories": [entry["referenceCategory"]],
        "sampleType": entry["referenceSampleType"],
        "sampleConsistency": entry["referenceSampleConsistency"],
        "sampleForJoining": entry["referenceForJoining"],
        "applicationTags": entry.get("applicationTags", []),
        "tempMinC": entry.get("serviceMin"),
        "tempMaxC": entry.get("serviceMax"),
        "offerCount": 1,
        "sourceUrl": entry["referenceUrl"],
        "sourceLabel": "TDS",
    }
    if pricing is not None:
        family["bestPricePerMl"] = unit_price
        family["lowestPriceUsd"] = entry.get("priceUsd")
        family["pricing"] = pricing
    return family


def main() -> None:
    source = json.loads(SOURCE_PATH.read_text())
    entries = source.get("entries", [])

    selector_products = [build_selector_product(entry) for entry in entries]
    reference_families = [build_reference_family(entry) for entry in entries]
    payload = (
        "window.TDS_MANUAL_PRODUCTS = "
        + json.dumps(selector_products, indent=2)
        + ";\n\nwindow.TDS_MANUAL_REFERENCE_FAMILIES = "
        + json.dumps(reference_families, indent=2)
        + ";\n\nwindow.TDS_MANUAL_STATS = "
        + json.dumps(
            {
                "selectorProducts": len(selector_products),
                "referenceFamilies": len(reference_families),
            },
            indent=2,
        )
        + ";\n"
    )
    OUTPUT_PATH.write_text(payload)


if __name__ == "__main__":
    main()
