# Glueboy Lab

Spreadsheet-style adhesive selector plus a larger McMaster-derived engineering reference library.

## Run locally

```bash
python3 -m http.server 4317
```

Open `http://127.0.0.1:4317/`.

## Catalog pipeline

1. Crawl McMaster glue families into raw JSON.

```bash
python scripts/mcmaster_glue_pipeline.py --max-pages 220 --output data/mcmaster-glues.json
```

2. Enrich the representative McMaster part page for each family into a reusable detail cache.

```bash
python scripts/enrich_mcmaster_product_details.py
```

This enriches the representative McMaster part page for each family into
`data/mcmaster-product-details.json`, adding higher-fidelity fields like part
numbers, package data, mix ratio, coverage, consistency, peel, `For Use On`,
and direct McMaster spec-page URLs.

3. Transform the raw crawl plus the detail cache into site-ready selector products and reference families.

```bash
python scripts/build_mcmaster_site_catalog.py
```

4. Build the manual TDS-backed additions that are not yet covered by the McMaster crawl.

```bash
python scripts/build_tds_manual_catalog.py
```

5. Run the autonomous coverage audit and backlog report.

```bash
python scripts/run_glue_autoresearch.py
```

This writes:

- `data/mcmaster-glues.json`
- `data/mcmaster-product-details.json`
- `data/mcmaster-site-summary.json`
- `data/mcmaster-site-catalog.js`
- `data/tds-manual-catalog.js`
- `data/autonomous-discovered-products.json`
- `data/autonomous-research-report.json`
- `data/autonomous-research-report.md`
- `data/autonomous-results.tsv`

## Verification

```bash
python -m py_compile scripts/enrich_mcmaster_product_details.py scripts/build_mcmaster_site_catalog.py scripts/build_tds_manual_catalog.py scripts/discover_official_glue_products.py scripts/autonomous_glue_research.py scripts/mcmaster_glue_pipeline.py
node --check app.js
```

## Autonomous loop

- `program.md` defines the autoresearch-style operating loop for this repo.
- `data/autonomous-research-seeds.json` defines target manufacturers and products.
- `data/autonomous-discovery-config.json` defines which official sitemap surfaces should be mined automatically.
- `scripts/discover_official_glue_products.py` expands the backlog from official manufacturer surfaces.
- `scripts/run_glue_autoresearch.py` executes one measurable discovery-plus-audit experiment and appends it to `data/autonomous-results.tsv`.
- `scripts/autonomous_glue_research.py` merges curated seeds plus discovered official leads into a ranked backlog report.

## Current pipeline snapshot

- `428` McMaster-derived selector products
- `503` McMaster reference families
- `11` manual TDS-backed entries
- `298` McMaster families matched to an official TDS
- `42` McMaster families with product-page-only fallback
- `881` observed McMaster package offers
