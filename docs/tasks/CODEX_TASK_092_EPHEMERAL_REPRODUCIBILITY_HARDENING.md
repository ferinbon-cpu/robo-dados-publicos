# TASK 092 — ephemeral digest reproducibility hardening

## Authorization

Owner authorized the structural redesign on 2026-09-04 with: **`autorizado`**.

This task is **T0/offline only**. It does not authorize a Drive read, public-network request, source mutation, remote persistence, retry, recurrence, schedule, serving or publication.

## Problem discovered in TASK 091

TASK 091 proved that the merged TASK 090 executor could digest an exact immutable Drive source locally and produce four ephemeral candidate roles. The run then stopped at historical count comparison.

The operational weakness was not the digest itself. The workflow compared historical row counts before durably capturing the observed counts and candidate hashes. That made the historical reproduction drift visible but left the exact observed divergence unavailable.

## New invariant

Historical comparison must never erase or reclassify a successful digest.

The required order is:

1. accept only a successful local TASK 090 digest result;
2. capture source identity, row counts and every candidate hash;
3. capture the runtime fingerprint;
4. create the observation record locally with create-only semantics;
5. only then compare against historical expectations;
6. report historical reproduction as `MATCH` or `DRIFT` while preserving the independent digest status.

A historical mismatch is **not** a digest failure.

## Implementation

- `robo_dados_publicos/manual_ingest/ephemeral_reproducibility.py`
  - captures a deterministic observation envelope around an already successful digest;
  - records Silver/Gold/RAG counts and candidate hashes before comparison;
  - records Python/platform/pypdf/project runtime fingerprint;
  - separates `digest_status` from `historical_reproduction_status`;
  - writes observation and report with create-only local semantics.

- `scripts/build_ephemeral_reproducibility_report.py`
  - reusable local CLI for future workflows;
  - removes historical comparison logic from ad-hoc inline workflow code.

- `tests/test_task_092_ephemeral_reproducibility.py`
  - successful observation capture;
  - exact historical match;
  - historical drift with digest PASS preserved;
  - proof that observation is written before malformed comparison can STOP;
  - create-only overwrite protection;
  - non-PASS digest rejection;
  - runtime fingerprint coverage.

## Semantic statuses

Digest:
- `PASS_EPHEMERAL_RUNTIME_DIGEST_NOT_PERSISTED`

Historical reproduction:
- `HISTORICAL_REPRODUCTION_MATCH`
- `HISTORICAL_REPRODUCTION_DRIFT`

The second dimension never upgrades, downgrades or rewrites the first.

## Effects

All remote-effect classes remain zero.

This task changes only local code, tests and documentation. It creates no workflow and no execution authorization.

## Next structural task

After TASK 092 passes CI/review, TASK 093 may introduce the generic research ontology/schema that generalizes the existing TASK 055A EITI terminology ontology without weakening its anti-overreach rules.
