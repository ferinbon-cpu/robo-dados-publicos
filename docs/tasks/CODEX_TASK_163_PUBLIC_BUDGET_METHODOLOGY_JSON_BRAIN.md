# TASK 163 — Public budget methodology JSON brain

## Goal

Turn the project's public-budget methodology into machine-readable JSON rather than leaving it only in prose, while absorbing the useful conceptual grammar of James Giacomoni's *Orçamento Público* (18th edition) without persisting copyrighted full text.

This task is methodology only. It does not ingest a new municipal amount, create an EITI financial identity, or change serving/publication.

## Knowledge architecture

Three layers are deliberately separated:

1. **ACADEMIC / METHODOLOGICAL** — explains concepts and cautions;
2. **OFFICIAL NORMATIVE** — proves dated legal/regulatory semantics;
3. **EMPIRICAL PRIMARY** — proves observed planning, authorization, procurement, accounting, contract or payment facts.

An academic source cannot prove that a current legal rule is still in force and cannot prove a municipal transaction.

## JSON engineering

The methodology is split into three contracts.

### 1. `config/public_budget_methodology.v1.json`

Contains:

- public budget as a planning/programming/management/control instrument;
- budget-program logic;
- PPA, LDO and LOA roles;
- institutional, functional, programmatic, economic and funding classifications;
- evidence stages from planning to payment;
- amount semantics;
- calculation recipes;
- policy-financial identity chain;
- forbidden promotions.

Key guardrails include:

`PPA != execution`

`LOA authorization != commitment/liquidation/payment`

`PNCP procurement != payment`

`program total != specific policy budget`

`nominal change != real change`

`spending != policy effect`

### 2. `config/public_budget_observation_contract.v1.json`

Every future budget observation should be normalized with:

- source role/family/authority;
- entity and period scope;
- evidence stage;
- amount + explicit semantic;
- five classification dimensions;
- stable administrative keys;
- policy-linkage status and basis;
- provenance;
- quality/anomaly state.

Missing classifications are `UNKNOWN_NOT_INFERRED`, not guessed.

### 3. `config/public_budget_question_router.v1.json`

Routes the analytical question to the source capable of answering it.

Examples:

- planned? → PPA;
- annual priority? → LDO;
- authorized? → LOA;
- procured/contracted? → PNCP/contract;
- committed/liquidated/paid? → accounting execution source;
- policy-specific financial identity? → cross-source chain with stable keys;
- causal effect? → separate causal research design, not budget data alone.

The router ends by naming the next source required to close an evidence gap rather than merely returning an opaque no-answer.

## Integration with existing robot semantics

This generalizes rules already present in F01, SIOPE, the EITI crosswalk and the PNCP discovery work.

For EITI-Limeira the target chain remains:

`policy/indicator → program → action/subaction → unit → funding → economic nature → appropriation → procurement/contract when applicable → commitment → liquidation → payment`

Each link must preserve its own evidence semantics.

## Copyright and freshness

No book text is stored. Only paraphrased methodological concepts and bibliographic metadata are encoded.

The methodology also carries a freshness rule: Giacomoni guides interpretation, but current law, current classifications and current source semantics must be established from official sources applicable to the relevant date.

## Effects

- public network: 0;
- Drive read/write: 0;
- new municipal source acquisition: 0;
- Bronze/Silver/Gold: 0;
- financial identity promotion: 0;
- serving/publication: 0.

## Next integration

Future digest adapters should emit `PUBLIC_BUDGET_OBSERVATION_CONTRACT_V1` packets before budget facts are used by research queries. The question router can then decide whether the available sources are sufficient or which source family is missing.
