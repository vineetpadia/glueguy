#!/usr/bin/env python3
"""Build site-ready manual TDS-backed catalog additions."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "tds-manual-source.json"
OUTPUT_PATH = ROOT / "data" / "tds-manual-catalog.js"
APP_PATH = ROOT / "app.js"

FL_OZ_TO_ML = 29.5735


def round_money(value: float) -> float:
    return round(value + 1e-9, 4)


def package_unit_size(size: float, unit: str) -> tuple[float, str]:
    if unit == "fl-oz":
        return size * FL_OZ_TO_ML, "mL"
    if unit == "mL":
        return size, "mL"
    if unit == "g":
        return size, "g"
    if unit == "stick":
        return size, "stick"
    if unit == "pack":
        return size, "pack"
    if unit == "m2":
        return size, "m2"
    raise ValueError(f"Unsupported price unit: {unit}")


def load_profile_registry() -> tuple[set[str], dict[str, str]]:
    """Read the app's explicit profile registry so generated data cannot drift."""
    import re

    app_text = APP_PATH.read_text()
    profile_match = re.search(
        r"const PROFILE_LIBRARY = \{(?P<body>.*?)\n\};\n\nfunction inferApplicationTagsForProduct",
        app_text,
        re.S,
    )
    alias_match = re.search(r"const PROFILE_ALIASES = \{(?P<body>.*?)\n\};", app_text, re.S)
    if not profile_match or not alias_match:
        raise ValueError("Could not locate PROFILE_LIBRARY and PROFILE_ALIASES in app.js")

    profile_names = set(re.findall(r"^  ([A-Za-z0-9_]+): \{", profile_match.group("body"), re.M))
    aliases = dict(re.findall(r'^  ([A-Za-z0-9_]+): "([A-Za-z0-9_]+)",?$', alias_match.group("body"), re.M))
    bad_aliases = {alias: target for alias, target in aliases.items() if target not in profile_names}
    if bad_aliases:
        raise ValueError(f"Profile aliases point at unknown PROFILE_LIBRARY entries: {bad_aliases}")
    return profile_names, aliases


def validate_profiles(entries: list[dict], profile_names: set[str], aliases: dict[str, str]) -> None:
    invalid = [
        {
            "id": entry.get("id"),
            "profile": entry.get("profile"),
        }
        for entry in entries
        if entry.get("profile") not in profile_names and entry.get("profile") not in aliases
    ]
    if invalid:
        raise ValueError(
            "Manual TDS entries use profiles that are neither in PROFILE_LIBRARY nor PROFILE_ALIASES: "
            + json.dumps(invalid, indent=2)
        )


def omit_null_values(entry: dict) -> dict:
    return {key: value for key, value in entry.items() if value is not None}


def build_pricing(entry: dict) -> tuple[dict | None, float | None]:
    """Return observed pricing when a distributor price is present, else (None, None).

    Pricing evidence is optional: direct-sale or specialty manufacturers (Master
    Bond, EPO-TEK, DELO, Panacol, etc.) often do not have a public unit price.
    Leaving pricing blank is preferred over inventing a number.
    """
    if entry.get("priceUsd") is None or entry.get("priceSize") is None or not entry.get("priceUnit"):
        return None, None
    normalized_size, normalized_unit = package_unit_size(entry["priceSize"], entry["priceUnit"])
    unit_price = round_money(entry["priceUsd"] / normalized_size)
    pricing = {
        "basis": "observed",
        "unit": normalized_unit,
        "unitPrice": unit_price,
        "example": entry.get("priceExample"),
        "sourceUrl": entry.get("priceSourceUrl"),
    }
    return pricing, unit_price


def build_selector_product(entry: dict) -> dict:
    pricing, _ = build_pricing(entry)
    product = {
        key: value
        for key, value in omit_null_values(entry).items()
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
    if pricing is not None and pricing.get("unit") == "mL":
        family["bestPricePerMl"] = unit_price
    if pricing is not None:
        family["bestUnitPrice"] = unit_price
        family["bestUnit"] = pricing.get("unit")
        family["lowestPriceUsd"] = entry.get("priceUsd")
        family["pricing"] = pricing
    return family


def main() -> None:
    source = json.loads(SOURCE_PATH.read_text())
    entries = source.get("entries", [])
    profile_names, aliases = load_profile_registry()
    validate_profiles(entries, profile_names, aliases)

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
