# TASK 219AA — official TDA strong procurement/accounting bridge

Issue: #744  
Parent: #691

## Result

Operator-assisted navigation of the official Limeira transparency portal recovered the missing documentary bridge without weakening the repository identity rules.

The exact chain is:

`Contrato 45/2026`
→ `Processo Administrativo 902.281/2025`
→ `Pregão Eletrônico 10/2026`
→ municipal typed procurement key `E00010/2026`
→ TDA commitment `03286-01`.

The identity edge from the TDA Contracts row to the official TDA Empenhado export is the exact typed municipal procurement identifier **E00010/2026**. Supplier CNPJ, amount, date and object text are retained only as consistency checks after that edge is proven.

## Official contract document

The PDF downloaded from the `Documentos` control of the exact 2026 Contract 45 row has SHA-256:

`1c202a188bd3a2a6dc0babc0d29e8c56594462f80b1e64df2c551b5b3be7f5a3`

It explicitly states:

- Termo de Contrato 45/2026;
- Processo Administrativo 902.281/2025;
- Pregão Eletrônico 10/2026;
- Med Doctor Acessórios Ltda, CNPJ 37.457.979/0001-31;
- locação de sistema de endoscopia;
- 12 monthly units at R$ 17.500,00;
- total R$ 210.000,00.

Its final appended Jornal Oficial page reproduces edition 7210 / 27-03-2026 with the same contract/process/bidding/supplier/value identity.

## Official structured commitment export

The TDA `Empenhado (Extração de Dados)` XLSX has SHA-256:

`08c10cb019f93ec408b4b8d30afa5474594a13a36d030e988a1503007c175735`

The exact supplier-filtered export has one row:

- Nro Empenho `03286-01`;
- Nro Processo `E00010/2026`;
- Pregão Eletrônico;
- Med Doctor / CNPJ 37.457.979/0001-31;
- locação de sistema de endoscopia;
- R$ 174.999,99 empenhados;
- R$ 35.000,00 processados;
- R$ 35.000,00 pagos.

The separate `Detalhe Empenho` XLSX confirms the exact commitment, supplier/CNPJ, object and procurement modality but does not expose contract/process identifiers. It is corroboration, not the bridge edge.

## Contract row and execution drill-down

The TDA Contracts UI was filtered exactly by `Ano Contrato=2026` and `Nro Contrato=45`, producing one row. The row exposes R$ 210.000,00 contracted, R$ 174.999,99 committed, R$ 35.000,00 processed/paid, `Pregao Eletronico (E00010/2026)` and process-administration display `902281`.

The `Documentos` control on that exact row returned the official Contract 45/2026 PDF above. This binds the UI row to the legal contract without relying on visual similarity.

The official Processado/Pago drill-down showed two R$ 17.500,00 payment events:

- NF 0000000059 → liquidation 06-07-2026 → order 10071-01 → payment 27-07-2026;
- NF 0000000074 → liquidation 10-08-2026 → order 11818-01 → payment 25-08-2026.

The structured Empenhado export independently carries the resulting R$ 35.000,00 processed and paid totals, so the high-level execution claim does not depend only on screenshots.

## Historical TCESP reconciliation

TASK 219H remains historically correct. Its Jan-Jul 2026 TCESP snapshot found commitment `3286-2026` for the exact supplier/object with R$ 174.999,99 committed and R$ 17.500,00 liquidated/paid.

TASK 219AA does **not** silently assert that TDA `03286-01` and TCESP `3286-2026` are formally identical commitment-number formats. The TCESP row remains independent historical accounting corroboration. The later TDA R$ 35.000,00 total does not rewrite or contradict the older Jan-Jul bounded snapshot.

## Contextual execution consequence

Only `CTRL_Q2 — O que TCE e demais controles corroboram?` is promoted in this task.

Coverage changes from **34/38 → 35/38**.

The answer returns this one proven chain as a bounded example and explicitly distinguishes:

- R$ 210.000,00 contracted;
- R$ 174.999,99 committed;
- R$ 35.000,00 processed;
- R$ 35.000,00 paid.

It never calls payment contract completion and never invents an execution percentage.

`PROC_Q1`, `PROC_Q2` and `PROC_Q3` remain blocked here. One exact chain cannot be generalized into a complete 2026 procurement inventory, supplier/term inventory or additives/apostilamentos/licitation answer. TASK 220 / #697 remains the correct next offline productization step.

## Custody and safety

Raw operator PDF/XLSX/screenshots are not committed to Git. The canonical evidence persists their SHA-256 values and bounded structured facts only.

Runtime effects remain all false: network, Drive, acquisition, OCR, LLM, serving, publication, retry, recurrence and schedule.
