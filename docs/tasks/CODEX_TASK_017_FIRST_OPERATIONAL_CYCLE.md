# TASK 017 — first operational cycle preparation

This T0/offline contract composes the already-proven Jornal Oficial edition 7310 reference,
reconciliation constraints, observability, and the existing product builder. It does not
recollect or reprocess the source and does not execute reconciliation.

The eight stages are PREFLIGHT, SOURCE_SELECTION, ACQUISITION_OR_REUSE, PROCESSING,
RECONCILIATION, OBSERVABILITY, PRODUCT_BUILD, and OPERATIONAL_SUMMARY. Every stage emits
status, execution flag, input/output identities, evidence, warnings/stops, and remote effect
counts. A STOP makes every downstream stage `STOP_DEPENDENCY`.

`PINNED_REUSE` passes only when its source, processing counts and identity, reconciliation
policy, observability identity, and frozen release state exactly match their pre-existing
canonical repository contracts. Drift produces `PINNED_EVIDENCE_CONTRACT_DRIFT` or
`CANONICAL_RELEASE_STATE_DRIFT` and stops before product construction.

The boundary remains 0.7.0 ACTIVE, 0.8.0 CANDIDATE, closed series 2016–2024, Gold 2025
UNKNOWN/BLOCKED, and B1/B2/B3 PENDING. TASK 018, under later owner authorization, is the
place for a first bounded live cycle; TASK 017 executes none of it.

The product records `0.8.0 CANDIDATE` as the code that generated it while separately
preserving `0.7.0 ACTIVE`. A deterministic `snapshot_id` identifies content/state; a
deterministic `run_id` identifies the execution using that snapshot and `started_at`.
