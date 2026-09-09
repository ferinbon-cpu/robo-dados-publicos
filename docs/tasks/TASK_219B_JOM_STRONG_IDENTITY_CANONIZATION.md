# TASK 219B — Full 2026 JOM strong-identity canonization

Issue: #691

## Goal

Canonize the successful TASK 219A runtime without performing any new public-source read.

Source runtime:

- run: `34354027245`
- artifact: `10105583802`
- 87/87 pinned Jornal Oficial PDFs validated
- 2,408 sanitized events
- 940 procurement-shaped events
- 395 strong administrative anchor rows across 330 events
- zero document failures

TASK 219B preserves the exact 395-row strong-anchor file, reconstructs the legacy TASK 216 anchor set from the existing 303-event fixture, and produces a combined identity-grain index.

## Identity semantics

The identifier grain is:

`anchor_type + normalized administrative identifier`

Allowed types remain:

- exact complete process identifier
- exact complete typed contract identifier

The following are explicitly not identity:

- supplier CNPJ by itself
- amount similarity
- date proximity
- object/history text
- semantic similarity
- incomplete administrative identifiers

A process may legitimately span multiple suppliers, especially registry-price or multi-lot proceedings. A contract identifier with conflicting suppliers is treated as a blocker; TASK 219B expects zero such conflicts in the new corpus.

## Expected result

- legacy TASK 216 anchor rows: 54
- new TASK 219A anchor rows: 395
- combined anchor rows: 449
- legacy unique identities: 42
- new-corpus unique identities: 270
- overlap: 9
- genuinely new identities: 261
  - 165 process identities
  - 96 contract identities
- combined unique identities: 303
  - 195 processes
  - 108 contracts

This task does **not** prove a JOM↔PNCP↔TCE chain and does not promote any canonical question. Contextual coverage remains 34/38.

## Next gate

Only after this canonization is merged should a fresh bounded PNCP exact-identifier bridge be considered. That future live read requires a fresh authorization token pinned to its merged implementation SHA.
