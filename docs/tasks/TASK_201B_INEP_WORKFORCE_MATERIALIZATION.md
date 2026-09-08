# TASK 201B — INEP 2025 workforce materialization

## Manual handoff

The owner supplied the exact official INEP 2025 statistical synopsis package after the GitHub runner could not retrieve the fixed INEP URL.

Pinned identities:

- package SHA-256: `a8a41fcd487e98dc26c9107dfd92f403641983b2737d50497bac3e47b4f051c8`
- package bytes: `232142480`
- XLSX SHA-256: `af3a0f13731214730c4baa362bfc542c526c8c81d31c48e699919623c491462c`
- XLSX MD5: `07461C4FD19E120EF31945AF8A3D0625`
- the XLSX MD5 is present in the official package manifest.

## Canonical 2025 municipal docente count

Sheet 2.2, Limeira row 3608:

- all dependencies in municipality: 3,113 unique docentes;
- public network: 2,169;
- municipal dependency: **1,280**.

The canonical `STAFF_COUNT` is 1,280 and means unique docentes in effective classroom teaching within the municipal dependency. It is not a count of all Education workers.

## Municipal employment bonds

Sheet 2.6, Limeira row 3607:

- concursado / efetivo / estável: **681**
- contrato temporário: **291**
- contrato terceirizado: **0**
- contrato CLT: **400**

These category counts are **not additive**. INEP notes that the same docente may have more than one functional bond; each docente is counted once within each bond/dependency cell.

## Current SME context

The prior privacy-safe live probe remains supplemental context:

- 07/09/2026
- 843 assignment rows
- 842 unique contracted teachers
- 72 school labels
- 1 person represented by multiple assignment rows
- no person-level output persisted.

This operational snapshot is not directly comparable to the 2025 Census totals or bond counts.

## Answerability hardening

V1 and V2 remain immutable.

Current V3 changes only the STAFFING_BONDS metric signal:

- prior: `STAFF_COUNT OR EMPLOYMENT_BOND`
- current: `STAFF_COUNT AND EMPLOYMENT_BOND`
- required scope: NETWORK.

Expected canonical transition:

- before: 36 answerable / 2 partial / 0 gaps
- after: 37 answerable / 1 partial / 0 gaps
- only `TEACH_Q2` may change
- `EQUITY_Q1` remains partial.

The regression test explicitly removes each of the two required workforce metrics in turn and requires TEACH_Q2 to fall back to partial.

No serving, publication, schedule or recurrence is enabled by this task.
