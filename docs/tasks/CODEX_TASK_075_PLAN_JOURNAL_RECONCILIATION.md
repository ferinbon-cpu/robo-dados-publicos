# TASK 075 — plan Jornal reconciliation deterministically

Consumes owner token 5/7. This task reads only the three exact TASK074 persisted Gold event files and applies the existing `ReconciliationPlanner` without executing any target resolver.

The three inputs are pinned by full SHA-256 and contain exactly 52 Gold events: 15 from edition 7024, 10 from edition 7119 and 27 from edition 7127.

Planning produced 65 generated tasks and 65 unique task IDs, with zero duplicate task IDs. The canonical sorted JSONL representation is 52,843 bytes with SHA-256 `faf27576b5b2c3b3c542ae41eeac90c415da1d2f50b6ae8021e1c04bf246d7bc`.

Target distribution:

- `SIAVE_LIMEIRA`: 37
- `LIMEIRA_LICITACOES`: 14
- `LIMEIRA_CONTRATOS`: 5
- `TDA_LIMEIRA`: 5
- `TCE_SP_DESPESAS`: 4

Status distribution is fail-closed: 60 `READY_SEARCH` and all 5 TDA tasks remain `BLOCKED_CONNECTOR_DISCOVERY` because the TDA connector contract is not proven.

These are search/reconciliation instructions only. No task is a financial-identity assertion, no supplier/value clue is promoted to identity, and no `MATCH_CANDIDATE` or other semantic promotion is produced.

No reconciliation plan was persisted to Drive in this task. No queue/StateRegistry write, resolver request, serving mutation, publication, source move or source delete occurred.

Result: `PASS_TASK075_52_GOLD_EVENTS_65_UNIQUE_RECONCILIATION_TASKS_PLANNED_NO_IDENTITY_PROMOTION`.

Next gate: TASK 076 may persist this exact hash-pinned reconciliation plan as create-only Gold derived evidence with full SHA-256 readback. It must not execute any reconciliation resolver, mutate StateRegistry, assert financial identity, write serving data or publish products.
