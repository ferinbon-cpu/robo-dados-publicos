# TASK 168 — PNCP resource API recovery and machine-readable fallback

Issue: #548

TASK 167 used the documented production resource API routes for two stable PNCP identities and received HTTP 502/503 with zero body bytes. Those responses are source/transport unavailability, not evidence of absent detail, budget sources, contracts, accounting execution, or EITI linkage.

This task preserves DIRECT_JSON_FIRST and introduces a circuit-breaker before any target traversal.

## Preflight

The current PNCP Manual de Integração documents production `BASE_URL` as:

`https://pncp.gov.br/api/pncp`

and documents the public domain query:

`GET /v1/modalidades?statusAtivo=true`

The live task therefore performs exactly one preflight GET:

`https://pncp.gov.br/api/pncp/v1/modalidades?statusAtivo=true`

The preflight only passes when it returns parseable JSON with active modality id 9 (Inexigibilidade).

## If preflight is healthy

Only six essential requests are allowed, three for each TASK 166 stable identity:

1. purchase detail;
2. all budget sources for the purchase;
3. contracts/empenhos linked to the purchase.

Total request budget: 7 including preflight. No retry and no redirect follow.

## If preflight is unavailable or invalid

No target resource route is attempted. The next action is restricted to official PNCP open-data/API consultation documentation to identify an alternative documented machine-readable surface. HTML/DOM/JS/internal-path reverse engineering is explicitly outside TASK 168.

## Evidence semantics

- transport/HTTP failure != NO_DATA;
- 404 != absence unless the exact route contract supports that interpretation;
- raw bodies are not persisted to Git, Drive, or workflow artifacts;
- only sanitized selected fields, structural metadata, byte counts and hashes can leave the live step;
- budget/accounting-looking fields are candidate evidence only;
- PNCP does not prove payment;
- no automatic EITI financial, transaction, supplier, or causal identity is created.
