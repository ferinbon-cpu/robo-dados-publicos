# TASK 089 — immutable pre-run gate source snapshot

This file is post-run evidence reconstructed only from immutable Git objects that existed **before** the live request. It does not create authorization retroactively.

## Pre-run task contract

- commit: `a1efbc2960012cc7fcda456beaf2f100e4fcfdbc`
- path: `docs/tasks/CODEX_TASK_089_BOUNDED_NEXT_EXECUTABLE_CONTRACT_QUERY.md`
- blob SHA: `7e568df40a2eda20e25da1ba3c2c27f18558ee83`

The exact pre-run contract already contained, before network execution:

> Fresh owner authorization is the user's 2026-09-04 instruction `Prossiga e registre no drive`, interpreted for one bounded public-source read after TASK 088 proved the next resolver-executable target.

It also fixed:
- exactly one target: `RECTASK_bf460d6fbffa22124902553f`;
- year `2025`, contract `10/2025.`;
- maximum three HTTP requests;
- host only `serv42.limeira.sp.gov.br`;
- zero Drive/StateRegistry/queue/serving/publication writes;
- no retry, schedule, recurrence, identity promotion or future execution;
- single-use workflow removed immediately after the run.

## Executed workflow Git object

- execution head: `46aafb71a0656a9607d456cf0de887ce3c7749c8`
- original path: `.github/workflows/task-089-contract-resolver-live-once.yml`
- original blob SHA: `c5741a55a14e98736475ae271975963dd18d9691`
- preserved inert source: `docs/evidence/TASK_089_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt`
- preserved source blob SHA: `c5741a55a14e98736475ae271975963dd18d9691`
- exact byte identity: **true**

The executed workflow was therefore not reconstructed from memory: its Git blob is byte-identical to the inert historical source now reviewed by CI.

## Policy interpretation

The canonical T1 tier says: “Auto execution requires capability-limited read-only credentials…” and AGENTS.md says T1 “pode se tornar automático somente” under that trust boundary. TASK 089 was not promoted as recurring/no-click automation. It was a single-use branch-local run created only after the explicit owner instruction above, then removed immediately.

No persistent TASK 089 workflow or future remote trigger exists after the run.
