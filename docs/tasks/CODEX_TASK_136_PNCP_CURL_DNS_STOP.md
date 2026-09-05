# TASK 136 — PNCP curl DNS stop

TASK 135 was merged and the authorized alternate transport was invoked exactly once.

Observed result:

- curl exit: 6
- error: `Could not resolve host: pncp.gov.br`
- HTTP status: `000`
- HTTP GET emitted to PNCP: false
- bytes received: 0
- raw response file: not created
- redirects followed: 0
- retry: 0
- temporary local files: removed

This is a **pre-HTTP DNS transport STOP**. It is not a PNCP response and creates neither a candidate nor a bounded `NO_MATCH`.

The TASK 135 local transport attempt is consumed and must not be retried. The source-read scope remains unconsumed because no HTTP request reached PNCP and no source bytes were read.

Any further transport attempt requires a new gate. No detail/items/history/budget-source/linked-contract request is authorized, and financial/transaction identity remains unchanged.
