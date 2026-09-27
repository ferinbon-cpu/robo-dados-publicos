# TASK 223 — safe high-value slice of MD_01.3

## Goal

Convert the discovered MD_01.3 corpus manifest into a deterministic operational partition that maximizes public/fiscal/institutional value while explicitly excluding raw payroll and personnel content.

Issue: #757.

This task depends on the TASK 222 branch only for sequencing; its substantive input is the File Library source `md_01_3_indice_corpus_documental_transcrito_limeira.md` already canonized by TASK 221.

## Source facts

MD_01.3 declares 228 source files, 194 unique documents, 34 ignored duplicates, 191 `ok` and 3 `sem_texto`.

The task partitions all 194 IDs exactly.

### Eligible high-value slice — 101 documents

- 50 FUNDEB / 25% Educação;
- 18 RREO/LRF;
- 10 monthly revenue/expense;
- 9 balances/accountability;
- 6 RGF/LRF;
- 5 PPA/LDO/LOA and budget legislation;
- 1 public hearing/fiscal targets;
- 1 Education trial balance;
- 1 COCEM/institutional document.

Exact eligible ranges:

- `DOC-003..DOC-066`;
- `DOC-068..DOC-101`;
- `DOC-103..DOC-105`.

The family-level ID mapping in `config/md_01_3_safe_high_value_slice.v1.json` reconstructs the same 101-document set and is unit-tested for completeness and disjointness.

### Excluded raw personnel/payroll slice — 93 documents

- 70 payroll/payslip files: `DOC-106..DOC-175`;
- 22 staff-count files: `DOC-001`, `DOC-002`, `DOC-102`, `DOC-176..DOC-194`;
- 1 positions/pay file: `DOC-067`.

This is a purpose/minimization boundary, not a claim that personnel statistics are irrelevant. Future personnel analytics should use an explicitly designed aggregate/query-safe schema rather than dumping row-level payroll data into the robot.

## `sem_texto` semantics

The historical source has three `sem_texto` documents.

- `DOC-065` public-hearing deck remains indexed as `sem_texto`; absence of extracted text is not zero content.
- `DOC-100` LOA 2026 remains historically `sem_texto` in MD_01.3. Operational LOA content is already supported by the stronger F01/JOM canonical chain, so this old record is marked superseded for content without rewriting source history.
- `DOC-102` is outside the safe slice because it belongs to the staff family; its `sem_texto` state remains source history.

## Exact locators

The config materializes exact filenames for the non-repetitive high-value entries visible in the manifest, including monthly revenue/expense, balances, RREO/RGF, MDE, the September 2025 Education trial balance, PPA/LDO/LOA, accountability files and the COCEM regulation.

The 50 FUNDEB portal files use deterministic exact document-ID ranges while their repetitive opaque filenames remain in the source manifest. This avoids duplicating filename noise while preserving traceability to the canonical source manifest.

## Numeric authority

MD_01.3 is a documentary/transcription corpus. A transcription may locate candidate evidence, but it does not automatically become fiscal numeric truth. Existing official structured sources and exact primary documents keep their precedence.

No F01/F02 fact should be counted again merely because the same underlying document appears in MD_01.3.

## Next incremental targets

1. `DOC-066 — Balancete_Mes_Setembro_2025_Educacao.pdf`: education-specific granular accounting with high incremental value.
2. `DOC-105 — XIII COCEM 2025- REGIMENTO FINALIZADO.pdf`: institutional/governance material not equivalent to fiscal APIs.
3. historical balances/accountability after overlap analysis against already structured fiscal evidence.

## Non-effects

No public-source network, Drive write, serving change, publication, schedule or recurrence. Contextual coverage remains 38/38; this task increases corpus depth and routing safety.
