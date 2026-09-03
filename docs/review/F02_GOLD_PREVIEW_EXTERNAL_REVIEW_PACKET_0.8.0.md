# F02 Gold preview — external adversarial review packet — 0.8.0

Status: **EXTERNAL_REVIEW_PENDING**

## Purpose

Ask an independent reviewer (intended reviewer: DeepSeek) to red-team the proposed F02 Gold boundary before any Gold persistence.

This artifact is a review packet, not evidence that an external review already occurred.

## Pinned prerequisites

- repository main before design: `d87f12c724bf2cc54d3e4de8fc180e9b5fe3c996`
- Jan–Apr Silver Drive ID: `1YmINhBM_jE2BnsYrVN5BuZMv5mE4ElmP`
- Jan–Apr Silver file SHA-256: `fe76d088143e61b9f0d5b1f611757bee924b5a2c95abae5fa5908b1b85b742f9`
- Jan–Apr Silver logical SHA-256: `72cc2cb29990809c043877ef8b0ef19d61f1064b093ef58fdb8fcc0f87386c81`
- Jan–May local Silver Drive ID: `10GNOfBEKJOgRNS0Ord2asR2UdwKc1gse`
- Jan–May local Silver file SHA-256: `ec1cb12dec7349cd391ed12ad9654d598136781acca0138bf6bc286f35827a42`
- Jan–May local Silver logical SHA-256: `d244b94d04f954c01771d9a416d97814fd163a0ecb693003677becfde06bf1a1`

## Proposed Gold semantic boundary

Gold may publish *typed observations*, but must never collapse unlike authorities or periods.

Required distinctions:

1. Jan–Apr RREO MDE: official primary source for the partial Jan–Apr MDE observation.
2. Jan–May MDE 25% local: local monitoring only; no same-period RREO exists.
3. Jan–Apr RREO FUNDEB professionals percentage: official RREO observation for that partial period.
4. Jan–May FUNDEB local professionals percentage: local monitoring only.

Every observation must carry:
- exact period;
- authority class;
- claim class;
- source Silver identity;
- whether an official MDE claim is allowed;
- whether an annual compliance claim is allowed.

No annual compliance conclusion is permitted from either partial period.

## Red-team questions

Classify each finding under `docs/EXTERNAL_REVIEW_ADJUDICATION_PROTOCOL.md`.

1. Can the design accidentally present 23.60% Jan–May local MDE as official MDE?
2. Can a consumer compare 24.27% Jan–Apr RREO and 23.60% Jan–May local without seeing the authority/period mismatch?
3. Can 88.67% Jan–Apr RREO and 96.99% Jan–May local be silently merged into one FUNDEB compliance series?
4. Can a missing RREO May value be imputed, forward-filled, inferred, or substituted?
5. Can any partial observation be upgraded to annual compliance?
6. Can tampered Silver bytes or logical hashes still produce Gold?
7. Can Gold preview cause Drive, serving, publication, site, network, overwrite, move, or delete effects?
8. Does the proposed schema preserve provenance strongly enough to reproduce every Gold observation?

## Current adjudicator pre-review

The architect/adjudicator treats items 1–8 as genuine hardening targets and intends to convert them into executable fail-closed invariants. This is **not** a substitute for external review.

## Operational boundary

This design phase authorizes no Gold persistence, serving, publication, site mutation, source network, Drive network, delete, move, overwrite, recurrence, or schedule.

A successful offline Gold preview is only evidence for a later, separately bounded Gold-persistence gate.
