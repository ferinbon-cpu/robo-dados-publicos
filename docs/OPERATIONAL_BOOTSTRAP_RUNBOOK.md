# Full operational bootstrap runbook

## Authorization and execution order

1. Audit and merge the implementation PR without dispatching the workflow.
2. In a separate authorization-only PR, change only
   `docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json`.
3. Pin its `implementation_merge_sha`, retain
   `ALL_CURRENTLY_ELIGIBLE_PROVEN_ITEMS_AT_AUTHORIZATION_SHA`, explicitly authorize
   the seven bounded capabilities, and keep overwrite/replace/delete/retry/schedule/
   recurrence and every release/SIOPE-2025 promotion false.
4. Merge that authorization PR after review. One owner `workflow_dispatch` performs
   the whole campaign.

The live workflow first creates a deterministic create-only **one-shot reservation marker**
in `07_LOGS` before any Jornal Oficial request. This consumes the single execution attempt
for that authorization even if a later stage stops. A second dispatch or any
`GITHUB_RUN_ATTEMPT != 1` stops before source collection.

After that reservation, the same runner executes:

- T1 declared-link discovery and bounded collection;
- T2 create-only Bronze/derived persistence, canonical `StateRegistry` task handling and
  bounded `LIMEIRA_CONTRATOS` reconciliation;
- T3 create-only Outputs publication with manifest-last and final readback.

The checked-in runtime reuses `JornalOficialLimeira`, `JournalPdfProcessor`, the existing
Drive REST/OAuth/`CloudLayout` stack, `StateRegistry`, the bounded
`LIMEIRA_CONTRATOS` resolver and the existing product bundle. The authorization-only PR
changes evidence, not code.

Before any source request, the runner validates owner evidence, exact implementation
lineage, the complete 0.7.0/0.8.0 and SIOPE frozen boundary, B1/B2/B3 pending state,
canonical source registry, Drive layout, create-only policy and budgets. Discovery must
return exactly `PASS_DISCOVERY`; partial pagination never proceeds to document GET.

## Bounded drain and recovery

The hard ceilings are 10,800 seconds, 500 source/reconciliation remote GETs,
**50 discovery pages**, 300 documents, 50 MiB/document, 1 GiB aggregate source bytes,
2,500 Drive creates and 200 reconciliation requests.

The first collection scope is deliberately narrower than parser capability: every declared
item in the proven **August 2026 modern window**. `ecrie.com.br` and separately proven
municipal hosts are fixed before execution. Legacy parser capability is not treated as
live-contract proof.

Discovery identities are deduplicated before document GET. Conflicting provenance becomes
`STOP_DISCOVERY_AMBIGUITY` without fetching either candidate. Individual fetch, host,
format, oversize, OCR and schema failures remain visible while independent items continue.
A global budget stop is `PARTIAL_BATCH_SAFETY_BUDGET_REACHED` with a deterministic
continuation checkpoint.

When the canonical `ROBOT_STATE.sqlite` already proves a source URL/hash/remote object,
the batch reuses that Bronze object instead of duplicating it. Reconciliation task JSONL
remains derived Gold evidence; the actual task queue uses `StateRegistry`, and TASK 018
persists an immutable batch state snapshot in `06_BANCOS` rather than repurposing
`reconciliation_tasks.jsonl` as database state.

Publication uses the canonical `08_OUTPUTS`, creates uniquely batch-named objects,
writes `manifest.json` last, performs final readback and preserves `PARTIAL` or item-local
STOPs in the published report. The Actions artifact is sanitized and contains no OAuth
values, raw environment dumps, source PDFs or unbounded extracted text.

Release freeze: 0.7.0 is ACTIVE; 0.8.0 is CANDIDATE; SIOPE 2016–2024 is the closed
historical series; 2025 remains `PROVEN_STRUCTURAL_RECENT` with S1/S2 NOT_PROVEN,
annual closure/comparability UNKNOWN and Gold 2025 UNKNOWN/BLOCKED; 2026 remains
UNPROVEN_CURRENT_YEAR; B1/B2/B3 remain PENDING.
