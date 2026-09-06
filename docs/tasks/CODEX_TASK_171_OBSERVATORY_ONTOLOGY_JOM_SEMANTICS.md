# TASK 171 — Observatory question ontology, budget map and JOM semantic autodifferentiation

## Objective

Re-anchor ROBO_DADOS_PUBLICOS on its already established scope: a general municipal public-data observatory for Limeira/SP.

Education/SIOPE remains a major module. EITI remains a demanding analytic use case. Neither is the global inclusion filter.

## Added architecture

### Observatory question ontology

`config/observatory_question_ontology.v1.json`

Defines 15 user-facing domains around questions a municipal teacher, school manager, council member, researcher or citizen may ask. Each domain maps questions to metrics, source families and evidence roles.

The answer contract prefers, when available:

`number/fact -> time reference -> comparison/trend -> plain-language explanation -> source/provenance -> caution/limit`.

### Budget/fiscal source acquisition map

`config/budget_fiscal_source_acquisition_map.v1.json`

Separates planning, budget authorization, commitment, liquidation, payment, procurement and control reconciliation. It preserves DIRECT_JSON_FIRST and records which source families already have proven machine-readable contracts versus which still need exact official route discovery.

The current missing-route priority is:

1. Limeira TDA;
2. SICONFI/STN RREO/RGF;
3. current TCE-SP machine-readable route for 2020+;
4. recurring FUNDEB machine-readable source;
5. other municipal fiscal exports.

### Jornal Oficial semantic facets

`config/jornal_semantic_layers.v1.json`
`robo_dados_publicos/journal/semantic_layers.py`

The existing conservative act parser remains unchanged. A new second-stage classifier now treats four dimensions independently:

- document/event type;
- policy domain;
- evidence layer;
- financial stage.

Education-specific topics are an additional facet.

A single event can therefore be, for example:

- event type: DECRETO;
- domain: EDUCATION;
- layers: NORMATIVE + BUDGET_AUTHORIZATION + INFRASTRUCTURE;
- financial stage: AUTHORIZATION;
- education topic: FULL_TIME_EDUCATION.

This is classification, not identity promotion.

## JOM pipeline integration

The existing `JournalPdfProcessor` now emits:

`event_semantics_gold.jsonl`

alongside:

- `events_gold.jsonl`;
- `pages_silver.jsonl`;
- `chunks_rag.jsonl`;
- reconciliation tasks.

Semantic rows are linked by `event_id` and preserve source/provenance fields.

## Epistemic guards

- type of act != subject != evidence layer != financial stage;
- one JOM event may have multiple semantic facets;
- JOM procurement/contract publication != payment;
- explicit payment/accounting wording in JOM creates at most a payment evidence candidate;
- semantic classification never proves policy identity or financial identity;
- PPA != execution;
- LOA authorization != commitment/liquidation/payment;
- unknown domains/layers remain UNCLASSIFIED/REVIEW.

## Remote effects

TASK 171 is T0/offline only:

- network: 0;
- Drive reads/writes: 0;
- serving/publication: 0;
- recurrence/schedule: 0.

## Next task

After CI and merge, create a separate bounded source discovery/acquisition task for the missing official machine-readable routes. That task must use exact source/host/purpose scopes and DIRECT_JSON_FIRST.
