# TASK 173 — TCE-SP 2026 accounting ledger and JOM-to-accounting router

## Purpose

TASK 173 turns the current TCE-SP 2026 expense schema proven by TASK 172 into a reusable accounting layer for the general Limeira observatory.

It is not an EITI-specific implementation and performs no new network read.

## Canonical accounting observation

`config/municipal_accounting_observation.v1.json` separates:

- commitment;
- liquidation;
- payment;
- reversal;
- unknown/other event requiring review.

The observation also keeps the accounting-programmatic dimensions independent:

- function/subfunction;
- program/action;
- funding source;
- application code;
- expense element;
- procurement modality.

Those dimensions support questions, filters and crosswalks. They do not automatically establish a policy identity.

## Current TCE-SP 2026 adapter

`config/tcesp_current_expense_adapter.v1.json`

The adapter is pinned only to the exact current 2026 ZIP/CSV schema observed in TASK 172. It does not promote family-wide auto-ingest or assume columns that were not proven.

The 17 proven source columns are normalized into the canonical accounting observation.

Strong accounting key candidates:

1. exact source expense identifier;
2. fiscal year + exact empenho number.

Program/action/source/application is a contextual programmatic key, not a policy identity.

Amount/date/history similarity remains weak corroboration only.

## JOM -> accounting query router

`route_jom_event_to_tcesp()` converts a JOM event plus its TASK 171 semantic facets into a deterministic accounting query instruction.

Routing strength:

- `READY_EXACT_ACCOUNTING_KEY_QUERY`: exact empenho found in the published event;
- `CANDIDATE_EXTERNAL_KEY_REQUIRES_TCE_COLUMN_OR_CROSSWALK`: CNPJ/contract/process/procurement identifier is strong externally but the pinned TCE schema has not proven that corresponding query column;
- `CONTEXTUAL_FILTER_ONLY_NO_IDENTITY`: only year/domain/stage context exists;
- `WEAK_HINTS_ONLY_REVIEW`: value/date/text only.

No route state is itself a financial or policy identity.

## Jornal Oficial pipeline

Normal JOM processing now emits:

- `events_gold.jsonl`;
- `event_semantics_gold.jsonl`;
- **`accounting_query_tasks.jsonl`**;
- `chunks_rag.jsonl`;
- existing reconciliation tasks.

This makes the Jornal Oficial a real event radar: an extracted event can immediately generate a controlled accounting-investigation instruction without claiming a match.

The historical TASK 090 ephemeral digest remains on its exact four-file contract because it calls the processor with `emit_semantic_facets=false`. Its processor blob pin is explicitly updated.

## Epistemic boundary

TCE-SP is a control source. It can directly evidence the accounting record it publishes, but it does not replace a missing municipal-primary bridge when a claim requires exact local policy identity.

Therefore:

`JOM event -> accounting query -> TCE record candidate -> identity/crosswalk gate -> answer`

not:

`JOM theme/value/date -> payment`.

## Remote effects

TASK 173 is T0/offline:

- network 0;
- Drive read/write 0;
- serving/publication 0;
- schedule/recurrence 0.

## Next recommended task

Broaden the JOM event extraction taxonomy conservatively so that the radar captures additional municipal events beyond the existing 11 act types, especially school-operation, budget-credit, personnel and policy-regulation events.
