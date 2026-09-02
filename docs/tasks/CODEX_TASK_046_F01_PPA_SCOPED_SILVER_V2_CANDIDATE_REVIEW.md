# CODEX TASK 046 — F01 PPA scoped Silver v2 candidate review

## Purpose

TASK 046 is a T0/offline candidate review. It performs no Drive read or write and consumes no new owner authorization. It converts the directly resolved TASK 045 PPA action 2690 Ensino Médio e Superior row into a new immutable scoped-Silver candidate while preserving the already persisted v1.

## Upstream closure

- TASK 042 proves the existing PPA Silver v1 was persisted create-only and read back with SHA-256 `0cba09dade1c09224e549e817a859c63edb12a6fb0a5223c5ddb8aa5fe6dc730`.
- TASK 045 directly resolves the previously excluded `2690 / ENSINO MEDIO E SUPERIOR` row from primary-JOM page 15: function/subfunction 12/362; values 16.020, 15.520, 15.521, 15.522 and total 62.583 in R$ thousands mean/2025; physical targets 180, 190, 200 and 210.
- TASK 045 remains fail-closed on EITI financial identity.

## Silver v2 candidate

The candidate contract is `F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001_SILVER_V2` with scope `SCOPED_PROGRAM_2001_AND_SELECTED_ACTIONS_V2_NOT_COMPLETE_PPA_PARSE`.

It preserves the three v1 promoted rows and adds the directly resolved fourth row:

- 2690 Transporte Escolar — Educação Infantil — 12/365;
- 2690 Transporte Escolar — Ensino Fundamental — 12/361;
- 2690 Transporte Escolar — Ensino Médio e Superior — 12/362;
- 2720 Alimentação Escolar — multietapa — 12/306.

The old `PARSER_REVIEW_REQUIRED` row is moved into `resolved_review_rows`, with TASK 045 as the explicit resolution provenance. `excluded_review_rows` becomes empty for this scoped subset. This does not claim a complete PPA parse.

Canonical candidate SHA-256:

`1326c17b53b12064a04cc84123b0414ea77a3e80a8f62fe7cea0dc13eafdd280`

Proposed create-only target:

`F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001__1326c17b53b1__silver_v2.json`

The persisted v1 must remain untouched. No overwrite, replacement or delete is allowed.

## Governance

This task does not authorize persistence. Readiness is exactly:

`READY_FOR_SCOPED_SILVER_V2_CREATE_ONLY_SEPARATE_AUTH_REQUIRED`

EITI financial identity remains `EVIDENCIA_INSUFICIENTE`; all four selected actions remain `eiti_specific=false`. No Program 2001 total may be attributed to EITI, and no compliance, Gold, serving or publication conclusion is authorized.

Canonical result:

`PASS_TASK046_PPA_SCOPED_SILVER_V2_CANDIDATE_READY_NO_WRITE`
