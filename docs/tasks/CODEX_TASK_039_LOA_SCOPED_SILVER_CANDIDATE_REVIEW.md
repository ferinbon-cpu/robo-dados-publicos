# CODEX TASK 039 — LOA 2026 scoped Silver candidate review

Base: `68d37d9cc50ec062e3d9e514f2a2bfa666b52b22`

## Purpose
Review, entirely offline, whether the evidence accumulated in TASKS 036–038 is sufficient to define a **scoped** Silver candidate for JOM 7127 / Lei 7.223/2025 without claiming a complete LOA parse and without writing to Drive.

## Decision
`READY_FOR_SCOPED_SILVER_CREATE_ONLY_SEPARATE_AUTH_REQUIRED`

Candidate contract: `F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE_SILVER_V1`.

The candidate may carry only:
- exact source and legal-instrument identity;
- page-coverage/provenance ledger;
- directly source-validated action records on pages 171 and 174;
- validated summaries and hashes of the numeric tables on pages 480 and 481;
- explicit exclusions, QA status and upstream evidence pins.

It must not carry as source truth:
- the 6,060 OCR monetary candidates from TASK 036;
- OCR text from pages 475–479 as canonical source text;
- a complete-LOA-parse claim;
- attribution of Program 2001 totals to EITI;
- EITI financial identity;
- MDE/Fundeb compliance or audit conclusions.

## Governance
This task is T0/offline and has zero source network, Drive read/write, OCR, Bronze, Silver, Gold, serving or publication effects. F01 remains `NOT_SILVER`.

A future write to `02_SILVER` is a separate create-only operation and requires fresh explicit owner authorization pinned to the reviewed implementation/main SHA. Gold, serving and publication remain outside that boundary.
