# TASK 175 — unified observatory question-to-evidence query layer

## Objective

Turn the observatory from a collection of mature source-specific modules into one deterministic planning layer for user questions.

TASK 175 does not answer from the LLM's memory and does not fetch new data. It decides what evidence a later answer must use.

## Inputs

- canonical domain id from `observatory_question_ontology.v1.json`;
- optional question text as routing context only;
- optional timeframe;
- optional school/unit;
- optional policy/service;
- optional desired granularity.

Question text is never a numeric truth source.

## Output

`UNIFIED_OBSERVATORY_QUERY_PLAN_V1` includes:

- domain and metric classes;
- NUMERIC / DOCUMENT / HYBRID route mode;
- ordered source plan;
- family maturity plus exact route/schema overrides;
- deterministic numeric candidates;
- query-ready numeric sources;
- document/RAG explanation candidates;
- allowed join strengths;
- explicit gaps;
- evidence and causal guards;
- answer contract.

## Reuse

The new router extends the existing routing architecture. It retains the legacy `router.rules.route_query` result only as a compatibility hint; the observatory domain contract controls the final plan.

It consumes:

- observatory question ontology;
- source-family maturity registry;
- source-role evidence semantics;
- budget/fiscal source map;
- exact capabilities proven by TASK 172;
- JOM maturity and semantic outputs from TASKS 171/174;
- accounting semantics from TASK 173.

## Readiness semantics

Family maturity and exact route/schema proof remain separate.

For example, the current TCE-SP 2026 route may be query-ready for its exact proven schema while the broad TCE family remains supervised rather than globally auto-ingest-ready.

Blocked or unregistered sources remain visible as explicit gaps.

## Hybrid examples

School reform:
JOM + procurement/contracts + TCE accounting + Censo infrastructure.

School transport:
JOM + procurement/PNCP + TCE/SIOPE + Censo denominator/context.

School meals:
JOM + procurement/PNCP + TCE/SIOPE + enrollment.

Policy/norm change:
JOM/CME/legislation + PPA/LDO/LOA; accounting only when a separate bridge exists.

Personnel:
Censo + JOM + RGF/SICONFI + personnel transparency where available.

## Join rules

Strong:
exact accounting/administrative identifiers such as empenho, source expense id, exact contract/process/PNCP id and explicit CNPJ when the source exposes it.

Contextual:
year, program, action, funding source, application and school/unit.

Weak:
amount, date proximity, object/history text and semantic similarity.

Weak joins never create identity.

## Answer contract

When evidence exists, the planned answer should contain:

fact/number -> time reference -> comparison/trend -> plain-language explanation -> source/provenance -> caution/limit.

## Remote effects

T0/offline only:

- network 0;
- Drive read/write 0;
- serving/publication 0;
- schedule/recurrence 0.
