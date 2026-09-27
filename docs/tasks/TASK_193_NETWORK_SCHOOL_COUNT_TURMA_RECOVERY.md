# TASK 193 — Network school count and official turma recovery

## Goal

Advance `NETWORK_Q1 — Quantos alunos, turmas e escolas existem?` without weakening the evidence rules.

## What is materialized

The 2025 municipal network scope remains `3526902:MUNICIPAL:CURRENT_69_UNITS`.

- `BASIC_EDUCATION_ENROLLMENT = 22,788` is preserved from TASK 191.
- `SCHOOL_COUNT = 69` is materialized from the validated V08 Censo panel.
- The 69 active establishments reconcile as 40 units with early years + 29 early-childhood-only units.

## What is deliberately not materialized

`CLASS_COUNT` remains blocked.

The official source identity is known: `Tabela_Turma_2025_v2.csv`, MD5 `438A3A3FC37F28E7E50E57D7CD8B9DAC`. Its raw bytes are not present in active custody.

Existing primary-derived audit evidence proves that all 29 early-childhood-only units were found in `Tabela_Turma` and that this subgroup has 294 classes. That number must not be promoted to a network total because the 40 units with early years are still missing from the directly recoverable class-count evidence.

Secondary web mirrors may be used only as diagnostics; they are not canonical substitutes for the missing primary raw file.

## Semantic transition

Before TASK 193, NETWORK_Q1 is partial with two missing metrics: `CLASS_COUNT` and `SCHOOL_COUNT`.

After TASK 193 it remains partial, but the only remaining missing metric is `CLASS_COUNT`.

This is intentional. The task improves precision without inflating answerability.

## Next valid action

Recover the official `Tabela_Turma_2025_v2.csv` bytes, verify the official MD5, filter the 69 active municipal Limeira establishments, count the applicable unique classes, reconcile the known EI29 subtotal of 294, then materialize `CLASS_COUNT`.
