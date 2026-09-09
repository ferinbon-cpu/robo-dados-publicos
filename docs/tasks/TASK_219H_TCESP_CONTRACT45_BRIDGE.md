# TASK 219H — JOM contract 45/2026 → TCESP exact-supplier bridge

Issue: #705  
Parent: #691

## Result

TASK 219H queried the current official TCESP 2026 detailed-expense resource for Limeira using the exact supplier CNPJ from JOM:

**37.457.979/0001-31 — Med Doctor Acessórios Ltda**

The run used exactly two GETs, both HTTP 200, with retry disabled:

1. Limeira 2026 municipal panel;
2. the single `Despesa Detalhada` ZIP discovered from the panel.

The official ZIP and CSV hashes are exactly the same as the previously validated TASK 187 snapshot. The current source still covers months **January–July 2026** and contains 39,779 rows.

## Exact TCESP supplier records

The exact CNPJ occurs in three control-primary records. All belong to the same accounting commitment:

**Empenho 3286-2026**

| Stage | Date | Amount |
|---|---|---:|
| Empenhado | 06/03/2026 | R$ 174.999,99 |
| Valor Liquidado | 06/07/2026 | R$ 17.500,00 |
| Valor Pago | 27/07/2026 | R$ 17.500,00 |

All three rows also share:

- Prefeitura Municipal de Limeira;
- Função Saúde;
- Assistência Hospitalar e Ambulatorial;
- modalidade **Pregão Eletrônico**;
- histórico **“LOCAÇÃO DE SISTEMA DE ENDOSCOPIA”**;
- supplier CNPJ 37.457.979/0001-31;
- supplier name MED DOCTOR ACESSORIOS LTDA.

This creates a new real accounting seed: **3286-2026**.

## Why this is not yet a proven procurement identity

The JOM seed contains exact documentary identifiers:

- Contrato 45/2026;
- Processo 902.281/2025;
- Pregão Eletrônico 10/2026.

None of these complete typed identifiers appears in the matched TCESP rows. The TCESP history contains only the object description and generic procurement modality.

Therefore the canonical rule remains fail-closed:

- exact CNPJ = strong supplier match, not contract identity;
- exact object wording = corroboration, not identity;
- same modality = corroboration, not identity;
- amount/date correspondence or difference = not identity.

The JOM→TCESP procurement identity remains **not proven**.

## Scientific gain

The task does establish, directly from TCESP, that the same legal supplier had 2026 accounting events under a single commitment **3286-2026** for `LOCAÇÃO DE SISTEMA DE ENDOSCOPIA`, including an observed payment event of R$ 17.500,00.

It does **not** attribute that payment to Contract 45/2026 because the explicit cross-source documentary key is still absent.

No balance, outstanding amount, execution percentage or contract-value reconciliation is inferred.

## Lifecycle

Run: `34390323471`  
Execution head: `752c80d592ce1cf3f5f9e1630d71fb4feb3fee7d`  
Artifact: `10119357131`

Artifact ZIP SHA-256:

`8d5e6755439ab4ff26233b0bdf7c0524a7632c305f8e6a183c51e17889fc1ac4`

Artifact member SHA-256:

`10bcdc27a4c1ed5fbed1fbd398d7c58ac2c9f139ea63a38551b6995e614a747a`

The executed workflow blob equals the preserved historical source blob:

`2e3391c15d52a91a9d790722a679cc03f44bf2b1`

The live workflow was removed after execution in commit:

`f5462e02df8c38829ab8c2acae4e806d689589a7`

## Coverage

Coverage remains **34/38**.

Still blocked:

- CTRL_Q2
- PROC_Q1
- PROC_Q2
- PROC_Q3

The next future bridge can use **Empenho 3286-2026** as a new exact accounting seed, but any new live source/query requires fresh authorization.
