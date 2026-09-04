# TASK 091 — one live Drive-to-ephemeral-runtime digest proof

## Authorization and archival policy

Fresh owner instruction: **2026-09-04 — `prossiga`**.

The instruction authorized exactly one bounded live TASK 091 run. It did not authorize retry, recurrence, schedule, a second file, future batches, derived persistence, publication, serving, StateRegistry/queue writes, source mutation or Drive mutation.

The exact prospective pre-run contract existed before network execution at:

- commit: `1e59ad3647e79c1783db3cf9568765234b2d99c2`;
- Git blob: `143bad34650ac1707df96875312ef8e3ed749189`.

That historical source contained the exact remote identifier required for the one-shot gate. The final canonical tree intentionally **does not reproduce that remote identifier**. This document is the redacted durable task record. The final PR is intended for squash merge so intermediate operational identifiers are not promoted into protected-main history.

## Base and executor

Protected main at task opening:

`7750b28e42be1b9e786b908c4f8eb9307a9809ad`

TASK 090 was already merged and provided the T0/offline executor:

- `config/ephemeral_runtime_digest.v1.json`;
- `scripts/run_ephemeral_runtime_digest.py`;
- family adapter `JORNAL_OFICIAL`;
- `stage_bronze=false`;
- `plan_reconciliation=false`;
- no OCR;
- no network inside the digest executor;
- no persistent derived writes.

## Redacted live source contract

Exactly one already-immutable TASK 071 Bronze Jornal object was selected.

Durable non-identifier evidence:

- remote-id SHA-256: `c4ddf384c210c0189c8c6da932de27cdaa70f810d026060736f10c76ed99dfc5`;
- edition: `7024`;
- publication date: `2025-07-08`;
- expected bytes: `17615179`;
- expected source SHA-256: `44d92a6ac948bbf43dcb3302733faac1a4ed5e592702f66c07f0c6ede4ecb73c`.

Historical TASK 073 comparison values for those same source bytes were:

- Silver pages: `79`;
- Gold events: `15`;
- RAG chunks: `126`.

These values were comparison evidence only and never authorized persistence.

## Executed runtime boundary

Execution head:

`0c777c647cefaacc9d1daba35c1cded42109c120`

Run:

`33873064071`

Job:

`101023430264`

Executed workflow Git blob:

`1e354d9c9129f9c3ac4ba1e3bf80947301c7616c`

The transport guard permitted exactly:

1. one OAuth token-exchange POST;
2. one exact Drive media GET bound to the pre-run remote identifier;
3. no additional guarded request.

No metadata/list/search call and no Drive mutation were allowed.

The source was staged only below the runner temporary directory. Before digest, byte count and source SHA-256 were checked. The merged TASK 090 executor then ran locally.

## Observed outcome

The run reached all of these gates successfully:

- exact request budget: 2;
- source byte-count gate;
- source SHA-256 gate;
- `PASS_EPHEMERAL_RUNTIME_DIGEST_NOT_PERSISTED`;
- input count = 1;
- candidate file count = 4.

The four local candidate roles were:

- edition manifest;
- Silver pages;
- Gold events;
- RAG chunks.

The run then stopped at:

`STOP_TASK091_HISTORICAL_COUNT_DRIFT`

The TASK 091 artifact did not capture the observed row counts before raising. Therefore the exact difference versus TASK 073 is unknown and the root cause remains:

`UNRESOLVED`

No explanation for the drift may be inferred from current evidence.

## Runtime fingerprint captured after the STOP

- GitHub runner: `2.337.0`;
- OS: Ubuntu 24.04.4 LTS;
- image: `ubuntu-24.04`;
- image version: `20260823.283.1`;
- Python: 3.12;
- pypdf: 6.10.0;
- project: robo-dados-publicos 0.8.0.

TASK 073 does not preserve an equally complete executable runtime fingerprint.

## Hard boundaries observed

- one Drive media GET;
- zero Drive mutating requests;
- zero source mutation;
- zero Bronze/Silver/Gold/RAG remote writes;
- zero StateRegistry writes;
- zero queue writes;
- zero serving writes;
- zero publication;
- zero retry runs;
- zero recurrence;
- zero schedule;
- source and candidate workspace removed after execution;
- only sanitized JSON evidence was uploaded.

## Single-use closure

The temporary live workflow was removed immediately after the consumed run at commit:

`715fea0d4eb0991b39500736dda1226e5317bbd6`

No second TASK 091 live run was observed.

The complete live workflow source is not retained in the final canonical tree. Its exact executed Git-blob SHA remains recorded for audit correlation.

## Result

`STOP_TASK091_DIGEST_PROVEN_EPHEMERAL_HISTORICAL_COUNT_DRIFT_UNRESOLVED`

## Next gate

No retry is authorized.

Before any future live proof, an offline follow-up must:

1. capture runtime fingerprint before processing;
2. capture observed counts and candidate hashes before historical comparison;
3. distinguish `DIGEST_PASS` from `HISTORICAL_REPRODUCTION_DRIFT`;
4. preserve the same zero-persistence boundary.

Any new live read requires fresh owner authorization.
