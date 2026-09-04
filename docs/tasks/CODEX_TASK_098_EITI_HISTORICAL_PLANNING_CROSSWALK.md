# TASK 098 — EITI-Limeira historical planning crosswalk

## Scope

T0/offline only. This task uses evidence already versioned in the repository and performs no new source acquisition, Drive content read, public-network source read, OCR, remote persistence, serving or publication.

## Objective

Extend the EITI-Limeira planning view backward across the three municipal PPA periods relevant to the research horizon:

- 2018–2021;
- 2022–2025;
- 2026–2029.

The task is explicitly a **coverage/provenance crosswalk**, not a claim that all three PPAs already have equally strong evidence in the repository.

## What the repository actually preserves

### PPA 2018–2021

TASK 055A preserves the local planning alias:

`escolas com programas em tempo integral`

Its validator explicitly tags this as the PPA2018 alias.

However, the current repository does not preserve, for this signal, a primary PPA document entity, stable source hash, typed page locator and direct text/visual evidence.

Therefore:

- planning signal: `CANDIDATE`;
- direct EITI policy link: `UNKNOWN`;
- financial identity: `UNKNOWN`.

The alias is a useful historical retrieval key, not direct primary evidence.

### PPA 2022–2025

TASK 055A preserves the local planning alias:

`indice de alunos em Educacao Integral`

Its validator explicitly tags this as the PPA2022 alias.

Again, the current repository does not preserve the primary PPA document identity + hash + typed locator required to elevate this historical signal to direct planning proof.

Therefore:

- planning signal: `CANDIDATE`;
- direct EITI policy link: `UNKNOWN`;
- financial identity: `UNKNOWN`.

### PPA 2026–2029

This period has a materially stronger chain:

- Lei 7.213/2025 / PPA 2026–2029;
- primary full Jornal Oficial edition 7119 source;
- stable source SHA-256;
- Program 2001 and the `Índice de Alunos em Educação Integral` validated on JOM PDF page 15;
- TASK 097 now types that coordinate as `JOURNAL_EDITION_PDF_PAGE` and prefers it for new citations.

Therefore:

- planning signal in the PPA: `PROVEN`;
- correspondence between the policy and Program 2001: `CORROBORATED`;
- financial identity: `UNKNOWN`.

The last status is intentionally unchanged: planning correspondence does not prove that the total Program 2001 budget belongs to EITI.

## Longitudinal conclusion allowed now

The repository contains a **candidate terminology trajectory** across all three PPA periods, but only the current PPA has direct primary planning evidence in the versioned corpus.

Therefore:

`THREE_PPA_PERIOD_POLICY_CONTINUITY = CANDIDATE`

and:

`THREE_PPA_PERIOD_BUDGETARY_PERSISTENCE = UNKNOWN`

This must not overwrite the distinct TASK 096 finding:

`NORMATIVE_PLANNING_PERSISTENCE = CORROBORATED`

That earlier finding is based on the already-evidenced 2021 CME → 2024 decree → PPA 2026–2029 → 2026 law continuity chain. TASK 098 preserves it and refuses to reinterpret it as proof of continuity across all three PPAs.

## Exact evidence gap before promotion

For each older PPA, promotion requires all of:

1. primary PPA document identity;
2. stable source hash or equivalent immutable identity;
3. typed locator for the relevant planning signal;
4. direct text or visual evidence.

Until these are present, the historical aliases remain retrieval hypotheses/signals.

## Scientific significance

This is a useful negative result. The new research architecture is now capable of distinguishing:

`we have seen this terminology in our prior validated research workflow`

from:

`the primary historical PPA evidence is currently versioned and can directly prove the claim`.

That distinction is exactly what prevents a dissertation-oriented system from laundering prior notes or search vocabulary into primary evidence.

## Forbidden promotions

TASK 098 forbids:

- TASK055A alias → proven primary planning fact;
- historical alias → financial identity;
- three aliases/signals → proven three-PPA policy continuity;
- planning signal → observed implementation;
- planning signal → causal outcome.

## Next decision

The next highest-value move is now sharply defined: acquire/recover the two missing historical PPA evidence packets **only if separately authorized**, preferably through the ephemeral digest architecture and with typed locator provenance from the start.

A separate offline alternative remains available: build the first `RESEARCH_QUERY` layer over TASK 096–098 before acquiring anything new.
