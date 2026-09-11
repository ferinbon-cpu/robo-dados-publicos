# TASK 222 — SME Legal v3 coverage matrix digest

## Goal

Turn the audit matrix embedded in `Cerebro_Normativo_Gestao_Escolar_Limeira_v3_0_ESPELHO_SME_LEGAL.md` into a deterministic machine-readable coverage map without converting the derived corpus into primary legal evidence.

Base main: `2a9dbbf96e0f53146d6c86d64f69a23ff5e82587`.

Issue: #755.

## Materialized map

`config/normative_sme_legal_coverage.v1.json` contains all 74 matrix items observed in the v3.0 coverage table, preserving their SME Legal groups and the four source-defined states:

- `INTEGRADO_CORPUS`: 11;
- `PARCIAL`: 28;
- `PENDENTE_CORPUS_INTEGRAL`: 34;
- `LACUNA_CONFIRMADA`: 1.

The 74 items span 11 groups. `Regulamentações Municipais` is the largest group with 43 items.

The only `LACUNA_CONFIRMADA` in the matrix is `Instrução de Serviço nº 4: Vale Alimentação`.

## Semantic rule

This map answers only a coverage question: **what does the v3 derived corpus say it has integrated, partially covered, still pending, or explicitly missing?**

It does not answer by itself:

- whether a norm is currently in force;
- whether a later amendment/revocation exists;
- whether OCR numbers are correct;
- whether an operational synthesis is an exact legal rule;
- whether an item not fully incorporated can be reconstructed from generic knowledge.

Normative precedence remains:

1. exact official normative document + current-vigency check;
2. exact transcribed document with proven source identity;
3. v3 coverage/RAG map;
4. free interpretation.

## Practical effect for the robot

The robot can now fail closed before answering a normative-management question:

- `INTEGRADO_CORPUS` -> the derived corpus has a candidate full text/OCR, but primary-source/vigency confirmation may still be required;
- `PARCIAL` -> answer only within proven content and declare that integral coverage is not guaranteed;
- `PENDENTE_CORPUS_INTEGRAL` -> do not invent missing integral content;
- `LACUNA_CONFIRMADA` -> explicitly report the gap.

This creates a reliable routing layer for the future normative RAG without inflating substantive answerability.

## Next frontier

Link selected `INTEGRADO_CORPUS` items to exact primary sources already under custody when identity is independently proven. High-value first links include the municipal statutes and already-canonized CME/municipal education-integral acts.

Do not use fuzzy title similarity as legal identity.

## Non-effects

Canonical contextual coverage remains 38/38. No new public-source request, Drive write, serving mutation, publication, schedule or recurrence is introduced by TASK 222.
