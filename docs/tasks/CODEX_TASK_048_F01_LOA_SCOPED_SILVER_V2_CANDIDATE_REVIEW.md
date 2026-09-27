# CODEX TASK 048 — LOA scoped Silver v2 candidate review

## Purpose
Review, entirely offline, the smallest deterministic LOA Silver v2 candidate that carries forward the persisted TASK 040 v1 and adds only the explicit budget fields directly resolved by TASK 045.

## Added evidence
For `12.362.2001.2690` the candidate records the explicit budget unit `10.04.00 ENSINO MEDIO E SUPERIOR`, appropriation R$ 6,152,000, expense-group split R$ 6,142,000 current + R$ 10,000 investment, and source split R$ 943,000 Tesouro + R$ 5,209,000 state-linked.

For `12.306.2001.2720` it records budget unit `10.05.00 ALIMENTACAO ESCOLAR`, direct-visual appropriation R$ 28,000,000, expense-group split R$ 27,999,000 current + R$ 1,000 investment, and source split R$ 8,680,000 Tesouro + R$ 19,320,000 federal-linked.

The material text/visual divergence remains first-class evidence: the extracted text reports R$ 29,000,000 on pages 173–174 while the rendered primary source shows R$ 28,000,000. No silent repair is permitted.

## Guardrails
- v1 remains immutable and preserved;
- no complete-LOA claim;
- missing expense nature remains `UNKNOWN_NOT_EXPLICIT_ON_SELECTED_PAGES`;
- LOA enactment does not prove committed/liquidated/paid execution;
- actions 2690 and 2720 remain `eiti_specific=false`;
- Program 2001 or generic action totals cannot be attributed to EITI;
- EITI financial identity remains `EVIDENCIA_INSUFICIENTE`;
- no Gold, serving or publication.

## Decision
`READY_FOR_SCOPED_LOA_SILVER_V2_CREATE_ONLY_SEPARATE_AUTH_REQUIRED`

Canonical candidate SHA-256:
`9f04a7202d03a58687d5382565777f15887b056ba28c65d9c01e226af7d3ef25`

Future create-only target:
`F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE__9f04a7202d03__silver_v2.json`

This task performs no Drive read/write, source network, OCR, Bronze, Silver persistence, Gold, serving or publication.
