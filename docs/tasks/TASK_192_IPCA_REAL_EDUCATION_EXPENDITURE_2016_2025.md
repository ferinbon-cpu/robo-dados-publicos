# TASK 192 — IPCA real education expenditure 2016–2025

## Goal

Materialize a comparable annual series of Limeira education expenditure in nominal BRL and in December-2025-equivalent BRL using official IBGE IPCA, then close FIN_Q4 without annualizing partial 2026.

## Source chain

- 2016–2024 nominal annual committed education expenditure: existing validated SIOPE Gold custody, using `VL_DESP_EMPE_EDU`; 2016 uses P1 under the proven historical regime and 2017–2024 use P6.
- 2025 nominal annual committed education expenditure: TASK 191 RREO Anexo 8 line 33, committed at the final bimester.
- Deflator: IBGE IPCA annual accumulated rates, official December 2025 publication.

No new FNDE/SIOPE collection is required by TASK 192.

## Price semantics

The constant-price metric is `REAL_EDUCATION_EXPENDITURE`, expressed as `BRL_DEC_2025_EQUIVALENT`.

For an annual observation in year Y, the year-end-equivalent factor compounds IPCA rates from Y+1 through 2025. The same-year rate is not reapplied. This is intentionally a year-end-equivalent annual comparison, not a monthly-weighted deflation of expenditure flows.

## Proven trend

- 2016 → 2025 nominal: +115.36%.
- 2016 → 2025 real, Dec/2025 equivalent: +38.91%.
- 2024 → 2025 nominal: +1.21%.
- 2024 → 2025 real, Dec/2025 equivalent: -2.92%.

The recent result is a useful semantic test: the nominal total rises slightly while its inflation-adjusted equivalent falls.

## Guards

- nominal is never silently presented as real;
- 2016–2024 SIOPE source family is not collapsed into the 2025 RREO source family;
- committed, liquidated and paid stages remain distinct;
- no compliance conclusion is derived;
- 2026 remains partial at `LIQUIDATED_TO_DATE` and is not annualized;
- year-end-equivalent IPCA adjustment is not mislabeled as monthly-weighted flow deflation.

## Expected product transition

FISCAL_SERIES grows from 42 to 61 rows: 9 historical nominal rows plus 10 real rows. FIN_Q4 moves from `MATERIALIZED_PARTIAL` to `MATERIALIZED_ANSWERABLE`. Global FISCAL_SERIES remains `READY_PARTIAL_ONLY`.
