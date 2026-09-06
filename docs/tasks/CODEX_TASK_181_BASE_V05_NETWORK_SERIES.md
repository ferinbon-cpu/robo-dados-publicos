# TASK 181 — materialize Base V05 network education and fiscal series

## Objective

Use the already-owned Base Mestra Limeira V05 network series as structured observatory input, without recollecting source data.

Source:
- BASE_MESTRA_LIMEIRA_V05.xlsx
- sheet: Series Rede
- SHA-256: 4d352dc55537240a4c1ffb3c37337e9c029577ab611f851f2ec925d0178b9eda
- period: 2007–2025

TASK 181 is T0/OFFLINE and uses a sanitized File-Library-mediated fixture. Binary workbook import remains false.

## Role separation

The source sheet mixes education performance, fiscal indicators and remuneration. TASK 181 does not flatten those into one semantic table.

### SCHOOL_INDICATOR_SERIES

The following become network-level school/education indicators: Ideb; Ideb LP and Mathematics proficiencies; DSU; TNR; approval; failure; dropout; Saeb LP/MAT; SARESP Adequado+Avançado LP/MAT; official SARESP municipal LP/MAT means; simple school SARESP LP/MAT means.

The scope id is LIMEIRA_MUNICIPAL_NETWORK_PRIMARY_YEARS, with an explicit caution that the historical network uses the effective universe of each year.

### FISCAL_SERIES

Only the two explicitly labeled SIOPE columns are promoted to fiscal rows: SIOPE MDE % and SIOPE FUNDEB remuneração %. They are kept as education-finance indicators, not execution stages.

### DEFERRED_SOURCE_ROLE_REVIEW

Average gross teacher remuneration and 40h teacher remuneration are preserved in a deferred ledger but are not promoted into a query product because the underlying source role is not pinned here.

## Row counts

The complete 2007–2025 sheet contains 19 year rows.

- SCHOOL_INDICATOR_SERIES: 171 non-null rows
- school missing ledger: 133 cells
- FISCAL_SERIES: 38 non-null rows
- fiscal missing: 0
- deferred remuneration: 16 observed + 22 missing cells

Blanks remain missing. Published numeric zero remains zero. In 2007, both SIOPE percentages are explicitly 0 and remain observations.

## SARESP guard

The source explicitly states that a simple mean of school values does not replace the official municipal mean. TASK 181 therefore uses separate indicator ids.

For 2025: official LP mean = 219; simple-school LP mean = 219.40499999999997; official Mathematics mean = 240; simple-school Mathematics mean = 240.60999999999996.

## 2025 network seed values

Ideb = 7.1; Ideb LP = 236.43; Ideb MAT = 254.45; DSU = 96.2%; TNR = 0.6%; approval = 99.9%; failure = 0.1%; dropout = 0%; SIOPE MDE = 28.48%; SIOPE FUNDEB remuneration = 99.47%.

## Quality boundary

All generated rows carry the pinned Base V05 hash and exact Series Rede:<year>:<source column> provenance. Quality is READY_WITH_CAUTION because this task uses a File-Library-mediated sanitized extraction rather than a binary XLSX/SQLite import.

## Remote effects

- network: 0
- Drive write: 0
- serving: 0
- publication: 0
- schedule: 0
- recurrence: 0

## Next

Continue existing-custody population with Camada V08 81 Censo 69 2018-25, annual ATU/HAD/TNR and other long-history sheets, then refresh the query-product catalog before the first remote serving proof.
