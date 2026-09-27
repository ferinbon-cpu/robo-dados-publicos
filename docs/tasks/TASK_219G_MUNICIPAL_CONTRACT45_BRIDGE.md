# TASK 219G — bounded municipal contract 45/2026 bridge

Issue: #703  
Parent: #691

## Authorization

The owner authorized completion of this exact municipal bridge after canonical main:

`aa86c2c60640cbb99d54b873c456662fc6ed8b98`

Instruction:

`Autorizado. A autorização vale até completar`

The authorization was interpreted only for TASK 219G: carrier preparation, one bounded live execution, artifact inspection, offline canonization, live-workflow removal, CI/merge and closure. It did not authorize PNCP, TCE, Drive, other sources, recurrence or additional queries.

## Exact query

Official municipal source:

`https://serv42.limeira.sp.gov.br/ncweb/cns_contratos_web_mestre/`

Existing resolver:

`LimeiraContractsResolver`

Strong query identity:

- year: 2026
- contract: 45/2026
- CNPJ: 37.457.979/0001-31
- supplier: Med Doctor Acessórios Ltda

Origin JOM evidence remains:

- event `JOEV_083e522d4145e4d27580`
- Pregão Eletrônico 10/2026
- Processo 902.281/2025
- R$ 210.000,00
- locação de sistema de endoscopia

Process, bidding number, amount and object are corroborating context only.

## Runtime

GitHub Actions run:

`34385352503`

Execution head:

`dda80fb817f5293e5c01b80545eb545dda9938f1`

Artifact:

`10117483856`

Artifact ZIP SHA-256:

`c998cf93eb2e2db0b3ac10c245dd725c9d813c539780059d7dcc6d40f6882a6c`

Payload SHA-256:

`d3a48ed22a6ec81ac89af72e52f31c6778445258fb6c5685d9c1e00257fc8431`

The executed workflow blob and preserved historical source are identical:

`8032fe6cdec503219c8f37af7999269ba5ee207e`

The live workflow was removed immediately after execution in commit:

`12bd4c2c29c30af2ad59c243e7e6b71bae9cb2ad`

## Transport result

Exactly three requests were made, with no retry:

1. GET landing — HTTP 200 — 39,470 bytes
2. POST stateful search — HTTP 200 — 1,075 bytes
3. POST proven ScriptCase relay — HTTP 200 — 72,634 bytes

All requests and final response URLs remained HTTPS on:

`serv42.limeira.sp.gov.br`

There was no timeout, 408, 429, 5xx, zero-byte response or transport/edge failure.

## Resolver result

Form discovery:

`PASS_FORM_DISCOVERY`

ScriptCase relay:

`PASS_PROVEN_AUTOSUBMIT_RELAY`

The relay returned an interpretable table with 17 rows.

Final resolver status:

`NO_MATCH`

Candidate count:

`0`

The existing fail-closed candidate policy required simultaneous agreement on:

- `CONTRACT_NUMBER_YEAR_NORMALIZED`
- `CNPJ`
- `SUPPLIER_NAME`

No returned row satisfied the exact triple for Contract 45/2026, CNPJ 37.457.979/0001-31 and Med Doctor Acessórios Ltda.

## Scientific meaning

This is a valid bounded negative result for this exact municipal query.

It means:

> The official municipal contracts search did not return a row that simultaneously matched the exact Contract 45/2026, exact CNPJ 37.457.979/0001-31 and supplier agreement required by the robot's candidate policy.

It does **not** mean:

- Contract 45/2026 universally does not exist;
- the JOM contract event is invalid;
- PNCP identity was disproven;
- no TCE expenditure exists;
- no payment/execution occurred.

The JOM event remains valid primary documentary evidence. The municipal bridge simply did not independently corroborate it under the exact bounded search.

## Scientific state

Coverage remains **34/38**.

Still blocked:

- CTRL_Q2
- PROC_Q1
- PROC_Q2
- PROC_Q3

No question promotion occurred.

Parent #691 remains open because a strong end-to-end procurement/financial identity bridge is still not proven.

## Authorization closure

TASK 219G is complete. The authorization used for this bridge is exhausted for future network activity. Any additional query, source or new live route requires a new authorization.
