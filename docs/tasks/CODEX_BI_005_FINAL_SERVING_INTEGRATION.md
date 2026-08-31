# BI-005 FINAL — Serving integration for the six current BI datasets

## Scope

BI-005 closes the offline engineering phase of the stable serving layer for the six BI datasets already materialized in `13_BI`.

Tier: `T0_OFFLINE_IMPLEMENTATION_REVIEW`.

Expected gate result:

`PASS_BI_005_FINAL_SERVING_INTEGRATION_OFFLINE`

## Base

Exact base main SHA:

`396ef26cdb38f79be3c2512329bc9e848774d6f9`

BI-004 remains the historical baseline and must not be rewritten.

## Design

The generalized executor supports:

- `BI_SIOPE_SERIES`
- `BI_JORNAL_EVENTOS`
- `BI_RECONCILIACAO`
- `BI_FONTES_STATUS`
- `BI_EXECUCOES_ROBO`
- `BI_DICIONARIO`

One invocation may target exactly one dataset and one pinned snapshot.

The executor receives raw rows, rebuilds the schema-bound target with the existing BI materialization/serving code, and verifies the exact row count, snapshot ID, canonical matrix SHA-256, schema fingerprint and stable serving name before the first injected transport call.

It never accepts a user-supplied hash as a substitute for rebuilding the target.

## Future operations

Only these operations are modelled as eligible:

- `CREATE_INITIAL_SERVING`
- `NO_CHANGE_IDEMPOTENT`

`REPLACE_SERVING_FROM_NEW_SNAPSHOT` remains STOP and requires a separate owner decision/task if ever needed.

## Future T3 authorization

A future live invocation requires a fresh, single-use authorization pinned to the exact audited implementation SHA and restricted to exactly:

- one dataset;
- one snapshot;
- one serving name.

It must keep Looker, replace, retry and cleanup unauthorized.

No active authorization is embedded in BI-005.

The consumed BI-004 SIOPE authorization is historical evidence only and cannot authorize BI-005 or another dataset.

## Bounded transport

Per dataset, the future maximum remains:

- one exact discovery;
- at most one spreadsheet creation;
- at most one logical batch update;
- one semantic readback;
- at most one generation-manifest create;
- zero retry;
- zero delete;
- zero cleanup;
- zero Looker publication.

For an existing exact serving Sheet, the executor performs a real semantic readback and returns `NO_CHANGE_IDEMPOTENT` only if the reconstructed matrix and META match the pinned target. Discovery metadata alone is never accepted as semantic proof.

## Semantic invariants

SIOPE remains limited to the closed 2016–2024 series; 2016=P1 and 2017–2024=P6. No automatic compliance conclusion is permitted.

Jornal fields remain non-invented and null remains null.

Reconciliation preserves `MATCH_CANDIDATE != FINANCIAL_IDENTITY`; candidates are not promoted to proven financial identity.

Existing BI privacy/schema restrictions remain authoritative and unknown fields fail closed.

## Offline effects

BI-005 itself performs zero Drive, Sheets, Looker, network, publication, schedule or recurrence effects.

The gate is executed by `tests/test_bi_005_gate_entrypoint.py`, which is included in the existing `python -m unittest discover -s tests -v` CI step. This avoids rewriting the large offline workflow solely to add another equivalent command.

## Engineering closure

After merge, BI-005 closes the offline serving-layer engineering phase for the six current datasets. Individual BI-006/BI-007/BI-008 tasks are not required merely to create the five remaining serving Sheets.

The next phase is operational:

1. obtain fresh explicit T3 authorization;
2. materialize and semantically verify the five remaining serving Sheets, one dataset per bounded execution;
3. connect the six verified serving Sheets to the dashboard layer.
