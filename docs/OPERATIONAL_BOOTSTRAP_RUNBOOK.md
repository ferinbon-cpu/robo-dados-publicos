# Full operational bootstrap runbook

## Authorization and execution order

1. Audit and merge the implementation PR without dispatching the workflow.
2. In a separate authorization-only PR, change only
   `docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json`.
3. Pin its `implementation_merge_sha`, retain the all-currently-eligible scope, explicitly
   authorize the seven bounded capabilities, and keep overwrite/replace/delete/retry/
   schedule/recurrence and all release/SIOPE-2025 promotions false.
4. Merge that authorization PR after review. One owner `workflow_dispatch` then chains
   T1 discovery/collection, T2 create-only persistence/processing, and separately gated
   T3 create-only Outputs publication. Never rerun automatically.

Before any remote effect, the runner verifies owner evidence, implementation ancestry,
that the authorization commit changed only the expected evidence path, canonical source
and release state, credential capability, CloudLayout, create-only policy, and budgets.
Missing evidence yields `STOP_OWNER_AUTHORIZATION_REQUIRED` with every effect counter zero.

## Bounded drain and recovery

The immutable ceilings are 10,800 seconds, 500 remote GETs, 120 discovery pages, 300
documents, 50 MiB/document, 1 GiB aggregate source bytes, 2,500 Drive creates, and 200
reconciliation requests. Reaching one returns
`PARTIAL_BATCH_SAFETY_BUDGET_REACHED` and a sorted continuation checkpoint.

Exact logical-key/hash evidence is skipped. A conflicting hash is quarantined and never
overwritten. OCR-required, unknown-schema, invalid-PDF, oversize, and other item-local
failures remain visible while independent items continue. Authorization, policy/release
drift, broken discovery, credential/layout, create-only, and manifest failures are systemic.

Publication uses the `Outputs` destination from `config/cloud.json`, validates the local
bundle, creates uniquely batch-named objects, writes `manifest.json` last, and requires
final exact-name/count/hash readback. The sanitized Actions artifact excludes credentials,
headers, raw environments, PDFs, and unbounded extracted text.

Release freeze: 0.7.0 is ACTIVE; 0.8.0 is CANDIDATE; the closed SIOPE series is 2016–2024;
Gold 2025 is UNKNOWN/BLOCKED; B1/B2/B3 remain PENDING.
