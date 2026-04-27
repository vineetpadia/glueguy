#!/usr/bin/env python3
"""Print the next high-impact TDS extraction targets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from autonomous_glue_research import (  # noqa: E402
    MANUAL_CORE_FIELDS,
    MANUAL_DECISION_FIELDS,
    MANUAL_ELECTRONICS_FIELDS,
    is_electronics_relevant,
    manual_field_status,
    normalized_electrical_behavior,
)

REPORT_PATH = ROOT / "data" / "autonomous-research-report.json"
SUGGESTIONS_PATH = ROOT / "data" / "tds-extraction-suggestions.json"
SOURCE_PATH = ROOT / "data" / "tds-manual-source.json"
MANIFEST_PATH = ROOT / "data" / "tds-cache-manifest.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def all_missing(entry: dict, fields: list[str]) -> list[str]:
    return [field for field in fields if manual_field_status(entry, field)["status"] == "missing"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--electronics-only", action="store_true")
    args = parser.parse_args()

    report = load_json(REPORT_PATH)
    suggestions = load_json(SUGGESTIONS_PATH)
    source = load_json(SOURCE_PATH)
    manifest = load_json(MANIFEST_PATH)

    suggestions_by_id = {
        item["id"]: item
        for item in suggestions.get("suggestions", [])
        if item.get("id")
    }
    manifest_by_id = {
        item["id"]: item
        for item in manifest.get("entries", [])
        if item.get("id")
    }
    report_by_id = {
        item["id"]: item
        for item in report.get("manualFieldCoverage", {}).get("weakestEntries", [])
        if item.get("id")
    }

    rows: list[dict] = []
    for entry in source.get("entries", []):
        entry_id = entry.get("id")
        if not entry_id:
            continue

        electronics_relevant = is_electronics_relevant(entry)
        if args.electronics_only and not electronics_relevant:
            continue

        missing_core = all_missing(entry, MANUAL_CORE_FIELDS)
        missing_decision = all_missing(entry, MANUAL_DECISION_FIELDS)
        missing_electronics = all_missing(entry, MANUAL_ELECTRONICS_FIELDS)
        if not missing_core and not missing_decision and not missing_electronics:
            continue

        all_monitored = [*MANUAL_CORE_FIELDS, *MANUAL_DECISION_FIELDS, *MANUAL_ELECTRONICS_FIELDS]
        verified_absent = [
            field
            for field in all_monitored
            if manual_field_status(entry, field)["status"] == "verified_absent"
        ]
        not_applicable = [
            field
            for field in all_monitored
            if manual_field_status(entry, field)["status"] == "not_applicable"
        ]

        decision_coverage = round(
            (len(MANUAL_DECISION_FIELDS) - len(missing_decision)) / len(MANUAL_DECISION_FIELDS),
            3,
        )
        electronics_coverage = round(
            (len(MANUAL_ELECTRONICS_FIELDS) - len(missing_electronics))
            / len(MANUAL_ELECTRONICS_FIELDS),
            3,
        )
        suggestion = suggestions_by_id.get(entry_id, {})
        report_item = report_by_id.get(entry_id, {})
        cache = manifest_by_id.get(entry_id, {})
        candidates = suggestion.get("candidates", [])

        actionable_candidates = [
            candidate
            for candidate in candidates
            if isinstance(candidate.get("field"), str)
            and manual_field_status(entry, candidate.get("field"))["status"] == "missing"
        ]

        rows.append(
            {
                "id": entry_id,
                "maker": entry.get("maker"),
                "name": entry.get("name"),
                "electronicsRelevant": electronics_relevant,
                "electricalBehaviorClass": normalized_electrical_behavior(entry),
                "coreCoverage": report_item.get("coreFieldCoverage"),
                "decisionCoverage": report_item.get("decisionFieldCoverage", decision_coverage),
                "electronicsCoverage": report_item.get("electronicsFieldCoverage", electronics_coverage),
                "candidateCount": len(actionable_candidates),
                "candidateFields": sorted(
                    {
                        candidate.get("field")
                        for candidate in actionable_candidates
                        if candidate.get("field")
                    }
                ),
                "missingCoreFields": report_item.get("missingCoreFields", missing_core),
                "missingDecisionFields": report_item.get("missingDecisionFields", missing_decision),
                "missingElectronicsFields": report_item.get(
                    "missingElectronicsFields",
                    missing_electronics,
                ),
                "verifiedAbsentCount": len(report_item.get("verifiedAbsentFields", verified_absent)),
                "notApplicableCount": len(report_item.get("notApplicableFields", not_applicable)),
                "textPath": suggestion.get("textPath") or cache.get("textPath"),
            }
        )

    rows.sort(
        key=lambda row: (
            not row["electronicsRelevant"],
            -(len(row["missingCoreFields"]) + len(row["missingDecisionFields"]) + len(row["missingElectronicsFields"])),
            -row["candidateCount"],
            row["electronicsCoverage"] if row["electronicsCoverage"] is not None else 1,
            row["decisionCoverage"] if row["decisionCoverage"] is not None else 1,
            row["maker"] or "",
            row["name"] or "",
        ),
    )

    print(
        "id\tmaker\tproduct\telectronics\tbehavior\tcore_cov\tdecision_cov\telectronics_cov\tcandidates\tverified_absent\tnot_applicable\tmissing_core\tmissing_decision\tmissing_electronics\tcandidate_fields\ttext_path"
    )
    for row in rows[: args.limit]:
        print(
            "\t".join(
                [
                    row["id"] or "",
                    row["maker"] or "",
                    row["name"] or "",
                    str(row["electronicsRelevant"]),
                    row["electricalBehaviorClass"] or "",
                    str(len(row["missingCoreFields"])),
                    str(row["decisionCoverage"]),
                    str(row["electronicsCoverage"]),
                    str(row["candidateCount"]),
                    str(row["verifiedAbsentCount"]),
                    str(row["notApplicableCount"]),
                    ",".join(row["missingCoreFields"]),
                    ",".join(row["missingDecisionFields"]),
                    ",".join(row["missingElectronicsFields"]),
                    ",".join(row["candidateFields"]),
                    row["textPath"] or "",
                ]
            )
        )


if __name__ == "__main__":
    main()
