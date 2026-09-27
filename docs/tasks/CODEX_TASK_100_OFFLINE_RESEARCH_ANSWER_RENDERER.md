# TASK 100 — Offline Research Answer Renderer

## Scope

T0/offline only.

No network, Drive access, source acquisition, OCR, LLM call, serving, publication, retry, recurrence or schedule is introduced.

## Objective

Convert an already validated RESEARCH_QUERY_RESULT_V1 packet into deterministic human-readable Markdown without changing the epistemic content of the packet.

TASK 099 created the evidence-bounded query packet. TASK 100 is deliberately only a renderer downstream of that boundary.

## Core rule

Formatting is allowed; inference is not.

The renderer may add headings, labels and deterministic ordering. It may not:

- rewrite claim text;
- promote or demote a claim status;
- infer financial identity;
- infer transaction identity;
- infer implementation from planning;
- infer outcome from target;
- infer causal effect;
- hide supplied UNKNOWN, CANDIDATE or CONFLICTED gaps;
- call an LLM.

## Markdown sections

The fixed order is:

1. Consulta
2. Síntese epistemológica
3. Afirmações
4. Matriz de institucionalização
5. Lacunas de institucionalização
6. Lacunas históricas de aquisição
7. Salvaguardas

The renderer emits a SHA-256 over the final Markdown so identical input can be checked for deterministic output.

## EITI-Limeira first integration

The first integration consumes a POLICY_STATUS_PACKET for POLICY:EITI_LIMEIRA.

The rendered answer must visibly preserve:

- CLAIM:EITI_FINANCIAL_IDENTITY as UNKNOWN;
- budgetary_policy_identity as UNKNOWN;
- transaction_execution_identity as UNKNOWN;
- outcome_effect as UNKNOWN;
- the 2018-2021 historical PPA acquisition gap;
- the 2022-2025 historical PPA acquisition gap;
- source document identities and evidence locators for evidence-bearing claims.

No sentence is generated to bridge those gaps.

## Fail-closed boundary

Rendering stops if the upstream packet:

- is not RESEARCH_QUERY_RESULT_V1;
- reports any status promotion;
- reports financial identity creation;
- reports causal-effect creation;
- reports upstream natural-language generation;
- contains invalid claim statuses;
- contains malformed evidence locators;
- contains invalid institutionalization statuses;
- contains malformed historical acquisition requirements.

The renderer contract also requires the exact known set of remote-effect keys and requires every one to be false.

## Architectural position

The research path is now:

DIGEST → PROVENANCE → ONTOLOGY → SOURCE/EVIDENCE SEMANTICS → POLICY CROSSWALK → RESEARCH QUERY PACKET → DETERMINISTIC MARKDOWN ANSWER

This is the first researcher-facing representation. A future prose layer may exist later, but it must remain downstream and must be separately governed.

## Files

- config/research_answer_renderer.v1.json
- robo_dados_publicos/research/answer_renderer.py
- tests/test_task_100_offline_research_answer_renderer.py
- docs/evidence/TASK_100_OFFLINE_RESEARCH_ANSWER_RENDERER_0.8.0.json

## Next step

After CI and review, TASK 101 should add an offline command-line entry point that executes a predefined research query and writes the deterministic Markdown only to the ephemeral runner workspace or stdout. It must not persist to Drive, serving or publication without a separate later gate.
