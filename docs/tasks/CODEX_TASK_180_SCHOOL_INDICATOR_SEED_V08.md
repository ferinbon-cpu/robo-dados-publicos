# TASK 180 — materialize 2025 school indicator seed from Base Mestra V05 / Camada V08

## Purpose

Correct the post-TASK-179 custody state and begin actual SCHOOL_INDICATOR_SERIES population from structured school assets already present in the user's File Library.

TASK 180 is T0/OFFLINE. It performs no new source acquisition and no Drive/Sheets/serving mutation.

## Custody correction

A deeper File Library search found both structured assets that TASK 179 initially considered handoff-missing:

- BASE_MESTRA_LIMEIRA_V05.xlsx
- CAMADA_ANALITICA_V06_40_ESCOLAS_V08.xlsx

The Base Mestra remains the canonical operational numeric source for already-materialized values.

Pinned Base Mestra V05 SHA-256:

`4d352dc55537240a4c1ffb3c37337e9c029577ab611f851f2ec925d0178b9eda`

Pinned Camada V08 XLSX SHA-256:

`0516868e06685aebe8254b11ca6488ef26b03dea61f927ff637840cf2a21e865`

Pinned Camada V08 SQLite SHA-256:

`7365bae889e866c5547089eac52a611c7b3e4a989d9f5bb601fff90eca54955b`

The V08 QA documents:
- 552 Censo panel rows for 2018–2025;
- 69/69 units in 2025;
- 40 primary-years schools;
- 29 Early Childhood units;
- 240/240 reconciliations in 2025;
- 0 divergences;
- 0 imputations.

## Seed scope

This task uses the directly readable V08 sheet:

`01 Escolas 40`

The sanitized evidence fixture contains exactly 40 unique Inep codes and 20 metric columns.

The seed is intentionally bounded to the 40 primary-years schools. It does not claim that the complete 69-school historical data model is already imported into the robot.

## Metrics

The seed materializes:

- INSE 2023;
- PPI 2023 and 2025;
- race/color non-declaration 2025;
- AFD 2025;
- IED levels 5/6 2025;
- IRD 2025;
- ICG 2025;
- ATU 2025;
- HAD 5th grade 2025;
- TDI 2025;
- approval 2025;
- full-time share 2025;
- infrastructure score;
- accessibility score;
- device count;
- Special Education enrollment;
- Ideb 2025;
- IEE 2025;
- SARESP participation 2025.

Source-family semantics are retained in the long rows:
- SAEB for INSE;
- CENSO_ESCOLAR for Census-derived context/teacher/flow/infrastructure metrics;
- IDEB for Ideb;
- SARESP for IEE/SARESP participation.

## Long-form conversion

The adapter converts the wide V08 sheet into TASK 176-compatible SCHOOL_INDICATOR_SERIES rows.

Expected universe:

- schools: 40
- metrics: 20
- potential school×metric cells: 800
- non-null long rows: 798
- missing cells: 2

The two missing values are both Ideb 2025:

- Inep 35276224 — CEIEF Mario Covas
- Inep 35217864 — EMEIEF Ary Gomes de Castro

They are stored in a separate missing ledger as:

`MISSING_SOURCE_CELL_NOT_ZERO`

No missing cell is converted to zero.

## Identity and provenance

Inep code is the school identity key.

Every long row carries:

- source family;
- pinned V08 SHA-256;
- exact sheet locator;
- source column;
- observation period;
- school code/name;
- quality status;
- caution.

The provenance locator format is:

`FILE_LIBRARY:CAMADA_ANALITICA_V06_40_ESCOLAS_V08.xlsx#01 Escolas 40:<inep>:<source_column>`

## Quality boundary

This seed is extracted through the File Library's readable representation of the pinned workbook.

Therefore:

- quality = READY_WITH_CAUTION
- binary import complete = false

The values may be queried and tested as a sanitized, pinned seed, but a future automated binary XLSX/SQLite import should revalidate them before promotion to a stronger import status.

## TASK 179 correction

Base Mestra V05 and Camada V08 are now marked:

`DISCOVERED_AND_READABLE_IN_USER_LIBRARY`

and:

`READY_FOR_FULL_STRUCTURED_ROW_MATERIALIZATION`

SCHOOL_INDICATOR_SERIES is now:

`READY_FROM_EXISTING_CUSTODY`

The first remaining custody handoff priority becomes MD_01.3B, not Base V05.

## Next materialization

After this seed:

1. materialize the Base V05 network series;
2. materialize the V08 69×year Censo 2018–2025 panel;
3. ingest remaining V08 long-history sheets;
4. then revisit the first remote OBS serving proof.

## Remote effects

- network: 0
- Drive write: 0
- serving: 0
- publication: 0
- schedule: 0
- recurrence: 0
