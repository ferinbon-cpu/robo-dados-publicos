# TASK 057 — F01 FUNDEB Fomento ETI linkage candidate selection

## Objective
Use only metadata-safe Drive search surfaces to compare the three existing-custody FUNDEB candidates retained by TASK 054 and determine whether metadata alone can justify which source is best for tracing the SIOPE/FUNDEB `FOMENTO ETI (4%)` reporting bucket to local accounting keys.

## Authorization
Owner message: `Prossiga autorizado`.

This authorization is consumed by TASK 057 only. It does not authorize any source-content read.

## Hard boundaries
- metadata-only Drive search;
- explicit `item_type=document`;
- `best_effort_fetch=false`;
- exact three-candidate set only;
- no Drive fetch/content hydration;
- no OCR;
- no public-source network;
- no Drive write;
- no Bronze/Silver/Gold write;
- no serving/publication.

## Candidates observed
1. `FUNDEB_LIMEIRA_2026_01.pdf` — `1zRG-7fXYMTOMjsbWWJzoaSF7kQ54kJMe`
2. `FUNDEB_LIMEIRA_2026_02.pdf` — `1xmAFcp2pYYeua3vHQQoY4_tfFZzr21-I`
3. `FUNDEB_LIMEIRA_2026_03.pdf` — `1m1mg8LX-7VOn81Rl4t-zgDoP23JPCTRd`

For all three, the metadata-safe surface exposed only title, Drive ID and Drive URL. No content was hydrated.

## Selection result
Metadata alone does **not** distinguish the candidates by evidentiary granularity. The `_01`, `_02`, `_03` suffixes cannot be treated as evidence that one document contains better program/action/ficha/transaction-level linkage than another.

Therefore TASK 057 records an evidentiary tie:

`METADATA_TIE_NO_EVIDENTIARY_BEST_CANDIDATE`

A forced claim that one candidate is 'best' is forbidden.

## Deterministic next probe
To continue without inventing a ranking, the next bounded probe selects `FUNDEB_LIMEIRA_2026_01.pdf` only by stable seed order. This is **not** a claim of superior evidentiary value.

Any content read of that file requires a fresh explicit owner authorization and remains bounded to exactly one source.

## Status
- F01: `SILVER_SCOPED_PARTIAL_VALIDATED`
- EITI reporting identity: `PARTIALLY_PROVEN_DEDICATED_FUNDEB_FOMENTO_ETI_BUCKET`
- transaction-level identity: `EVIDENCIA_INSUFICIENTE`
- overall EITI financial identity: `EVIDENCIA_INSUFICIENTE`
- Gold / serving / publication: blocked

## Result
`PASS_TASK057_METADATA_ONLY_TIE_NO_EVIDENTIARY_BEST_CANDIDATE_NEXT_PROBE_SELECTED_BY_STABLE_ORDER_NO_PROMOTION`

## Next bounded gate
`TASK_058_F01_FUNDEB_TIED_CANDIDATE_01_BOUNDED_CONTENT_READ`

Selected only as the first deterministic probe among tied candidates:
- `FUNDEB_LIMEIRA_2026_01.pdf`
- Drive ID `1zRG-7fXYMTOMjsbWWJzoaSF7kQ54kJMe`

Fresh owner authorization is required before opening it.
