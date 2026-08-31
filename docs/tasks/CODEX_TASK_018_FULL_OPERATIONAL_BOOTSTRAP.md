# TASK 018 — Full bounded operational bootstrap

## Movement A: implementation only

This PR prepares but does not authorize or execute the campaign. Its semantic is
`DRAIN_ALL_ELIGIBLE_ITEMS_WITHIN_AUTHORIZED_PROVEN_SCOPE`, with owner scope
`ALL_CURRENTLY_ELIGIBLE_PROVEN_ITEMS_AT_AUTHORIZATION_SHA`.

Eligibility is cross-validated against independent canonical repository evidence. The
only fresh-collection family in this first bootstrap is `LIMEIRA_JORNAL_OFICIAL`, and
only declared HTTPS links in the proven **August 2026 modern window** qualify. The
pre-proven document host `ecrie.com.br` and separately proven municipal hosts are fixed
before execution. TDA remains contract-unproven; SIOPE 2016–2024 is reused; SIOPE 2025
and 2026 remain blocked from promotion/collection expansion.

The implementation is already executable after a later authorization-only PR. That PR
does not activate adapters or change runtime code.

## One-shot chain

One `workflow_dispatch` performs a bounded compound operation:

1. create-only one-shot reservation in Logs before source network;
2. T1 discovery/collection;
3. T2 create-only persistence/processing and bounded reconciliation;
4. T3 create-only product publication with manifest-last and final readback.

`GITHUB_RUN_ATTEMPT` must be exactly `1`. Any later dispatch under the same authorization
finds the durable reservation marker and stops before Jornal Oficial requests.

Discovery must return exactly `PASS_DISCOVERY`. Logical-key provenance is deduplicated
before document GET. Item-local fetch/host/format/oversize/OCR/schema failures remain in
the final report while independent items continue. Hard-budget exhaustion produces
`PARTIAL_BATCH_SAFETY_BUDGET_REACHED`, never fake completion.

T1 telemetry is carried into T2, so local staged reads never masquerade as remote GETs.
The truthful discovery ceiling is 50 pages, matching `JornalOficialLimeira`.

The processing path reuses `JournalPdfProcessor`. `reconciliation_tasks.jsonl` remains
derived Gold evidence; tasks are inserted/upserted through the canonical `StateRegistry`.
TASK 018 persists an immutable batch `StateRegistry` snapshot in `06_BANCOS`, rather than
using the task JSONL as database state. `MATCH_CANDIDATE` never promotes financial
identity.

## Zero-effect statement for this implementation PR

- live source requests: **0**
- Drive reads: **0**
- Drive writes: **0**
- publication writes: **0**
- live reconciliation: **0**
- workflow_dispatch executions: **0**
- owner authorization: **PENDING**
- bootstrap live run: **NOT EXECUTED**

The later authorization-only PR may change only
`docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json`,
pin the exact implementation merge SHA, authorize this single batch, and keep
overwrite/replace/delete/retry/schedule/recurrence, release promotion and every SIOPE
2025 promotion false.
