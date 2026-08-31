# TASK 020 — Jornal Oficial incremental recurrence-readiness design

## Tier and purpose

`T0_OFFLINE` only.

This task designs and tests the decision contract required to distinguish a completed Jornal Oficial checkpoint from a later discovery result. It does not enable recurrence, schedule, source collection, Drive persistence, publication, retry, cleanup or future batch execution.

The purpose is to prove that the software can decide, deterministically and fail-closed, whether a hypothetical later discovery means:

1. nothing changed (`NO_CHANGE_IDEMPOTENT`);
2. only strictly newer editions appeared (`NEW_ITEMS_APPEND_ONLY`); or
3. the discovery/checkpoint relationship is unsafe and must STOP.

## Authoritative inputs

- `docs/evidence/TASK_019_POST_BOOTSTRAP_OPERATIONAL_REVIEW_0.8.0.json`
- `docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_CLOSURE_0.8.0.json`
- `config/automation_policy.v1.json`
- `config/limeira_sources_discovery.json`
- `config/jornal_incremental_recurrence_readiness.v1.json`
- `robo_dados_publicos/journal/official.py`
- `robo_dados_publicos/incremental/planner.py`

## Existing primitives reused

The current Jornal Oficial parser already defines the edition number as canonical identity, with derived `source_id=LIMEIRA_JO_<edition>` and `logical_key=limeira/jornal_oficial/edicao/<edition>`. The existing V14 incremental planner already recognizes an idempotent no-change outcome.

TASK 020 composes these ideas into a source-specific pure planner. It does not reuse a live batch as if one successful one-shot implied recurrence readiness.

## Required decision contract

### NO_CHANGE_IDEMPOTENT

Allowed only when:

- the previous checkpoint is `COMPLETE`;
- discovery status is exactly `PASS_DISCOVERY`;
- every known edition remains present;
- all immutable identity metadata for known editions is unchanged;
- no new edition exists.

The proposed work queue must be empty and there are no remote effects.

### NEW_ITEMS_APPEND_ONLY

Allowed as a **proposal only** when:

- all no-change safety conditions hold;
- every newly discovered edition number is strictly greater than the maximum completed checkpoint edition;
- the number of new editions does not exceed the configured bound;
- no duplicate edition exists.

The planner may return the sorted new-item queue and a candidate future checkpoint, but `advance_allowed=false` until all proposed new items complete every separately authorized downstream stage and final readback.

### STOP conditions

The planner must fail closed for:

- checkpoint not complete;
- partial/unknown discovery;
- duplicate edition;
- disappearance of a previously completed edition;
- identity drift in a previously completed edition;
- non-monotonic newly observed edition;
- delta larger than the configured bound;
- malformed canonical item identity.

## Continuation semantics

A future execution contract, if separately authorized later, must preserve these semantics:

- previous completed checkpoint remains authoritative until the full proposed delta finishes;
- partial/systemic failure does not advance the checkpoint;
- no partial checkpoint commit;
- no automatic retry;
- no automatic cleanup;
- no overwrite, replace or delete as recovery;
- unchanged discovery produces no remote work.

TASK 020 only proves these semantics offline. It does not persist a checkpoint.

## Cadence and recurrence boundary

TASK 020 deliberately does **not** select or activate a clock cadence. Cadence remains an owner/governance decision after technical readiness is established. No `schedule`, automatic trigger, or recurrence workflow may be added by this task.

Any later live incremental execution remains subject to the existing risk policy. A scheduled or recurring chain is T3 and requires a separate explicit owner authorization and a new gate; this task cannot self-promote that authorization.

## Release boundary

Unchanged:

- 0.7.0 ACTIVE;
- 0.8.0 CANDIDATE;
- B1/B2/B3 PENDING;
- closed SIOPE series 2016–2024;
- 2025 Gold UNKNOWN/BLOCKED;
- no SIOPE 2025 semantic promotion.

## Zero-effect statement

- source network: **0**
- Drive reads: **0**
- Drive writes: **0**
- publication writes: **0**
- workflow dispatch: **0**
- schedule changes: **0**
- recurrence changes: **0**
- release promotion: **0**
- SIOPE 2025 semantic promotion: **0**

## Completion criterion

TASK 020 is complete when the contract, pure planner, fail-closed gate and tests pass under CI while the automation policy still keeps recurrence/schedule/future batch and automatic T2/T3 blocked.

A successful TASK 020 means **incremental decision semantics are offline-proven**. It does not mean recurrence is authorized or live-ready by itself.
