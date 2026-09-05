# TASK 148 — fresh authorized retry of corrected PNCP page-size-50 probe

TASK 147 recorded a transport-layer managed-web cache miss after exactly one authorized open of the corrected PNCP URL. No PNCP content or HTTP status was observed, so that stop created no source-level conclusion.

The owner then supplied fresh explicit authorization: `Prossiga autorizado`.

This task creates a new fail-closed gate for exactly one fresh live open of the same corrected PNCP procurement-publication URL:

`https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20251128&dataFinal=20260904&codigoModalidadeContratacao=12&cnpj=45132495000140&pagina=1&tamanhoPagina=50`

## Bounds

- base SHA: `81e764fdf2a079c8151ae4d5bb7f0e29c885e682`
- exactly 1 managed-web open after merge
- 0 search queries
- 0 clicks
- 0 retries
- 0 follow-up opens
- no raw payload persistence
- transport/tool failure is not a PNCP response
- positive administrative identifier candidate may be recorded at most as `CORROBORATED`
- no exhaustive negative conclusion and no PNCP `NO_MATCH`
- municipal-primary verification remains mandatory
- no automatic financial identity, transaction identity or supplier linkage
- authorization is consumed by the single live open invocation
- any further live operation requires a new gate and fresh explicit owner authorization

This PR is design-only and performs no live source operation before merge.
