# TASK 168B — PNCP Consulta contracts fallback

This is the machine-readable fallback activated by TASK 168 after the documented PNCP resource API preflight returned HTTP 503.

Official PNCP API Consulta contract:

- base: `https://pncp.gov.br/api/consulta`;
- endpoint: `GET /v1/contratos`;
- filters include publication date range and optional `cnpjOrgao`;
- response exposes `numeroControlePNCP`, `numeroControlePNCPCompra`, `numeroContratoEmpenho`, contract year and PNCP contract sequence;
- pagination is mandatory for exhaustive conclusions and page size may be set up to 500;
- HTTP 204 is documented as a successful No Content response.

Exact fallback scope:

- CNPJ: `45132495000140`;
- contract publication dates: 20260608 through 20260905;
- page size: 500;
- max page cap: 20;
- target purchase IDs:
  - `45132495000140-1-000368/2026`;
  - `45132495000140-1-000593/2026`.

The start date is the earliest publication date of the two target purchases. The end date is the current research cutoff. A completed zero-match result is therefore bounded evidence only: it means no contract/empenho published in this exact PNCP Consulta scope linked to either target purchase ID. It is not a global or future absence claim.

Raw page bodies are processed ephemerally and never persisted. Per-page metadata, byte counts, SHA-256 values, pagination totals and exact target matches may be persisted in sanitized form.
