# Controlled operational cycle runbook

TASK 017 provides a local, create-only operational view. It authorizes no live action.

```bash
python main.py operational-cycle \
  --config config/operational_cycle.limeira_pilot.v1.json \
  --out-dir runtime/task_017_demo
```

The command creates `operational_result.json`, `operational_summary.md`, and the existing
local product bundle under `product/`. The destination must not exist. Collision, a live
mode, a remote effect, schedule, recurrence, or mutating persistence stops before downstream
stages. `LIVE_ONE_SHOT_AUTHORIZED` is an interface state only and requires a separate,
explicit owner authorization in TASK 018.

Before any PASS, `PINNED_REUSE` is cross-validated against the canonical source,
processing, reconciliation, and observability contracts, and the frozen release/2025 state
is cross-validated against the TASK 011 pending evidence. Any copied-value drift stops as
`STOP_CONTRACT_UNPROVEN`; the profile is never used as its own source of truth.

Source authorization states are `PINNED_REUSE`, `LIVE_READONLY_AUTHORIZED`,
`LIVE_CREATE_ONLY_AUTHORIZED`, `BLOCKED_AUTHORIZATION_REQUIRED`, and
`BLOCKED_CONTRACT_UNPROVEN`; the default live state is blocked.

Run comparison may report `FIRST_RUN`, `NO_CHANGE`, `SOURCE_CHANGED`,
`NEW_SOURCE_OBJECT`, `PROCESSING_CHANGED`, `NEW_RECONCILIATION_CANDIDATE`, and
`STOP_STATE_CHANGED`. These labels describe deterministic differences and never causality.
