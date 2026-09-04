# TASK 094 — Policy Budget Ledger T0

## Authorization

Owner authorized the structural redesign on 2026-09-04 with: **`autorizado`**.

This task is T0/offline only. It introduces no workflow, remote read, remote write, serving or publication.

## Objective

Represent a public budget as a reconstructible temporal event stream instead of treating one document snapshot as the budget itself.

The ledger separates:

- initial authorization;
- supplements;
- authorization cancellations;
- commitment (empenho);
- commitment cancellation;
- liquidation;
- liquidation cancellation;
- payment;
- payment cancellation.

## Budget identity

The ledger uses an exact multidimensional identity vector:

- entity;
- fiscal year;
- organization;
- unit;
- function;
- subfunction;
- program;
- action;
- subaction;
- economic category;
- expense group;
- application mode;
- expense nature;
- element;
- subelement;
- funding source;
- destination;
- fund;
- cost center;
- accounting key.

Only entity and fiscal year are structurally mandatory because source granularity varies. Missing dimensions remain null; they are not inferred.

The exact identity receives a SHA-256. A changed dimension produces a different identity.

## Policy boundary

Budget identity and policy attribution are deliberately separate.

A budget row/event can be exactly identified without proving that it belongs to a policy.

Text similarity or amount equality alone never creates a policy link.

## Canonical-state rule

By default only `PROVEN` and `CORROBORATED` events affect the canonical snapshot.

`CANDIDATE`, `UNKNOWN`, `CONFLICTED` and `REFUTED` events remain preserved but excluded from the canonical monetary state until explicit promotion.

## Accounting invariants

At every applied event:

- no net stage may become negative;
- net committed cannot exceed current authorization;
- net liquidated cannot exceed net committed;
- net paid cannot exceed net liquidated.

Cancellations are explicit event types; negative monetary events are forbidden.

## Temporal reconstruction

`reconstruct_budget_snapshot(..., as_of=...)` can rebuild the state at a selected date and returns:

- current authorization;
- committed;
- liquidated;
- paid;
- available authorization;
- applied event IDs;
- excluded noncanonical event IDs;
- future events beyond the cutoff;
- event-by-event history.

No causal or policy attribution is inferred by the snapshot.

## Integration with TASK 093

Each validated ledger event can be projected as a generic `BUDGET_EVENT` research entity.

The ledger therefore becomes a financial/temporal layer beneath the generic research ontology rather than a separate parallel model.

## Files

- `config/policy_budget_ledger.v1.json`
- `robo_dados_publicos/research/budget_ledger.py`
- `tests/test_task_094_policy_budget_ledger.py`

## Effects

All remote-effect classes remain zero.

## Next structural task

TASK 095 will define source roles, evidence semantics, inference provenance and negative-evidence handling so the ledger and research graph can distinguish what a source is allowed to prove.
