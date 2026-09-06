# TASK 182 — V08 Censo aggregates and 552-row panel import contract

## Purpose

Continue population of SCHOOL_INDICATOR_SERIES from the user's existing Camada Analítica V08 without pretending the File Library search layer is a binary transfer channel.

Source: CAMADA_ANALITICA_V06_40_ESCOLAS_V08.xlsx; SHA-256 0516868e06685aebe8254b11ca6488ef26b03dea61f927ff637840cf2a21e865; SQLite SHA-256 7365bae889e866c5547089eac52a611c7b3e4a989d9f5bb601fff90eca54955b.

## Part A — materialized aggregate series

Sheet 88 Dashboard V08 is fully readable and yields 8 years × 6 metrics = 48 SCHOOL_INDICATOR_SERIES rows for 2018–2025.

Metrics: Special Education enrollment AI40; Special Education enrollment EI; AEE room availability AI40; AEE room availability EI; accessible bathroom AI40; broadband EI.

The AI40 subgroup is the stable 40-school primary-years panel. The EI subgroup preserves the observed current-unit universe by year; it is not silently treated as a fixed denominator. Cadastral presence never means quality, sufficiency or pedagogical use.

## Part B — full 552-row panel contract

Sheet 81 Censo 69 2018-25 is pinned as a 552-row, 25-column panel for 2018–2025. The contract pins all 25 headers and 18 numeric/cadastral metrics, source status, first-year-with-same-code and declared source file.

Expected 2025 coverage: 69 units = 40 AI + 29 EI. QA: 240/240 reconciliations and 0 divergences; imputations 0.

The File Library currently supports search/readback of this workbook but not a complete binary/row stream into the GitHub runtime. Therefore full_panel_materialized remains false and runtime_row_transfer_complete remains false.

The adapter already validates an exact 552×25 row bundle and can convert it to 9,936 potential long school-indicator rows (552 × 18 metrics) while preserving missing cells separately. Partial search snippets are explicitly forbidden as a reconstruction mechanism.

## Quality and guards

Missing != zero. Source status is preserved. Pre-first-year state is preserved. Source-file column is preserved. Accessibility/connectivity presence is descriptive cadastral evidence, not quality or causal evidence.

## Remote effects

Network 0; Drive write 0; serving 0; publication 0; schedule 0; recurrence 0.

## Next

Continue with V08 annual ATU/HAD/TNR and other already-closed long-history sheets, and solve the binary/CSV row-transfer path for the 552-row panel before claiming full school-year Censo materialization.
