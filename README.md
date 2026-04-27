# Glueboy Lab

Spreadsheet-style adhesive selector plus a larger McMaster-derived engineering reference library.

## Run locally

```bash
python3 -m http.server 4317 --bind 0.0.0.0
```

Open `http://127.0.0.1:4317/` on the host, or from another machine on the same LAN/VPN open `http://<host-ip>:4317/`.

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

5. Build the machine-readable catalog intended for LLM/tool agents.

```bash
python scripts/build_agent_catalog.py
```

This writes `data/agent-catalog.json`, a compact JSON endpoint with source
URLs, cached TDS text paths, exact specs, missing-field lists, and agent notes.
Agents should treat missing fields as unavailable, not infer them from profile
defaults.

6. Normalize any Digi-Key electronics adhesive export into distributor/TDS leads.

```bash
python scripts/import_digikey_adhesive_applicators.py
```

7. Run the autonomous coverage audit and backlog report.

```bash
python scripts/run_glue_autoresearch.py
```

This writes:

- `data/mcmaster-glues.json`
- `data/mcmaster-product-details.json`
- `data/mcmaster-site-summary.json`
- `data/mcmaster-site-catalog.js`
- `data/tds-manual-catalog.js`
- `data/agent-catalog.json`
- `data/autonomous-discovered-products.json`
- `data/digikey-electronics-adhesives.json`
- `data/autonomous-research-report.json`
- `data/autonomous-research-report.md`
- `data/tds-extraction-suggestions.json`
- `data/tds-extraction-suggestions.md`
- `data/autonomous-results.tsv`

8. Mine cached TDS text for reviewable field candidates when working the manual backlog.

```bash
python scripts/extract_tds_field_candidates.py
```

This reads `data/tds-cache-manifest.json` plus the current missing-field audit
and writes source-snippet-backed candidates for viscosity, electrical,
mechanical, cure, service-temperature, and thermal fields. It deliberately does
not edit `data/tds-manual-source.json`; the output is a ranked verification
queue that makes exact TDS transcription faster without inventing values.

The cache pipeline is Mistral-first for PDFs when an OCR sidecar exists:
`scripts/cache_tds_sources.py` prefers `data/tds-cache/<id>.mistral.md` over
`pdftotext` and records `textExtraction: mistral-ocr-markdown` in
`data/tds-cache-manifest.json`. `pdftotext` remains only as the fallback for
entries that do not yet have Mistral OCR output.

To import a Mistral OCR MCP result into the cache sidecars:

```bash
python scripts/import_mistral_ocr_result.py <entry-id> --input /path/to/mistral-result.json
```

To generate OCR sidecars directly from cached PDFs using the local Codex MCP
Mistral credential:

```bash
/home/scandium/.local/share/mcp-mistral-ocr-venv/bin/python scripts/ocr_tds_with_mistral.py --limit 25
python scripts/cache_tds_sources.py
python scripts/extract_tds_field_candidates.py
```

To print the next highest-impact products with candidate fields:

```bash
python scripts/tds_gap_queue.py --electronics-only --limit 25
```

## Verification

```bash
python -m py_compile scripts/enrich_mcmaster_product_details.py scripts/build_mcmaster_site_catalog.py scripts/build_tds_manual_catalog.py scripts/build_agent_catalog.py scripts/discover_official_glue_products.py scripts/autonomous_glue_research.py scripts/mcmaster_glue_pipeline.py
python -m py_compile scripts/cache_tds_sources.py scripts/extract_tds_field_candidates.py scripts/import_mistral_ocr_result.py scripts/ocr_tds_with_mistral.py scripts/tds_gap_queue.py
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
