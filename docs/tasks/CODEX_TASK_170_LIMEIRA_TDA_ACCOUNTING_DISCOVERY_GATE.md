# TASK 170 — Limeira TDA primary accounting discovery gate

## Scope

T0/offline source selection only. No municipal live request is executed or authorized by this task.

## Upstream state

TASK 169 ranked the municipal primary transparency expense-detail class first for the EITI accounting-execution bridge. The versioned Limeira source registry identifies `LIMEIRA_TDA_PORTAL` at `https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418` with declared capabilities including despesas and empenho/liquidação/pagamento, while preserving `BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN`.

Prior bounded M4E evidence observed the exact route redirect to logout/root and no explicit API/download hint. That state is an access-surface limitation, not evidence of no accounting data.

## Selection

`LIMEIRA_TDA_PORTAL` is selected as the next municipal-primary accounting discovery target because it is the strongest already-versioned municipal surface for the capabilities required by TASK 169. TCE-SP remains corroboration after a policy/accounting key exists; it does not replace unresolved municipal-primary EITI identity.

## Future live gate

A future separately authorized live phase may:

1. perform one GET to the exact known official TDA route;
2. inspect only the returned public surface for an explicitly declared official JSON/API/CSV/XLSX/download or other machine-readable route;
3. if and only if such a route is explicitly declared, follow at most one exact read-only machine-readable route after host/entity validation.

Maximum future budget: two requests total, no retry and no redirect follow.

The future phase must not guess endpoints, brute-force paths, execute JavaScript, reverse engineer internal paths, submit forms, authenticate, emulate sessions, use credentials, or bypass CAPTCHA. Login/logout/session barriers are `SOURCE_ACCESS_SURFACE_BLOCKED`; transport failures are `SOURCE_TRANSPORT_UNAVAILABLE`; neither is `NO_DATA`.

## Scientific boundary

Selection of the TDA surface proves no EITI financial identity and no transaction stage. The current states remain:

- financial identity: `UNKNOWN`;
- transaction identity: `UNKNOWN`;
- commitment: `NOT_PROVEN`;
- liquidation: `NOT_PROVEN`;
- payment: `NOT_PROVEN`.

Any future promotion still requires the TASK 169 minimum policy-financial identity bundle and rejects weak joins such as program 2001 alone, unit similarity, C.Apl 2607004 alone, value proximity, chronology, semantic similarity, or PNCP linkage without an accounting key.

## Authorization boundary

TASK 170 performs zero network requests and grants zero live authorization. After merge, a future Limeira municipal transparency read requires fresh explicit owner authorization scoped to `transparencia.limeira.sp.gov.br`, `LIMEIRA_TDA_PORTAL`, and the declared-route discovery purpose.

## Result

`PASS_TASK170_LIMEIRA_TDA_SELECTED_FOR_FUTURE_BOUNDED_DISCOVERY_NO_LIVE_REQUEST`
