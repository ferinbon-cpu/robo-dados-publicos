# M4E live validation — evidence record

## Boundary

Validation ran in an isolated local workspace and disposable SQLite databases. No Drive production database or append-only operational log was replaced. Every match below remains candidate-only.

## Jornal Oficial de Limeira

- requested index: `https://www.limeira.sp.gov.br/jornaloficial/?ano=2026&mes=8`;
- result: `PASS_DISCOVERY`, 12 editions declared by the official page;
- validated document: edition 7310, publication date 2026-08-22;
- declared PDF URL: `https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_21082026170515.pdf`;
- response: HTTP 200, `application/pdf`, 16,952,899 bytes;
- SHA-256: `78a23262023f6233cb59fdc78f1fadc196d0a7bbd52c418bbdd9244229f46680`;
- processing: 76 pages, 195,540 extracted characters, 53 Gold events, 148 RAG chunks and 68 reconciliation tasks;
- queue: 63 `READY_SEARCH` and 5 `BLOCKED_CONNECTOR_DISCOVERY` for TDA.

## Cadastro municipal de contratos

- landing: HTTP 200, `text/html; charset=ISO-8859-1`;
- observed form: ScriptCase POST with `ano_ano`, paired `numero`/`numero_autocomp`, `fornecedor`/`fornecedor_autocomp` and `objeto`/`objeto_autocomp`;
- proof used: the returned JavaScript explicitly copies each autocomplete value into the canonical `SC_*` field;
- result relay: hidden POST form with `script_case_init`, `script_case_session`, `nmgp_opcao=pesq` and explicit `document.form_ok.submit()`;
- same-origin and cookie/session continuity were required;
- positive controlled proof: year 2025 + contract 51 returned two candidate rows, one contract and one price-registration record;
- current edition tasks 119/2026 and 131/2026 returned `NO_MATCH` at validation time;
- tasks lacking contract number and supplier name now stop without broad object-only submission.

## TCE-SP

- 2026 panel: `https://transparencia.tce.sp.gov.br/municipio/limeira/2026`;
- discovered resource: `https://transparencia.tce.sp.gov.br/sites/default/files/csv/despesas-limeira-2026.zip`;
- response: HTTP 200, `application/zip`, 2,132,655 bytes;
- SHA-256: `e696c40b1af0e68efca01e8f819cd26c62a3f62881692e0da33d867604d4d11b`;
- CSV: CP1252, semicolon delimiter, 39,779 records;
- observed aliases: `tp_despesa` → event, `identificador_despesa` → supplier identifier, `ds_despesa` → supplier name, `ds_orgao` → organ and `mes_referencia` → month;
- actual task CNPJ 23.610.910/0001-91 returned `NO_MATCH`;
- controlled one-record proof CNPJ 00.647.935/0001-64 returned `MATCH_CANDIDATE`.

## Reconciliation evidence ledger

- controlled candidate: commitment 1250-2026, `EMPENHADO`, value 1,125.00, supplier CNPJ 00.647.935/0001-64;
- persisted edge: relation `supplier_expense_candidate`, confidence `B_SUPPLIER`, status `CANDIDATE_ONLY`;
- evidence explicitly records `prohibited_promotion = financial_identity`;
- one candidate produced one deterministic ledger edge.

## TDA Limeira

- exact requested route: `https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418`;
- robots policy: `ALLOW`;
- redirects: target → `/logout.aspx` → portal root;
- final response: HTTP 200, `text/html`, 148 bytes;
- static surface exposed only `/login.html` and no API/download endpoint hint;
- decision: remain `BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN`; no authentication, form submission, JavaScript execution, CAPTCHA bypass or endpoint guessing was attempted.

## Gate conclusion

Jornal Oficial, municipal contracts, TCE-SP current schema and the evidence ledger are live-validated for candidate use. TDA remains blocked by evidence. Release promotion is not automatic and requires human review; the GitHub live gate remains pending.
