#!/usr/bin/env python3
"""Build the lightweight first-load selector catalog."""

from __future__ import annotations

import re
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MCMASTER_PATH = ROOT / "data" / "mcmaster-site-catalog.js"
TDS_PATH = ROOT / "data" / "tds-manual-catalog.js"
OUTPUT_PATH = ROOT / "data" / "selector-catalog.js"
JSON_OUTPUT_PATH = ROOT / "data" / "selector-catalog.json"

SELECTOR_PRODUCT_FIELDS = {
    "id",
    "profile",
    "maker",
    "name",
    "chemistry",
    "cureFamily",
    "serviceMin",
    "serviceMax",
    "viscosityClass",
    "thixotropic",
    "gapFill",
    "thermalConductivity",
    "clarity",
    "potLife",
    "fixtureTime",
    "lapShear",
    "stress",
    "environment",
    "substrates",
    "cautions",
    "pricing",
    "mcmaster",
    "applicationTags",
    "referenceUrl",
    "specUrl",
    "tdsUrl",
    "productUrl",
    "sdsUrl",
    "catalogUrl",
    "sourceLabel",
    "compatibleMaterialPairs",
    "incompatibleMaterialPairs",
    "professionalUseOnly",
    "rawSolventMethod",
    "flammable",
    "chlorinatedSolvent",
    "containsMethyleneChloride",
    "containsChloroform",
    "containsMek",
    "vocFree",
    "pipeCodeWarning",
}

MCMASTER_FIELDS = {
    "partNo",
    "packageSize",
    "packageType",
    "packageLabel",
    "color",
    "peelStrength",
    "consistency",
    "cureType",
    "mixRatio",
    "sourceLabel",
}


def extract_assignment(text: str, name: str) -> str:
    match = re.search(
        rf"window\.{re.escape(name)} = (?P<body>.*?);\n",
        text,
        re.S,
    )
    if not match:
        raise ValueError(f"Could not find window.{name}")
    return match.group("body")


def compact_products(products: list[dict]) -> list[dict]:
    compacted = []
    for product in products:
        item = {key: product[key] for key in SELECTOR_PRODUCT_FIELDS if key in product}
        if "mcmaster" in item:
            item["mcmaster"] = {
                key: item["mcmaster"][key]
                for key in MCMASTER_FIELDS
                if key in item["mcmaster"]
            }
        compacted.append(item)
    return compacted


def main() -> None:
    mcmaster = MCMASTER_PATH.read_text()
    tds = TDS_PATH.read_text()
    mcmaster_products = compact_products(
        json.loads(extract_assignment(mcmaster, "MCMASTER_SITE_PRODUCTS")),
    )
    tds_products = compact_products(json.loads(extract_assignment(tds, "TDS_MANUAL_PRODUCTS")))
    payload = "\n\n".join(
        [
            "window.MCMASTER_SITE_PRODUCTS = "
            + json.dumps(mcmaster_products, separators=(",", ":"))
            + ";",
            f"window.MCMASTER_PIPELINE_STATS = {extract_assignment(mcmaster, 'MCMASTER_PIPELINE_STATS')};",
            "window.TDS_MANUAL_PRODUCTS = "
            + json.dumps(tds_products, separators=(",", ":"))
            + ";",
            f"window.TDS_MANUAL_STATS = {extract_assignment(tds, 'TDS_MANUAL_STATS')};",
        ],
    )
    OUTPUT_PATH.write_text(payload + "\n")
    JSON_OUTPUT_PATH.write_text(
        json.dumps(
            {
                "mcmasterProducts": mcmaster_products,
                "mcmasterStats": json.loads(extract_assignment(mcmaster, "MCMASTER_PIPELINE_STATS")),
                "tdsProducts": tds_products,
                "tdsStats": json.loads(extract_assignment(tds, "TDS_MANUAL_STATS")),
            },
            separators=(",", ":"),
        )
        + "\n",
    )


if __name__ == "__main__":
    main()
