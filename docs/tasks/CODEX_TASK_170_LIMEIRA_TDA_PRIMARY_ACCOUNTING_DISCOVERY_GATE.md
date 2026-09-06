# TASK 170 — Limeira TDA primary accounting discovery gate

TASK 170 is T0/offline only.

The source router from TASK 169 ranks municipal primary transparency first. Existing repository evidence identifies the Limeira TDA portal as the municipal financial transparency core and records capabilities for despesas, fornecedor, empenho/liquidação/pagamento and related accounting surfaces. However, its public machine-readable endpoint contract is still unproven.

This task therefore selects the TDA as the next source but does not access it.

## Future first request

Only after fresh owner authorization for the new municipal source scope:

- one read-only GET;
- exact URL: `https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418`;
- no redirect follow;
- no retry;
- no authentication;
- no form submission;
- no JavaScript execution;
- no CAPTCHA bypass;
- no endpoint guessing.

If the response is a redirect/login barrier, the result is `SOURCE_ACCESS_SURFACE_BLOCKED`, never NO_DATA.

If the response is 200, inspection is limited to literal declarations of official machine-readable routes or downloads. A candidate JSON/API/CSV/XLSX/ZIP/download route must be explicitly declared by the official response; it is then pinned for a separate schema-validation gate before any collection.

TCE-SP remains useful only after a stable municipal policy/accounting key exists, because its normalized current schema exposes transaction event, commitment number, supplier, date, value, organ and month but not the policy/programmatic/ficha dimensions needed to discover EITI identity independently.
