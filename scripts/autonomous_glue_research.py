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
BLOCKED_TARGETS_PATH = ROOT / "data" / "autonomous-blocked-targets.json"
MANUAL_SOURCE_PATH = ROOT / "data" / "tds-manual-source.json"
MCMASTER_CATALOG_PATH = ROOT / "data" / "mcmaster-site-catalog.js"
MCMASTER_SUMMARY_PATH = ROOT / "data" / "mcmaster-site-summary.json"
MCMASTER_TDS_PATH = ROOT / "data" / "mcmaster-tds-links.json"
RETAILER_DISCOVERED_PATH = ROOT / "data" / "retailer-discovered-products.json"
TDS_CACHE_MANIFEST_PATH = ROOT / "data" / "tds-cache-manifest.json"
DIGIKEY_ELECTRONICS_PATH = ROOT / "data" / "digikey-electronics-adhesives.json"
APP_PATH = ROOT / "app.js"
REPORT_JSON_PATH = ROOT / "data" / "autonomous-research-report.json"
REPORT_MD_PATH = ROOT / "data" / "autonomous-research-report.md"

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
MANUAL_CORE_FIELDS = [
    "summary",
    "cureFamily",
    "cureDetail",
    "applicationTags",
    "referenceUrl",
    "referenceCategory",
    "referenceSampleType",
    "referenceSampleConsistency",
    "referenceForJoining",
]
MANUAL_DECISION_FIELDS = [
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
MANUAL_ELECTRONICS_FIELDS = [
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
MANUAL_FIELD_ALIASES = {
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
    "potLife": ["potLifeRangeMinutes", "workingLife", "workingLifeDays", "workingLifeMinutes", "stencilLife"],
    "serviceMin": ["operatingTemperatureRangeC", "serviceTemperatureNote"],
    "serviceMax": ["operatingTemperatureRangeC", "serviceTemperatureNote"],
    "thermalConductivity": ["thermalConductivityRangeWmK", "thermalConductivityRange"],
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
    "hardnessValue": ["hardnessRange", "hardnessValueAlt", "vickersHardness"],
    "peelStrengthNPerM": ["peelStrengthNPer25Mm", "peelStrengthProfilesNPerM", "peelAdhesionProfilesNPer100Mm", "initialPeelStrengthNPerMm", "peelStrengthsNPerMm"],
    "chipBondStrengthMPa": ["dieShearStrengthPsi", "dieShearStrengthKgf", "dieShearStrengthProfilesN"],
    "cureDepthMm": ["depthCurabilityMm", "thickFilmCurabilityMm"],
    "tackFreeTime": ["tackFreeTimeMinutes", "tackFreeTimeRangeMinutes"],
    "cureProfiles": ["fullCureProfiles", "fullCureMinutes", "fullCureHours", "workingStrengthProfiles", "handlingStrengthProfiles", "handlingTimeMinutes", "uvDoseKJPerM2", "cureDoseMjCm2"],
}
VERIFIED_ABSENT_FIELD_KEYS = ("unpublishedFields", "verifiedAbsentFields")
NON_APPLICABLE_FIELD_KEYS = ("notApplicableFields", "nonApplicableFields")
CONDUCTIVE_NON_APPLICABLE_WHEN_MISSING = {
    "dielectricConstant",
    "dissipationFactor",
    "dielectricBreakdownVPerMil",
    "dielectricBreakdownKVPerMm",
}
INSULATING_NON_APPLICABLE_WHEN_MISSING = {"connectionResistanceOhm"}


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_space(value).lower())


def official_source_rank(row: dict) -> int:
    """Rank direct technical sources ahead of product pages and URL-less seeds."""
    url = normalize_space(row.get("officialUrl")).lower()
    if not url:
        return 2
    if "/download/" in url or ".pdf" in url or "documentdelivery" in url:
        return 0
    return 1


def tokenize_name(value: str | None) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", normalize_space(value).lower()) if token]


def normalize_maker(value: str | None) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    if "loctite" in text or ("henkel" in text and "adhes" in text):
        return "loctite"
    if "dow" in text or "dupont" in text or "dowsil" in text:
        return "dow"
    if "momentive" in text or "ge" == text:
        return "momentive"
    if "mgchemicals" in text:
        return "mgchemicals"
    if "chipquik" in text:
        return "chipquik"
    if "chemtronics" in text:
        return "chemtronics"
    if "sika" in text:
        return "sika"
    if "carlon" in text or "thomasandbetts" in text or "abbinstallationproducts" in text or "abbelectrification" in text:
        return "abbinstallationproducts"
    if "teconnectivity" in text or "raychem" in text:
        return "teconnectivity"
    if "penchem" in text:
        return "penchem"
    if "gluedots" in text or "gdiadhesives" in text:
        return "gluedots"
    if "resintech" in text or "traktronix" in text:
        return "resintech"
    if "titebond" in text:
        return "titebond"
    if "liquidnails" in text:
        return "liquidnails"
    if "bobsmith" in text or text == "bsi" or "bsiinc" in text:
        return "bobsmithindustries"
    if text == "dap" or text.startswith("dapprod") or "dapglobal" in text or "dapinc" in text:
        return "dap"
    if "weldon" in text or "oatey" in text or "ipsadhesives" in text:
        return "oateyweldon"
    if "e6000" in text or "eclecticproducts" in text:
        return "e6000"
    if "elmers" in text:
        return "elmers"
    if "wacker" in text or "semicosil" in text or "elastosil" in text:
        return "wacker"
    if "shinetsu" in text:
        return "shinetsu"
    if "cemedine" in text:
        return "cemedine"
    if "weicon" in text:
        return "weicon"
    if "itwperformancepolymers" in text or "itwpolymersadhesives" in text or "devcon" in text or "plexus" in text:
        return "itwdevcon"
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
    if "gorilla" in text:
        return "gorilla"
    return text


def load_window_json(path: Path, variable_name: str):
    text = path.read_text()
    match = re.search(rf"window\.{re.escape(variable_name)} = (.*?);\s*(?:window\.|$)", text, re.S)
    if not match:
        raise ValueError(f"Could not find {variable_name} in {path}")
    return json.loads(match.group(1))


def has_meaningful_value(value) -> bool:
    """Return False for absent/sparse source values, including explicit JSON null."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(normalize_space(value))
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def fields_from_keys(entry: dict, keys: tuple[str, ...]) -> set[str]:
    fields: set[str] = set()
    for key in keys:
        value = entry.get(key) or []
        if isinstance(value, dict):
            fields.update(value.keys())
        elif isinstance(value, list):
            fields.update(item for item in value if isinstance(item, str))
    return fields


def normalized_electrical_behavior(entry: dict) -> str:
    value = normalize_space(entry.get("electricalBehavior")).lower()
    if not value:
        if has_meaningful_value(entry.get("connectionResistanceOhm")) or has_meaningful_value(entry.get("connectionResistanceProfilesOhm")):
            return "anisotropic-conductive"
        resistivity = entry.get("volumeResistivityOhmM")
        if isinstance(resistivity, (int, float)) and resistivity < 1:
            return "conductive"
        if any(has_meaningful_value(entry.get(field)) for field in ["dielectricConstant", "dielectricBreakdownKVPerMm", "dielectricBreakdownVPerMil", "insulationResistanceOhm"]):
            return "insulating"
        return ""
    if "anisotropic" in value or "z-axis" in value or "z axis" in value:
        return "anisotropic-conductive"
    if "not rated" in value:
        return "not-rated"
    if "non-conductive" in value or "non conductive" in value or "insulat" in value or "dielectric" in value:
        return "insulating"
    if "conductive" in value or "electroconductive" in value:
        return "conductive"
    return value


def manual_field_status(entry: dict, field: str) -> dict:
    if has_meaningful_value(entry.get(field)):
        return {"status": "value", "sourceField": field}
    for alias in MANUAL_FIELD_ALIASES.get(field, []):
        if has_meaningful_value(entry.get(alias)):
            return {"status": "alias", "sourceField": alias}
    if field in fields_from_keys(entry, VERIFIED_ABSENT_FIELD_KEYS):
        return {"status": "verified_absent", "sourceField": "unpublishedFields"}
    if field in fields_from_keys(entry, NON_APPLICABLE_FIELD_KEYS):
        return {"status": "not_applicable", "sourceField": "notApplicableFields"}

    behavior = normalized_electrical_behavior(entry)
    if behavior == "conductive" and field in CONDUCTIVE_NON_APPLICABLE_WHEN_MISSING:
        return {"status": "not_applicable", "sourceField": "electricalBehavior"}
    if behavior == "insulating" and field in INSULATING_NON_APPLICABLE_WHEN_MISSING:
        return {"status": "not_applicable", "sourceField": "electricalBehavior"}
    if not is_electronics_relevant(entry) and field in MANUAL_ELECTRONICS_FIELDS:
        return {"status": "not_applicable", "sourceField": "electronicsRelevance"}
    return {"status": "missing", "sourceField": None}


def manual_field_present(entry: dict, field: str) -> bool:
    return manual_field_status(entry, field)["status"] in {"value", "alias", "verified_absent", "not_applicable"}


def manual_field_has_value(entry: dict, field: str) -> bool:
    return manual_field_status(entry, field)["status"] in {"value", "alias"}


def manual_field_is_actionable_missing(entry: dict, field: str) -> bool:
    return manual_field_status(entry, field)["status"] == "missing"


def coverage_status_counts(entry: dict, fields: list[str]) -> dict[str, int]:
    counts = {"value": 0, "alias": 0, "verified_absent": 0, "not_applicable": 0, "missing": 0}
    for field in fields:
        counts[manual_field_status(entry, field)["status"]] += 1
    return counts


def field_names_by_status(entry: dict, fields: list[str]) -> dict[str, list[str]]:
    grouped = {"value": [], "alias": [], "verified_absent": [], "not_applicable": [], "missing": []}
    for field in fields:
        grouped[manual_field_status(entry, field)["status"]].append(field)
    return grouped


def ratio(count: int, total: int) -> float:
    return round(count / total, 3) if total else 0.0


def covered_count(status_counts: dict[str, int]) -> int:
    return sum(status_counts[status] for status in ["value", "alias", "verified_absent", "not_applicable"])


def is_electronics_relevant(entry: dict) -> bool:
    if entry.get("excludeElectronicsCompleteness"):
        return False
    tags = entry.get("applicationTags") or []
    category = normalize_space(entry.get("referenceCategory"))
    ref_join = normalize_space(entry.get("referenceForJoining"))
    cure_family = normalize_space(entry.get("cureFamily"))
    combined = " ".join([category, ref_join, cure_family]).lower()
    if any(
        token in combined
        for token in [
            "accelerator",
            "activator",
            "spray adhesive",
            "solvent cement",
            "threadlocker",
            "thread lock",
            "threadsealant",
            "thread sealant",
            "retaining compound",
            "retainer",
            "anaerobic",
            "liquid electrical tape",
        ]
    ):
        return False
    if normalized_electrical_behavior(entry) or entry.get("volumeResistivityOhmM") or entry.get("dielectricBreakdownKVPerMm"):
        return True
    if any(tag in tags for tag in ["potting-thermal", "conformal-coating", "conductive-adhesive"]):
        return True
    return any(
        token in combined
        for token in [
            "electronics",
            "electronic",
            "conformal",
            "conductive",
            "encapsul",
            "pcb",
            "die attach",
            "semiconductor",
            "sensor",
        ]
    )


def load_manual_entries() -> list[dict]:
    manual_source = json.loads(MANUAL_SOURCE_PATH.read_text())
    return manual_source.get("entries", [])


def load_tds_cache_index() -> dict[str, dict]:
    if not TDS_CACHE_MANIFEST_PATH.exists():
        return {}
    payload = json.loads(TDS_CACHE_MANIFEST_PATH.read_text())
    return {entry.get("id"): entry for entry in payload.get("entries", []) if entry.get("id")}


def build_manual_field_coverage(entries: list[dict], cache_index: dict[str, dict]) -> dict:
    field_presence = {
        field: 0 for field in [*MANUAL_CORE_FIELDS, *MANUAL_DECISION_FIELDS, *MANUAL_ELECTRONICS_FIELDS]
    }
    core_complete = 0
    cached_text = 0
    entry_rows = []
    electronics_relevant_rows = []
    value_field_presence = {
        field: 0 for field in [*MANUAL_CORE_FIELDS, *MANUAL_DECISION_FIELDS, *MANUAL_ELECTRONICS_FIELDS]
    }
    status_totals = {"value": 0, "alias": 0, "verified_absent": 0, "not_applicable": 0, "missing": 0}

    for entry in entries:
        core_groups = field_names_by_status(entry, MANUAL_CORE_FIELDS)
        decision_groups = field_names_by_status(entry, MANUAL_DECISION_FIELDS)
        electronics_groups = field_names_by_status(entry, MANUAL_ELECTRONICS_FIELDS)
        present_core = [field for field in MANUAL_CORE_FIELDS if field not in core_groups["missing"]]
        present_decision = [field for field in MANUAL_DECISION_FIELDS if field not in decision_groups["missing"]]
        present_electronics = [field for field in MANUAL_ELECTRONICS_FIELDS if field not in electronics_groups["missing"]]
        value_core = core_groups["value"] + core_groups["alias"]
        value_decision = decision_groups["value"] + decision_groups["alias"]
        value_electronics = electronics_groups["value"] + electronics_groups["alias"]
        missing_core = core_groups["missing"]
        missing_decision = decision_groups["missing"]
        missing_electronics = electronics_groups["missing"]
        for field in present_core + present_decision + present_electronics:
            field_presence[field] += 1
        for field in value_core + value_decision + value_electronics:
            value_field_presence[field] += 1
        for groups in [core_groups, decision_groups, electronics_groups]:
            for status, fields in groups.items():
                status_totals[status] += len(fields)
        cache_entry = cache_index.get(entry.get("id"))
        cached = bool(cache_entry and cache_entry.get("textPath") and not cache_entry.get("error"))
        if cached:
            cached_text += 1
        if not missing_core:
            core_complete += 1
        electronics_relevant = is_electronics_relevant(entry)
        entry_rows.append(
            {
                "id": entry.get("id"),
                "maker": entry.get("maker"),
                "name": entry.get("name"),
                "electronicsRelevant": electronics_relevant,
                "cachedText": cached,
                "electricalBehaviorClass": normalized_electrical_behavior(entry),
                "coreFieldCoverage": ratio(len(present_core), len(MANUAL_CORE_FIELDS)),
                "decisionFieldCoverage": ratio(len(present_decision), len(MANUAL_DECISION_FIELDS)),
                "electronicsFieldCoverage": ratio(len(present_electronics), len(MANUAL_ELECTRONICS_FIELDS)),
                "coreValueCoverage": ratio(len(value_core), len(MANUAL_CORE_FIELDS)),
                "decisionValueCoverage": ratio(len(value_decision), len(MANUAL_DECISION_FIELDS)),
                "electronicsValueCoverage": ratio(len(value_electronics), len(MANUAL_ELECTRONICS_FIELDS)),
                "missingCoreFields": missing_core,
                "missingDecisionFields": missing_decision,
                "missingElectronicsFields": missing_electronics,
                "verifiedAbsentFields": sorted(core_groups["verified_absent"] + decision_groups["verified_absent"] + electronics_groups["verified_absent"]),
                "notApplicableFields": sorted(core_groups["not_applicable"] + decision_groups["not_applicable"] + electronics_groups["not_applicable"]),
                "aliasCoveredFields": sorted(core_groups["alias"] + decision_groups["alias"] + electronics_groups["alias"]),
            }
        )
        if electronics_relevant:
            electronics_relevant_rows.append(entry_rows[-1])

    entry_rows.sort(
        key=lambda row: (
            row["decisionFieldCoverage"],
            row["coreFieldCoverage"],
            row["electronicsFieldCoverage"],
            0 if row["cachedText"] else -1,
            normalize_text(row["maker"]),
            normalize_text(row["name"]),
        )
    )
    field_coverage = {
        field: {
            "present": count,
            "valuePresent": value_field_presence[field],
            "ratio": ratio(count, len(entries)),
            "valueRatio": ratio(value_field_presence[field], len(entries)),
        }
        for field, count in field_presence.items()
    }
    return {
        "coreFields": MANUAL_CORE_FIELDS,
        "decisionFields": MANUAL_DECISION_FIELDS,
        "electronicsFields": MANUAL_ELECTRONICS_FIELDS,
        "fieldCoverage": field_coverage,
        "fieldStatusTotals": status_totals,
        "entryCount": len(entries),
        "cachedTextCount": cached_text,
        "coreCompleteCount": core_complete,
        "coreCoverageRatio": round(core_complete / len(entries), 3) if entries else 0.0,
        "decisionCoverageRatio": round(
            sum(row["decisionFieldCoverage"] for row in entry_rows) / len(entry_rows), 3
        )
        if entry_rows
        else 0.0,
        "electronicsCoverageRatio": round(
            sum(row["electronicsFieldCoverage"] for row in electronics_relevant_rows)
            / len(electronics_relevant_rows),
            3,
        )
        if electronics_relevant_rows
        else 0.0,
        "electronicsRelevantCount": len(electronics_relevant_rows),
        "weakestEntries": entry_rows[:25],
        "weakestElectronicsEntries": sorted(
            electronics_relevant_rows,
            key=lambda row: (
                row["electronicsFieldCoverage"],
                row["decisionFieldCoverage"],
                normalize_text(row["maker"]),
                normalize_text(row["name"]),
            ),
        )[:20],
    }


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

    seed_tokens = tokenize_name(seed_name)
    candidate_tokens = tokenize_name(candidate_name)
    if not seed_tokens or not candidate_tokens:
        return False

    shared_tokens = set(seed_tokens) & set(candidate_tokens)
    if any(re.search(r"[a-z]", token) and re.search(r"\d", token) for token in shared_tokens):
        return True
    if any(token.isdigit() and len(token) >= 4 for token in shared_tokens):
        return True

    # Handle family seeds such as 108B/109B.
    if seed_tokens and all(token in candidate_name.lower() for token in seed_tokens if any(char.isdigit() for char in token)):
        return True
    return False


def record_matches(seed_maker: str, seed_name: str, record: dict) -> bool:
    seed_maker_key = normalize_maker(seed_maker)
    record_maker_key = normalize_maker(record.get("maker"))
    seed_name_key = normalize_text(seed_name)
    distributed_3m = (
        seed_maker_key == "ellsworthadhesives"
        and record_maker_key == "3m"
        and any(token in seed_name_key for token in ["3m", "scotchweld", "scotchcast", "scotchkote"])
    )
    if seed_maker_key != record_maker_key and not distributed_3m:
        return False
    return name_matches(seed_name, record.get("name", ""))


def load_catalog_records() -> tuple[list[dict], dict]:
    manual_entries = load_manual_entries()
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


def load_retailer_records() -> tuple[list[dict], dict]:
    if not RETAILER_DISCOVERED_PATH.exists():
        return [], {"retailerEntries": 0, "retailerByName": {}}
    payload = json.loads(RETAILER_DISCOVERED_PATH.read_text())
    entries = payload.get("entries", [])
    records = [
        {
            "source": f"retailer:{entry.get('retailer', '').lower()}",
            "retailer": entry.get("retailer"),
            "maker": entry.get("maker", ""),
            "name": entry.get("name", ""),
            "referenceUrl": entry.get("retailerUrl"),
        }
        for entry in entries
        if entry.get("retailer") and entry.get("maker") and entry.get("name")
    ]
    by_name = {
        retailer.get("name"): retailer.get("discoveredEntries", 0)
        for retailer in payload.get("retailers", [])
    }
    return records, {"retailerEntries": len(records), "retailerByName": by_name}


def load_electronics_distributor_records() -> tuple[list[dict], dict, list[dict]]:
    if not DIGIKEY_ELECTRONICS_PATH.exists():
        return [], {
            "electronicsDistributorRows": 0,
            "electronicsDistributorAdhesiveRows": 0,
            "electronicsDistributorProductLeads": 0,
            "electronicsDistributorDatasheets": 0,
            "electronicsDistributorElectronicsLeads": 0,
        }, []
    payload = json.loads(DIGIKEY_ELECTRONICS_PATH.read_text())
    leads = [
        lead
        for lead in payload.get("productLeads", [])
        if lead.get("maker") and lead.get("name") and lead.get("datasheetUrl")
    ]
    records = [
        {
            "source": "digikey-electronics",
            "distributor": "Digi-Key",
            "maker": lead.get("maker", ""),
            "name": lead.get("name", ""),
            "referenceUrl": lead.get("datasheetUrl"),
            "productUrl": (lead.get("offers") or [{}])[0].get("productUrl"),
            "leadScore": lead.get("leadScore", 0),
        }
        for lead in leads
    ]
    stats = payload.get("stats", {})
    return records, {
        "electronicsDistributorRows": stats.get("rows", 0),
        "electronicsDistributorAdhesiveRows": stats.get("adhesiveLikelyRows", 0),
        "electronicsDistributorProductLeads": stats.get("productLeads", len(leads)),
        "electronicsDistributorDatasheets": stats.get("uniqueDatasheets", 0),
        "electronicsDistributorElectronicsLeads": stats.get("electronicsProductLeads", 0),
    }, leads


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


def load_blocked_targets() -> dict[tuple[str, str, str, str], dict]:
    if not BLOCKED_TARGETS_PATH.exists():
        return {}
    payload = json.loads(BLOCKED_TARGETS_PATH.read_text())
    entries = payload.get("entries", [])
    blocked: dict[tuple[str, str, str, str], dict] = {}
    for entry in entries:
        maker = entry.get("maker")
        name = entry.get("name")
        if not maker or not name:
            continue
        key = (
            normalize_maker(maker),
            normalize_text(name),
            entry.get("targetSource", "curated"),
            entry.get("targetKind", "product"),
        )
        blocked[key] = entry
    return blocked


def find_blocked_target(
    blocked_targets: dict[tuple[str, str, str, str], dict],
    maker: str,
    name: str,
    target_source: str,
    target_kind: str,
) -> dict | None:
    exact_key = (normalize_maker(maker), normalize_text(name), target_source, target_kind)
    exact = blocked_targets.get(exact_key)
    if exact:
        return exact
    target_tokens = set(tokenize_name(name))
    maker_tokens = set(tokenize_name(maker))
    target_product_tokens = target_tokens - maker_tokens
    normalized_maker = normalize_maker(maker)
    for (blocked_maker, _blocked_name, blocked_source, blocked_kind), entry in blocked_targets.items():
        if blocked_maker != normalized_maker or blocked_source != target_source or blocked_kind != target_kind:
            continue
        blocked_tokens = set(tokenize_name(entry.get("name", ""))) - maker_tokens
        if blocked_tokens and blocked_tokens == target_product_tokens:
            return entry
    return None


def build_report() -> dict:
    seeds = json.loads(SEEDS_PATH.read_text())
    records, catalog_stats = load_catalog_records()
    retailer_records, retailer_stats = load_retailer_records()
    electronics_records, electronics_stats, electronics_leads = load_electronics_distributor_records()
    discovered_targets = load_discovered_targets()
    blocked_targets = load_blocked_targets()
    manual_entries = load_manual_entries()
    tds_cache_index = load_tds_cache_index()
    manual_field_coverage = build_manual_field_coverage(manual_entries, tds_cache_index)

    manufacturer_rows = []
    missing_rows = []
    blocked_rows = []
    covered_count = 0
    total_targets = 0
    curated_total = 0

    for manufacturer in seeds.get("manufacturers", []):
        products = []
        for product in manufacturer.get("products", []):
            total_targets += 1
            curated_total += 1
            matches = [record for record in records if record_matches(manufacturer["name"], product["name"], record)]
            retailer_matches = [record for record in retailer_records if record_matches(manufacturer["name"], product["name"], record)]
            electronics_matches = [
                record for record in electronics_records if record_matches(manufacturer["name"], product["name"], record)
            ]
            coverage_sources = sorted({match["source"] for match in matches})
            covered = bool(matches)
            blocked_entry = find_blocked_target(blocked_targets, manufacturer["name"], product["name"], "curated", "product")
            if covered:
                covered_count += 1
            elif blocked_entry:
                blocked_rows.append(
                    {
                        "priority": manufacturer.get("priority", "medium"),
                        "maker": manufacturer["name"],
                        "name": product["name"],
                        "officialUrl": product.get("officialUrl"),
                        "officialDomains": manufacturer.get("officialDomains", []),
                        "targetSource": "curated",
                        "targetKind": "product",
                        "blockedStatus": blocked_entry.get("status"),
                        "blockedNote": blocked_entry.get("note"),
                    }
                )
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
                    "blocked": bool(blocked_entry) and not covered,
                    "blockedStatus": blocked_entry.get("status") if blocked_entry and not covered else None,
                    "blockedNote": blocked_entry.get("note") if blocked_entry and not covered else None,
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
                    "retailerAvailability": [
                        {
                            "retailer": match.get("retailer"),
                            "referenceUrl": match.get("referenceUrl"),
                        }
                        for match in retailer_matches[:6]
                    ],
                    "electronicsDistributorAvailability": [
                        {
                            "distributor": match.get("distributor"),
                            "referenceUrl": match.get("referenceUrl"),
                            "productUrl": match.get("productUrl"),
                            "leadScore": match.get("leadScore"),
                        }
                        for match in electronics_matches[:6]
                    ],
                    "targetSource": "curated",
                    "targetKind": "product",
                }
            )

        covered_products = sum(1 for product in products if product["covered"])
        blocked_products = sum(1 for product in products if product.get("blocked"))
        missing_products = sum(1 for product in products if not product["covered"] and not product.get("blocked"))
        manufacturer_rows.append(
            {
                "name": manufacturer["name"],
                "priority": manufacturer.get("priority", "medium"),
                "officialDomains": manufacturer.get("officialDomains", []),
                "seededProducts": len(products),
                "coveredProducts": covered_products,
                "blockedProducts": blocked_products,
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
            retailer_matches = [record for record in retailer_records if record_matches(maker, product["name"], record)]
            electronics_matches = [record for record in electronics_records if record_matches(maker, product["name"], record)]
            coverage_sources = sorted({match["source"] for match in matches})
            covered = bool(matches)
            blocked_entry = find_blocked_target(
                blocked_targets,
                maker,
                product["name"],
                "discovered",
                product.get("kind", "product"),
            )
            if covered:
                covered_count += 1
                row["coveredProducts"] += 1
            elif blocked_entry:
                row["blockedProducts"] = row.get("blockedProducts", 0) + 1
                blocked_rows.append(
                    {
                        "priority": product.get("priority", "medium"),
                        "maker": maker,
                        "name": product["name"],
                        "officialUrl": product.get("officialUrl"),
                        "officialDomains": product.get("officialDomains", []),
                        "targetSource": "discovered",
                        "targetKind": product.get("kind", "product"),
                        "blockedStatus": blocked_entry.get("status"),
                        "blockedNote": blocked_entry.get("note"),
                    }
                )
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
                    "blocked": bool(blocked_entry) and not covered,
                    "blockedStatus": blocked_entry.get("status") if blocked_entry and not covered else None,
                    "blockedNote": blocked_entry.get("note") if blocked_entry and not covered else None,
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
                    "retailerAvailability": [
                        {
                            "retailer": match.get("retailer"),
                            "referenceUrl": match.get("referenceUrl"),
                        }
                        for match in retailer_matches[:6]
                    ],
                    "electronicsDistributorAvailability": [
                        {
                            "distributor": match.get("distributor"),
                            "referenceUrl": match.get("referenceUrl"),
                            "productUrl": match.get("productUrl"),
                            "leadScore": match.get("leadScore"),
                        }
                        for match in electronics_matches[:6]
                    ],
                    "targetSource": "discovered",
                    "targetKind": product.get("kind", "product"),
                }
            )

    electronics_tds_backlog = []
    for lead in electronics_leads:
        matches = [record for record in records if record_matches(lead.get("maker", ""), lead.get("name", ""), record)]
        if matches:
            continue
        electronics_tds_backlog.append(
            {
                "priority": "high" if lead.get("electronicsRelevant") else "medium",
                "maker": lead.get("maker"),
                "name": lead.get("name"),
                "type": lead.get("type"),
                "description": lead.get("description"),
                "features": lead.get("features"),
                "forUseWith": lead.get("forUseWith"),
                "datasheetUrl": lead.get("datasheetUrl"),
                "datasheetHost": lead.get("datasheetHost"),
                "offerCount": lead.get("offerCount", 0),
                "totalStock": lead.get("totalStock", 0),
                "bestPriceUsd": lead.get("bestPriceUsd"),
                "leadScore": lead.get("leadScore", 0),
            }
        )
    electronics_tds_backlog.sort(
        key=lambda row: (
            PRIORITY_ORDER.get(row["priority"], 99),
            -row.get("leadScore", 0),
            -row.get("totalStock", 0),
            normalize_text(row.get("maker")),
            normalize_text(row.get("name")),
        )
    )

    for row in manufacturer_rows:
        row["seededProducts"] = len(row["products"])
        row.setdefault("blockedProducts", 0)
        row["coverageRatio"] = round(row["coveredProducts"] / row["seededProducts"], 3) if row["seededProducts"] else 0.0

    missing_rows.sort(
        key=lambda row: (
            PRIORITY_ORDER.get(row["priority"], 99),
            official_source_rank(row),
            0 if row.get("targetSource") == "curated" else 1,
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
            **retailer_stats,
            **electronics_stats,
            "manualCachedTdsText": manual_field_coverage["cachedTextCount"],
            "manualCoreComplete": manual_field_coverage["coreCompleteCount"],
            "manualCoreCoverageRatio": manual_field_coverage["coreCoverageRatio"],
            "manualDecisionCoverageRatio": manual_field_coverage["decisionCoverageRatio"],
            "manualElectronicsCoverageRatio": manual_field_coverage["electronicsCoverageRatio"],
            "manualElectronicsRelevantEntries": manual_field_coverage["electronicsRelevantCount"],
            "seededManufacturers": len(manufacturer_rows),
            "curatedSeedProducts": curated_total,
            "discoveredProducts": len(discovered_targets),
            "blockedOrExcludedTargets": len(blocked_rows),
            "electronicsDistributorMissingTdsLeads": len(electronics_tds_backlog),
            "seededProducts": total_targets,
            "coveredSeedProducts": covered_count,
            "missingSeedProducts": len(missing_rows),
            "coverageRatio": round(covered_count / total_targets, 3) if total_targets else 0.0,
        },
        "manualFieldCoverage": manual_field_coverage,
        "manufacturers": manufacturer_rows,
        "nextActions": missing_rows[:20],
        "allMissing": missing_rows,
        "electronicsTdsBacklog": electronics_tds_backlog[:100],
        "blockedTargets": blocked_rows,
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
        f"- Manual entries with cached TDS text: {stats.get('manualCachedTdsText', 0)}",
        f"- Manual entries with complete core metadata: {stats.get('manualCoreComplete', 0)}",
        f"- Manual core-field completeness ratio: {stats.get('manualCoreCoverageRatio', 0.0)}",
        f"- Manual decision-field completeness ratio: {stats.get('manualDecisionCoverageRatio', 0.0)}",
        f"- Electronics-relevant manual entries: {stats.get('manualElectronicsRelevantEntries', 0)}",
        f"- Manual electronics-field completeness ratio: {stats.get('manualElectronicsCoverageRatio', 0.0)}",
        f"- McMaster selector products: {stats['mcmasterSelectorProducts']}",
        f"- McMaster reference families: {stats['mcmasterReferenceFamilies']}",
        f"- McMaster official-TDS matches: {stats['mcmasterTdsFound']}",
        f"- McMaster product-page-only matches: {stats['mcmasterProductOnly']}",
        f"- Retailer-discovered product pages: {stats.get('retailerEntries', 0)}",
        f"- Digi-Key electronics adhesive rows: {stats.get('electronicsDistributorRows', 0)}",
        f"- Digi-Key unique TDS/datasheet leads: {stats.get('electronicsDistributorDatasheets', 0)}",
        f"- Digi-Key electronics product leads missing manual TDS extraction: {stats.get('electronicsDistributorMissingTdsLeads', 0)}",
        f"- Seeded manufacturers: {stats['seededManufacturers']}",
        f"- Curated seed products: {stats['curatedSeedProducts']}",
        f"- Discovered official-source leads: {stats['discoveredProducts']}",
        f"- Blocked or excluded targets: {stats.get('blockedOrExcludedTargets', 0)}",
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
            "## Blocked Or Excluded Targets",
            "",
            "| Priority | Source | Kind | Manufacturer | Product | Status | Note |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in report.get("blockedTargets", []):
        lines.append(
            f"| {row['priority']} | {row.get('targetSource', 'curated')} | {row.get('targetKind', 'product')} | "
            f"{row['maker']} | {row['name']} | {row.get('blockedStatus', '')} | {row.get('blockedNote', '')} |"
        )

    lines.extend(
        [
            "",
            "## Retailer Discovery",
            "",
            "| Retailer | Discovered pages |",
            "| --- | ---: |",
        ]
    )

    for retailer, count in sorted((stats.get("retailerByName") or {}).items()):
        lines.append(f"| {retailer} | {count} |")

    lines.extend(
        [
            "",
            "## Digi-Key Electronics TDS Leads",
            "",
            "| Priority | Manufacturer | Product | Type | Datasheet | Stock | Score |",
            "| --- | --- | --- | --- | --- | ---: | ---: |",
        ]
    )

    for row in report.get("electronicsTdsBacklog", [])[:30]:
        lines.append(
            f"| {row['priority']} | {row['maker']} | {row['name']} | {row.get('type', '')} | "
            f"{row.get('datasheetUrl', '')} | {row.get('totalStock', 0)} | {row.get('leadScore', 0)} |"
        )

    lines.extend(
        [
            "",
            "## Manual TDS Field Coverage",
            "",
            "| Field | Present | Ratio |",
            "| --- | ---: | ---: |",
        ]
    )

    for field, data in report.get("manualFieldCoverage", {}).get("fieldCoverage", {}).items():
        lines.append(f"| {field} | {data['present']} | {data['ratio']} |")

    lines.extend(
        [
            "",
            "## Weakest Manual TDS Records",
            "",
            "| Maker | Product | Cached text | Core coverage | Decision coverage | Electronics coverage | Missing decision fields |",
            "| --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )

    for row in report.get("manualFieldCoverage", {}).get("weakestEntries", [])[:15]:
        lines.append(
            f"| {row['maker']} | {row['name']} | {'yes' if row['cachedText'] else 'no'} | "
            f"{row['coreFieldCoverage']} | {row['decisionFieldCoverage']} | {row['electronicsFieldCoverage']} | "
            f"{', '.join(row['missingDecisionFields']) or '—'} |"
        )

    lines.extend(
        [
            "",
            "## Weakest Electronics TDS Records",
            "",
            "| Maker | Product | Electronics coverage | Missing electronics fields |",
            "| --- | --- | ---: | --- |",
        ]
    )

    for row in report.get("manualFieldCoverage", {}).get("weakestElectronicsEntries", [])[:12]:
        lines.append(
            f"| {row['maker']} | {row['name']} | {row['electronicsFieldCoverage']} | "
            f"{', '.join(row['missingElectronicsFields']) or '—'} |"
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
        missing = [product for product in row["products"] if not product["covered"] and not product.get("blocked")]
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
