# TASK 202 — EQUITY_Q1 missingness-aware semantic correction

## Why this task exists

After TASK 201, only EQUITY_Q1 remained partial:

> Existem desigualdades por contexto social, raça/cor, deficiência ou território?

The equity metric signal is already materially populated by PPI_SHARE, INSE and SPECIAL_EDUCATION_ENROLLMENT. TERRITORY_PROFILE also contains official census-sector and income context for 59 of 69 active municipal schools.

The remaining blocker in V3 was not missing equity evidence. It was a literal `SCHOOL_TO_SECTOR_LINK_FULL_NETWORK` capability requiring 69/69 school geocoding.

That requirement is stricter than the disjunctive research question and conflicts with the project's fail-closed geography rule: ten schools have real address ambiguities, including rural KM addresses and current-vs-CNEFE conflicts. Promoting those weakly just to reach 69/69 would make the system less trustworthy.

## Correction

V1, V2 and V3 remain immutable.

TASK 202 adds a V4 overlay that changes only EQUITY_CONTEXT. It still requires all three equity metrics and official census-sector context, but replaces the full-network geography gate with:

`SCHOOL_TO_SECTOR_LINK_SUBSTANTIAL_COVERAGE_WITH_EXPLICIT_MISSINGNESS`

This capability is deliberately narrower than full-network coverage.

## Capability contract

The capability may exist only when all of the following remain true:

- denominator = 69 active municipal schools;
- strong links = 59 or more;
- coverage >= 0.85;
- held count = exactly 10;
- the exact held roster is hash-pinned;
- linked and held rosters are disjoint and partition the 69 schools;
- none of the held schools is promoted;
- `SCHOOL_TO_SECTOR_LINK_FULL_NETWORK` is absent.

Current observed state is 59/69 = 85.5%, with all ten unresolved schools preserved as HELD.

## What this does NOT claim

TASK 202 does not say that all 69 schools were geolocated. It does not treat the census sector around a school as the socioeconomic profile of its enrolled students. It does not authorize a complete territorial ranking of all 69 schools.

It says only that the observatory has enough material evidence to answer the broad EQUITY_Q1 question while making geographic missingness explicit instead of fabricating precision.

## Fail-closed tests

The task must fall back to partial or fail contract validation if:

- strong links fall below 59;
- coverage falls below 0.85;
- the held roster changes;
- any of PPI_SHARE, INSE or SPECIAL_EDUCATION_ENROLLMENT is missing;
- census-sector context is absent;
- the new capability is absent;
- full-network capability is falsely asserted.

Expected transition after CI:

37 answerable / 1 partial / 0 gaps -> 38 answerable / 0 partial / 0 gaps.

Exactly EQUITY_Q1 may change.

No serving, publication, schedule or recurrence is enabled.
