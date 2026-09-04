# TASK 093 — generic research ontology and schema

## Authorization

Owner authorized the structural redesign on 2026-09-04 with: **`autorizado`**.

This task is T0/offline only. It introduces no workflow, no network capability and no remote write.

## Objective

Generalize the policy-specific terminology work already proven in TASK 055A into a reusable research semantics layer.

The central design decision is to keep four record kinds distinct:

1. **ENTITY** — a thing in the researched world;
2. **RELATION** — an asserted relationship between entities;
3. **CLAIM** — a research statement that may be tested;
4. **EVIDENCE** — a source-grounded support object.

CLAIM and EVIDENCE are deliberately **not** entity types.

## Generic entity types

- POLICY
- DOCUMENT
- PLAN
- PROGRAM
- ACTION
- BUDGET_EVENT
- EXPENSE
- CONTRACT
- PROVIDER
- DELIVERY
- ORGANIZATION
- TERRITORY
- INDICATOR

No policy name is hardcoded into the runtime schema. EITI-Limeira can use the schema later as one policy instance.

## Assertion statuses

- PROVEN
- CORROBORATED
- CANDIDATE
- UNKNOWN
- CONFLICTED
- REFUTED

PROVEN and CORROBORATED require evidence references.

A PROVEN claim cannot retain contradicting evidence. A CONFLICTED claim must preserve both supporting and contradicting evidence. REFUTED requires contradicting evidence.

## Referential integrity

A research bundle is accepted only when:

- every relation source and target exists;
- every claim subject exists;
- every evidence record points to a DOCUMENT entity;
- every evidence reference used by a relation or claim exists;
- IDs are typed and unique.

## Legacy compatibility

Existing semantics are preserved rather than replaced:

- TASK 055A remains the policy-specific EITI terminology layer;
- `EvidenceGraph` remains a valid legacy edge reader;
- financial identity A/B/C/D maps into the generic layer as:
  - A -> PROVEN
  - B -> CORROBORATED
  - C -> CANDIDATE
  - D -> UNKNOWN
- upstream `EVIDENCIA_INSUFICIENTE` remains valid and is not silently promoted.

## Anti-overreach

The generic ontology does not create financial identity from textual similarity.

TASK 055A's rule that financial/accounting terms alone do not prove EITI attribution remains intact and will be generalized further in TASK 095.

## Files

- `config/research_ontology.v1.json`
- `robo_dados_publicos/research/__init__.py`
- `robo_dados_publicos/research/ontology.py`
- `tests/test_task_093_research_ontology.py`

## Effects

All remote-effect classes are zero.

## Next structural task

TASK 094 will add the temporal Policy Budget Ledger over this ontology, representing authorization, amendments and execution stages without assuming that a document snapshot is the budget itself.
