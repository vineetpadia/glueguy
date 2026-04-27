#!/usr/bin/env python3
"""Build a compact, LLM-agent-friendly adhesive catalog."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from autonomous_glue_research import manual_field_status, normalized_electrical_behavior


ROOT = Path(__file__).resolve().parents[1]
MANUAL_SOURCE_PATH = ROOT / "data" / "tds-manual-source.json"
MCMASTER_CATALOG_PATH = ROOT / "data" / "mcmaster-site-catalog.js"
REPORT_PATH = ROOT / "data" / "autonomous-research-report.json"
CACHE_MANIFEST_PATH = ROOT / "data" / "tds-cache-manifest.json"
EXTRACTION_SUGGESTIONS_PATH = ROOT / "data" / "tds-extraction-suggestions.json"
OUTPUT_PATH = ROOT / "data" / "agent-catalog.json"

DECISION_FIELDS = [
    "serviceMin",
    "serviceMax",
    "potLife",
    "fixtureTime",
    "lapShear",
    "viscosityClass",
    "clarity",
    "thermalConductivity",
    "stress",
    "substrates",
    "cautions",
]
ELECTRONICS_FIELDS = [
    "viscosityValue",
    "viscosityUnit",
    "electricalBehavior",
    "volumeResistivityOhmM",
    "surfaceResistivityOhm",
    "connectionResistanceOhm",
    "insulationResistanceOhm",
    "dielectricConstant",
    "dissipationFactor",
    "dielectricBreakdownVPerMil",
    "dielectricBreakdownKVPerMm",
    "tensileStrengthMPa",
    "elongationPct",
    "hardnessValue",
    "hardnessScale",
    "peelStrengthNPerM",
    "chipBondStrengthMPa",
    "cureDepthMm",
    "tackFreeTime",
    "cureProfiles",
]
FIELD_ALIASES = {
    "electricalBehavior": [
        "electricalBehaviorDetail",
        "electricalBehaviorNote",
        "dielectricBreakdownKVPerMm",
        "dielectricBreakdownVPerMil",
        "dielectricConstant",
        "volumeResistivityOhmM",
        "volumeResistivityOhmCm",
        "surfaceResistivityOhm",
        "connectionResistanceOhm",
        "coatingResistanceOhm",
        "electricalResistanceOhm",
        "insulationResistanceOhm",
    ],
    "viscosityValue": ["viscosityRangeMpaS", "viscosityByShearRateMpaS", "componentViscositiesCps"],
    "viscosityUnit": ["viscosityRangeMpaS", "viscosityByShearRateMpaS", "componentViscositiesCps"],
    "connectionResistanceOhm": [
        "connectionResistance",
        "coatingResistanceOhm",
        "electricalResistanceOhm",
        "surfaceResistanceOhm",
        "connectionResistanceProfilesOhm",
    ],
    "surfaceResistivityOhm": ["surfaceResistivity", "surfaceResistivityOhmCm"],
    "insulationResistanceOhm": ["insulationResistance", "dielectricResistanceOhm", "surfaceInsulationResistanceOhm"],
    "volumeResistivityOhmM": ["volumeResistivity", "volumeResistivityOhmCm", "volumeResistivityRangeOhmM", "volumeResistivityRangeOhmCm"],
    "dielectricConstant": ["dielectricConstantRange", "dielectricConstantProfiles"],
    "dielectricBreakdownVPerMil": ["dielectricBreakdown", "dielectricBreakdownVoltageKV", "dielectricBreakdownKVPerMm"],
    "dielectricBreakdownKVPerMm": ["dielectricBreakdown", "dielectricBreakdownRangeKVPerMm", "dielectricBreakdownKVPerM", "dielectricBreakdownVoltageKV"],
    "tensileStrengthMPa": ["tensileStrength", "tensileStrengthRangeMPa", "tensileStrengthPsi", "tensileStrengthRangePsi"],
    "elongationPct": ["elongationRangePct", "elongation"],
    "hardnessValue": ["hardnessRange", "hardnessValueAlt"],
    "peelStrengthNPerM": ["peelStrengthNPer25Mm", "peelStrengthProfilesNPerM", "peelAdhesionProfilesNPer100Mm"],
    "chipBondStrengthMPa": ["dieShearStrengthPsi", "dieShearStrengthKgf", "dieShearStrengthProfilesN"],
    "cureDepthMm": ["depthCurabilityMm", "thickFilmCurabilityMm"],
    "tackFreeTime": ["tackFreeTimeMinutes", "tackFreeTimeRangeMinutes"],
    "cureProfiles": ["fullCureProfiles", "fullCureMinutes", "fullCureHours", "workingStrengthProfiles", "uvDoseKJPerM2", "cureDoseMjCm2"],
}
RANK_SPEC_FIELDS = [
    "lapShear",
    "thermalConductivity",
    "dielectricBreakdownKVPerMm",
    "volumeResistivityOhmM",
    "tensileStrengthMPa",
    "elongationPct",
    "hardnessValue",
    "peelStrengthNPerM",
]


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def load_window_json(path: Path, variable_name: str):
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"window\.{re.escape(variable_name)} = (.*?);\s*(?:window\.|$)", text, re.S)
    if not match:
        raise ValueError(f"Could not find {variable_name} in {path}")
    return json.loads(match.group(1))


def has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(normalize_space(value))
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def field_value(entry: dict, field: str):
    if has_value(entry.get(field)):
        return entry.get(field)
    for alias in FIELD_ALIASES.get(field, []):
        if has_value(entry.get(alias)):
            return entry.get(alias)
    return None


def fields_by_status(entry: dict, fields: list[str]) -> dict[str, list[str]]:
    grouped = {"value": [], "alias": [], "verified_absent": [], "not_applicable": [], "missing": []}
    for field in fields:
        grouped[manual_field_status(entry, field)["status"]].append(field)
    return grouped


def build_cache_index() -> dict[str, dict]:
    if not CACHE_MANIFEST_PATH.exists():
        return {}
    payload = json.loads(CACHE_MANIFEST_PATH.read_text(encoding="utf-8"))
    return {entry.get("id"): entry for entry in payload.get("entries", []) if entry.get("id")}


def build_extraction_index() -> dict[str, dict]:
    if not EXTRACTION_SUGGESTIONS_PATH.exists():
        return {}
    payload = json.loads(EXTRACTION_SUGGESTIONS_PATH.read_text(encoding="utf-8"))
    return {entry.get("id"): entry for entry in payload.get("suggestions", []) if entry.get("id")}


def coverage(entry: dict, fields: list[str]) -> tuple[float, float, list[str], list[str], list[str], list[str], list[str]]:
    grouped = fields_by_status(entry, fields)
    value_present = grouped["value"] + grouped["alias"]
    covered = value_present + grouped["verified_absent"] + grouped["not_applicable"]
    return (
        round(len(covered) / len(fields), 3),
        round(len(value_present) / len(fields), 3),
        value_present,
        grouped["missing"],
        grouped["verified_absent"],
        grouped["not_applicable"],
        grouped["alias"],
    )


def source_quality(entry: dict, cache_index: dict[str, dict]) -> str:
    cache = cache_index.get(entry.get("id"), {})
    if cache.get("textPath") and not cache.get("error"):
        return "cached-official-tds-text"
    url = normalize_space(entry.get("tdsUrl") or entry.get("referenceUrl")).lower()
    if ".pdf" in url or "/download/" in url or "documentdelivery" in url:
        return "official-tds-url"
    if entry.get("sourceLabel") == "McMaster":
        return "mcmaster-product-page"
    return "product-or-catalog-page"


def compact_specs(entry: dict) -> dict:
    keys = [
        "chemistry",
        "cureFamily",
        "cureDetail",
        "serviceMin",
        "serviceMax",
        "serviceTemperatureNote",
        "gapFill",
        "potLife",
        "fixtureTime",
        "lapShear",
        "lapShearSubstrate",
        "viscosityClass",
        "viscosityValue",
        "viscosityUnit",
        "clarity",
        "thermalConductivity",
        "electricalBehavior",
        "volumeResistivityOhmM",
        "surfaceResistivityOhm",
        "dielectricConstant",
        "dissipationFactor",
        "dielectricBreakdownKVPerMm",
        "tensileStrengthMPa",
        "elongationPct",
        "hardnessValue",
        "hardnessScale",
        "peelStrengthNPerM",
        "chipBondStrengthMPa",
        "cureDepthMm",
        "tackFreeTime",
        "cureProfiles",
    ]
    return {key: value for key in keys if has_value(value := field_value(entry, key))}


def agent_notes(entry: dict, decision_missing: list[str], electronics_missing: list[str], verified_absent: list[str], not_applicable: list[str]) -> list[str]:
    notes = []
    if entry.get("excludeElectronicsCompleteness"):
        notes.append("Do not score this as an electronics-performance adhesive unless another source is added.")
    if decision_missing:
        notes.append("Missing decision fields: " + ", ".join(decision_missing))
    if electronics_missing and not entry.get("excludeElectronicsCompleteness"):
        notes.append("Missing electronics fields: " + ", ".join(electronics_missing[:8]))
    if verified_absent:
        notes.append("Verified absent from available TDS fields: " + ", ".join(verified_absent[:8]))
    if not_applicable:
        notes.append("Not applicable to this product/behavior: " + ", ".join(not_applicable[:8]))
    if entry.get("cautions"):
        notes.extend(entry["cautions"][:3])
    return notes


def product_record(entry: dict, cache_index: dict[str, dict], extraction_index: dict[str, dict], source: str) -> dict:
    decision_score, decision_value_score, decision_present, decision_missing, decision_absent, decision_na, decision_alias = coverage(entry, DECISION_FIELDS)
    electronics_score, electronics_value_score, electronics_present, electronics_missing, electronics_absent, electronics_na, electronics_alias = coverage(entry, ELECTRONICS_FIELDS)
    cache = cache_index.get(entry.get("id"), {})
    extraction = extraction_index.get(entry.get("id"), {})
    specs = compact_specs(entry)
    rankable = {field: specs[field] for field in RANK_SPEC_FIELDS if field in specs}
    return {
        "id": entry.get("id"),
        "source": source,
        "maker": entry.get("maker"),
        "name": entry.get("name"),
        "profile": entry.get("profile") or entry.get("profileKey"),
        "summary": entry.get("summary"),
        "applicationTags": entry.get("applicationTags", []),
        "referenceCategory": entry.get("referenceCategory"),
        "referenceForJoining": entry.get("referenceForJoining"),
        "electricalBehaviorClass": normalized_electrical_behavior(entry),
        "specs": specs,
        "rankableSpecs": rankable,
        "pricing": entry.get("pricing"),
        "sources": {
            "referenceUrl": entry.get("referenceUrl"),
            "tdsUrl": entry.get("tdsUrl"),
            "productUrl": entry.get("productUrl"),
            "sourceLabel": entry.get("sourceLabel"),
            "tdsCacheTextPath": cache.get("textPath"),
            "sourceQuality": source_quality(entry, cache_index),
        },
        "coverage": {
            "decision": decision_score,
            "electronics": electronics_score,
            "decisionValueCoverage": decision_value_score,
            "electronicsValueCoverage": electronics_value_score,
            "decisionFieldsPresent": decision_present,
            "electronicsFieldsPresent": electronics_present,
            "decisionFieldsMissing": decision_missing,
            "electronicsFieldsMissing": electronics_missing,
            "decisionFieldsVerifiedAbsent": decision_absent,
            "electronicsFieldsVerifiedAbsent": electronics_absent,
            "decisionFieldsNotApplicable": decision_na,
            "electronicsFieldsNotApplicable": electronics_na,
            "decisionFieldsAliasCovered": decision_alias,
            "electronicsFieldsAliasCovered": electronics_alias,
        },
        "agentNotes": agent_notes(entry, decision_missing, electronics_missing, decision_absent + electronics_absent, decision_na + electronics_na),
        "extractionCandidates": [
            {
                "field": candidate.get("field"),
                "value": candidate.get("value"),
                "confidence": candidate.get("confidence"),
                "evidence": candidate.get("evidence"),
                "note": candidate.get("note"),
            }
            for candidate in extraction.get("candidates", [])[:8]
        ],
    }


def build_indexes(products: list[dict]) -> dict:
    by_maker: dict[str, list[str]] = {}
    by_application: dict[str, list[str]] = {}
    by_source_quality: dict[str, int] = {}
    for product in products:
        by_maker.setdefault(product["maker"] or "Unknown", []).append(product["id"])
        for tag in product.get("applicationTags", []):
            by_application.setdefault(tag, []).append(product["id"])
        quality = product["sources"]["sourceQuality"]
        by_source_quality[quality] = by_source_quality.get(quality, 0) + 1
    return {
        "byMaker": {key: sorted(value) for key, value in sorted(by_maker.items())},
        "byApplicationTag": {key: sorted(value) for key, value in sorted(by_application.items())},
        "sourceQualityCounts": dict(sorted(by_source_quality.items())),
    }


def main() -> None:
    manual = json.loads(MANUAL_SOURCE_PATH.read_text(encoding="utf-8")).get("entries", [])
    mcmaster = load_window_json(MCMASTER_CATALOG_PATH, "MCMASTER_SITE_PRODUCTS")
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8")) if REPORT_PATH.exists() else {}
    cache_index = build_cache_index()
    extraction_index = build_extraction_index()

    products = [
        *(product_record(entry, cache_index, extraction_index, "manual-tds") for entry in manual),
        *(product_record(entry, cache_index, extraction_index, "mcmaster-derived") for entry in mcmaster),
    ]
    products.sort(key=lambda row: (normalize_space(row.get("maker")).lower(), normalize_space(row.get("name")).lower(), row["id"]))

    payload = {
        "schemaVersion": 2,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "intendedUse": "Machine-readable adhesive catalog for LLM/tool agents. Prefer exact specs and source URLs; do not infer missing values.",
        "queryGuidance": [
            "Filter by applicationTags, substrates, serviceMin/serviceMax, chemistry/cureFamily, and sourceQuality before ranking.",
            "Use rankableSpecs only when comparing numeric performance; read agentNotes before recommending.",
            "If a required field is listed under coverage.*FieldsMissing, report it as unavailable instead of backfilling from profile defaults.",
            "Treat coverage.*FieldsVerifiedAbsent as source-checked omissions and coverage.*FieldsNotApplicable as excluded from behavior-specific scoring.",
            "Use sources.tdsCacheTextPath or sources.tdsUrl for evidence lookup before high-stakes recommendations.",
        ],
        "stats": {
            "products": len(products),
            "manualTdsProducts": len(manual),
            "mcmasterDerivedProducts": len(mcmaster),
            "productsWithExtractionCandidates": sum(1 for product in products if product["extractionCandidates"]),
            "auditStats": report.get("stats", {}),
        },
        "indexes": build_indexes(products),
        "products": products,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_PATH.relative_to(ROOT)), "products": len(products)}, indent=2))


if __name__ == "__main__":
    main()
