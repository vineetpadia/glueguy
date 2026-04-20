#!/usr/bin/env python3
"""Audit autonomous-source adhesive coverage and emit a ranked backlog report."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEEDS_PATH = ROOT / "data" / "autonomous-research-seeds.json"
DISCOVERED_PATH = ROOT / "data" / "autonomous-discovered-products.json"
MANUAL_SOURCE_PATH = ROOT / "data" / "tds-manual-source.json"
MCMASTER_CATALOG_PATH = ROOT / "data" / "mcmaster-site-catalog.js"
MCMASTER_SUMMARY_PATH = ROOT / "data" / "mcmaster-site-summary.json"
MCMASTER_TDS_PATH = ROOT / "data" / "mcmaster-tds-links.json"
APP_PATH = ROOT / "app.js"
REPORT_JSON_PATH = ROOT / "data" / "autonomous-research-report.json"
REPORT_MD_PATH = ROOT / "data" / "autonomous-research-report.md"

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_space(value).lower())


def normalize_maker(value: str | None) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    if "lord" in text or "fusor" in text:
        return "lord"
    if "epoxyt" in text or "epotek" in text:
        return "epotek"
    if "araldite" in text or "huntsman" in text:
        return "araldite"
    if "born2bond" in text or "bostik" in text or "arkema" in text:
        return "born2bond"
    if "3m" in text:
        return "3m"
    return text


def load_window_json(path: Path, variable_name: str):
    text = path.read_text()
    match = re.search(rf"window\.{re.escape(variable_name)} = (.*?);\s*(?:window\.|$)", text, re.S)
    if not match:
        raise ValueError(f"Could not find {variable_name} in {path}")
    return json.loads(match.group(1))


def load_app_base_records() -> list[dict]:
    text = APP_PATH.read_text()
    records = []
    pattern = re.compile(r'maker:\s*"([^"]+)"[\s\S]{0,240}?name:\s*"([^"]+)"', re.S)
    for match in pattern.finditer(text):
        records.append(
            {
                "source": "app-base",
                "maker": normalize_space(match.group(1)),
                "name": normalize_space(match.group(2)),
                "referenceUrl": None,
            }
        )
    return records


def name_matches(seed_name: str, candidate_name: str) -> bool:
    seed = normalize_text(seed_name)
    candidate = normalize_text(candidate_name)
    if not seed or not candidate:
        return False
    if seed == candidate:
        return True
    if seed in candidate or candidate in seed:
        return True

    # Handle family seeds such as 108B/109B.
    seed_tokens = [token for token in re.split(r"[^a-z0-9]+", seed_name.lower()) if token]
    if seed_tokens and all(token in candidate_name.lower() for token in seed_tokens if any(char.isdigit() for char in token)):
        return True
    return False


def record_matches(seed_maker: str, seed_name: str, record: dict) -> bool:
    if normalize_maker(seed_maker) != normalize_maker(record.get("maker")):
        return False
    return name_matches(seed_name, record.get("name", ""))


def load_catalog_records() -> tuple[list[dict], dict]:
    manual_source = json.loads(MANUAL_SOURCE_PATH.read_text())
    manual_entries = manual_source.get("entries", [])
    mcmaster_products = load_window_json(MCMASTER_CATALOG_PATH, "MCMASTER_SITE_PRODUCTS")
    mcmaster_refs = load_window_json(MCMASTER_CATALOG_PATH, "MCMASTER_REFERENCE_FAMILIES")
    mcmaster_summary = json.loads(MCMASTER_SUMMARY_PATH.read_text())
    mcmaster_tds = json.loads(MCMASTER_TDS_PATH.read_text())
    app_base_records = load_app_base_records()

    records = list(app_base_records)
    for entry in manual_entries:
        records.append(
            {
                "source": "manual",
                "maker": entry.get("maker", ""),
                "name": entry.get("name", ""),
                "referenceUrl": entry.get("referenceUrl"),
            }
        )
    for entry in mcmaster_products:
        records.append(
            {
                "source": "mcmaster",
                "maker": entry.get("maker", ""),
                "name": entry.get("name", ""),
                "referenceUrl": entry.get("referenceUrl"),
            }
        )

    stats = {
        "appBaseRecords": len(app_base_records),
        "manualEntries": len(manual_entries),
        "mcmasterSelectorProducts": len(mcmaster_products),
        "mcmasterReferenceFamilies": len(mcmaster_refs),
        "mcmasterTdsFound": mcmaster_tds.get("stats", {}).get("found", 0),
        "mcmasterProductOnly": mcmaster_tds.get("stats", {}).get("product_only", 0),
        "mcmasterSkipped": mcmaster_tds.get("stats", {}).get("skipped", 0),
        "mcmasterErrors": mcmaster_tds.get("stats", {}).get("errors", 0),
        "mcmasterSummary": mcmaster_summary.get("stats", {}),
    }
    return records, stats


def load_discovered_targets() -> list[dict]:
    if not DISCOVERED_PATH.exists():
        return []
    payload = json.loads(DISCOVERED_PATH.read_text())
    entries = payload.get("entries", [])
    return [
        {
            "maker": entry.get("maker", ""),
            "name": entry.get("name", ""),
            "priority": entry.get("priority", "medium"),
            "officialUrl": entry.get("officialUrl"),
            "officialDomains": entry.get("officialDomains", []),
            "kind": entry.get("kind", "product"),
            "source": "discovered",
        }
        for entry in entries
        if entry.get("maker") and entry.get("name")
    ]


def build_report() -> dict:
    seeds = json.loads(SEEDS_PATH.read_text())
    records, catalog_stats = load_catalog_records()
    discovered_targets = load_discovered_targets()

    manufacturer_rows = []
    missing_rows = []
    covered_count = 0
    total_targets = 0
    curated_total = 0

    for manufacturer in seeds.get("manufacturers", []):
        products = []
        for product in manufacturer.get("products", []):
            total_targets += 1
            curated_total += 1
            matches = [record for record in records if record_matches(manufacturer["name"], product["name"], record)]
            coverage_sources = sorted({match["source"] for match in matches})
            covered = bool(matches)
            if covered:
                covered_count += 1
            else:
                missing_rows.append(
                    {
                        "priority": manufacturer.get("priority", "medium"),
                        "maker": manufacturer["name"],
                        "name": product["name"],
                        "officialUrl": product.get("officialUrl"),
                        "officialDomains": manufacturer.get("officialDomains", []),
                        "targetSource": "curated",
                        "targetKind": "product",
                    }
                )
            products.append(
                {
                    "name": product["name"],
                    "officialUrl": product.get("officialUrl"),
                    "covered": covered,
                    "coverageSources": coverage_sources,
                    "matchedProducts": [
                        {
                            "source": match["source"],
                            "maker": match["maker"],
                            "name": match["name"],
                            "referenceUrl": match.get("referenceUrl"),
                        }
                        for match in matches[:6]
                    ],
                    "targetSource": "curated",
                    "targetKind": "product",
                }
            )

        covered_products = sum(1 for product in products if product["covered"])
        missing_products = sum(1 for product in products if not product["covered"])
        manufacturer_rows.append(
            {
                "name": manufacturer["name"],
                "priority": manufacturer.get("priority", "medium"),
                "officialDomains": manufacturer.get("officialDomains", []),
                "seededProducts": len(products),
                "coveredProducts": covered_products,
                "missingProducts": missing_products,
                "coverageRatio": round(covered_products / len(products), 3) if products else 0.0,
                "products": products,
            }
        )

    discovered_by_maker: dict[str, list[dict]] = {}
    for target in discovered_targets:
        discovered_by_maker.setdefault(target["maker"], []).append(target)

    for maker, products in discovered_by_maker.items():
        row = next((entry for entry in manufacturer_rows if normalize_maker(entry["name"]) == normalize_maker(maker)), None)
        if row is None:
            row = {
                "name": maker,
                "priority": products[0].get("priority", "medium"),
                "officialDomains": products[0].get("officialDomains", []),
                "seededProducts": 0,
                "coveredProducts": 0,
                "missingProducts": 0,
                "coverageRatio": 0.0,
                "products": [],
            }
            manufacturer_rows.append(row)
        for product in products:
            if any(name_matches(product["name"], existing["name"]) for existing in row["products"]):
                continue
            total_targets += 1
            matches = [record for record in records if record_matches(maker, product["name"], record)]
            coverage_sources = sorted({match["source"] for match in matches})
            covered = bool(matches)
            if covered:
                covered_count += 1
                row["coveredProducts"] += 1
            else:
                row["missingProducts"] += 1
                missing_rows.append(
                    {
                        "priority": product.get("priority", "medium"),
                        "maker": maker,
                        "name": product["name"],
                        "officialUrl": product.get("officialUrl"),
                        "officialDomains": product.get("officialDomains", []),
                        "targetSource": "discovered",
                        "targetKind": product.get("kind", "product"),
                    }
                )
            row["products"].append(
                {
                    "name": product["name"],
                    "officialUrl": product.get("officialUrl"),
                    "covered": covered,
                    "coverageSources": coverage_sources,
                    "matchedProducts": [
                        {
                            "source": match["source"],
                            "maker": match["maker"],
                            "name": match["name"],
                            "referenceUrl": match.get("referenceUrl"),
                        }
                        for match in matches[:6]
                    ],
                    "targetSource": "discovered",
                    "targetKind": product.get("kind", "product"),
                }
            )

    for row in manufacturer_rows:
        row["seededProducts"] = len(row["products"])
        row["coverageRatio"] = round(row["coveredProducts"] / row["seededProducts"], 3) if row["seededProducts"] else 0.0

    missing_rows.sort(
        key=lambda row: (
            PRIORITY_ORDER.get(row["priority"], 99),
            0 if row.get("targetSource") == "curated" else 1,
            0 if row.get("officialUrl") else 1,
            normalize_text(row["maker"]),
            normalize_text(row["name"]),
        )
    )
    manufacturer_rows.sort(
        key=lambda row: (
            PRIORITY_ORDER.get(row["priority"], 99),
            row["missingProducts"] == 0,
            normalize_text(row["name"]),
        )
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            **catalog_stats,
            "seededManufacturers": len(manufacturer_rows),
            "curatedSeedProducts": curated_total,
            "discoveredProducts": len(discovered_targets),
            "seededProducts": total_targets,
            "coveredSeedProducts": covered_count,
            "missingSeedProducts": total_targets - covered_count,
            "coverageRatio": round(covered_count / total_targets, 3) if total_targets else 0.0,
        },
        "manufacturers": manufacturer_rows,
        "nextActions": missing_rows[:20],
        "allMissing": missing_rows,
    }


def render_report_md(report: dict) -> str:
    stats = report["stats"]
    lines = [
        "# Autonomous Glue Research Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Snapshot",
        "",
        f"- Built-in app catalog records scanned: {stats['appBaseRecords']}",
        f"- Manual TDS-backed entries: {stats['manualEntries']}",
        f"- McMaster selector products: {stats['mcmasterSelectorProducts']}",
        f"- McMaster reference families: {stats['mcmasterReferenceFamilies']}",
        f"- McMaster official-TDS matches: {stats['mcmasterTdsFound']}",
        f"- McMaster product-page-only matches: {stats['mcmasterProductOnly']}",
        f"- Seeded manufacturers: {stats['seededManufacturers']}",
        f"- Curated seed products: {stats['curatedSeedProducts']}",
        f"- Discovered official-source leads: {stats['discoveredProducts']}",
        f"- Total target products/families: {stats['seededProducts']}",
        f"- Covered seed products in autonomous sources: {stats['coveredSeedProducts']}",
        f"- Missing seed products in autonomous sources: {stats['missingSeedProducts']}",
        "",
        "## Next Actions",
        "",
        "| Priority | Source | Kind | Manufacturer | Product | Official lead |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for row in report["nextActions"]:
        official = row["officialUrl"] or ", ".join(row.get("officialDomains", [])) or "Search official site"
        lines.append(
            f"| {row['priority']} | {row.get('targetSource', 'curated')} | {row.get('targetKind', 'product')} | {row['maker']} | {row['name']} | {official} |"
        )

    lines.extend(
        [
            "",
            "## Manufacturer Coverage",
            "",
            "| Priority | Manufacturer | Seeded | Covered | Missing | Official domains |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )

    for row in report["manufacturers"]:
        domains = ", ".join(row.get("officialDomains", []))
        lines.append(
            f"| {row['priority']} | {row['name']} | {row['seededProducts']} | {row['coveredProducts']} | {row['missingProducts']} | {domains} |"
        )

    lines.append("")
    lines.append("## Missing By Manufacturer")
    lines.append("")

    for row in report["manufacturers"]:
        missing = [product for product in row["products"] if not product["covered"]]
        if not missing:
            continue
        lines.append(f"### {row['name']}")
        lines.append("")
        for product in missing:
            official = f" ({product['officialUrl']})" if product.get("officialUrl") else ""
            lines.append(
                f"- [{product.get('targetSource', 'curated')}/{product.get('targetKind', 'product')}] {product['name']}{official}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    report = build_report()
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2) + "\n")
    REPORT_MD_PATH.write_text(render_report_md(report))


if __name__ == "__main__":
    main()
