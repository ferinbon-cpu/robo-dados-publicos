# TASK 199A — IBGE territorial foundation for Limeira

## What changed

This task creates the territorial foundation before any school-level socioeconomic inference is allowed.

The repository audit found no canonical IBGE/territorial product already materialized. Therefore the task does not retrofit geography into `SCHOOL_INDICATOR_SERIES`. It defines a separate future product, `TERRITORY_PROFILE`, and pins the official source ladder.

## Official source ladder

The foundation pins:

1. IBGE Cidades@ for Limeira municipal identity and high-level context.
2. Censo 2022 basic aggregates by census sector, current BR package updated 2026-05-20.
3. Censo 2022 income-of-household-head aggregates by census sector, updated 2026-05-08.
4. 2022 São Paulo census-sector GeoPackage.
5. CNEFE 2022 municipality-specific Limeira ZIP.

The official binary URLs are discovered, but their bytes are not yet in robot custody. No source SHA-256 is invented.

The owner-independent runtime could inspect the official indexes but could not materialize ZIP/GPKG bytes in the current environment. The source registry is therefore classified as discovery evidence, not raw custody.

## Municipal facts observed from IBGE Cidades@

For Limeira, IBGE code `3526902`, the current official page exposes:

- Census population 2022: 291,869.
- Population density 2022: 502.61 inhabitants/km².
- Area 2025: 580.577 km².
- Population estimate 2025: 301,292.
- PIB per capita 2023: R$ 71,528.46.

These values are useful municipal context, but they are not yet promoted into `TERRITORY_PROFILE` because raw-page bytes were not captured and sector/income context is still missing.

## New territorial product contract

Planned product:

`TERRITORY_PROFILE`

Grain:

`one geographic unit x reference period x metric`

Planned capabilities:

- municipal identity;
- municipal demography;
- municipal economy;
- census-sector context;
- school-to-sector link.

## School-to-sector rule

Preferred canonical join:

`official school coordinate -> point in polygon -> 2022 census sector`

Fallback:

`official school address -> auditable CNEFE match -> census sector`

A school name by itself can never geocode a school canonically.

Most importantly:

`territory where a school is located != socioeconomic profile of its students`

The robot may say that a school is located in a territory with certain IBGE characteristics. It may not transfer those characteristics to individual students or the enrolled population without separate evidence.

## Answerability hardening

The current TERRITORY recipe uses `match=ANY` across population, income, vulnerability and demographic profile. This is too permissive because a single population metric could make both territory questions appear answerable.

TASK 199A designs a replacement rule:

- municipal territory context requires demography plus economic/income context;
- school-level territory context additionally requires census-sector context plus a proven school-to-sector link.

The overlay is deliberately **not applied yet**. Source discovery is not materialized answerability.

## Next acquisition order

1. CNEFE Limeira 2022 (3.3M, municipality-specific).
2. Censo 2022 basic sector aggregates (15M).
3. Censo 2022 income sector aggregates (8.9M).
4. São Paulo sector GeoPackage (174M).

After exact bytes are acquired and hashed, TASK 199B can perform deterministic Limeira filtering, schema validation and the first school-to-sector crosswalk.

## Guards

- PIB per capita is not income.
- population estimate is not census population.
- municipal context is not school-level context.
- school location context is not student profile.
- no synthetic vulnerability index without an explicit method.
- missing geography is not zero.
- no third-party geocoder may define canonical identity.
