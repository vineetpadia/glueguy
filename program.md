# Glueguy Autoresearch Program

This repo uses an autoresearch-style loop for expanding an engineering adhesive database.

The goal is not to maximize raw entry count at any cost. The goal is to increase trustworthy coverage:

- Prefer official technical data sheets over distributor summaries.
- Keep observed pricing separate from technical evidence.
- Leave unsupported numeric fields blank instead of inventing values.
- Rebuild generated bundles after every data update.

## Files that matter

- `data/tds-manual-source.json`
  Manual, evidence-backed entries that are missing or materially under-modeled in the McMaster pipeline.
- `data/autonomous-research-seeds.json`
  Priority manufacturers and products that define the research backlog.
- `data/autonomous-discovery-config.json`
  Official sitemap and product-surface configs used to discover additional adhesive leads automatically.
- `scripts/discover_official_glue_products.py`
  Expands the official-source target universe beyond the hand-curated seed list.
- `scripts/run_glue_autoresearch.py`
  Runs one Glueguy research iteration and logs the result as a measurable experiment row.
- `scripts/autonomous_glue_research.py`
  Coverage audit that turns curated seeds plus discovered official leads into a ranked backlog report.
- `scripts/build_tds_manual_catalog.py`
  Compiles manual entries into the site bundle.
- `scripts/build_mcmaster_site_catalog.py`
  Rebuilds the McMaster-derived catalog and reference library.

## Operating loop

1. Run `python scripts/run_glue_autoresearch.py`.
2. Read `data/autonomous-research-report.md` and `data/autonomous-results.tsv`.
3. Pick the highest-priority missing product that has an official lead or an easy official search path.
4. Find the official TDS or official product page.
5. Extract only evidence-backed details:
   - chemistry / cure family
   - cure detail
   - work time / clamp time / cure time
   - explicit service range only if the source gives a real service rating
   - lap shear, peel, impact, or other mechanical metrics only if the source states them
   - recommended substrates
   - important warnings
6. Find an observed market price from McMaster or a distributor and store it separately as pricing evidence.
7. Add or improve the manual entry in `data/tds-manual-source.json`.
8. Rebuild:
   - `python scripts/build_tds_manual_catalog.py`
   - `python scripts/run_glue_autoresearch.py`
9. Verify:
   - `python -m py_compile scripts/build_tds_manual_catalog.py scripts/discover_official_glue_products.py scripts/run_glue_autoresearch.py scripts/autonomous_glue_research.py`
   - `node --check app.js`

## Data rules

- If a profile default would imply a metric that the source does not support, override it with `null`.
- Tested temperatures are not the same as rated service temperatures. Do not convert test conditions into service ratings.
- Distributor copy can help with packaging and observed price, but technical values should come from official sources whenever possible.
- Keep summaries concise and engineering-facing.
- Favor family-level entries when one TDS covers multiple pack sizes or close variants.

## What success looks like

- The report shows shrinking backlog for high-priority manufacturers.
- The discovery dataset grows without collapsing into junk URLs or marketing pages.
- `data/autonomous-results.tsv` shows improving total targets and falling missing-count over time.
- Manual entries raise fidelity where McMaster is thin or where official TDS data is better than catalog copy.
- The app remains robust when some products legitimately lack service range, thermal conductivity, gap-fill, or lap shear data.
