# TASK 087 — select next municipal contract reconciliation task

Owner authorization is the 2026-09-03 instruction `Prossiga`, interpreted only for the bounded next gate after TASK 086: read exactly one pinned TASK 076 reconciliation-plan object from Google Drive in read-only mode, verify its exact byte count and SHA-256, and feed those bytes to the already-merged deterministic selector.

## Exact scope

Read only Drive object `11Yb8zIF5g4sTgAp1yhraWFixVFrLcBXs`. Expected size is 52,843 bytes and expected SHA-256 is `faf27576b5b2c3b3c542ae41eeac90c415da1d2f50b6ae8021e1c04bf246d7bc`.

Run the TASK 084 selector for `target_source=LIMEIRA_CONTRATOS`, excluding the two already-consumed tasks `RECTASK_39a82b72abdffa19e0dba705` and `RECTASK_6600049d5284824e9a0a44a6`.

## Hard boundaries

Exactly one Drive object may be read. No Drive write, overwrite, move or delete. No municipal-source request. No StateRegistry or queue mutation. No serving write or publication. No contract or financial identity assertion.

The selected task is only the next deterministic rollout target. A live municipal resolver query remains a separate gate and is **not authorized by TASK 087**.
