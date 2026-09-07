# TASK 194K — MIEST class-count materialization

## Goal

Close the last missing metric in `NETWORK_Q1 — Quantos alunos, turmas e escolas existem?` without using the forbidden `matrículas ÷ ATU` proxy.

## User-mediated official handoff

TASK 194J correctly stopped on HTTP 403 when the automated runner attempted the official SEDUC-SP MIEST December 2025 CSV. The owner then opened the exact official URLs in a normal browser and handed off the downloaded artifacts for offline inspection.

The public repository stores only sanitized provenance, hashes, field semantics and aggregates. Raw CSV/XLSX bytes are not committed.

### Artifacts

- `MIEST CICLO - 12 2025.csv`
  - SHA-256 `72577ea79fcdacd22f96daf114b25fa49f623bd3496ca0bba619e43c291f2b6b`
  - 30,244 rows × 183 columns.
- `DICIONÁRIO_MIEST.xlsx`
  - SHA-256 `4444763557f26e76164a331a495601b042ce161f1fa4eb0ba26a93e163392391`.

## Direct network evidence

Filtering the MIEST by Limeira and `NOMEDEP=MUNICIPAL` yields exactly 69 rows and 69 unique INEP school codes.

All 40 INEP codes already pinned by TASK 180 are present. Their complement is exactly the 29 EI-only units previously validated by TASK 193.

Direct curricular class sums:

- Educação Infantil: **538**;
- Ensino Fundamental: **565**;
- EJA: **7**;
- total: **1,110**.

Subgroup reconciliation:

- AI40: **816**;
- EI29: **294**;
- network: **816 + 294 = 1,110**.

The EI29 subtotal exactly reproduces the independently validated `Tabela_Turma` subtotal from TASK 193.

## Complementary education boundary

The MIEST also contains `CLASSESEC=131` for the 69-school municipal scope. The official dictionary defines this field as `CLASSES EDUCAÇÃO COMPLIMENTAR`. Those 131 classes are preserved as a distinct complementary-activity count and are not silently added to the curricular/basic-education `CLASS_COUNT`.

Therefore:

`CLASS_COUNT_2025 = 1110`.

## Semantic transition

Before TASK 194K:

- `BASIC_EDUCATION_ENROLLMENT = 22,788`;
- `SCHOOL_COUNT = 69`;
- `CLASS_COUNT = UNKNOWN`;
- `NETWORK_Q1 = MATERIALIZED_PARTIAL`.

After TASK 194K:

- `BASIC_EDUCATION_ENROLLMENT = 22,788`;
- `SCHOOL_COUNT = 69`;
- `CLASS_COUNT = 1,110`;
- `NETWORK_Q1 = MATERIALIZED_ANSWERABLE`.

Expected global answerability changes from **27 answerable / 9 partial / 2 gaps** to **28 / 8 / 2**.

## Guards

- direct class count only;
- no enrollment/ATU derivation;
- AI40 + EI29 reconciliation required;
- EI29 must reproduce 294;
- complementary education must remain distinct;
- user-mediated download provenance must remain explicit;
- TASK 194J HTTP 403 remains valid historical transport evidence;
- no serving, publication, scheduling or recurrence in this task.
