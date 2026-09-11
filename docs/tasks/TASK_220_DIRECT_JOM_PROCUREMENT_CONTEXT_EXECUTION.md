# TASK 220 — direct JOM procurement contextual execution V9

## Goal

Close the remaining contextual procurement questions without forcing an accounting identity requirement onto claims that the Jornal Oficial already proves directly.

After TASK 219AA, contextual coverage is 35/38 and the remaining questions are:

- `PROC_Q1` — O que a prefeitura está comprando?
- `PROC_Q2` — Quem fornece, por quanto e por quanto tempo?
- `PROC_Q3` — Houve aditivo, apostilamento ou nova licitação?

## Scope

The bounded source scope is Limeira JOM `2026-01-01..2026-09-08`, with 99 official documents processed: 12 legacy detailed documents plus 87 later documents whose general-event processing completed 87/87 with zero failures.

The combined parsed corpus contains 2,711 event rows and 1,078 procurement-shaped publication rows. These counts are publication-event rows, **not unique purchases or contracts**.

## PROC_Q1

The executor can answer with direct procurement objects preserved in canonical JOM evidence, including examples such as:

- eventual acquisition of furniture;
- dental materials for municipal health units;
- contracting for CASM building reform;
- school water-reservoir maintenance;
- endoscopy-system rental.

It explicitly states that these are bounded examples and not an exhaustive 2026 inventory.

## Source-text custody

Canonical source fields preserve the retained JOM extraction literally. Human-readable cleanup, when needed, is stored separately as a display field and never replaces the canonical `object_text`. The validator continues to compare the canonical field byte-for-byte with the retained source fixture. This separation is what caught and corrected the CASM normalization mismatch during CI.

## PROC_Q2

The strongest same-publication case is Contract 45/2026, JOM edition 7210. The same official publication/contract record establishes:

- Med Doctor Acessórios Ltda.;
- CNPJ 37.457.979/0001-31;
- published contract value R$ 210,000.00;
- term of 12 months from the date stated in the service order;
- process 902.281/2025 and electronic auction 10/2026.

This answer does **not** import TDA/TCESP execution amounts. Published contract value is not converted into paid or executed value.

## PROC_Q3

The retained detailed JOM corpus proves positive signals for:

- 5 validated `TERMO_ADITIVO_CONTRATO` publication events in the retained August detailed corpus;
- a new procurement notice example, Dispensa/Edital 326/2026 for the CASM reform.

Apostilamentos remain an explicit evidence gap for the full 99-document scope. Missing detailed apostilamento evidence is not treated as proof of absence. Relationships between change events and contracts are not inferred without explicit reference.

## Context behavior

V9 supports municipal 2026 context, interpreted strictly as the bounded observed scope through 08/09/2026. It does not substitute another year, does not assign generic procurement events to a school and does not generalize arbitrary service/policy facets.

Non-procurement questions delegate unchanged to V8, preserving the TASK 219AA `CTRL_Q2` strong TDA bridge.

## Coverage decision

If validation and CI pass:

`35/38 -> 38/38`

This means all 38 canonical questions have a contextual execution path under their declared bounded semantics. It does **not** mean every real-world procurement fact is exhaustively collected or every future period is covered.

## Remote effects

TASK 220 is offline. It performs no public-source network access, Drive write, serving write, publication, schedule, recurrence, OCR or LLM call.
