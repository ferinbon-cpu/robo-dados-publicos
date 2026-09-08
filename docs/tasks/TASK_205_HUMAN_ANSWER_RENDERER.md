# TASK 205 — deterministic human answer renderer

## Goal

Convert the 38 canonical TASK204 renderable observatory packets into deterministic, human-facing answer cards and Markdown without adding an inferential or generative truth layer.

The rule is inherited from TASK 100:

`FORMATTING_ALLOWED_INFERENCE_FORBIDDEN`.

## Input boundary

- canonical main base: `fa6a4d8bd4c04d28986266d1ba2f079b43dbc70a`
- semantic answerability: 38/38
- ontology-summary renderability: 38/38
- backing: 27 local-record + 11 bounded source-pinned projection questions
- TASK204 source snapshots remain canonical.

## Answer contract

Every card contains:

1. NUMBER_OR_FACT
2. TIME_REFERENCE
3. COMPARISON_OR_TREND
4. PLAIN_LANGUAGE_EXPLANATION
5. SOURCE_AND_PROVENANCE
6. CAUTION_OR_LIMIT

Comparison is emitted only when the structured packet provides a deterministic comparison. Otherwise the card contains the explicit marker `NOT_AVAILABLE_IN_BOUNDED_PACKET`.

## Selection semantics

For locally backed questions, rows are selected using the current canonical answerability recipe for that question. The renderer does not use all records in the domain indiscriminately.

For TASK204 projection-backed questions, the renderer copies already-validated bounded projection values. It does not recompute source ledgers and does not replace the remote source snapshot.

## Plain language boundary

The explanation field is a fixed, reviewed domain template. It may explain what the evidence means and preserve category boundaries, but it may not introduce a new numeric claim, causal claim, administrative identity, financial identity or implementation claim.

## Fail-closed guards

- no LLM call;
- no numeric invention;
- no causal-effect creation;
- revenue != expenditure;
- restos payable != current-year expenditure;
- planning != execution;
- capability metadata != numeric truth;
- selected projection rankings are not exhaustive;
- missing comparison remains explicit;
- provenance and caution remain visible;
- identical input produces identical card and Markdown hashes.

## Outputs

- `OBSERVATORY_HUMAN_ANSWER_CARD_V1`
- `OBSERVATORY_HUMAN_ANSWER_RENDER_V1`
- `OBSERVATORY_HUMAN_ANSWER_BUNDLE_V1`

No Drive write, serving, publication, schedule or recurrence is introduced by the runtime.
