#!/usr/bin/env python3
"""Run Glueboy autoresearch cycles and append measurable result rows."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "data" / "autonomous-results.tsv"
DISCOVERED_PATH = ROOT / "data" / "autonomous-discovered-products.json"
REPORT_PATH = ROOT / "data" / "autonomous-research-report.json"
CACHE_MANIFEST_PATH = ROOT / "data" / "tds-cache-manifest.json"
RESULTS_HEADER = (
    "timestamp\tofficial_discovered_entries\tretailer_entries\tcached_tds_entries\t"
    "cached_tds_errors\tseeded_products\tmissing_seed_products\tcoverage_ratio\t"
    "action\tcycle_label\n"
)


def run_step(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def ensure_results_header() -> None:
    if RESULTS_PATH.exists() and RESULTS_PATH.stat().st_size > 0:
        first_line = RESULTS_PATH.read_text(encoding="utf-8").splitlines()[0]
        if first_line == RESULTS_HEADER.strip():
            return
    RESULTS_PATH.write_text(RESULTS_HEADER, encoding="utf-8")


def run_cycle() -> None:
    python = sys.executable
    ensure_results_header()
    run_step(python, "scripts/discover_official_glue_products.py")
    run_step(python, "scripts/discover_retailer_glue_products.py")
    run_step(python, "scripts/import_digikey_adhesive_applicators.py")
    run_step(python, "scripts/cache_tds_sources.py")
    run_step(python, "scripts/autonomous_glue_research.py")
    run_step(python, "scripts/extract_tds_field_candidates.py")

    discovered = json.loads(DISCOVERED_PATH.read_text())
    report = json.loads(REPORT_PATH.read_text())
    cache = json.loads(CACHE_MANIFEST_PATH.read_text()) if CACHE_MANIFEST_PATH.exists() else {"stats": {}}
    stats = report["stats"]
    row = "\t".join(
        [
            datetime.now(timezone.utc).isoformat(),
            str(discovered["stats"]["discoveredEntries"]),
            str(stats.get("retailerEntries", 0)),
            str(cache.get("stats", {}).get("cached", 0)),
            str(cache.get("stats", {}).get("errors", 0)),
            str(stats["seededProducts"]),
            str(stats["missingSeedProducts"]),
            f"{stats['coverageRatio']:.3f}",
            "keep",
            "discover + retailer + cache + audit cycle",
        ]
    )
    with RESULTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(row + "\n")


def main() -> None:
    continuous = os.environ.get("GLUEBOY_CONTINUOUS", "").lower() in {"1", "true", "yes"}
    sleep_seconds = int(os.environ.get("GLUEBOY_SLEEP_SECONDS", "1800"))
    if not continuous:
        run_cycle()
        return
    while True:
        run_cycle()
        time.sleep(max(60, sleep_seconds))


if __name__ == "__main__":
    main()
