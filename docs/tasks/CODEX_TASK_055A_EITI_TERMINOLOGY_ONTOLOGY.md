# TASK 055A — EITI terminology and normative ontology

## Why this gate exists
TASK 055 used a bounded lexical check on one aggregate expense report. That structural conclusion remains valid, but the owner correctly identified a methodological risk: EITI-related policy and finance documents may use multiple official, historical, local, operational and accounting formulations without using the acronym `EITI`.

The Unicamp project v13 explicitly distinguishes `Programa ETI`, `EITI` and `EITI-Limeira`, and already defines a broader documentary descriptor set including Educação Integral, Programa Escola em Tempo Integral, tempo integral, jornada ampliada, Meta 6, seven/35-hour markers, FUNDEB, MDE, budget appropriation, resource source and expansion plan.

## Objective
Create a permanent fail-closed terminology ontology that future F01 reads must use before classifying a source as related or unrelated to the policy.

## Five families
1. **A — Canonical policy identifiers**: official/local policy names and stable acronyms.
2. **B — Local planning/normative aliases**: historically observed Limeira formulations and planning labels.
3. **C — Operational offer/journey signals**: matriculation, expanded/full-time journey and 7h/35h formulations.
4. **D — Financing/induction signals**: fomento, transfers, FNDE, FUNDEB, MDE, appropriation, source and pactuation.
5. **E — Accounting/planning linkage keys**: program/action/subaction/unit/source/ficha/cost center and execution-stage vocabulary.

## Core inference rules
- A term hit is a candidate signal, not proof of expenditure.
- `7 horas` / `35 horas` alone is weak and requires school, matriculation or journey context.
- FUNDEB/MDE/fomento/transfer terms alone must never be treated as EITI spending.
- Generic accounting terms alone must never be treated as EITI spending.
- Financial identity requires a policy signal plus an explicit or stably proven accounting linkage key plus an amount and execution stage.
- When available, the same stable key should support the chain `empenhado -> liquidado -> pago`.
- Matching must be case-insensitive, accent-insensitive and tolerant of acronym/full-form, whitespace and hyphen variation.

## TASK 055 compatibility
The structural finding remains: `05 - Maio_despesa.pdf` is an aggregate economic-element report and is not sufficient to attribute money to EITI. However, the pre-055A lexical absence check is explicitly non-exhaustive and must not be reused as proof that all EITI terminology was absent.

## Next gate
TASK 056 remains bounded to exactly one source:
- `Demonstrativo SIOPE-MAVS - 1º BIMESTRE 2026.pdf`
- Drive ID `17Fl8opb1pkqdFa485-bkQR3j6LnApnE-`

TASK 056 must load and apply all five ontology families. A fresh owner authorization remains required before that source is opened.

No F01 source content was opened in TASK 055A and no Bronze/Silver/Gold/serving/publication promotion is authorized.
