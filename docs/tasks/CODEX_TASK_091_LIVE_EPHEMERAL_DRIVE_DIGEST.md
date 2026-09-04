# TASK 091 — one live Drive-to-ephemeral-runtime digest proof

## Prospective owner authorization

Fresh owner instruction: **2026-09-04 — `prossiga`**.

This instruction is consumed only by this single bounded TASK 091 live gate. It does not authorize retry, recurrence, schedule, a second file, future batches, derived persistence, publication, serving, StateRegistry/queue writes, source mutation, Drive mutation or any later live gate.

## Base

Protected main at task opening:

`7750b28e42be1b9e786b908c4f8eb9307a9809ad`

TASK 090 is already merged and provides the T0/offline executor:

- `config/ephemeral_runtime_digest.v1.json`
- `scripts/run_ephemeral_runtime_digest.py`
- family adapter: `JORNAL_OFICIAL`
- `stage_bronze=false`
- `plan_reconciliation=false`
- no OCR
- no network inside the digest executor
- no persistent derived writes

## Exact live source

Use exactly one already-immutable TASK 071 Bronze object:

- Drive file ID: `1JTpCPj4_rL08RubO5wOVvBHjuwqKWfQ8`
- canonical name: `limeira_jornal_oficial_edicao_7024.pdf`
- edition: `7024`
- publication date: `2025-07-08`
- expected bytes: `17615179`
- expected SHA-256: `44d92a6ac948bbf43dcb3302733faac1a4ed5e592702f66c07f0c6ede4ecb73c`

Historical TASK 073 deterministic expectations for the same source bytes:

- Silver rows/pages: `79`
- Gold events: `15`
- RAG chunks: `126`

These counts are comparison evidence only; they do not authorize persistence.

## Exact runtime boundary

The live part must run only on branch:

`task-091-live-ephemeral-drive-digest`

The live transport is bounded after repository checkout/setup:

1. exactly one OAuth token-exchange POST to `https://oauth2.googleapis.com/token`;
2. exactly one Drive media GET to the exact file ID above;
3. no other request may pass through the live transport guard.

The downloaded source must be written only below `$RUNNER_TEMP`.

Before digest:

- bytes must equal `17615179`;
- SHA-256 must equal `44d92a6ac948bbf43dcb3302733faac1a4ed5e592702f66c07f0c6ede4ecb73c`;
- any mismatch is STOP before processing.

## Digest behavior

Invoke the merged TASK 090 executor over the staged source inside a fresh runner temp workspace.

Expected semantic result:

- `PASS_EPHEMERAL_RUNTIME_DIGEST_NOT_PERSISTED`;
- input count `1`;
- candidate file count `4`;
- Silver rows `79`;
- Gold rows `15`;
- RAG rows `126`;
- all remote/persistent effect counters `0`.

The candidate files remain ephemeral:

- `edition_manifest.json`
- `pages_silver.jsonl`
- `events_gold.jsonl`
- `chunks_rag.jsonl`

They must **not** be uploaded as GitHub artifacts and must **not** be written to Drive.

## Allowed durable evidence

Only one sanitized JSON evidence artifact may be uploaded, containing:

- run identity;
- exact source file ID;
- observed source bytes and SHA-256;
- request count/method/host/path class without credentials;
- digest status;
- source/candidate hashes;
- row/file counts;
- zero-effect counters;
- comparison against TASK 073 counts.

The evidence must contain no source PDF bytes, no Silver/Gold/RAG text, no OAuth values and no personal data.

## Forbidden

- Drive metadata/list/search requests;
- any Drive POST/PATCH/PUT/DELETE;
- any source mutation;
- any Bronze/Silver/Gold/RAG Drive write;
- artifact upload of source or derived candidates;
- StateRegistry or reconciliation-queue write;
- serving/publication;
- retry;
- pagination;
- recurrence;
- schedule;
- workflow_dispatch;
- repository_dispatch;
- workflow_call;
- future execution authorization.

## Single-use closure

After the one live run:

1. remove the temporary live workflow from the branch;
2. preserve the exact executed workflow source inertly under `docs/evidence/`;
3. commit sanitized run evidence and a verifier;
4. confirm final PR diff contains zero live TASK 091 workflow path;
5. run all required CI and DeepSeek review;
6. merge only if no unresolved concrete blocker remains.

## Result before execution

`READY_FOR_ONE_OWNER_AUTHORIZED_LIVE_RUN`

No live request has occurred merely because this contract exists.
