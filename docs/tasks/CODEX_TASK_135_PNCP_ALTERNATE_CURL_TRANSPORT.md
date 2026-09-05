# TASK 135 — alternate curl transport for the authorized PNCP one-shot

TASK 134 remains authorized but unconsumed after the GitHub connector blocked creation of the temporary workflow file.

TASK 135 introduces no new source-read scope. It only defines an alternate execution transport that preserves the already-merged TASK 133 limits.

## Fixed transport

The future execution uses local `curl` against the exact TASK 133 URL with:

- method: GET
- HTTPS only
- requests: max 1
- redirects followed: 0
- retry: 0
- connect timeout: 15 s
- total timeout: 60 s
- response cap: 20 MiB
- Accept: application/json
- raw response: temporary local file only
- raw Git/Drive persistence: forbidden
- sanitized evidence only

The response must be interpreted with the TASK 133 parser contract. Strong Educação Integral policy markers are mandatory; weak credenciamento/oficineiro context alone never qualifies.

No detail, items, history, budget-source or linked-contract endpoint is authorized.

## Authorization

The owner authorization already recorded in TASK 134 remains the sole live authorization source. It must still be unconsumed immediately before execution. TASK 135 does not authorize a second request or a retry.

## Failure semantics

Any transport failure, redirect, oversized response, invalid JSON or malformed payload produces a STOP without a data conclusion. A request attempt, once emitted, consumes the single GET budget even if the response is unsuccessful.
