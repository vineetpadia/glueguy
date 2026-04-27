#!/usr/bin/env python3
"""Extract reviewable field candidates from cached TDS text.

This script does not mutate the curated manual source. It turns the slow manual
step into a ranked queue by finding likely values and preserving source evidence
snippets from the cached PDF text.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "tds-manual-source.json"
REPORT_PATH = ROOT / "data" / "autonomous-research-report.json"
MANIFEST_PATH = ROOT / "data" / "tds-cache-manifest.json"
OUTPUT_JSON_PATH = ROOT / "data" / "tds-extraction-suggestions.json"
OUTPUT_MD_PATH = ROOT / "data" / "tds-extraction-suggestions.md"

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
    "potLife": ["potLifeRangeMinutes", "workingLife", "workingLifeDays", "workingLifeMinutes", "stencilLife"],
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
    "serviceMin": ["operatingTemperatureRangeC", "serviceTemperatureNote"],
    "serviceMax": ["operatingTemperatureRangeC", "serviceTemperatureNote"],
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

MISSING_FIELD_ORDER = [
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
    "serviceMin",
    "serviceMax",
    "potLife",
    "fixtureTime",
    "lapShear",
    "thermalConductivity",
]
ELECTRONICS_FIELDS = {
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
}

UNIT_NORMALIZERS = [
    (re.compile(r"(?i)\bpa\s*[.\-]?\s*s\b"), "Pa s"),
    (re.compile(r"(?i)\bmpa\s*[.\-]?\s*s\b"), "mPa s"),
    (re.compile(r"(?i)\bcps?\b"), "cP"),
    (re.compile(r"(?i)\bcentipoise\b"), "cP"),
    (re.compile(r"(?i)\bshore\s*([adco])\b"), "Shore {group1}"),
]


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(normalize_space(value))
    if isinstance(value, (list, tuple, dict, set)):
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
        if has_value(entry.get("connectionResistanceOhm")) or has_value(entry.get("connectionResistanceProfilesOhm")):
            return "anisotropic-conductive"
        resistivity = entry.get("volumeResistivityOhmM")
        if isinstance(resistivity, (int, float)) and resistivity < 1:
            return "conductive"
        if any(has_value(entry.get(field)) for field in ["dielectricConstant", "dielectricBreakdownKVPerMm", "dielectricBreakdownVPerMil", "insulationResistanceOhm"]):
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


def field_status(entry: dict, field: str) -> str:
    if has_value(entry.get(field)):
        return "value"
    if any(has_value(entry.get(alias)) for alias in FIELD_ALIASES.get(field, [])):
        return "alias"
    if field in fields_from_keys(entry, VERIFIED_ABSENT_FIELD_KEYS):
        return "verified_absent"
    if field in fields_from_keys(entry, NON_APPLICABLE_FIELD_KEYS):
        return "not_applicable"
    behavior = normalized_electrical_behavior(entry)
    if behavior == "conductive" and field in CONDUCTIVE_NON_APPLICABLE_WHEN_MISSING:
        return "not_applicable"
    if behavior == "insulating" and field in INSULATING_NON_APPLICABLE_WHEN_MISSING:
        return "not_applicable"
    if field in ELECTRONICS_FIELDS and not is_electronics_relevant(entry):
        return "not_applicable"
    return "missing"


def field_present(entry: dict, field: str) -> bool:
    return field_status(entry, field) != "missing"


def actionable_missing(entry: dict, fields: list[str]) -> list[str]:
    return [field for field in fields if field_status(entry, field) == "missing"]


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


def number_text(pattern: str) -> str:
    return rf"(?P<{pattern}>[<>≥≤~]?\s*-?\d+(?:[.,]\d+)?(?:\s*(?:-|to|–)\s*[<>≥≤~]?\s*-?\d+(?:[.,]\d+)?)?)"


def clean_number(value: str) -> str:
    return normalize_space(value).replace(",", "")


def unit_label(value: str) -> str:
    label = normalize_space(value)
    for pattern, replacement in UNIT_NORMALIZERS:
        match = pattern.search(label)
        if match:
            if "{group1}" in replacement:
                return replacement.format(group1=match.group(1).upper())
            return replacement
    return label


def parse_service_range(text: str) -> tuple[float | None, float | None]:
    cleaned = text.replace("〜", "~").replace("～", "~")
    low = cleaned.lower()
    if not any(token in low for token in ["service", "operating", "ambient", "storage", "temp", "temperature", "store", "room"]):
        return None, None

    if not re.search(r"[°º]?\s*[cfk]\b", low):
        # Avoid parsing generic two-number patterns in legal text, phone numbers,
        # or document metadata.
        return None, None

    num_pattern = r"[+-]?\d+(?:\.\d+)?"

    for pattern in [
        rf"(?i)(?:service|operating|ambient|storage|use)\s*(?:temperatures?|temp)\s*[:\-]?[\s\(\)]*(?P<min>{num_pattern})\s*(?:°?\s*[CFK])?\s*(?:to|\-|–|~|through|\band\b)\s*(?P<max>{num_pattern})\s*(?P<unit>°?\s*[CF]|°?\s*K)?",
        rf"(?i)(?:service|operating|ambient|storage|use)\s*(?:range|interval)\s*[:\-]?[\s\(\)]*(?P<min>{num_pattern})\s*(?:°?\s*[CFK])?\s*(?:to|\-|–|~|through|\band\b)\s*(?P<max>{num_pattern})\s*(?P<unit>°?\s*[CF]|°?\s*K)?",
        rf"(?i)(?:service|operating|ambient|storage|use)\s*(?:temperature)?\s*(?:range|temperatures?|temp)\s*[:\-]?\s*(?P<min>{num_pattern})\s*(?:°?\s*[CFK])?\s*(?:to|\-|–|~|through|\band\b)\s*(?P<max>{num_pattern})\s*(?P<unit>°?\s*[CF]|°?\s*K)?",
        rf"(?i)(?:service|operating|ambient|storage|use)?\s*(?:the\s*)?(?:temperature|temp)\s*(?:between|range|interval)?\s*[:\-]?\s*(?P<min>{num_pattern})\s*(?:°?\s*[CFK])?\s*(?:to|\-|–|~|through|\band\b)\s*(?P<max>{num_pattern})\s*(?P<unit>°?\s*[CF]|°?\s*K)?",
        rf"(?i)(?:storage|ambient|service|operating|room)\s*(?:temperature|temp)\s*.*?(?:between|from)\s*(?P<min>{num_pattern})\s*(?:°?\s*[CFK])?\s*(?:and|&|to|\-|–|~)\s*(?P<max>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)?",
        rf"(?i)(?:storage|ambient|service|operating|room)\s*(?:temperature|temp)\s*.*?(?:range|interval)\s*(?P<min>{num_pattern})\s*(?:°?\s*[CFK])?\s*(?:to|\-|–|~|through|\band\b)\s*(?P<max>{num_pattern})\s*(?P<unit>°?\s*[CF]|°?\s*K)?",
        rf"(?i)(?:storage|ambient|service|operating|room)\s*[^\n]{{0,120}}?\bbetween\b\s*[^\n]{{0,120}}?(?P<min>{num_pattern})\s*(?:°?\s*[CFK])?\s*(?:to|\-|–|~|\band\b|and|\&)\s*(?P<max>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)?",
        rf"(?i)(?:storage|ambient|service|operating|room)\s*[^\n]{{0,120}}?\bfrom\b\s*[^\n]{{0,120}}?(?P<min>{num_pattern})\s*(?:°?\s*[CFK])?\s*(?:to|\-|–|~|\band\b|and|\&)\s*(?P<max>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)?",
        rf"(?i)(?:store|storage|stored)\s*at\s*[:\-]?[\s\(\)]*(?P<min>{num_pattern})\s*(?:°?\s*[CFK])?\s*(?:to|\-|–|~|through|\band\b)\s*(?P<max>{num_pattern})\s*(?P<unit>°?\s*[CF]|°?\s*K)?",
        rf"(?i)(?:storage|keep|store|stored|shelf|shelf life)\b[^\n]{{0,90}}?(?:at|is|are|can be)\s*(?P<min>{num_pattern})\s*(?:°?\s*[CFK])?\s*(?:to|-|–|~|through|\band\b)\s*(?P<max>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)?",
        rf"(?i)(?:temperatures?|temperature)\s*(?:of|exceed(?:ing)?|above|over|do not exceed|cannot exceed|may not exceed|do not exceed)\s*(?P<max>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)?(?:\s*/\s*(?P<max2>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)?)?(?:[^\n]{{0,30}}?(?:service|storage|ambient|operating))?",
        rf"(?i)(?:storage|store|shelf|refrigeration|temperatures?)\s*[^\n]{{0,80}}?(?P<max>{num_pattern})\s*°?\s*(?P<max_unit>[cfk])\s*(?:/|\bor\b|\band\b)\s*(?P<max2>{num_pattern})\s*°?\s*(?P<max2_unit>[cfk])\b",
        rf"(?i)(?:at\s*)?(?P<min>{num_pattern})\s*(?:°?\s*[CFK])\s*(?:to|\-|–|~|through|\band\b)\s*(?P<max>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)?\s*(?:storage|ambient|room|operating|service|while in use)",
        rf"(?i)(?:service|min|minimum|low)\s*(?:temperature)?\s*(?:must|can|should|is|are)?\s*(?:not\s*)?(?:go(?:es)?\s*)?below\s*(?P<max>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)\b",
        rf"(?i)(?:service|min|minimum|low)\s*(?:temperature)?\s*(?:must|can|should|is|are)?\s*(?:not\s*)?(?:exceed|exceeds|more\s*than|above|over|>?\s*=?)\s*(?P<max>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)\b",
        rf"(?i)(?:service|max|maximum|high)\s*(?:temperature)?\s*(?:must|can|should|is|are)?\s*(?:not\s*)?(?:go(?:es)?\s*)?below\s*(?P<max>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)\b",
        rf"(?i)(?:storage|ambient|operating|service)\s*(?:temperature)?\s*(?:must|can|should|is|are)?\s*(?:remain|stay|go|be)\s*(?:at|above)\s*(?P<min>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)\b",
        rf"(?i)(?:storage|ambient|operating|service)\s*(?:temperature)?\s*(?:must|can|should|is|are)?\s*(?:not\s*)?(?:go(?:es)?\s*)?below\s*(?P<max>{num_pattern})\s*(?:°?\s*[CF]|°?\s*K)\b",
    ]:
        match = re.search(pattern, cleaned)
        if not match:
            continue
        groups = match.groupdict()
        minimum = groups.get("min")
        maximum = groups.get("max")
        maximum2 = groups.get("max2")
        maximum_unit = groups.get("max_unit")
        maximum2_unit = groups.get("max2_unit")
        if minimum is None and maximum is None:
            continue
        if minimum is not None:
            minimum = clean_number(minimum)
        if maximum is not None:
            maximum = clean_number(maximum)
        if maximum is None and maximum2 is not None:
            maximum = clean_number(maximum2)
            maximum_unit = maximum2_unit
        min_pos = match.start("min") if "min" in groups and minimum is not None else None
        if min_pos is not None and min_pos > 0:
            previous = cleaned[min_pos - 1]
            if (
                previous == "-"
                and minimum is not None
                and "-" not in minimum
                and min_pos > 1
                and cleaned[min_pos - 2].isspace()
            ):
                minimum = f"-{minimum}"
        if not minimum and not maximum:
            continue
        unit = normalize_space(match.groupdict().get("unit", "") or "")
        if not unit:
            unit = normalize_space(maximum_unit or "")
        min_value = float(minimum) if minimum else None
        max_value = float(maximum) if maximum else None
        if "f" in unit.lower():
            if min_value is not None:
                min_value = (min_value - 32) * 5 / 9
            if max_value is not None:
                max_value = (max_value - 32) * 5 / 9
        elif "k" in unit.lower():
            if min_value is not None:
                min_value = min_value - 273.15
            if max_value is not None:
                max_value = max_value - 273.15
        return min_value, max_value
    return None, None


def _append_service_candidates_from_source(
    entry: dict,
    missing: set[str],
    candidates_by_field: dict[str, list[dict]],
    evidence: str,
) -> None:
    if ("serviceMin" in missing) and ("serviceMin" not in candidates_by_field):
        if (value := entry.get("serviceMin")) is not None:
            add_candidate(candidates_by_field, candidate("serviceMin", float(value), evidence, 0.82, "Source metadata temperature minimum from crawled reference data."))
        elif entry.get("storageTemperatureMinC") is not None:
            add_candidate(candidates_by_field, candidate("serviceMin", float(entry["storageTemperatureMinC"]), evidence, 0.78, "Source metadata temperature minimum from crawled reference data."))
        elif entry.get("storageTemperatureMinF") is not None:
            f_value = float(entry["storageTemperatureMinF"])
            add_candidate(candidates_by_field, candidate("serviceMin", (f_value - 32) * 5 / 9, evidence, 0.76, "Source metadata temperature minimum from crawled reference data."))
    if ("serviceMax" in missing) and ("serviceMax" not in candidates_by_field):
        if (value := entry.get("serviceMax")) is not None:
            add_candidate(candidates_by_field, candidate("serviceMax", float(value), evidence, 0.82, "Source metadata temperature maximum from crawled reference data."))
        elif entry.get("storageTemperatureMaxC") is not None:
            add_candidate(candidates_by_field, candidate("serviceMax", float(entry["storageTemperatureMaxC"]), evidence, 0.78, "Source metadata temperature maximum from crawled reference data."))
        elif entry.get("storageTemperatureMaxF") is not None:
            f_value = float(entry["storageTemperatureMaxF"])
            add_candidate(candidates_by_field, candidate("serviceMax", (f_value - 32) * 5 / 9, evidence, 0.76, "Source metadata temperature maximum from crawled reference data."))
        elif range_f := entry.get("publishedTemperatureRangeF"):
            try:
                min_f, max_f = range_f
                if "serviceMax" in missing and "serviceMax" not in candidates_by_field:
                    add_candidate(candidates_by_field, candidate("serviceMax", (float(max_f) - 32) * 5 / 9, evidence, 0.72, "Source metadata published temperature range from crawled reference data."))
            except Exception:
                pass
            if ("serviceMin" in missing) and ("serviceMin" not in candidates_by_field):
                try:
                    add_candidate(candidates_by_field, candidate("serviceMin", (float(min_f) - 32) * 5 / 9, evidence, 0.72, "Source metadata published temperature range from crawled reference data."))
                except Exception:
                    pass
    if "serviceMin" in missing and "serviceMin" not in candidates_by_field and "serviceMax" in missing and "serviceMax" not in candidates_by_field:
        range_f = entry.get("publishedTemperatureRangeF")
        if isinstance(range_f, (list, tuple)) and len(range_f) == 2:
            try:
                min_f, max_f = (float(range_f[0]), float(range_f[1]))
                if "serviceMin" not in candidates_by_field:
                    add_candidate(candidates_by_field, candidate("serviceMin", (min_f - 32) * 5 / 9, evidence, 0.72, "Source metadata published temperature range from crawled reference data."))
                if "serviceMax" not in candidates_by_field:
                    add_candidate(candidates_by_field, candidate("serviceMax", (max_f - 32) * 5 / 9, evidence, 0.72, "Source metadata published temperature range from crawled reference data."))
            except Exception:
                pass


def window(lines: list[str], index: int, radius: int = 2) -> str:
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    return normalize_space(" | ".join(lines[start:end]))


def nearby_nonempty(lines: list[str], index: int, limit: int = 12) -> list[tuple[int, str]]:
    values = []
    for offset in range(index + 1, min(len(lines), index + limit + 1)):
        text = normalize_space(lines[offset])
        if text:
            values.append((offset, text))
    return values


def first_number(value: str) -> str | None:
    match = re.search(r"[<>≥≤~]?\s*-?\d+(?:[.,]\d+)?(?:\s*(?:-|to|–)\s*[<>≥≤~]?\s*-?\d+(?:[.,]\d+)?)?", value)
    return clean_number(match.group(0)) if match else None


def likely_unit_line(value: str, units: tuple[str, ...]) -> str | None:
    low = value.lower()
    for unit in units:
        if unit in low:
            return value
    return None


def table_value_after(lines: list[str], index: int, units: tuple[str, ...] = ()) -> tuple[str | None, str | None, str]:
    """Find values from simple PDF-extracted tables where property/unit/value are split across lines."""
    nearby = nearby_nonempty(lines, index)
    unit = None
    for _, text in nearby[:5]:
        if text.lower() in {"units", "value", "test method", "remarks", "property"}:
            continue
        unit = likely_unit_line(text, units) or unit
        if unit:
            break
    for value_index, text in nearby:
        low = text.lower()
        if low in {"units", "value", "test method", "remarks", "property"}:
            continue
        if any(stop in low for stop in ["test method", "remarks", "astm", "jis"]) and first_number(text) is None:
            continue
        number = first_number(text)
        if number is None:
            continue
        if unit and text == unit:
            continue
        return number, unit, window(lines, value_index, 4)
    return None, unit, window(lines, index)


def candidate(field: str, value, evidence: str, confidence: float, note: str = "") -> dict:
    result = {
        "field": field,
        "value": value,
        "confidence": round(confidence, 3),
        "evidence": evidence[:900],
    }
    if note:
        result["note"] = note
    return result


def infer_electrical_behavior_from_text(text: str) -> tuple[str | None, str]:
    low = text.lower()
    insulating_terms = [
        "electrically insulating",
        "electrically insulative",
        "electrical insulation",
        "non-conductive",
        "non conductive",
        "dielectric strength",
        "dielectric constant",
        "volume resistivity",
        "surface resistivity",
    ]
    conductive_terms = [
        "electrically conductive",
        "electroconductive",
        "electrical conductivity",
        "contact resistance",
        "connection resistance",
        "conductive epoxy",
        "conductive adhesive",
        "conductive paint",
        "conductive coating",
    ]
    conductive_hits = [term for term in conductive_terms if term in low]
    insulating_hits = [term for term in insulating_terms if term in low]
    if conductive_hits and insulating_hits:
        if any(term in low for term in ["anisotropic conductive", "z-axis conductive", "z axis conductive"]):
            return "anisotropic-conductive", "TDS text contains anisotropic conductive language with insulating/isolation context."
        return None, "TDS text contains both conductive and insulating language; verify product behavior manually."
    if conductive_hits:
        return "conductive", "TDS text contains electrical conductive/contact-resistance language."
    if insulating_hits:
        return "insulating", "TDS text contains insulating/dielectric/resistivity language."
    return None, ""


def add_candidate(results: dict[str, list[dict]], item: dict) -> None:
    field = item["field"]
    existing = results.setdefault(field, [])
    signature = (json.dumps(item["value"], sort_keys=True), item["evidence"])
    if any((json.dumps(old["value"], sort_keys=True), old["evidence"]) == signature for old in existing):
        return
    existing.append(item)


def extract_line_candidates(lines: list[str], missing: set[str]) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    joined_lower = "\n".join(lines).lower()

    for idx, line in enumerate(lines):
        text = normalize_space(line)
        if not text:
            continue
        low = text.lower()
        evidence = window(lines, idx)

        if {"viscosityValue", "viscosityUnit"} & missing and "viscos" in low:
            match = re.search(rf"viscosity[^0-9<>≥≤~]*(?:\([^)]*\))?[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>cps?|mPa\s*[.\-]?\s*s|Pa\s*[.\-]?\s*s|centipoise)\b", text, re.I)
            if match:
                value = clean_number(match.group("value"))
                unit = unit_label(match.group("unit"))
                if "viscosityValue" in missing:
                    add_candidate(results, candidate("viscosityValue", value, evidence, 0.82))
                if "viscosityUnit" in missing:
                    add_candidate(results, candidate("viscosityUnit", unit, evidence, 0.86))
            else:
                value, unit, table_evidence = table_value_after(lines, idx, ("cp", "cps", "pa", "mpa", "poise"))
                if value:
                    if "viscosityValue" in missing:
                        add_candidate(results, candidate("viscosityValue", value, table_evidence, 0.7, "PDF table extraction; verify unit/value alignment."))
                    if "viscosityUnit" in missing and unit:
                        add_candidate(results, candidate("viscosityUnit", unit_label(unit), table_evidence, 0.72, "PDF table extraction; verify unit/value alignment."))

        if "volumeResistivityOhmM" in missing and "volume" in low and "resist" in low:
            match = re.search(rf"volume\s+resist\w*[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>ohm(?:s)?[-\s]*(?:cm|m|meter)|Ω[-\s]*(?:cm|m))", text, re.I)
            if match:
                value = clean_number(match.group("value"))
                unit = unit_label(match.group("unit"))
                field = "volumeResistivityOhmCm" if "cm" in unit.lower() else "volumeResistivityOhmM"
                add_candidate(results, candidate(field, value, evidence, 0.82, "Unit preserved from TDS; convert only after verification."))

        if "surfaceResistivityOhm" in missing and "surface" in low and "resist" in low:
            match = re.search(rf"surface\s+resist\w*[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>ohm(?:s)?|Ω)", text, re.I)
            if match:
                add_candidate(results, candidate("surfaceResistivityOhm", clean_number(match.group("value")), evidence, 0.8))

        if "insulationResistanceOhm" in missing and "insulation" in low and "resist" in low:
            match = re.search(rf"insulation\s+resist\w*[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>ohm(?:s)?|Ω)", text, re.I)
            if match:
                add_candidate(results, candidate("insulationResistanceOhm", clean_number(match.group("value")), evidence, 0.8))

        if "connectionResistanceOhm" in missing and "resist" in low and any(token in low for token in ["connection", "contact", "circuit", "electrical"]):
            match = re.search(rf"(?:connection|contact|circuit|electrical)\s+resist\w*[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>m?ohm(?:s)?|m?Ω)", text, re.I)
            if match:
                add_candidate(results, candidate("connectionResistanceOhm", clean_number(match.group("value")), evidence, 0.72, "Check whether value is ohm or milliohm before committing."))

        if "dielectricConstant" in missing and "dielectric constant" in low:
            if len(evidence) > 600:
                continue
            match = re.search(rf"dielectric\s+constant[^0-9<>≥≤~]*{number_text('value')}", text, re.I)
            if match and not re.search(rf"{re.escape(match.group('value').strip())}\s*hz\b", text, re.I):
                add_candidate(results, candidate("dielectricConstant", clean_number(match.group("value")), evidence, 0.78))
            elif not re.search(r"hz\b", low):
                value, _, table_evidence = table_value_after(lines, idx)
                if value:
                    add_candidate(results, candidate("dielectricConstant", value, table_evidence, 0.68, "PDF table extraction; verify this is the property value, not frequency."))

        if "dissipationFactor" in missing and "dissipation" in low:
            match = re.search(rf"dissipation\s+factor[^0-9<>≥≤~]*{number_text('value')}", text, re.I)
            if match and not re.search(rf"{re.escape(match.group('value').strip())}\s*hz\b", text, re.I):
                add_candidate(results, candidate("dissipationFactor", clean_number(match.group("value")), evidence, 0.78))
            elif not re.search(r"hz\b", low):
                value, _, table_evidence = table_value_after(lines, idx)
                if value:
                    add_candidate(results, candidate("dissipationFactor", value, table_evidence, 0.68, "PDF table extraction; verify this is the property value, not frequency."))

        if {"dielectricBreakdownVPerMil", "dielectricBreakdownKVPerMm"} & missing and "dielectric" in low and any(token in low for token in ["breakdown", "strength"]):
            if len(evidence) > 600:
                continue
            match = re.search(rf"dielectric\s+(?:breakdown|strength)[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>v/mil|kv/mm|kV/mm|V/mil)", text, re.I)
            if match:
                unit = match.group("unit").lower()
                field = "dielectricBreakdownVPerMil" if "mil" in unit else "dielectricBreakdownKVPerMm"
                if field in missing:
                    add_candidate(results, candidate(field, clean_number(match.group("value")), evidence, 0.82))

        if "tensileStrengthMPa" in missing and "tensile" in low and "strength" in low and "shear" not in low and "tester" not in low and "test method" not in low and "equipment" not in low and "number of test" not in low:
            match = re.search(rf"tensile\s+strength[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>mpa|psi|n/mm2)", text, re.I)
            if match:
                unit = match.group("unit").lower()
                field = "tensileStrengthPsi" if "psi" in unit else "tensileStrengthMPa"
                add_candidate(results, candidate(field, clean_number(match.group("value")), evidence, 0.8, "Unit preserved from TDS; convert only after verification."))
            else:
                value, unit, table_evidence = table_value_after(lines, idx, ("mpa", "psi", "n/mm"))
                if value:
                    field = "tensileStrengthPsi" if unit and "psi" in unit.lower() else "tensileStrengthMPa"
                    add_candidate(results, candidate(field, value, table_evidence, 0.68, "PDF table extraction; verify unit/value alignment."))

        if "elongationPct" in missing and "elongation" in low:
            match = re.search(rf"elongation[^0-9<>≥≤~]*{number_text('value')}\s*%", text, re.I)
            if match:
                add_candidate(results, candidate("elongationPct", clean_number(match.group("value")), evidence, 0.82))
            else:
                value, unit, table_evidence = table_value_after(lines, idx, ("%",))
                if value and (not unit or "%" in unit):
                    add_candidate(results, candidate("elongationPct", value, table_evidence, 0.68, "PDF table extraction; verify this is cured elongation."))

        if {"hardnessValue", "hardnessScale"} & missing and "hardness" in low:
            match = re.search(rf"hardness[^0-9a-z<>≥≤~]*(?:shore\s*)?(?P<scale>[adco])?[^0-9<>≥≤~]*{number_text('value')}", text, re.I)
            if match:
                value = clean_number(match.group("value"))
                scale = match.group("scale")
                if "hardnessValue" in missing:
                    add_candidate(results, candidate("hardnessValue", value, evidence, 0.78))
                if "hardnessScale" in missing and scale:
                    add_candidate(results, candidate("hardnessScale", f"Shore {scale.upper()}", evidence, 0.82))
            else:
                value, _, table_evidence = table_value_after(lines, idx)
                scale_match = re.search(r"shore\s*([adco])|hardness\s*\(?\s*(?:shore\s*)?([adco])\s*\)?", text, re.I)
                if value:
                    if "hardnessValue" in missing:
                        add_candidate(results, candidate("hardnessValue", value, table_evidence, 0.68, "PDF table extraction; verify scale/value alignment."))
                    if "hardnessScale" in missing and scale_match:
                        scale = scale_match.group(1) or scale_match.group(2)
                        add_candidate(results, candidate("hardnessScale", f"Shore {scale.upper()}", table_evidence, 0.72))

        if "peelStrengthNPerM" in missing and "peel" in low:
            match = re.search(rf"peel[^0-9<>≥≤~]*(?:strength|adhesion)?[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>n/m|n/25\s*mm|n/100\s*mm|pli|lb/in)", text, re.I)
            if match:
                add_candidate(results, candidate("peelStrengthRaw", {"value": clean_number(match.group("value")), "unit": normalize_space(match.group("unit"))}, evidence, 0.74, "Normalize to N/m after verifying peel geometry."))

        if "chipBondStrengthMPa" in missing and ("die shear" in low or "chip" in low):
            match = re.search(rf"(?:die\s+shear|chip[^0-9]+(?:bond|shear))[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>kgf|mpa|psi|n)", text, re.I)
            if match:
                add_candidate(results, candidate("chipBondStrengthRaw", {"value": clean_number(match.group("value")), "unit": normalize_space(match.group("unit"))}, evidence, 0.74, "Normalize only after die/chip area is known."))

        if "tackFreeTime" in missing and "tack" in low and "free" in low:
            match = re.search(rf"tack\s*free[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>sec(?:onds)?|min(?:utes)?|h(?:ours?)?)", text, re.I)
            if match:
                add_candidate(results, candidate("tackFreeTime", f"{clean_number(match.group('value'))} {unit_label(match.group('unit'))}", evidence, 0.78))

        if "cureDepthMm" in missing and "depth" in low and "cure" in low:
            match = re.search(rf"(?:cure|curing)\s+depth[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>mm|mil)", text, re.I)
            if match:
                add_candidate(results, candidate("cureDepthRaw", {"value": clean_number(match.group("value")), "unit": normalize_space(match.group("unit"))}, evidence, 0.74))

        if "thermalConductivity" in missing and "thermal" in low and "conduct" in low:
            match = re.search(rf"thermal\s+conduct\w*[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>w/mk|w/m-k|btu[^,; ]*)", text, re.I)
            if match:
                add_candidate(results, candidate("thermalConductivity", f"{clean_number(match.group('value'))} {normalize_space(match.group('unit'))}", evidence, 0.78))

        if "lapShear" in missing and "lap" in low and "shear" in low:
            match = re.search(rf"lap\s+shear[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>mpa|psi|n/mm2)", text, re.I)
            if match:
                add_candidate(results, candidate("lapShearRaw", {"value": clean_number(match.group("value")), "unit": normalize_space(match.group("unit"))}, evidence, 0.76))

        if "potLife" in missing and ("pot life" in low or "working life" in low):
            match = re.search(rf"(?:pot|working)\s+life[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>sec(?:onds)?|min(?:utes)?|h(?:ours?)?)", text, re.I)
            if match:
                add_candidate(results, candidate("potLife", f"{clean_number(match.group('value'))} {unit_label(match.group('unit'))}", evidence, 0.78))

        if "fixtureTime" in missing and ("fixture" in low or "handling" in low):
            match = re.search(rf"(?:fixture|handling)[^0-9<>≥≤~]*(?:time|strength)?[^0-9<>≥≤~]*{number_text('value')}\s*(?P<unit>sec(?:onds)?|min(?:utes)?|h(?:ours?)?)", text, re.I)
            if match:
                add_candidate(results, candidate("fixtureTime", f"{clean_number(match.group('value'))} {unit_label(match.group('unit'))}", evidence, 0.72))

        if {"serviceMin", "serviceMax"} & missing and any(token in low for token in ["service", "operating", "ambient", "storage", "temperature", "temp"]):
            service_min, service_max = parse_service_range(text)
            if service_min is not None:
                if "serviceMin" in missing:
                    add_candidate(results, candidate("serviceMin", service_min, evidence, 0.74, "Parsed service/storage temperature bound."))
            if service_max is not None:
                if "serviceMax" in missing:
                    add_candidate(results, candidate("serviceMax", service_max, evidence, 0.74, "Parsed service/storage temperature bound."))

    if "electricalBehavior" in missing:
        behavior, note = infer_electrical_behavior_from_text(joined_lower)
        if behavior:
            confidence = 0.72 if behavior == "anisotropic-conductive" else 0.68
            add_candidate(results, candidate("electricalBehavior", behavior, note, confidence))

    if "cureProfiles" in missing:
        for match in re.finditer(
            r"(?P<temp>\d{2,3})\s*[°º]?\s*C[^.\n]{0,80}?(?P<time>\d+(?:\.\d+)?)\s*(?P<unit>sec(?:onds)?|min(?:utes)?|h(?:ours?)?)",
            "\n".join(lines),
            re.I,
        ):
            snippet_start = max(0, match.start() - 180)
            snippet_end = min(len("\n".join(lines)), match.end() + 180)
            snippet = normalize_space("\n".join(lines)[snippet_start:snippet_end])
            if not re.search(r"(?i)\b(cure|curing|cured|fixture|handling|set)\b", snippet):
                continue
            add_candidate(
                results,
                candidate(
                    "cureProfiles",
                    {"temperatureC": float(match.group("temp")), "time": f"{match.group('time')} {unit_label(match.group('unit'))}"},
                    snippet,
                    0.66,
                    "Verify this is a cure schedule, not storage or test conditioning.",
                ),
            )
            if len(results.get("cureProfiles", [])) >= 4:
                break

    return results


def split_markdown_row(line: str) -> list[str]:
    text = line.strip()
    if not (text.startswith("|") and text.endswith("|")):
        return []
    cells = [normalize_space(cell) for cell in text.strip("|").split("|")]
    if cells and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
        return []
    return cells


def is_markdown_table_divider(line: str) -> bool:
    text = line.strip()
    if not (text.startswith("|") and text.endswith("|")):
        return False
    cells = [normalize_space(cell) for cell in text.strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def split_markdown_rows(text: str) -> list[str]:
    return [normalize_space(line) for line in text.splitlines() if normalize_space(line)]


def _first_numeric_token(value: str) -> str | None:
    return first_number(value)


def _extract_numeric_with_unit(value: str) -> tuple[str | None, str]:
    match = re.search(rf"{number_text('value')}\s*(?P<unit>[a-zA-Z°/%μΩ]+)?", value, re.I)
    if not match:
        return None, ""
    return clean_number(match.group("value")), normalize_space(match.group("unit") or "")


def _find_unit_from_row(row: list[str], value_index: int) -> str:
    if value_index < 0:
        return ""
    unit_candidates = [
        row[i] for i in range(len(row))
        if i != value_index and row[i] and re.search(r"[a-zA-Z%°]+", row[i])
    ]
    for candidate in unit_candidates:
        if any(token in candidate.lower() for token in ["mpa", "psi", "n/mm", "n/mm²", "pa", "mpa", "w/m", "k", "sec", "min", "hr", "h", "℃", "°c", "f", "%", "c"]):
            return candidate
    return unit_candidates[0] if unit_candidates else ""


def _label_matches(label: str, terms: tuple[str, ...]) -> bool:
    lower = label.lower()
    return any(term in lower for term in terms)


def pick_value_cell(row: list[str], default_index: int = 1) -> tuple[int, str]:
    if default_index >= len(row):
        return -1, ""
    for index in range(default_index, len(row)):
        candidate = normalize_space(row[index])
        if not candidate or candidate == "-":
            continue
        if _first_numeric_token(candidate):
            return index, candidate
    fallback = normalize_space(row[default_index]) if default_index < len(row) else ""
    return (default_index, fallback) if fallback and fallback != "-" else (-1, "")


def parse_label_value_row_for_candidates(
    label: str,
    value: str,
    unit: str,
    missing: set[str],
    evidence: str,
    results: dict[str, list[dict]],
) -> None:
    low = label.lower()
    clean_value = normalize_space(value)

    if not clean_value or clean_value in {"-", "–", "n/a", "na", "not available"}:
        return

    if {"viscosityValue", "viscosityUnit"} & missing and _label_matches(low, ("viscos",)):
        if "viscosityValue" in missing:
            value_number = _first_numeric_token(clean_value)
            if value_number:
                add_candidate(
                    results,
                    candidate("viscosityValue", value_number, evidence, 0.84, "Mistral OCR markdown table without explicit product column."),
                )
        if "viscosityUnit" in missing and unit:
            add_candidate(
                results,
                candidate("viscosityUnit", unit_label(unit), evidence, 0.84, "Mistral OCR markdown table without explicit product column."),
            )

    if "serviceMin" in missing or "serviceMax" in missing:
        service_min, service_max = parse_service_range(f"{label} {clean_value} {unit}")
        if service_min is not None and service_max is not None:
            if "serviceMin" in missing:
                add_candidate(results, candidate("serviceMin", service_min, evidence, 0.82, "Parsed service/storage temperature from table row."))
            if "serviceMax" in missing:
                add_candidate(results, candidate("serviceMax", service_max, evidence, 0.82, "Parsed service/storage temperature from table row."))

    if {"lapShear", "chipBondStrengthMPa"} & missing and _label_matches(low, ("lap shear", "shear strength", "bond strength", "chip shear")):
        parsed = None
        for field in ("lapShear", "chipBondStrengthMPa"):
            if field in missing:
                unit_low = unit.lower()
                if any(token in unit_low for token in ("n/mm", "mpa", "psi")):
                    parsed = {"value": clean_value, "unit": normalize_space(unit)}
                    if field == "lapShear":
                        add_candidate(results, candidate("lapShearRaw", parsed, evidence, 0.82, "Parsed mechanical strength from table row."))
                    else:
                        add_candidate(results, candidate("chipBondStrengthRaw", parsed, evidence, 0.82, "Parsed mechanical strength from table row."))
                elif any(char.isdigit() for char in clean_value):
                    parsed = {"value": _first_numeric_token(clean_value) or clean_value, "unit": normalize_space(unit)}
                    if field == "lapShear":
                        add_candidate(results, candidate("lapShearRaw", parsed, evidence, 0.74, "Parsed potential lap-shear style value from table row."))
                    else:
                        add_candidate(results, candidate("chipBondStrengthRaw", parsed, evidence, 0.74, "Parsed potential die-shear/chip-bond value from table row."))
                break

    if "tensileStrengthMPa" in missing and _label_matches(low, ("tensile strength",)):
        parsed_value = _first_numeric_token(clean_value)
        if parsed_value:
            field = "tensileStrengthPsi" if "psi" in (unit + " " + low).lower() else "tensileStrengthMPa"
            add_candidate(results, candidate(field, parsed_value, evidence, 0.84, "Parsed tensile strength from table row."))

    if "hardnessValue" in missing and _label_matches(low, ("hardness", "durometer", "shore")):
        value_number = _first_numeric_token(clean_value)
        if value_number:
            add_candidate(results, candidate("hardnessValue", value_number, evidence, 0.8, "Parsed hardness from table row."))
        scale = None
        if "shore" in low:
            match = re.search(r"shore\s*([adco])", low)
            if match:
                scale = f"Shore {match.group(1).upper()}"
        if not scale:
            match = re.search(r"\b([ADCO])\b", clean_value.upper())
            if match:
                scale = f"Shore {match.group(1)}"
            elif "durometer" in low and any(ch in unit.lower() for ch in ("a", "d", "c", "o")):
                scale = f"Shore {unit[-1].upper()}"
        if "hardnessScale" in missing and scale:
            add_candidate(results, candidate("hardnessScale", scale, evidence, 0.8, "Parsed hardness scale from table row."))

    if "tackFreeTime" in missing and _label_matches(low, ("tack", "tack-free", "tack free", "tack-free time")):
        value_number, value_unit = _extract_numeric_with_unit(clean_value)
        if value_number is not None:
            unit_guess = value_unit or unit or next((u for u in ("sec", "min", "hour", "seconds", "minutes", "s", "h") if u in (low + " " + unit + " " + clean_value).lower()), "min")
            add_candidate(results, candidate("tackFreeTime", f"{value_number} {unit_label(unit_guess)}", evidence, 0.76, "Parsed tack-free/open time from table row."))

    if "potLife" in missing and _label_matches(
        low,
        (
            "open time",
            "working life",
            "pot life",
            "handling time",
            "open",
            "cure time",
            "drying time",
            "dry",
        ),
    ):
        value_number, value_unit = _extract_numeric_with_unit(clean_value)
        if value_number is not None:
            unit_guess = value_unit or unit or next((u for u in ("sec", "min", "hour", "s", "h") if u in (low + " " + clean_value).lower()), "min")
            add_candidate(results, candidate("potLife", f"{value_number} {unit_label(unit_guess)}", evidence, 0.74, "Parsed pot-life/open-time from table row."))

    if "fixtureTime" in missing and _label_matches(
        low,
        (
            "fixture",
            "handling time",
            "set time",
            "handling strength",
            "tack free",
            "drying time",
            "open time",
            "open",
            "cure time",
        ),
    ):
        value_number, value_unit = _extract_numeric_with_unit(clean_value)
        if value_number is not None:
            unit_guess = value_unit or unit or next((u for u in ("sec", "min", "hour", "s", "h") if u in (low + " " + clean_value).lower()), "min")
            add_candidate(results, candidate("fixtureTime", f"{value_number} {unit_label(unit_guess)}", evidence, 0.72, "Parsed fixture/handling time from table row."))

    if "thermalConductivity" in missing and _label_matches(low, ("thermal conductivity", "thermal conduct")):
        if _first_numeric_token(clean_value):
            add_candidate(results, candidate("thermalConductivity", clean_value if not unit else f"{clean_value} {unit}", evidence, 0.84, "Parsed thermal conductivity from table row."))

    if "dielectricConstant" in missing and _label_matches(low, ("dielectric constant",)):
        if _first_numeric_token(clean_value):
            add_candidate(results, candidate("dielectricConstant", clean_value, evidence, 0.78, "Parsed dielectric constant from table row."))

    if "dissipationFactor" in missing and _label_matches(low, ("dissipation factor",)):
        if _first_numeric_token(clean_value):
            add_candidate(results, candidate("dissipationFactor", clean_value, evidence, 0.78, "Parsed dissipation factor from table row."))

    if "cureDepthMm" in missing and _label_matches(low, ("depth of cure", "cure depth", "curing depth")):
        if (value_number := _first_numeric_token(clean_value)) is not None:
            unit_guess = unit if unit else "mm"
            add_candidate(results, candidate("cureDepthRaw", {"value": value_number, "unit": unit_label(unit_guess)}, evidence, 0.77, "Parsed cure depth from table row."))

    if "volumeResistivityOhmM" in missing and _label_matches(low, ("volume resist",)):
        if (value := _first_numeric_token(clean_value)) is not None:
            add_candidate(results, candidate("volumeResistivityRaw", {"value": value, "unit": unit or "ohm·m"}, evidence, 0.8, "Parsed volume resistivity from table row."))

    if "surfaceResistivityOhm" in missing and _label_matches(low, ("surface resist",)):
        if (value := _first_numeric_token(clean_value)) is not None:
            add_candidate(results, candidate("surfaceResistivityOhm", value, evidence, 0.8, "Parsed surface resistivity from table row."))

    if "insulationResistanceOhm" in missing and _label_matches(low, ("insulation resist",)):
        if (value := _first_numeric_token(clean_value)) is not None:
            add_candidate(results, candidate("insulationResistanceOhm", value, evidence, 0.8, "Parsed insulation resistance from table row."))

    if "connectionResistanceOhm" in missing and _label_matches(low, ("contact resistance", "connection resistance", "electrical resistance")):
        if (value := _first_numeric_token(clean_value)) is not None:
            add_candidate(results, candidate("connectionResistanceOhm", value, evidence, 0.76, "Parsed electrical resistance from table row."))


def markdown_tables(lines: list[str]) -> list[list[list[str]]]:
    normalized_lines: list[str] = []
    i = 0
    while i < len(lines):
        current = normalize_space(lines[i])
        if "|" in current and not current.endswith("|"):
            j = i + 1
            while j < len(lines):
                fragment = normalize_space(lines[j])
                current = f"{current} {fragment}".strip()
                if current.endswith("|"):
                    break
                j += 1
            i = j
        normalized_lines.append(current)
        i += 1

    tables = []
    current = []
    in_table = False
    has_row_data = False
    for line in normalized_lines:
        if is_markdown_table_divider(line):
            if in_table:
                continue
            if not in_table:
                continue
        row = split_markdown_row(line)
        if row:
            if not in_table:
                in_table = True
            has_row_data = True
            current.append(row)
            continue
        if in_table:
            if len(current) >= 2 and has_row_data:
                tables.append(current)
            current = []
            in_table = False
            has_row_data = False
    if len(current) >= 2:
        tables.append(current)
    return tables


def product_column_indexes(headers: list[str], product_name: str) -> list[int]:
    normalized_product = normalize_space(product_name).lower()
    indexes = [
        index
        for index, header in enumerate(headers)
        if normalized_product and normalized_product in normalize_space(header).lower()
    ]
    return indexes


def parse_markdown_table_candidates(lines: list[str], product_name: str, missing: set[str]) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}

    def is_probable_data_row(row: list[str], fallback_terms: tuple[str, ...]) -> bool:
        if not row:
            return False
        label = normalize_space(row[0]).lower()
        if not label:
            return False
        if label in fallback_terms:
            return False
        return any(_first_numeric_token(cell) is not None for cell in row[1:])

    for table in markdown_tables(lines):
        headers = table[0]
        product_indexes = product_column_indexes(headers, product_name)
        if not product_indexes and len(table) > 1:
            product_indexes = product_column_indexes(table[1], product_name)
            if product_indexes:
                headers = table[1]

        row_iter = table[1:] if product_indexes else table
        if not product_indexes and is_probable_data_row(table[0], ("test item", "property", "test item", "typical properties", "property and value", "property", "item")):
            # Some OCR tables are property/value rows with a single data row that
            # ended up in the first line due missing header reconstruction.
            row_iter = table

        for row in row_iter:
            if len(row) < 2:
                continue
            label = normalize_space(row[0])
            if not label:
                continue

            if product_indexes:
                unit = normalize_space(row[1]) if len(row) > 2 else ""
                for product_index in product_indexes:
                    if product_index >= len(row):
                        continue
                    value = normalize_space(row[product_index])
                    if not value or value == "-":
                        continue
                    evidence = " | ".join(row)
                    parse_label_value_row_for_candidates(label, value, unit, missing, evidence, results)
            else:
                # Property/value tables often arrive as:
                # | Test item | Unit | Result | ...
                # or simply | Test item | Value |
                value_index, value = pick_value_cell(row, default_index=1)
                if value_index == -1:
                    continue
                if not value or value == "-":
                    continue
                unit = "" if value_index == 1 else normalize_space(row[1])
                if not unit and len(row) > 2:
                    unit = _find_unit_from_row(row, value_index)
                evidence = " | ".join(row)
                parse_label_value_row_for_candidates(label, value, unit, missing, evidence, results)

    return results


def sort_missing(fields: list[str]) -> list[str]:
    order = {field: index for index, field in enumerate(MISSING_FIELD_ORDER)}
    return sorted(fields, key=lambda field: order.get(field, 999))


def load_missing_by_id() -> dict[str, list[str]]:
    if not REPORT_PATH.exists():
        return {}
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    entries = report.get("manualFieldCoverage", {}).get("weakestEntries", [])
    return {
        item["id"]: sort_missing((item.get("missingDecisionFields") or []) + (item.get("missingElectronicsFields") or []))
        for item in entries
        if item.get("id")
    }


def main() -> None:
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {"entries": []}
    manifest_by_id = {entry.get("id"): entry for entry in manifest.get("entries", []) if entry.get("id")}
    missing_by_id = load_missing_by_id()

    suggestions = []
    stats = {"entriesScanned": 0, "entriesWithSuggestions": 0, "candidateFields": 0}

    for entry in source.get("entries", []):
        entry_id = entry.get("id")
        cache = manifest_by_id.get(entry_id) or {}
        text_path_value = cache.get("textPath") or f"data/tds-cache/{entry_id}.txt"
        text_path = ROOT / text_path_value
        if not entry_id or not text_path.exists():
            continue

        missing = set(missing_by_id.get(entry_id) or [])
        if not missing:
            missing = set(actionable_missing(entry, MISSING_FIELD_ORDER))
        else:
            missing = {field for field in missing if field_status(entry, field) == "missing"}
        if not missing:
            continue

        lines = text_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        stats["entriesScanned"] += 1
        candidates_by_field = parse_markdown_table_candidates(lines, entry.get("name") or "", missing)
        line_candidates = extract_line_candidates(lines, missing)
        if cache.get("mistralMarkdownPath"):
            # Frequency-bearing electrical rows are reliable only when column
            # aligned. Do not let fallback line heuristics re-read 50 Hz or
            # adjacent tables as product values after Mistral table OCR exists.
            for field in ["dielectricConstant", "dissipationFactor"]:
                line_candidates.pop(field, None)
        for field, candidates in line_candidates.items():
            for item in candidates:
                add_candidate(candidates_by_field, item)
        _append_service_candidates_from_source(entry, set(missing), candidates_by_field, f"Cached source metadata from {entry.get('id')}")
        flat_candidates = []
        for field in sort_missing(list(candidates_by_field.keys())):
            flat_candidates.extend(sorted(candidates_by_field[field], key=lambda item: item["confidence"], reverse=True)[:3])
        if not flat_candidates:
            continue

        stats["entriesWithSuggestions"] += 1
        stats["candidateFields"] += len({item["field"] for item in flat_candidates})
        suggestions.append(
            {
                "id": entry_id,
                "maker": entry.get("maker"),
                "name": entry.get("name"),
                "referenceUrl": entry.get("referenceUrl"),
                "textPath": text_path_value,
                "missingFields": sort_missing(list(missing)),
                "candidates": flat_candidates,
            }
        )

    suggestions.sort(key=lambda item: (-len(item["candidates"]), item["maker"] or "", item["name"] or ""))
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": stats | {"suggestionEntries": len(suggestions)},
        "suggestions": suggestions,
    }
    OUTPUT_JSON_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# TDS Extraction Suggestions",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Entries scanned: {stats['entriesScanned']}",
        f"- Entries with suggestions: {stats['entriesWithSuggestions']}",
        f"- Candidate fields: {stats['candidateFields']}",
        "",
        "| Maker | Product | Candidates | Cache |",
        "| --- | --- | ---: | --- |",
    ]
    for item in suggestions[:40]:
        lines.append(
            f"| {item['maker']} | {item['name']} | {len(item['candidates'])} | `{item['textPath']}` |"
        )
    OUTPUT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_JSON_PATH.relative_to(ROOT)), **payload["stats"]}, indent=2))


if __name__ == "__main__":
    main()
