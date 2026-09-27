# TASK 228 — materialize the 2024 annual accounting comparator

## Purpose

TASK 228 adds the 2024 prior-year source layer for the annual municipal accounting product created by TASK 227 and materializes a bounded 2024→2025 nominal comparator.

Comparison is allowed only when the accounting concept, semantic domain and execution stage are the same. A shared word such as `resultado`, `saldo` or `total` is never enough by itself.

## Primary sources

The four source files were rechecked directly against the primary PDFs and are mapped by the MD_01.3/MD_01.3B corpus index:

- `DOC-016` — Balanço Patrimonial 2024;
- `DOC-009` — Balanço Financeiro 2024;
- `DOC-005` — Balanço Orçamentário 2024;
- `DOC-013` — Demonstrativo das Variações Patrimoniais 2024.

Money is stored as integer BRL cents. Byte-hash identity is not claimed in this task; identity is title/content plus manifest mapping.

## Four semantic domains

### `PATRIMONIAL_POSITION`

Selected Balanço Patrimonial rows include assets, cash, investments, liabilities, provisions, equity, financial assets/liabilities and patrimonial balance.

The source has an important presentation anomaly that is preserved rather than repaired: the asset-side printed total is R$ 3,495,132,026.59 while the passivo + patrimônio líquido side prints R$ 3,547,955,731.84, a difference of R$ 52,823,705.25. Therefore the 2025 QA identity `total liabilities + net equity = total assets` is explicitly unavailable for 2024.

Safe 2024 internal checks are limited to identities that actually hold in the extracted source, such as current + noncurrent assets = total assets and current + noncurrent liabilities = total liabilities.

### `FINANCIAL_FLOWS`

The Balanço Financeiro preserves source-labelled rows, including:

- linked `Educacao` budget revenue: R$ 493,687,862.27;
- linked `Educacao` budget expense: R$ 446,147,870.66;
- total budget revenue: R$ 1,201,670,351.38;
- total budget expense: R$ 1,465,086,693.03;
- opening cash balance: R$ 1,056,151,540.67;
- closing cash balance: R$ 1,110,745,984.90.

The printed ingress and outflow totals are preserved separately because they differ in the source extraction. No balancing value is invented.

`Educacao` remains the source label. It is not silently renamed MDE, FUNDEB or EITI.

### `BUDGET_EXECUTION`

The Balanço Orçamentário preserves forecast/appropriation and execution stages. Selected 2024 rows include:

- realized revenue subtotal: R$ 1,965,345,706.50;
- prior-year financial surplus used for additional credits: R$ 77,827,650.04;
- expenditure total with refinancing: R$ 2,021,080,525.47 committed, R$ 1,926,282,583.58 liquidated and R$ 1,778,856,695.67 paid.

Stages remain distinct: committed != liquidated != paid.

### `PATRIMONIAL_VARIATIONS`

The 2024 DVP is kept in its own domain:

- augmentative variations: R$ 6,791,506,688.04;
- diminutive variations: R$ 6,822,233,679.91;
- patrimonial result: deficit of R$ 30,726,991.87.

Qualitative incorporations/desincorporations are kept apart from the quantitative result.

A second source-specific anomaly is preserved: the DVP result (-R$ 30,726,991.87) differs from the `resultado do exercicio` row in the Balanço Patrimonial (-R$ 28,755,731.46). TASK 228 does not reconcile or force these rows equal.

## 2024 → 2025 comparator

The comparator is nominal, not inflation-adjusted. Each row must match the same semantic domain, metric and, when applicable, execution stage.

Representative nominal changes:

- linked `Educacao` budget revenue: +7.422787%;
- linked `Educacao` budget expense: -0.096681%;
- closing cash balance: +11.331728%;
- realized revenue subtotal: +5.357773%;
- total with refinancing committed: -1.596242%;
- liquidated: -2.950367%;
- paid: -0.108139%;
- prior-year financial surplus used for additional credits: -29.919325%.

Percent change uses 2024 as the base and six decimal places. The percentage is a transparent derivation, never a source value.

## Withheld/non-comparable rows

TASK 228 deliberately withholds some apparently tempting comparisons:

- patrimonial result, because 2024 itself has statement-specific result rows that differ;
- net equity headline comparison, because the 2024 printed balance presentation requires source-specific reconciliation first;
- DVP 2024 vs 2025, because TASK 227 did not materialize a 2025 DVP peer;
- one generic Balanço Financeiro total, because 2024 ingress/outflow printed totals differ.

## Hard guards

- preserve 2024 statement display anomalies;
- do not assert liabilities + equity = assets for 2024;
- DVP result != Balanço Patrimonial result row without reconciliation;
- qualitative patrimonial movements != quantitative result;
- financial ingress total != forced outflow total;
- source label `Educacao` != MDE/FUNDEB/EITI;
- committed != liquidated != paid;
- nominal change != real change without a deflator;
- cross-statement arithmetic cannot manufacture comparability;
- contextual coverage remains 38/38.

## Non-effects

No new public acquisition, Drive write, serving mutation, publication, schedule or recurrence. TASK 228 deepens annual accounting interpretation and comparison only.
