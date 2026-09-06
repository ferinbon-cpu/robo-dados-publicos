# TASK 177 — integrate observatory query products with 13_BI stable serving architecture

## Objective

Connect TASK 176 deterministic query-product snapshots to the already proven BI serving architecture without altering the historical BI-003 allowlist and without authorizing any remote write.

TASK 177 is T0/OFFLINE only.

## Architecture

The existing BI architecture remains authoritative:

OPTION_3_CREATE_ONLY_SNAPSHOTS_PLUS_STABLE_SERVING_SHEET

Parent:

`13_BI/02_SERVING`

Tabs:

- DATA
- META

The historical `config/bi/serving.v1.json` remains unchanged with its original six `BI_*` datasets.

TASK 177 adds a sibling OBS namespace:

- SCHOOL_INDICATOR_SERIES -> OBS_SCHOOL_INDICATOR_SERIES__SERVING
- JOM_EVENT_INDEX -> OBS_JOM_EVENT_INDEX__SERVING
- ACCOUNTING_LEDGER -> OBS_ACCOUNTING_LEDGER__SERVING
- FISCAL_SERIES -> OBS_FISCAL_SERIES__SERVING
- PLANNING_DOCUMENT_INDEX -> OBS_PLANNING_DOCUMENT_INDEX__SERVING
- QUERY_PRODUCT_CATALOG -> OBS_QUERY_PRODUCT_CATALOG__SERVING

## Serving source

Each serving target is generated from exactly one already-materialized TASK 176 query-product snapshot.

The planner recomputes:

- content SHA-256;
- snapshot id;
- row count;
- ordered columns;
- schema/type fingerprint;
- source families;
- cautions.

A snapshot with inconsistent content/hash/meta is rejected before any remote phase could be considered.

## Plan states

### CREATE_INITIAL_SERVING

Valid snapshot and no existing serving.

### NO_CHANGE_IDEMPOTENT

Existing serving has the exact same snapshot, content hash, schema fingerprint, logical rows and META.

No update is planned.

### REPLACE_SERVING_FROM_NEW_SNAPSHOT

Existing serving is internally valid, has the same product schema fingerprint, but points to an older valid snapshot.

The future mutation would fully replace the derived serving view from the new pinned snapshot.

Schema drift is not an in-place replace. It requires a separate migration.

## DATA serialization

The pure serializer emits locale-independent logical CellData:

- text -> stringValue;
- integers/floats -> numberValue;
- booleans -> boolValue;
- nested lists/dicts -> deterministic JSON text;
- null -> empty cell.

The future write mode is RAW.

## META

The exact META contract binds:

- product name;
- product schema;
- serving contract version;
- snapshot id;
- content SHA-256;
- schema fingerprint;
- row/column count;
- ordered columns;
- generated_at;
- software version;
- source families;
- cautions;
- source role.

Source role is fixed:

`DERIVED_QUERY_CACHE_NOT_SOURCE_OF_TRUTH`.

## Existing-state validation

An old serving is validated against its own metadata before it can be replaced.

The planner fails closed on:

- wrong tabs;
- formulas;
- residual/extra cells;
- duplicate headers;
- row-width mismatch;
- row-count or column-count mismatch;
- content hash mismatch;
- snapshot-id mismatch;
- product-schema mismatch;
- schema-fingerprint mismatch;
- source-family metadata mismatch;
- caution metadata mismatch;
- generated_at/software metadata mismatch.

This separates a valid older snapshot from a corrupted remote state.

## Remote preflight

A future executor must fail closed on:

- parent outside `13_BI/02_SERVING`;
- wrong title;
- duplicate remote names;
- non-Sheets MIME;
- unvalidated snapshot.

TASK 177 itself performs no remote call.

## Authorization

Remote serving mutation is T3 and requires a new authorization shaped specifically for TASK 177.

The authorization must pin:

- repository;
- T3 tier;
- exact Drive root/parent;
- task;
- scope;
- implementation SHA;
- one selected product;
- one selected snapshot id;
- unconsumed state;
- non-test state;
- serving mutation true;
- Looker publication false.

Prior BI-003/004/005 authorizations cannot be reused.

## Readback

After any future write, the logical readback must match target headers, rows and META exactly.

Only then can a create-only serving-generation manifest be produced.

The manifest never modifies source snapshots and never authorizes Looker, recurrence or schedule.

## Remote effects in this task

- source network: 0
- Drive read/write: 0
- Sheets write: 0
- Looker: 0
- publication: 0
- schedule: 0
- recurrence: 0

## Next step

After merge, a separate bounded execution task may select one or more exact TASK 176 snapshots for remote materialization. That task must receive fresh explicit authorization and must not auto-publish all six products.
