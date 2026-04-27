# Autonomous Glue Research Report

Generated: 2026-04-27T01:30:47.083624+00:00

## Snapshot

- Built-in app catalog records scanned: 215
- Manual TDS-backed entries: 517
- Manual entries with cached TDS text: 517
- Manual entries with complete core metadata: 517
- Manual core-field completeness ratio: 1.0
- Manual decision-field completeness ratio: 1.0
- Electronics-relevant manual entries: 241
- Manual electronics-field completeness ratio: 1.0
- McMaster selector products: 428
- McMaster reference families: 503
- McMaster official-TDS matches: 298
- McMaster product-page-only matches: 42
- Retailer-discovered product pages: 11
- Digi-Key electronics adhesive rows: 500
- Digi-Key unique TDS/datasheet leads: 286
- Digi-Key electronics product leads missing manual TDS extraction: 0
- Seeded manufacturers: 51
- Curated seed products: 265
- Discovered official-source leads: 481
- Blocked or excluded targets: 14
- Total target products/families: 548
- Covered seed products in autonomous sources: 534
- Missing seed products in autonomous sources: 0

## Next Actions

| Priority | Source | Kind | Manufacturer | Product | Official lead |
| --- | --- | --- | --- | --- | --- |

## Blocked Or Excluded Targets

| Priority | Source | Kind | Manufacturer | Product | Status | Note |
| --- | --- | --- | --- | --- | --- | --- |
| high | curated | product | Master Bond | EP30DPBF | exact-name-official-absent | No current exact official Master Bond page was found for EP30DPBF. Do not treat EP30DPBFMed as the same SKU. |
| high | curated | product | Permabond | MT3835 | exact-name-official-absent | No current exact official Permabond page was found for MT3835. Do not treat MT3836 as the same SKU. |
| medium | curated | product | 3M Thermally Conductive / Thermal Interface | TC-2035 | nearest-3m-official-match-is-non-adhesive | Do not satisfy the 3M TC-2035 seed with either non-adhesive 3M TCG-2035 grease or a different-maker Dow adhesive. The official 3M source is a grease/TIM, so it remains excluded from the adhesive catalog despite extractable thermal-interface fields. |
| medium | curated | product | DELO | PHOTOBOND 4497 | exact-official-tds-not-found | Do not encode PHOTOBOND 4497 from family-level UV-cure descriptions or unverified snippets; exact TDS is required. |
| medium | curated | product | DELO | DUOPOX AD895 | exact-official-tds-not-found | Family-level DELO DUOPOX claims are insufficient for the high-fidelity manual catalog; keep blocked until exact AD895 TDS is available. |
| medium | curated | product | DELO | PHOTOBOND AC245 | exact-official-tds-not-found | Treat PHOTOBOND AC245 as an unresolved/exact-name target; do not fill it with MONOPOX AC family data without official SKU mapping. |
| medium | curated | product | Bostik / Born2Bond (Arkema) | MM4001 | exact-official-tds-not-found | Do not substitute XMA 5005, MP515 or Structural for MM4001 without an official mapping. |
| high | discovered | product | Permabond | A905 | ancillary-not-adhesive | A905 is a surface activator/accelerator, not an adhesive product; exclude from the glue product backlog while retaining evidence. |
| high | discovered | product | Permabond | ASC10 | ancillary-not-adhesive | ASC10 is a surface conditioner/accelerator, not an adhesive product; exclude from the glue product backlog while retaining evidence. |
| high | discovered | product | Permabond | QFS10 | ancillary-not-adhesive | QFS10 is an activator/accelerator, not an adhesive product; exclude from the glue product backlog while retaining evidence. |
| high | discovered | product | Permabond | QFS16 | ancillary-not-adhesive | QFS16 is an activator/accelerator, not an adhesive product; exclude from the glue product backlog while retaining evidence. |
| medium | discovered | product | ThreeBond | TB1101 | lead-product-mismatch | TB1101 has no dedicated product page or TDS on threebond.com; the discovery lead points to TB1102 which is a different product. Do not substitute TB1102 data for TB1101. |
| medium | discovered | product | ThreeBond | TB1772M | lead-product-mismatch | TB1772M has no dedicated product page or TDS on threebond.com; the discovery lead points to TB1771M (different SKU). Do not substitute TB1771M data for TB1772M. |
| medium | discovered | product | ThreeBond | TB2027G | lead-product-mismatch | TB2027G has no dedicated product page or TDS on threebond.com; the discovery lead points to TB3027G (different product series). Do not substitute TB3027G data for TB2027G. |

## Retailer Discovery

| Retailer | Discovered pages |
| --- | ---: |
| Home Depot | 7 |
| Lowe's | 4 |

## Digi-Key Electronics TDS Leads

| Priority | Manufacturer | Product | Type | Datasheet | Stock | Score |
| --- | --- | --- | --- | --- | ---: | ---: |

## Manual TDS Field Coverage

| Field | Present | Ratio |
| --- | ---: | ---: |
| summary | 517 | 1.0 |
| cureFamily | 517 | 1.0 |
| cureDetail | 517 | 1.0 |
| applicationTags | 517 | 1.0 |
| referenceUrl | 517 | 1.0 |
| referenceCategory | 517 | 1.0 |
| referenceSampleType | 517 | 1.0 |
| referenceSampleConsistency | 517 | 1.0 |
| referenceForJoining | 517 | 1.0 |
| serviceMin | 517 | 1.0 |
| serviceMax | 517 | 1.0 |
| potLife | 517 | 1.0 |
| fixtureTime | 517 | 1.0 |
| lapShear | 517 | 1.0 |
| viscosityClass | 517 | 1.0 |
| clarity | 517 | 1.0 |
| thermalConductivity | 517 | 1.0 |
| stress | 517 | 1.0 |
| substrates | 517 | 1.0 |
| cautions | 517 | 1.0 |
| viscosityValue | 517 | 1.0 |
| viscosityUnit | 517 | 1.0 |
| electricalBehavior | 517 | 1.0 |
| volumeResistivityOhmM | 517 | 1.0 |
| surfaceResistivityOhm | 517 | 1.0 |
| connectionResistanceOhm | 517 | 1.0 |
| insulationResistanceOhm | 517 | 1.0 |
| dielectricConstant | 517 | 1.0 |
| dissipationFactor | 517 | 1.0 |
| dielectricBreakdownVPerMil | 517 | 1.0 |
| dielectricBreakdownKVPerMm | 517 | 1.0 |
| tensileStrengthMPa | 517 | 1.0 |
| elongationPct | 517 | 1.0 |
| hardnessValue | 517 | 1.0 |
| hardnessScale | 517 | 1.0 |
| peelStrengthNPerM | 517 | 1.0 |
| chipBondStrengthMPa | 517 | 1.0 |
| cureDepthMm | 517 | 1.0 |
| tackFreeTime | 517 | 1.0 |
| cureProfiles | 517 | 1.0 |

## Weakest Manual TDS Records

| Maker | Product | Cached text | Core coverage | Decision coverage | Electronics coverage | Missing decision fields |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 3M | 8211 Optically Clear Adhesive | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Bondo Fiberglass Resin 0401 / 00401 / Liquid Resin for Fiberglass | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | High-Temperature Masking Liquid 2538UV | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Marine Adhesive Sealant Fast Cure 4200FC Black / 4200FC-BLACK / 06564 | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Neoprene High Performance Rubber & Gasket Adhesive 1300 / 1300L | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Plastic Bonding Adhesive 2665B | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Scotchcast Connector Sealing Pack 3570G-N | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Scotchcast Flame-Retardant Electrical Insulating Resin 2131 / 2131B | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Scotchcast Re-enterable Electrical Insulating Resin 2123 / 2123D | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Scotch-Grip 847 Nitrile High Performance Rubber and Gasket Adhesive | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Scotchkote Liquid Epoxy Coating 323+ / 7100168702 | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Scotch-Seal Tamper Proof Sealant 1252 | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Scotch Spray Mount Adhesive 6065 / 7100129195 | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Scotch Super Glue Liquid in Precision Applicator AD124 | yes | 1.0 | 1.0 | 1.0 | — |
| 3M | Scotch-Weld 2216 B/A Translucent / Clear / 7000046479 | yes | 1.0 | 1.0 | 1.0 | — |

## Weakest Electronics TDS Records

| Maker | Product | Electronics coverage | Missing electronics fields |
| --- | --- | ---: | --- |
| 3M | High-Temperature Masking Liquid 2538UV | 1.0 | — |
| 3M | Plastic Bonding Adhesive 2665B | 1.0 | — |
| 3M | Scotchcast Connector Sealing Pack 3570G-N | 1.0 | — |
| 3M | Scotchcast Flame-Retardant Electrical Insulating Resin 2131 / 2131B | 1.0 | — |
| 3M | Scotchcast Re-enterable Electrical Insulating Resin 2123 / 2123D | 1.0 | — |
| 3M | Scotch-Seal Tamper Proof Sealant 1252 | 1.0 | — |
| 3M | Scotch-Weld 2216 B/A Translucent / Clear / 7000046479 | 1.0 | — |
| 3M | Scotch-Weld DP125 Gray / 7100320278 / 7100320279 | 1.0 | — |
| 3M | Scotch-Weld DP125 Translucent / 7100320463 | 1.0 | — |
| 3M | Scotch-Weld DP2216 Gray / 2216 B/A Gray | 1.0 | — |
| 3M | Scotch-Weld DP420 Black / 7100319970 / DP420 BLACK 200ML | 1.0 | — |
| 3M | Scotch-Weld DP420 Off White / 7100320185 / 7100320494 | 1.0 | — |

## Manufacturer Coverage

| Priority | Manufacturer | Seeded | Covered | Missing | Official domains |
| --- | --- | ---: | ---: | ---: | --- |
| high | 3M | 17 | 17 | 0 | 3m.com, multimedia.3m.com |
| high | Dow / Dupont Silicones | 6 | 6 | 0 | dupont.com, dow.com, consumer.dow.com |
| high | Dymax | 7 | 7 | 0 | dymax.com |
| high | Epoxy Technology (EPO-TEK) | 9 | 9 | 0 | epotek.com, meridianadhesives.com |
| high | Henkel Loctite | 28 | 28 | 0 | henkel-adhesives.com, loctite.com |
| high | Huntsman Araldite | 9 | 9 | 0 | advancedmaterials.huntsman.com, aralditeadhesives.com, huntsman.com |
| high | LORD / Parker | 10 | 10 | 0 | parker.com, fusor.com |
| high | Master Bond | 8 | 7 | 0 | masterbond.com |
| high | Permabond | 165 | 160 | 0 | permabond.com |
| high | Plexus (ITW) | 6 | 6 | 0 | itwperformancepolymers.com, plexus.com |
| high | Sika | 10 | 10 | 0 | usa.sika.com, sika.com |
| medium | 3M Thermally Conductive / Thermal Interface | 3 | 2 | 0 | 3m.com |
| medium | Aremco | 3 | 3 | 0 | aremco.com |
| medium | Bostik / Born2Bond (Arkema) | 3 | 2 | 0 | born2bond.com, bostik.com |
| medium | CEMEDINE | 5 | 5 | 0 | cemedine.co.jp |
| medium | Chip Quik Inc. | 22 | 22 | 0 | chipquik.com |
| medium | Cotronics | 4 | 4 | 0 | cotronics.com |
| medium | DELO | 5 | 2 | 0 | delo-adhesives.com, delo.de |
| medium | Devcon (ITW) | 4 | 4 | 0 | itwperformancepolymers.com, devcon.com |
| medium | DOW | 3 | 3 | 0 | dow.com |
| medium | E6000 | 4 | 4 | 0 | eclecticproducts.com |
| medium | GC Electronics | 5 | 5 | 0 | gcelectronics.com |
| medium | Gorilla Glue | 4 | 4 | 0 | gorillatough.com |
| medium | J-B Weld | 8 | 8 | 0 | jbweld.com |
| medium | Limitless Shielding Limited | 4 | 4 | 0 | limitlessshielding.com, limitlessshld.com |
| medium | Liquid Nails | 4 | 4 | 0 | liquid-nails.com, buyat.ppg.com |
| medium | MG Chemicals | 2 | 2 | 0 | mgchemicals.com |
| medium | Momentive | 1 | 1 | 0 | momentive.com |
| medium | Oatey / IPS Weld-On | 5 | 5 | 0 | oatey.com, ipscorp.com, weldon.com |
| medium | Panacol | 3 | 3 | 0 | panacol.com |
| medium | Penchem Technologies | 4 | 4 | 0 | penchem.com |
| medium | Shin-Etsu Silicone | 5 | 5 | 0 | shinetsusilicone-global.com |
| medium | ThreeBond | 126 | 123 | 0 | threebond.com, threebond.co.jp |
| medium | Titebond | 4 | 4 | 0 | titebond.com |
| medium | WACKER / SEMICOSIL | 5 | 5 | 0 | wacker.com |
| medium | WEICON | 5 | 5 | 0 | weicon.com |
| low | ABB Installation Products / Carlon | 2 | 2 | 0 | carlon.com, abb.com |
| low | Atom Adhesives | 2 | 2 | 0 |  |
| low | Bob Smith Industries (BSI) | 3 | 3 | 0 | bsi-inc.com |
| low | Chemtronics | 1 | 1 | 0 | chemtronics.com |
| low | DAP | 3 | 3 | 0 | dap.com |
| low | Digiwave | 1 | 1 | 0 | digiwave.com |
| low | Gardner Bender | 2 | 2 | 0 | gardnerbender.com |
| low | Glue Dots / GDI Adhesives | 2 | 2 | 0 | gdiaffix.com |
| low | ITW Performance Polymers | 2 | 2 | 0 | itwperformancepolymers.com, devcon.com |
| low | Micro-Measurements (Division of Vishay Precision Group) | 1 | 1 | 0 | vishayprecision.com |
| low | Momentive Performance Materials | 4 | 4 | 0 | momentive.com |
| low | Omega | 1 | 1 | 0 | omegaeng.com |
| low | Panduit Corp | 1 | 1 | 0 | panduit.com |
| low | ResinTech / Traktronix | 3 | 3 | 0 | resintech.com, raktronix.com |
| low | TE Connectivity Raychem | 4 | 4 | 0 | raychem.com, te.com |

## Missing By Manufacturer
