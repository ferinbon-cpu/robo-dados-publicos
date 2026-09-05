# TASK 164 — General methodology JSON engineering pattern

## Why

TASK 163 proved that methodology becomes more useful to the robot when it is encoded as machine-readable contracts rather than left only as prose.

This task makes that architecture a **robot-wide default pattern** for comparable methodological domains.

## Decision rule

Prefer methodology JSON engineering whenever a domain has reusable:

- concepts or ontology;
- evidence stages;
- source capabilities;
- observation normalization;
- allowed/forbidden inferences;
- stable cross-source identity rules;
- question routing;
- evidence-gap routing.

Prose-only notes remain acceptable for narrative context with no reusable machine-decision semantics.

## Required architecture

A conforming methodological domain contains:

1. domain methodology/ontology;
2. observation contract;
3. question/source router;
4. fail-closed validator;
5. regression tests;
6. sanitized evidence record.

It must also register itself in `config/methodology_domain_registry.v1.json`.

## General guards

The pattern forbids promoting:

- thematic similarity to identity;
- chronology to identity;
- search snippets to exhaustive evidence;
- transport failure to source no-match;
- aggregate records to individual identity without keys;
- academic references to current normative facts;
- missing fields to guessed values.

Default uncertainty remains `UNKNOWN_NOT_INFERRED` / `EVIDENCIA_INSUFICIENTE`.

## First conforming implementation

`PUBLIC_BUDGET`, created in TASK 163, is registered as the first reference implementation.

This means future comparable domains can reuse the same shape:

`ontology → observation contract → question/source router → inference guards → validator/tests`

without copying the budget-specific concepts.

## Scope

T0/offline only. No network, Drive, source acquisition, serving or publication.
