# TASK 043 — F01 scoped reconciliation across PPA, LDO and LOA

## Purpose

Build and review, entirely offline, the first bounded reconciliation ledger across the three F01 budget-law scoped Silver objects. The task must distinguish program/action continuity from financial identity and preserve every unresolved boundary already established upstream.

## Inputs

- LOA scoped candidate/persisted Silver: SHA-256 `3894ede7c67e60d3e12795dec3964d78baf24ff350355d98f3825dd5f81caf4c`
- PPA scoped Silver: SHA-256 `0cba09dade1c09224e549e817a859c63edb12a6fb0a5223c5ddb8aa5fe6dc730`
- LDO scoped Silver: SHA-256 `4719631a3dd476efe8c760f2b9ce07eba15d678c85b56e95345af70237f02182`
- TASK 042 must prove PPA/LDO create-only persistence and byte-identical readback before this reconciliation is accepted.

## Reconciliation decisions

### LDO

The current scoped LDO Silver is framework context only. It contains legal identity, corrected JOM pages 5–38 and five structural markers, but no promoted action-level key. Therefore it cannot establish an item-level PPA↔LDO or LDO↔LOA financial link.

Classification: `FRAMEWORK_CONTEXT_ONLY_NO_ITEM_LEVEL_LINK`.

### Program 2001 / action 2720 / Alimentação Escolar

The promoted PPA subset and the directly validated LOA record align on program 2001, action 2720, function 12, subfunction 306 and label Alimentação Escolar. The PPA 2026 value is 28000 in `R$ milhares medios/2025`; the LOA record is BRL 28,000,000. The scale alignment is recorded as diagnostic corroboration only.

Classification: `PROGRAM_ACTION_KEY_CONTINUITY_PROVEN_AMOUNT_SCALE_ALIGNMENT_OBSERVED_NO_FINANCIAL_IDENTITY`.

This is not financial identity. Both records are `eiti_specific=false`.

### Program 2001 / action 2690 / Transporte Escolar

The promoted PPA rows cover Educação Infantil (12/365) and Ensino Fundamental (12/361). The LOA record directly validated is `12.362.2001.2690`. The potentially relevant PPA Ensino Médio/Superior row remains `PARSER_REVIEW_REQUIRED` and unpromoted.

Classification: `REVIEW_REQUIRED_BLOCKED_RELEVANT_PPA_ROW_UNPROMOTED`.

No 12/362 PPA↔LOA continuity or financial identity is promoted.

### EITI

The PPA proves an education-integral indicator and targets inside Program 2001, but no validated action record is EITI-specific. The explicit chain from target to appropriation and execution is still absent.

Classification: `EVIDENCIA_INSUFICIENTE`.

Required chain remains:
indicator/target → program → explicit action/subaction → budget unit → funding source/destination → expense nature → appropriation → committed → liquidated → paid.

## Prohibited conclusions

TASK 043 must not infer financial identity from a shared program, action code, label or scaled amount. It must not promote the review-required 2690 row, attribute Program 2001 totals or global LOA tables to EITI, infer MDE/FUNDEB/fiscal compliance, infer causality, write a new Silver object, create Gold, update serving, or publish anything.

## Expected result

`PASS_TASK043_SCOPED_BUDGET_LAW_RECONCILIATION_NO_FINANCIAL_IDENTITY_PROMOTION`

F01 remains `SILVER_SCOPED_PARTIAL_VALIDATED`. The task creates only a versioned offline reconciliation contract/evidence in GitHub.
