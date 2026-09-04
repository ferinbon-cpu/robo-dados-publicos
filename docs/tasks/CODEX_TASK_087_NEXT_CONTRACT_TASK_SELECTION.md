# TASK 087 — revalidate next municipal contract reconciliation task on current main

The paused PR #366 required reconstruction against the current protected `main` and the current consumed-task state before any further contract-resolver step.

Owner instruction on 2026-09-04: `Retome o robo minerador daonde parou no github`.

This gate interprets that instruction narrowly: re-run only the already-proven TASK 084 deterministic selection using one read-only fetch of the pinned TASK 076 reconciliation-plan object. It does not authorize a municipal live query.

## Current-main anchor

Base `main`: `25ad59d500691dea21246e46218726284f64be27`.

Current merged evidence confirms the consumed `LIMEIRA_CONTRATOS` tasks are:

- `RECTASK_39a82b72abdffa19e0dba705` — consumed by TASK 081;
- `RECTASK_6600049d5284824e9a0a44a6` — consumed by TASK 086.

No additional consumed `LIMEIRA_CONTRATOS` task was found on current `main`.

## Exact read-only reconstruction

Read exactly Drive object `11Yb8zIF5g4sTgAp1yhraWFixVFrLcBXs`.

Pinned identity:

- bytes: `52843`;
- SHA-256: `faf27576b5b2c3b3c542ae41eeac90c415da1d2f50b6ae8021e1c04bf246d7bc`;
- tasks: `65`;
- eligible `READY_SEARCH / LIMEIRA_CONTRATOS`: `5`.

After excluding the two consumed task IDs, exactly `3` remain. The deterministic next task is unchanged from paused PR #366:

- task: `RECTASK_78d06bc26f825243c23375c6`;
- selected-task SHA-256: `abf65314248db88f3d26c615281b2c8f3871efee3b1b8725e0fd5de653352287`;
- year: `2025`;
- CNPJ corroborator: `29494115000161`;
- edital hint: `15/2024`;
- process hint: `903.340/2025`.

## Hard boundaries

Exactly one Drive object was read. There was no Drive write, overwrite, move or delete; no municipal-source request; no StateRegistry or queue mutation; no serving write; no publication; and no contract or financial identity assertion.

TASK 087 only proves the next deterministic rollout target. A live municipal resolver query remains a separate gate and is not authorized by this TASK 087 revalidation.
