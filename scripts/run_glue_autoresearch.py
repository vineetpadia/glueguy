#!/usr/bin/env python3
"""Run one Glueboy autoresearch cycle and append a measurable result row."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "data" / "autonomous-results.tsv"
DISCOVERED_PATH = ROOT / "data" / "autonomous-discovered-products.json"
REPORT_PATH = ROOT / "data" / "autonomous-research-report.json"


def run_step(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    run_step("python", "scripts/discover_official_glue_products.py")
    run_step("python", "scripts/autonomous_glue_research.py")

    discovered = json.loads(DISCOVERED_PATH.read_text())
    report = json.loads(REPORT_PATH.read_text())
    stats = report["stats"]
    row = "\t".join(
        [
            datetime.now(timezone.utc).isoformat(),
            str(discovered["stats"]["discoveredEntries"]),
            str(stats["seededProducts"]),
            str(stats["missingSeedProducts"]),
            f"{stats['coverageRatio']:.3f}",
            "keep",
            "discover + audit cycle",
        ]
    )
    with RESULTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(row + "\n")


if __name__ == "__main__":
    main()
