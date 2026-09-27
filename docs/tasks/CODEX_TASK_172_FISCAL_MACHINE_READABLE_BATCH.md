# TASK 172 — bounded observatory fiscal machine-readable acquisition batch

## Purpose

Turn the TASK 171 budget/fiscal source map into a bounded read-only acquisition batch for Limeira/SP.

This task is not EITI-specific. It builds reusable fiscal evidence for the general observatory.

## Source groups

### SICONFI / Tesouro — JSON

Four closed-year 2025 queries are pinned for Limeira (IBGE 3526902):

- RREO Anexo 01 — budget balance;
- RREO Anexo 02 — expenditure by function/subfunction;
- RREO Anexo 08 — MDE / education revenue and expenditure;
- RGF Anexo 01 — Executive personnel expenditure and fiscal limits.

### FNDE / FUNDEB — official CSV

The current 2026 FNDE publication explicitly offers CSV/XLSX/PDF rather than an exposed JSON endpoint for these tables. DIRECT_JSON_FIRST therefore falls back to the declared official CSV without reverse engineering.

Pinned datasets:

- total Fundeb revenue by entity;
- VAAR beneficiary/coefficient/forecast;
- VAAR attendance and learning indicators;
- final VAAT eligibility status.

Only Limeira rows/schema are allowed into sanitized evidence.

### TCE-SP — current official ZIP datasets

The current Limeira page explicitly publishes:

- 2026 detailed revenue;
- 2026 detailed expenses;
- 2026 restos a pagar.

The direct official ZIP URLs are pinned. The runtime inspects ZIP members in memory and emits only member names, headers, counts and bounded row samples. Raw ZIP/CSV bytes are never persisted by TASK 172.

### TDA Limeira — declared-route discovery only

The exact known public surface selected by TASK 170 is requested once with redirects disabled.

If the returned HTML explicitly declares an allowlisted JSON/API/CSV/XLSX/ZIP route, at most one exact follow-up GET may occur.

No endpoint guessing, form submission, JavaScript execution, authentication or CAPTCHA handling is permitted.

## Request budget

- 12 base GETs;
- at most 1 TDA declared-route follow-up;
- 13 GETs maximum;
- retry 0;
- redirect follow 0;
- 30 MB compressed/response bound;
- ZIP expansion bound 100 MB.

## Evidence semantics

Transport/HTTP failure is not NO_DATA.

An empty exact query is not global absence.

Procurement is not payment.

A TCE or SICONFI row does not automatically create policy identity.

This batch never promotes policy, financial or payment identity.

## Raw payload rule

No raw source body persists to Git, Drive or workflow artifacts. Only the sanitized TASK172 result may be retained.

## Authorization

The owner explicitly instructed the robot to proceed and retrieve the missing machine-readable URLs/categories. TASK 172 narrows that instruction to the exact official hosts, routes and GET-only request budget pinned in the contract.

## Next gate

After offline CI passes, execute the exact bounded batch once and pin only sanitized evidence. Then update source-family maturity based on observed route/schema results.
