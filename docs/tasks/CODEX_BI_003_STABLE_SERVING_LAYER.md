# BI-003 — stable serving layer (implementation review offline)

## Boundary and preserved checkpoint

BI-003 is strictly `T0_OFFLINE_IMPLEMENTATION_REVIEW`. It implements contracts and pure planners only: no source network, Drive, Sheets API, Looker, publication, files, manifests, state mutation, schedule, or recurrence. The stable serving parent is planned as `13_BI/02_SERVING`; it is not accessed or changed by this task.

The sanitized checkpoint records six verified immutable snapshots and manifests, 520 analytical rows, and closure SHA-256 `7907b225b0b7f806034aaae5c15e78be391af0b5e7149c8a869297772217d6f8`. `02_SERVING` was empty at that checkpoint. Earlier T2 materialization and T3 cleanup/governance authorizations are consumed and cannot be reused. The reference deliberately contains no remote file IDs.

## Stable sheet contract

Exactly six future Sheets are named `<DATASET_ID>__SERVING`, under `13_BI/02_SERVING`. Each has exactly `DATA` and `META`. `DATA` contains one exact contract header and snapshot rows in primary-key order, without formulas, merges, subtotals, calculated columns, or residual cells. `META` binds dataset, contract/schema versions, snapshot and schema identities, dimensions, keys, filenames, software, quality, and cautions. A timestamp is never its identity.

The view strategy is `FULL_REPLACE_DERIVED_SERVING_VIEW_FROM_IMMUTABLE_SNAPSHOT`. The serving view represents one selected snapshot, is not canonical, and never changes Gold or a snapshot. The pure planner returns `CREATE_INITIAL_SERVING`, `NO_CHANGE_IDEMPOTENT`, or `REPLACE_SERVING_FROM_NEW_SNAPSHOT`. Existing state must first pass full validation. Schema drift, invalid hash/META, unexpected tabs/formulas/cells, duplicate name, MIME/parent mismatch, or unproved snapshot stops rather than being repaired.

The future bounded replacement is modeled as one logical `spreadsheets.batchUpdate`: clear the union of the validated old and target grids and write new `DATA` plus `META`, then perform semantic readback. The union prevents stale trailing rows when a snapshot shrinks. There is no retry or cleanup. Ambiguous failure requires readback; partial initial creation requires owner decision.

## Typed serialization and readback

The serializer emits future CellData with explicit `stringValue`, `numberValue`, or `boolValue`; null has no `userEnteredValue`. Dates/datetimes use deterministic numeric serials and explicit formats. Currency remains numeric. The future input mode is `RAW`, not locale parsing or CSV import.

Semantic readback requires exact tabs, dimensions, headers, scalar types/nulls, PK uniqueness, zero formulas/residual cells, complete META, schema fingerprint, snapshot ID, and the BI-002 schema-bound canonical matrix hash. Only exact equality yields `PASS_BI_SERVING_SEMANTIC_READBACK_VERIFIED`; divergence stops without another write.

## Authorization and Looker separation

Future mutation requires a fresh structured `T3_MUTATING_OR_PUBLICATION` authorization for repository, root, parent, task, scope, exact implementation SHA, selected datasets, and selected snapshots. The implementation SHA must be an exact lowercase 40-character hexadecimal commit SHA. Consumed, test-only, wrong-SHA, out-of-scope, or Looker-combined authorization stops. No active authorization is embedded here.

Serving and Looker are separate boundaries. Serving authorization requires `looker_publication_authorized=false`; `plan_looker_publication` always returns `STOP_BI_LOOKER_SEPARATE_AUTHORIZATION_REQUIRED` in BI-003. A future generation manifest is planned create-only and last, never written here.

After audit and merge, the recommended first operational proof is `BI_SIOPE_SERIES` alone (72 rows, closed 2016–2024 schema), under a new explicit SHA-pinned T3 authorization. This is a recommendation, not authorization. A rollback is another newly authorized generation from an older validated snapshot; snapshots and history are never deleted or modified.

Release remains `0.7.0=ACTIVE`, `0.8.0=CANDIDATE`, B1/B2/B3 pending. SIOPE remains closed at 2016–2024 with no Gold 2025, compliance, imputation, or causality. Jornal nulls remain null, and `MATCH_CANDIDATE != financial_identity` remains enforced.
