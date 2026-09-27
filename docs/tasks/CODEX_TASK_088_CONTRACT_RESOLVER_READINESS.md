# TASK 088 — contract resolver readiness before next live query

## Purpose

Prevent a pointless or over-broad municipal request after TASK 087 selected the next raw `READY_SEARCH / LIMEIRA_CONTRATOS` task.

TASK 087 deterministically selected `RECTASK_78d06bc26f825243c23375c6`, but the already-merged municipal resolver has an explicit minimum-search-key contract: a bounded query may use a contract number or supplier name. CNPJ, object text, process and edital remain corroborating signals and must not be used alone to broaden the public search.

## Offline readiness decision

Apply `LimeiraContractsResolver.has_minimum_search_key(...)` to the remaining rollout candidates, preserving the canonical plan order and excluding the two already-consumed tasks from TASK 081 and TASK 086.

- `RECTASK_78d06bc26f825243c23375c6`: **not executable** by the current resolver; year+CNPJ only, no contract number or contractor name.
- `RECTASK_bf460d6fbffa22124902553f`: **executable**; contract number `10/2025.`, year `2025`.
- `RECTASK_9060935fe5220f738bddfdb4`: **executable**; contract number `08/2025.`, year `2025`.

The next executable target is therefore `RECTASK_bf460d6fbffa22124902553f`.

## Hard boundaries

This TASK is T0/offline only. It performs no municipal-source request, no new Drive read, no Drive write, no StateRegistry/queue mutation, no serving write, no publication, no identity promotion, no schedule and no recurrence.

The ineligible task is not treated as matched, consumed or absent. It remains unresolved and must be routed to a future connector-discovery/enrichment path if the project later supports a bounded search by a different proven key.

A later live query for `RECTASK_bf460d6fbffa22124902553f` is a separate gate.
