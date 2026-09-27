# TASK 219F — recover JOM contract 45/2026 and prepare municipal primary-source bridge

Issue: #701  
Parent: #691

## Result

TASK 219F recovers one exact documentary contract reference from already validated, already sanitized TASK 219A evidence:

- event: `JOEV_083e522d4145e4d27580`
- Jornal Oficial: edition 7210, page 4, 2026-03-27
- original structured field: `contract_number = "45/"`
- exact label-scoped excerpt: `CONTRATO Nº: 45/ 2026`
- recovered documentary reference: **45/2026**
- Pregão Eletrônico: **10/2026**
- Processo: **902.281/2025**
- Contratada: **Med Doctor Acessórios Ltda**
- CNPJ: **37.457.979/0001-31**
- Objeto: **locação de sistema de endoscopia**
- Valor: **R$ 210.000,00**

The source row comes from TASK 219A run `34354027245`, artifact `10105583802`. The downloaded artifact was independently rehashed before the fixture was pinned:

- artifact ZIP SHA-256: `599c9329f40de5b040b331ada17224614d197a332c12844f523e4a0d9d1aa35d`
- events JSONL SHA-256: `5ca4bf1411f6b8bfa6ad2b8fdede9937f495458963439fa579d40caa7d988c5b`

Both equal the hashes already canonized by TASK 219B/219D.

## Why the structured field was insufficient

The generic Jornal parser uses a compact token field for `CONTRATO Nº`. In this document the PDF extraction contains whitespace between the slash and year:

`45/ 2026`

The resulting structured field became `45/`, so TASK 219B correctly rejected it as an incomplete strong contract identifier.

TASK 219F does **not** rewrite the historical parser or event ID. The original validated event is preserved exactly. Instead, it adds a bounded recovery layer over the already-sanitized excerpt.

## Recovery rule

The repaired contract number is accepted only when all conditions hold:

1. the source event is the pinned validated contract event;
2. exactly one reference occurs under the explicit `CONTRATO Nº` label using the recovery regex;
3. the numeric prefix agrees with the incomplete structured value;
4. the recovered result is a complete number/year documentary reference.

The later text `Termo Contratual nº 12/2026` cannot be selected because it is not under the exact `CONTRATO Nº` label.

No arbitrary slash reference, date, process, amount, object text or semantic similarity can create the recovered identity.

## Primary municipal bridge

The repository already has a live-validated resolver for the Prefeitura Municipal de Limeira contracts search:

`https://serv42.limeira.sp.gov.br/ncweb/cns_contratos_web_mestre/`

TASK 219F prepares the exact future query:

- year: `2026`
- contract number: `45/2026`
- CNPJ: `37457979000131`
- supplier: `Med Doctor Acessórios Ltda`

The existing fail-closed candidate policy requires the returned municipal row to agree on:

- `CONTRACT_NUMBER_YEAR_NORMALIZED`
- `CNPJ`
- `SUPPLIER_NAME`

The process `902.281/2025`, Pregão `10/2026`, object and value are context only. They cannot rescue a contract/CNPJ/supplier mismatch.

## Execution boundary

The municipal live query is intentionally **not implemented or authorized** in TASK 219F.

A future one-shot carrier may perform at most three same-origin HTTP requests using the existing `LimeiraContractsResolver`:

1. landing/search form GET;
2. one stateful search submission;
3. one same-origin ScriptCase autosubmit relay only if unambiguously proven.

That future execution requires fresh owner authorization pinned to the merged implementation SHA. No prior PNCP or reconciliation authorization may be reused.

## Scientific state

TASK 219F proves the exact JOM documentary contract identity **45/2026**. It does not yet prove the municipal search result, TCE commitment identity, PNCP identity, payment, or any procurement-question answer.

Coverage remains **34/38**:

- CTRL_Q2
- PROC_Q1
- PROC_Q2
- PROC_Q3

No PNCP, municipal, TCE or Drive network; no serving, publication, schedule, recurrence or question promotion occurs in this task.
