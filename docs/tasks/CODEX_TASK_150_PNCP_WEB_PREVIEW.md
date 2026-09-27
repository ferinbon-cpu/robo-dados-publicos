# TASK 150 — one authorized PNCP web preview after TASK 149

TASK 149 stopped before reaching PNCP because the direct-download safety layer required the URL to be viewed first via web. The owner then provided fresh explicit authorization: `Prossiga autorizado`.

This task authorizes exactly one web open of the corrected PNCP procurement-publication URL after merge:

`https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20251128&dataFinal=20260904&codigoModalidadeContratacao=12&cnpj=45132495000140&pagina=1&tamanhoPagina=50`

Bounds: one web open; zero search, clicks, retries, follow-up opens or direct downloads; no raw persistence. A transport/tool failure is not a PNCP response. A positive administrative identifier may be retained only as a candidate, at most `CORROBORATED`; no PNCP `NO_MATCH` or exhaustive negative conclusion is allowed. Municipal-primary verification remains mandatory, and no automatic financial, transaction or supplier identity may be created.

The single authorization is consumed by the one web-open invocation. Any later live operation requires a new gate and fresh owner authorization.
