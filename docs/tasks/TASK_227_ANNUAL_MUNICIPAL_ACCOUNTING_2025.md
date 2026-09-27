# TASK 227 — materialize the 2025 annual municipal accounting triad

## Purpose

TASK 226 identified the 2025 annual accounting statements as the highest-value substantive gap in the safe MD_01.3 corpus. TASK 227 materializes a bounded set of high-value rows from three exact primary statements while preserving their distinct accounting meanings.

The three statements are not flattened into a generic money table.

## Sources

### DOC-017 — Balanço Patrimonial 2025

`04-Balanço Patrimonial do Exercício de 2025.pdf`, Município de Limeira — Consolidado, CN-SIFPM/CONAM, Anexo 14, Jan–Dec/2025, generated 06/04/2026, 28 pages.

TASK 227 materializes selected page-1 position rows only. It does not claim a full 28-page parse.

Key directly printed current-year rows include:
- current assets: R$ 1,396,520,822.38;
- noncurrent assets: R$ 1,640,989,412.15;
- total assets: R$ 3,037,510,234.53;
- cash and cash equivalents: R$ 286,879,824.27;
- current liabilities: R$ 261,778,479.20;
- noncurrent liabilities: R$ 1,475,941,763.89;
- total liabilities: R$ 1,737,720,243.09;
- net equity: R$ 1,299,789,991.44;
- result of year: -R$ 453,380,847.48;
- long-term provisions: R$ 957,751,619.55;
- financial assets: R$ 1,257,688,366.19;
- financial liabilities: R$ 270,139,903.93;
- patrimonial balance: R$ 1,179,973,597.05.

Safe internal identities are used only for QA: current + noncurrent assets = total assets; current + noncurrent liabilities = total liabilities; total liabilities + net equity = total assets.

## DOC-010 — Balanço Financeiro 2025

`02-Balanço Financeiro do Exercício de 2025.pdf`, Município de Limeira — Consolidado, CN-SIFPM/CONAM, Anexo 13/13-A, Jan–Dec/2025, generated 06/04/2026, 2 pages.

TASK 227 preserves source labels rather than redefining them. Directly printed page-1 rows include:
- ordinary budget revenue: R$ 843,599,857.23;
- linked `Educacao` budget revenue: R$ 530,333,259.75;
- total budget revenue: R$ 1,227,044,608.70;
- ordinary budget expense: R$ 592,588,005.66;
- linked `Educacao` budget expense: R$ 445,716,532.48;
- total budget expense: R$ 1,396,231,174.92;
- financial transfers received/granted;
- Restos a Pagar inscriptions/liquidations during the period;
- deposits received/returned;
- other extra-budgetary movements;
- prior-year cash balance: R$ 1,071,152,806.16;
- next-year cash balance: R$ 1,236,612,700.45.

The difference between the source-labelled Education revenue and expense rows is **not** promoted as an Education surplus, MDE surplus, FUNDEB balance, EITI margin, or free cash.

## DOC-006 — Balanço Orçamentário 2025

`01-Balanço Orçamentário do Exercício de 2025.pdf`, Município de Limeira — Consolidado, CN-SIFPM/CONAM, Anexo 12, Jan–Dec/2025, generated 06/04/2026, 5 pages.

Selected revenue rows preserve initial forecast, updated forecast, realized revenue and source balance. Selected expense rows preserve initial appropriation, updated appropriation, committed, liquidated, paid and appropriation balance.

Key totals include:
- revenue subtotal realized: R$ 2,070,644,465.93;
- financial surplus from prior years used for additional credits: R$ 54,542,142.35;
- expense total with refinancing committed: R$ 1,988,819,180.58;
- liquidated: R$ 1,869,450,172.86;
- paid: R$ 1,776,933,065.63;
- appropriation balance: R$ 416,182,014.85.

Safe source-internal identities are tested cent-for-cent. They are diagnostic checks, not invented source rows.

## Semantic domains

The config exposes three explicit domains:

- `PATRIMONIAL_POSITION`: stock/position concepts such as assets, liabilities and equity;
- `FINANCIAL_FLOWS`: source-labelled financial/budget flows and cash balances from the Balanço Financeiro;
- `BUDGET_EXECUTION`: budget forecasts, appropriations and execution stages.

A query or future adapter must preserve the domain and source statement. The task does not force these rows into the existing `FISCAL_SERIES` when doing so would erase accounting semantics.

## Hard guards

- asset != cash;
- liability != expenditure;
- net equity != available cash;
- patrimonial result != budget result;
- budget revenue != cash receipt;
- budget expense != paid expense;
- committed != liquidated != paid;
- source label `Educacao` != MDE != FUNDEB != EITI;
- Education revenue minus expense != free surplus;
- consolidated municipal statement != Education-only ledger;
- source balance != free cash;
- no cross-statement arithmetic without an explicit accounting identity;
- selected rows != full-document parse;
- title/content match != byte-hash identity.

## Provenance and precision

All money is stored as integer BRL cents. Each selected row keeps its source document, statement domain and page. No blank or omitted value is filled by inference.

The MD_01.3 manifest supplies the DOC-006/DOC-010/DOC-017 mapping. In this task, byte hashes of the PDFs are not proven, so source identity remains title-and-content matched rather than hash-pinned.

## Non-effects

No new public-source acquisition, Drive write, serving mutation, publication, schedule or recurrence. Canonical contextual coverage remains 38/38; TASK 227 adds annual accounting depth.
