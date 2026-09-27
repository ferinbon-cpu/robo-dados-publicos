# TDA Limeira — research notes (2026-08-21)

## Evidence status
These notes separate what is supported by public evidence from what remains to be technically proven.

### Supported

1. The project target is `https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418`.
2. A public crawler currently follows that target to the transparency domain root and then exposes `login.html` with a minimal `Loading` surface. This is consistent with a scripted entry page, but does **not** prove that citizen data requires authentication.
3. Limeira's 2019 procurement specification treated the transparency portal as one component of a broader integrated municipal management suite including budget/accounting/finance, HR/payroll, assets, materials, purchases/procurement and access-to-information functionality.
4. A 2025 Limeira municipal publication on the extinction of EMDEL states that contracts related to finance, HR, purchases, procurement, warehouse, transparency portal and accounting services would pass to the municipality, reinforcing the relevance of the portal as part of the administrative information ecosystem.
5. Official Limeira responses indexed on public legislative/municipal systems point citizens to the TDA transparency portal for detailed financial queries, including supplier-related information and specific accounting revenue codes.
6. Other public bodies using the same `TDAPortalClient.aspx?418` URL pattern document modules for expenses, revenues, procurement/contracts and HR; a Praia Grande municipal page explicitly describes a DESPESA module where empenho, liquidação and pagamento can be followed through filters. This is supporting evidence for product-family capability, not proof of Limeira's exact field set or endpoint contract.

### Not yet proven

- exact Limeira public API path;
- exact request payload used by the current JavaScript application;
- availability of CSV/XLSX/JSON export for every module;
- pagination contract;
- whether `C.Apl 2607004` is exposed as a filterable field in the current portal;
- whether a stable public endpoint can be called without browser execution;
- rate-limit behavior and current robots.txt policy from the production runtime.

## Engineering consequence
Do not build a production scraper by guessing URL patterns from another municipality. First run the passive probe, then—if needed—perform a one-session browser network inspection of the public citizen workflow and record only requests that the portal itself makes. A stable public request/response contract must be captured as a fixture before enabling automated collection.

## Public references used for discovery

- Limeira transparency target: https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418
- Limeira procurement specification (2019): https://www.limeira.sp.gov.br/sitenovo/downloads/EDITAL%20N%20001%20Pregao%20-%20SISTEMA%20DE%20INFORMATICA%202019.pdf
- Limeira EMDEL extinction publication (2025): https://limeira.sp.gov.br/prefeitura-de-limeira-conclui-extincao-da-emdel-apos-20-anos
- Limeira official response with IPVA accounting codes: https://siave.limeira.sp.leg.br/arquivo?Id=511614
- Limeira official response referencing transparency data: https://consulta.limeira.sp.leg.br/arquivo?Id=567047
- Praia Grande municipal explanation of expense execution visibility: https://www2.praiagrande.sp.gov.br/pagina-introdutoria/emendas-impositivas-municipais
- Sorocaba example of supplier/CNPJ filtering in the homologous portal pattern: https://sorocaba.camarasempapel.com.br/Arquivo/Documents/REQ/REQ15382025/508091-20250610083135855209534XAP.pdf
