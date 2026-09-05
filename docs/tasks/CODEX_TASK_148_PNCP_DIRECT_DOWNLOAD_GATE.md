# TASK 148 — one exact PNCP direct-download transport gate

TASK 147 recorded a managed-web cache miss before any PNCP content was delivered.

The owner then supplied fresh task-specific authorization with the instruction `Prossiga autorizado`.

This task changes only the transport layer. It does not alter the corrected query or the epistemic rules.

After this gate is merged, exactly one direct temporary download may be attempted against:

`https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20251128&dataFinal=20260904&codigoModalidadeContratacao=12&cnpj=45132495000140&pagina=1&tamanhoPagina=50`

Bounds:

- one direct-download invocation maximum;
- zero retry, search, click, alternate endpoint, pagination, or follow-up request;
- raw payload may exist only as a temporary local file and must not be committed to Git or written to Drive;
- on success, byte count and SHA-256 are computed locally before structure inspection;
- a positive administrative identifier can be recorded only as a candidate, at most `CORROBORATED`;
- a failure or empty transport observation cannot create PNCP `NO_MATCH` or an exhaustive negative conclusion;
- municipal-primary verification remains mandatory;
- no automatic financial, transaction, or supplier identity promotion.

This PR is offline design only. The single live transport is permitted only after merge.
