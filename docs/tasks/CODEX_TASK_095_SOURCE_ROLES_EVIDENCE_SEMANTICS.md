# TASK 095 — source roles, evidence semantics and negative evidence

## Scope

T0/offline structural design only. No workflow, credential, network, Drive operation, persistence, serving or publication capability is added.

## Objective

Teach the research layer that different documents can prove different kinds of claims.

A source is no longer merely "evidence". It has an epistemic role that limits the maximum claim status it can support.

## Source roles

- DOCTRINAL_SOURCE
- ACADEMIC_RESEARCH
- NORMATIVE_PRIMARY
- PLANNING_PRIMARY
- BUDGET_PRIMARY
- ACCOUNTING_EXECUTION_PRIMARY
- ADMINISTRATIVE_PRIMARY
- STATISTICAL_PRIMARY
- SECONDARY_AGGREGATOR

Examples of the intended boundary:

- doctrine can support conceptual interpretation but cannot prove that Limeira executed a specific expense;
- a norm can prove a legal/normative proposition but not that implementation occurred;
- a PPA can prove planning intent/target but not payment;
- a LOA can prove budget authorization but not liquidation/payment;
- accounting execution can prove execution-stage facts;
- statistical primary data can prove an observed metric but not causal effect;
- secondary aggregators can corroborate selected factual domains but do not directly promote them to PROVEN.

## Claim domains

The contract distinguishes:

- CONCEPTUAL_INTERPRETATION
- ACADEMIC_FINDING
- LEGAL_NORM
- PLANNING_INTENT
- BUDGET_AUTHORIZATION
- ACCOUNTING_EXECUTION
- ADMINISTRATIVE_EVENT
- STATISTICAL_OBSERVATION
- POLICY_LINKAGE
- SEARCH_RESULT
- CAUSAL_EFFECT

## Evidence kinds

- DIRECT_EXPLICIT
- DETERMINISTIC_DERIVATION
- ANALYTICAL_INFERENCE
- NEGATIVE_SEARCH_OBSERVATION

Direct and reproducible deterministic evidence can reach PROVEN when the source role also permits it.

Analytical inference is capped at CANDIDATE by this layer.

Causal effect is also capped at CANDIDATE: this semantics layer does not replace a causal research design.

## Negative evidence

A bounded search result is stored independently.

If a search returns NO_MATCH, the research system may prove:

> no match was found within the declared scope, method and coverage.

It may **not** promote that observation into:

> the searched object does not exist.

Thus:

`NO_MATCH != NONEXISTENCE`

The negative-evidence record preserves target, scope, method, coverage, exhaustiveness declaration and result.

This generalizes the fail-closed interpretation already used in F01 and the contracts track.

## Search-result distinction

A `NEGATIVE_SEARCH_OBSERVATION` may reach PROVEN only in the dedicated `SEARCH_RESULT` domain.

That PROVEN status applies to the observation of the search itself. It cannot be reused as PROVEN evidence of accounting execution, policy linkage or nonexistence.

## Integration

TASK 093 supplies generic ENTITY / RELATION / CLAIM / EVIDENCE semantics.

TASK 094 supplies exact temporal budget facts.

TASK 095 determines what each source/evidence type is epistemically allowed to support.

Together these prevent a technically valid extraction from becoming an overclaimed research conclusion.

## Governance

This is a local library/config tested by the existing CI_OFFLINE suite. It adds no execution gate or remote capability.

## Next task

TASK 096 will build the first EITI-Limeira offline crosswalk/bundle from already versioned repository evidence only. It must not perform a Drive read, web request or new source acquisition.
