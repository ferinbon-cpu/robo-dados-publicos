# TASK 146 — correct PNCP procurement publication page size to 50

The owner supplied a fresh exact URL and explicit authorization after observing a PNCP HTTP 400 response for the prior `tamanhoPagina=500` request with the error `Tamanho de página inválido`.

This task preserves all historical TASK 132–138 artifacts as history. It does not rewrite them.

The canonical future managed-web probe is now exactly:

`https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20251128&dataFinal=20260904&codigoModalidadeContratacao=12&cnpj=45132495000140&pagina=1&tamanhoPagina=50`

Execution after merge is limited to one open of that user-supplied URL, with zero search, click, retry or follow-up open.

The managed-web layer may return a positive administrative identifier candidate, at most CORROBORATED, but may not issue an exhaustive negative PNCP conclusion. Municipal-primary verification remains mandatory. No financial, transaction or supplier identity promotion is authorized.
