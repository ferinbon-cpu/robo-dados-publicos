# TASK 099 — deterministic Research Query Layer

## Scope

T0/offline only. No network, Drive read/write, source acquisition, serving, publication or autonomous execution is introduced.

## Objective

Turn the validated research model into a queryable evidence packet **before** adding any natural-language answer generator.

The query engine does not read PDFs, search the web or infer new facts. It only reorganizes already validated entities, claims, evidence, institutionalization dimensions and acquisition gaps.

## Why this layer comes before conversational answers

A free-form language model could accidentally:

- hide UNKNOWN results;
- paraphrase a claim beyond its evidence;
- merge CANDIDATE and PROVEN facts;
- turn planning correspondence into financial identity;
- turn statistical association into causal effect.

TASK 099 therefore creates a deterministic intermediate answer packet first.

## Query types

- `CLAIM_AUDIT`
- `INSTITUTIONALIZATION_MATRIX`
- `EVIDENCE_GAPS`
- `POLICY_STATUS_PACKET`

## Output contract

The result can contain:

- exact subject entity;
- selected claims with their original text and unchanged epistemic status;
- supporting/contradicting evidence IDs;
- source document identity and source role;
- original evidence locator;
- institutionalization dimensions;
- explicit UNKNOWN/CANDIDATE/CONFLICTED gaps;
- historical acquisition gaps from TASK 098;
- deterministic result SHA-256.

The result also states explicitly that:

- status promotions performed = 0;
- financial identity created = false;
- causal effect created = false;
- natural-language generation performed = false.

## EITI-Limeira first integration

The first integration test queries `POLICY:EITI_LIMEIRA` using the TASK 096 research bundle and TASK 098 historical planning crosswalk.

The packet must preserve, among other things:

- `CLAIM:EITI_FINANCIAL_IDENTITY = UNKNOWN`;
- UNKNOWN/CANDIDATE institutionalization dimensions as visible gaps;
- the two missing historical PPA primary-evidence packets;
- source-document identities and locators for claims that have evidence.

This means a future narrative layer will receive both **what is known** and **what is not known**.

## Epistemic rule

Filtering is allowed; promotion is not.

For example, a query that asks for only PROVEN/CORROBORATED claims may omit an UNKNOWN claim from that specific view, but the engine cannot convert the UNKNOWN claim into a stronger status.

## Architectural position

The research pipeline is now:

`DIGEST → PROVENANCE → ONTOLOGY → BUDGET LEDGER → SOURCE/EVIDENCE SEMANTICS → POLICY CROSSWALK → RESEARCH QUERY PACKET`

A later natural-language layer may narrate this packet, but it must remain downstream of the deterministic evidence boundary.

## Files

- `config/research_query.v1.json`
- `robo_dados_publicos/research/query.py`
- `tests/test_task_099_research_query_layer.py`
- `docs/evidence/TASK_099_RESEARCH_QUERY_LAYER_0.8.0.json`

## Next step

After CI/review, TASK 100 may build a bounded offline **research answer renderer** that converts a query packet into human-readable Markdown while preserving statuses, evidence references and explicit uncertainty. It must not call an LLM, network or source connector in its first version.
