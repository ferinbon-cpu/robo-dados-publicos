# TASK 199E — expand school→sector crosswalk to 57/69

TASK 199E deepens the territorial layer without inflating answerability.

## Identity advance

The current official SME municipal-school directory exposes CIE, unit and current address. Across the current 69-school municipal roster, the CIE reconciles deterministically with the INEP identity by the verified scoped rule:

`int(SME_CIE) == int(last 6 digits of INEP code)`.

This is treated as a verified bridge for these 69 current rows only, not as a universal CIE/INEP law.

## Crosswalk

Strong links increase from 14 to 57:

- 41 Tier A: official SME CIE/INEP identity + exact current address + one resulting CNEFE sector;
- 15 Tier B: official identity + same current street + compatible named CNEFE school where the CNEFE number is absent/zero or the title alias is explicit;
- 1 Tier C: source-format anomaly reconciled between SME and CNEFE.

Coverage:
- network: 57/69 = 82.6%;
- years initial: 32/40;
- EI-only: 25/29.

Twelve schools remain held because current-address conflicts, rural KM ambiguity, missing exact address or incompatible historic CNEFE address make automatic promotion unsafe.

## Territory product

TERRITORY_PROFILE grows from 67 to 239 rows:

- 11 municipal rows unchanged from TASK 199D;
- 57 schools × four sector-context metrics = 228 rows.

The four school-location metrics remain population, V06004, V06006 and unweighted V06004 sector percentile.

## Answerability

No question status changes.

The matrix remains:

**32 answerable / 6 partial / 0 explicit gaps.**

EQUITY_Q1 remains partial because the canonical recipe still requires `SCHOOL_TO_SECTOR_LINK_FULL_NETWORK`. TASK 199E deliberately does not mint that capability from 57/69.

## Next evidence

The remaining 12 should be resolved, if possible, using stronger official current coordinates or municipal GIS evidence followed by point-in-polygon QA against the 2022 census-sector geometry. Name-only or third-party geocoder matches remain forbidden.
