# TASK 284 — Fail-closed month totals before JOM budget-credit collection

## Scope and reason

This is a **T0/offline repair**, prompted by an audit of Limeira's 2026 budget-credit evidence for the 2027 budget bill. The historical TASK217C/TASK219A baseline identifies 99 JOM editions through 2026-09-08, but a month-level completeness check against the current official archive must precede any inference that all acts were considered.

The known pinned fixture has 12 editions in January (2026-01-17..31), 12 in February (2026-02-11..28) and 12 in May (2026-05-15..30). The LOA audit records potentially greater totals shown by the archive. The historical `PASS` is preserved **as historical evidence**, not promoted into a fresh claim of exhaustive coverage.

## Failure mode

`JournalIndexParser.handle_data()` previously searched each HTML text node independently for `Total de itens encontrados: N`. Splitting label and number across DOM tags yielded `total_items=None`. `discover_month()` then returned `PASS_DISCOVERY` whenever pagination was exhausted, **even with no observed authoritative total**.

## Change

- Reconstruct the total label across HTML data-node boundaries with a bounded 512-character tail.
- Require at least one observed, unambiguous source total.
- Require count of deduplicated month editions to equal that observed total.
- Reject conflicting reported totals across pages.
- Keep the existing portal-declared-pagination-only and max-page behavior.
- Return `PARTIAL_DISCOVERY_TOTAL_UNOBSERVABLE`, `PARTIAL_DISCOVERY_TOTAL_CONFLICT` or `PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED` rather than a success on uncertain evidence.

## Offline test contract

`python -m unittest tests.test_task_284_jom_month_total_integrity -v`

Regression fixtures simulate a January page with 22 items reported but only 12 visible, a label split by HTML tags, no total, conflicting page totals, a correct matched total, and overcount. These are **synthetic tests**, not source-live proofs.

Existing tests and CI must be run before merge. The PR does not execute live GET, download PDFs, modify Drive/Bronze, publish data, change policy, or authorize a subsequent runtime.

## Separate next gate

After tests pass and owner review, a new bounded official-index discovery gate may be designed for **January 2026**, with a one-month limit, no PDFs, no Drive writes, no publication, no recurrence and one explicitly approved live attempt pinned to the reviewed implementation SHA. Its evidence must reconcile the official reported total, not only the first page.

Only after completing the inventory should separate T1 PDF acquisition and T2 create-only custody gates be considered for budget decree annexes I/II. The T0 budget ledger remains separate from publication and accounting execution proof.

## Source pointers

- `AGENTS.md`, `config/automation_policy.v1.json`.
- `robo_dados_publicos/journal/official.py`.
- `docs/evidence/TASK_217C_JOM_2026_DISCOVERY_CANONICAL_RESULT_0.8.0.json`.
- `docs/evidence/fixtures/task219/TASK_219A_CANONICAL_87_DOCUMENT_TARGETS.csv`.
- `docs/tasks/TASK_219A_JOM_GENERAL_EVENT_REDIGEST_CARRIER.md`.
- `docs/tasks/TASK_219B_JOM_STRONG_IDENTITY_CANONIZATION.md`.

**No retrospective mutation:** prior discovery artifacts and canonical snapshots are neither deleted nor silently rewritten. A new current-state proof must be separately acquired.
