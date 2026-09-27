# TASK 167 — PNCP stable-ID direct JSON traversal

Issue: #546

This task continues from TASK 166 and traverses two stable PNCP procurement identities using documented direct machine-readable PNCP routes.

Targets:

- school pass: 2026 / sequence 368 / `45132495000140-1-000368/2026` / process `I00055`;
- course: 2026 / sequence 593 / `45132495000140-1-000593/2026` / process `I00084`.

Routes per target:

1. purchase detail;
2. items;
3. history;
4. budget sources (`fonte-orcamentaria`);
5. linked contracts.

Standing authorization from TASK 161 is reused only for PNCP live read/discovery. No per-route authorization is required inside the same source/host/purpose scope until revoked or superseded.

The task is fail-closed independently by route:

- transport, HTTP, JSON, schema or identity failure is not converted into NO_DATA;
- the detail route must match CNPJ, year, sequence, `numeroControlePNCP` and process exactly;
- only sanitized structural metadata and selected fields may leave the live step;
- raw PNCP response bodies are not persisted to Git, Drive or workflow artifacts;
- budget/accounting-looking fields are only `CANDIDATE_NOT_PROVEN` signals;
- PNCP procurement evidence cannot prove payment;
- no EITI financial, transaction or supplier identity is auto-promoted.

The desired scientific outcome is not to force a match. It is to determine whether either stable procurement identity exposes a sufficiently explicit budget/accounting key to justify a separate accounting-execution bridge. If not, the EITI financial identity remains UNKNOWN.
