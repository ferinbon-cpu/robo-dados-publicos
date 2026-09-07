# TASK 195B — SIOPE UI dotação atualizada corroboration

## Goal

Preserve and adjudicate the official FNDE/SIOPE municipal UI export for Limeira 2025 with the expense phase **Dotação Atualizada**.

This is a corroboration task. It must not turn exact numerical agreement into a backend semantic rule.

## User-mediated official UI export

The owner navigated the official SIOPE municipal reports interface to:

- Relatório Quadro de Resumo de Despesas;
- Ano 2025;
- Período Anual;
- UF São Paulo;
- Município Limeira;
- Fase de Despesa: Dotação Atualizada.

The interface displayed **Quadro Resumo da Dotação Atualizada Segundo SubFunções/Natureza** and the owner exported the official CSV.

The raw CSV and the context screenshot are preserved in Drive under `01_BRONZE/SIOPE`, with exact hashes and byte sizes.

## Exact result

The CSV has 44 rows including the total, 12 columns, and 9 non-zero detail rows.

The final official row reports:

`TOTAL — Total Geral (Exceto Inativos) = R$ 526.804.985,21`

The nine non-zero detail rows sum exactly to the same amount.

This independently reproduces the `526804985.21` consolidated DA total already observed in TASK 010N_R_E_M3.

Therefore:

`UI_CSV_TOTAL == M3_CONSOLIDATED_DA_TOTAL == 526804985.21`

with exact variance `0.00`.

## What this proves

It proves that the current official SIOPE UI for Limeira/2025, when explicitly set to Dotação Atualizada, reports the consolidated total `526804985.21`.

It also proves that the earlier consolidated DA observation was not an accidental local reconstruction: it is independently visible in the official municipal report export.

## What this does not prove

The UI total is not equal to either disputed value:

- `VL_DESP_DOTA_ATUA_EDU = 520399255.47`;
- RREO line 33 DA = `520398255.47`.

Exact differences:

- UI total minus alias = `6405729.74`;
- UI total minus RREO line 33 = `6406729.74`;
- alias minus RREO line 33 = `1000.00`.

The report does not publish a backend formula or source-defined inclusion/exclusion mapping that explains how `526804985.21` becomes `520399255.47`.

Therefore the new evidence strengthens provenance but does **not** close the semantic bridge.

## Decision

Keep:

- `VL_DESP_DOTA_ATUA_EDU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`.

The smallest remaining authoritative evidence is still the FNDE response/dictionary/backend rule requested under protocol `23546.111504/2026-30`.

## Guards

- official UI total is not silently equated to the alias;
- exact corroboration is not a backend formula;
- no convenient subset-sum inference;
- no parent/child double counting without a source-defined hierarchy;
- no Gold/S2 promotion.
