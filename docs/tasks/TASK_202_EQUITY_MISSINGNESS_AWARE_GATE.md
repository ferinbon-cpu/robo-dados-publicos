# TASK 202 — EQUITY_Q1 missingness-aware semantic correction

## Current evidence after TASK 199G

TASK 199G independently promoted five previously held schools using multi-anchor official spatial triangulation. The territorial crosswalk is now 64/69 active municipal schools, or 92.75%, with five cases still explicitly HELD.

The remaining five have genuine boundary, anchor, current-address or relocation ambiguity. They are not promoted here.

## Why EQUITY_Q1 was still partial

EQUITY_Q1 asks whether inequalities exist by social context, race/color, disability **or** territory. Its metric signal already requires and has PPI_SHARE, INSE and SPECIAL_EDUCATION_ENROLLMENT. TERRITORY_PROFILE already contains official census-sector context for 64 schools.

V3 nevertheless required `SCHOOL_TO_SECTOR_LINK_FULL_NETWORK`, making the entire broad equity question depend on literal 69/69 geocoding. That gate is stricter than the question and creates pressure to weaken geographic identity rules.

## V4 correction

V1, V2 and V3 remain immutable. TASK 202 adds a V4 overlay changing only EQUITY_CONTEXT.

The three equity metrics remain mandatory. The territory signal still requires `CENSUS_SECTOR_CONTEXT`, but replaces the full-network capability with:

`SCHOOL_TO_SECTOR_LINK_SUBSTANTIAL_COVERAGE_WITH_EXPLICIT_MISSINGNESS`

The capability requires denominator=69, at least 64 strong links, coverage >=92%, exactly five HELD schools, the exact held roster pinned to TASK 199G evidence, linked/held disjointness, and the explicit absence of a full-network claim.

## Claim boundaries

This does **not** claim 69/69 geocoding. It does not claim that the census sector around a school is the socioeconomic profile of enrolled students. It does not authorize a complete territorial ranking of all 69 schools.

It recognizes that material equity evidence can be answerable while geographic missingness remains explicit and auditable.

## Expected answerability transition

37 answerable / 1 partial / 0 gaps -> 38 answerable / 0 partial / 0 gaps.

Exactly EQUITY_Q1 may change.

Fail-closed tests remove each equity metric and each required territory capability, mutate coverage/held contracts, and verify that V3 still reproduces the historical 37/1 state.

No serving, publication, schedule or recurrence is enabled.
