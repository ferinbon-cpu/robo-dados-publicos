# TASK 203 — canonical current bundle productization and renderability audit

## Goal

Move the post-TASK202 observatory from semantic completeness to a production-oriented offline query surface without enabling serving or publication.

## Why this task exists

The canonical V4 matrix proves 38/38 questions are `MATERIALIZED_ANSWERABLE`. That is a semantic/evidence-coverage statement. It is not identical to saying that every answer can already be rendered locally with all numeric/document rows.

Before TASK 203, the full post-TASK202 product assembly existed only in test helpers. In addition, the repository-side `ACCOUNTING_LEDGER` and `REVENUE_LEDGER` representations preserve the real remote snapshot identity, row count, content hash and capabilities, but intentionally carry `rows=[]` locally.

Therefore:

`SEMANTIC_ANSWERABILITY != LOCAL_RENDERABILITY != HUMAN_READY_ANSWER`

Capability metadata may prove that a snapshot supports payment amounts, funding source, classification or revenue amounts. It may not supply an absent numeric value.

## Canonical production bundle

`robo_dados_publicos.analytics.current_observatory_bundle` assembles the eight current query products without importing test helpers:

- SCHOOL_INDICATOR_SERIES
- JOM_EVENT_INDEX
- ACCOUNTING_LEDGER
- REVENUE_LEDGER
- FISCAL_SERIES
- PLANNING_DOCUMENT_INDEX
- QUERY_PRODUCT_CATALOG
- TERRITORY_PROFILE

The canonical V4 evaluator must return exactly 38/38 answerable.

## Productization readiness axis

`robo_dados_publicos.productization.question_readiness` evaluates every ontology question using its exact answerability recipe and classifies the local backing:

- `RECORD_BACKED`: every required signal has local record payload;
- `MIXED_RECORD_AND_CAPABILITY`: some required signals have local records and others are proven only by remote-snapshot capability metadata;
- `CAPABILITY_ONLY`: the required signals are semantically full, but the local bundle has no record payload for them.

Expected current result:

- 27 RECORD_BACKED;
- 8 MIXED_RECORD_AND_CAPABILITY;
- 3 CAPABILITY_ONLY;
- 11 questions in the local query-projection backlog.

The three accounting questions ACC_Q1, ACC_Q2 and ACC_Q3 must remain CAPABILITY_ONLY until a safe local query projection exposes the required records or aggregates.

## Next gate

Do not change the 38/38 semantic matrix.

The next productization gate should create bounded, source-pinned local query projections for the remote ACCOUNTING_LEDGER and REVENUE_LEDGER snapshots, sufficient to close the eleven renderability gaps without copying giant raw ledgers into GitHub and without weakening provenance.

No serving, publication, schedule or recurrence is enabled by this task.
