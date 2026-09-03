# TASK 084 — deterministic next reconciliation selector

## Purpose

Prepare the reconciliation rollout after TASK 081 without performing any new public-source request, Drive read/write, StateRegistry/queue mutation, serving write or publication.

TASK 075 produced a canonical 65-task JSONL plan, TASK 076 persisted the exact bytes create-only in Gold, TASK 077 selected the first `READY_SEARCH` `LIMEIRA_CONTRATOS` task, and TASK 081 consumed that same task in one bounded stateful public query. Four `LIMEIRA_CONTRATOS` tasks remain unpiloted, but their exact task IDs are not present in the current Git tree.

## Exact offline contract

Implement a deterministic selector that accepts plan bytes only from a separately authorized caller and:

1. requires the pinned plan SHA-256;
2. parses UTF-8 JSONL fail-closed;
3. rejects duplicate task IDs;
4. requires the planner's canonical order `(-priority, origin_event_id, target_source, task_id)`;
5. requires every consumed task ID to exist in the pinned plan;
6. filters only `status=READY_SEARCH` and the requested `target_source`;
7. excludes already consumed tasks;
8. returns exactly the first remaining task plus deterministic metadata;
9. performs zero network, Drive, registry, queue, serving or publication effects.

For the current rollout, the pinned plan is SHA-256 `faf27576b5b2c3b3c542ae41eeac90c415da1d2f50b6ae8021e1c04bf246d7bc`, 52,843 bytes and 65 tasks. The consumed contract task is `RECTASK_39a82b72abdffa19e0dba705`.

## Why the next task is not named in this T0 step

The exact 52,843 plan bytes were persisted in Drive and were never committed to GitHub; repository evidence contains aggregate counts and the first selected task, not the other four `LIMEIRA_CONTRATOS` task IDs. Guessing the next task would violate the deterministic/fail-closed contract.

## Next gate

After this T0 selector passes CI, a later separately bounded gate may read exactly the TASK 076 Gold plan object `11Yb8zIF5g4sTgAp1yhraWFixVFrLcBXs` read-only, verify the exact byte size and SHA-256 above, feed those bytes to this selector with the TASK 081 task excluded, and return the next task locally. That gate must not query the municipal source, mutate Drive/StateRegistry/queue, or publish anything. A further live resolver query remains separate.
