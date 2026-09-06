# TASK 194 — Official Censo Escolar 2025 turma recovery

## Purpose

Close the single remaining `NETWORK_Q1` gap through a bounded one-shot recovery from the official INEP Censo Escolar 2025 package.

## Authorization boundary

GitHub issue #598 is the authorization record. The live workflow can run only when a comment by `ferinbon-cpu` exactly matches the main SHA and the bounded contract.

The workflow permits only the fixed official URL:

`https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2025_.zip`

No alternate host, authentication, Drive write, serving, publication, schedule or recurrence is permitted.

## 2025 turma semantics

The 2025 package changed from the old consolidated school CSV to separate entity tables.

`Tabela_Turma_2025_V2.csv` is an aggregate table keyed by `CO_ENTIDADE`, with one school-level row and precomputed class-count fields. The network class metric is therefore:

`CLASS_COUNT = SUM(QT_TUR_BAS) across the 69 active municipal Limeira establishments`

It is **not** a count of rows and it is **not** derived from enrollment divided by ATU.

## Required proof

The live gate must fail closed unless all of the following hold:

1. the official package is retrieved from `download.inep.gov.br` only;
2. the internal `Tabela_Turma_2025_V2.csv` MD5 equals `438A3A3FC37F28E7E50E57D7CD8B9DAC`;
3. that MD5 is also present in the official package manifest;
4. the official school table yields exactly 69 active municipal Limeira establishments;
5. the existing TASK 180 AI40 seed contains exactly 40 codes and all are inside those 69;
6. the complement is exactly 29 EI-only establishments;
7. all 69 active establishments have exactly one `Tabela_Turma` aggregate row;
8. the 29-unit complement reproduces the already validated subtotal of 294 `QT_TUR_BAS`;
9. the network total equals AI40 subtotal + EI29 subtotal.

## Data minimization

The ~512 MiB official package and its raw CSV members remain ephemeral in the GitHub runner temporary directory.

Only a sanitized JSON containing hashes, counts, aggregate totals and boolean guards may be uploaded as a workflow artifact. No school names, row payloads or raw ZIP/CSV files are persisted by TASK 194.

## Expected next step

If the one-shot proof passes, pin the sanitized result into the repository, materialize `CLASS_COUNT` in `SCHOOL_INDICATOR_SERIES`, recompute answerability and promote `NETWORK_Q1` from `MATERIALIZED_PARTIAL` to `MATERIALIZED_ANSWERABLE`.
