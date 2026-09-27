# TASK 032 — bounded acquisition gate for F01 Jornal originals

## Objective
Implement, without executing live I/O, the exact bounded operation that can place the three full Jornal Oficial editions under F01 custody after a fresh owner authorization bound to the final reviewed implementation SHA.

## Exact documents
- JOM 7024 — 08/07/2025 — LDO Lei 7.141/2025 — 79 pages.
- JOM 7119 — 15/11/2025 — PPA Lei 7.213/2025 — 107 pages.
- JOM 7127 — 29/11/2025 — LOA Lei 7.223/2025 — 631 pages.

The exact three `ecrie.com.br` PDF URLs and deterministic target filenames are pinned in `config/budget_laws_journal_bounded_acquisition.v1.json`. No alternate URL discovery is allowed.

## Pre-write proof
The future authorized run must:
1. validate the live owner authorization before any remote dependency;
2. perform exactly three GET attempts, one exact URL per edition, with redirects disabled;
3. require HTTP 200, final URL identity, `application/pdf`, `%PDF-`, bounded bytes, SHA-256 and exact page count;
4. validate all three source PDFs before any Drive inventory/write;
5. perform one single-page inventory of the F01 target folder and require all three target names to be absent before the first create.

## Create/readback proof
Only after all preconditions pass may the run create the three PDFs, one per deterministic name, under F01. Each create is immediately followed by readback and exact byte/SHA-256/page-count verification.

The operation is not atomic. If a later create/readback fails after an earlier create succeeded, the result is a fail-closed partial-custody STOP with `owner_decision_required=true`. There is no automatic delete, cleanup, retry, replace or overwrite.

## What this task does not authorize
No OCR, parser, Bronze, Silver, Gold, serving, publication, schedule or recurrence. TASK 032 is implementation/review only and embeds no live authorization.

## Authorization contract
A real run requires a fresh owner authorization with:
- task `TASK_032_BUDGET_JOURNAL_BOUNDED_ACQUISITION`;
- repository and `main` branch identity;
- exact implementation SHA equal to the runtime SHA;
- exact source/target/operation;
- limits 3 GET / 1 Drive inventory / 3 create / 3 readback;
- all mutation-expansion and downstream flags false;
- `owner_authorized=true` and `consumed=false`.

A synthetic authorization is accepted only in `offline_test_mode` with non-network fake dependencies.
