# TASK 199B — CNEFE Limeira 2022 ingestion

## Handoff received

The owner supplied the official IBGE CNEFE municipality archive:

`3526902_LIMEIRA.zip`

This is classified as:

`USER_MEDIATED_DIRECT_OFFICIAL_IBGE_BINARY_HANDOFF`

The exact archive bytes are now preserved in Drive and have a reproducible SHA-256.

## Binary custody

Archive:

- bytes: 3,486,586
- SHA-256: `ab73250df889effcb01ddc2d060bddd3252e995468e97ef93b048564763626a7`
- one archive member.

CSV member:

- `3526902_LIMEIRA.csv`
- bytes: 26,082,570
- SHA-256: `8adb17d18a8c0a4de9e6d48b31ed63f74e0bfde27f11f63154c17456d35218b3`
- UTF-8;
- semicolon-delimited;
- 150,450 records;
- 34 columns.

Exact identity checks give only:

- `COD_UF=35`
- `COD_MUNICIPIO=3526902`

Therefore the municipality scope is exact.

## Geographic coverage

The file contains:

- 724 distinct census-sector codes;
- 2,471 distinct CEP values;
- 150,450 rows with both latitude and longitude.

This makes CNEFE a strong address/coordinate bridge for the territorial architecture.

It is not, by itself, the socioeconomic profile. Sector aggregates still have to be joined from the Censo 2022 aggregates.

## School candidates

The establishment-description field has 20,163 non-null rows and 13,528 unique descriptions.

A deliberately conservative textual scan for clear municipal-school markers (CEIEF, EMEIEF, EMEI, ESCOLA MUNICIPAL, CRECHE MUNICIPAL) found 41 candidate rows representing 38 unique descriptions.

These are stored separately as candidates only.

Example:

- description: `CEIEF RAFAEL AFONSO LEITE`
- CNEFE address id: `222923668`
- sector: `352690205000136P`
- latitude: `-22.574023`
- longitude: `-47.377727`

This is **not** yet promoted as the canonical location of the network school. The robot already uses INEP code as the preferred school identity, and the CNEFE spelling itself differs from the known school-name spelling in other project contexts.

Canonical promotion requires the official 69-school roster with INEP code plus address or coordinates, followed by deterministic reconciliation.

## Drive custody

Under `01_BRONZE/IBGE`:

- raw ZIP — Drive ID `1EfrJkwj6bcu9WiokX6zz59_4-Wt8Caiy`;
- extracted raw CSV — `1pqAYHvs9RTfHAymDJaR9QgVvIe8RBT2h`;
- ingestion evidence JSON — `1t0RZseEiTHLodv5C5obI8C7a2gs_EugA`;
- school-name candidate CSV — `1EPggDnjOECybG5wGP0PrQ6Ur3JgUzlhs`.

All four files were read back with exact byte sizes.

## Answerability

No territory question is promoted yet.

CNEFE gives addresses, coordinates and census-sector identifiers. It does not provide the complete demographic/income profile required by the stricter territory answerability contract.

Therefore the canonical matrix remains:

- 28 answerable;
- 8 partial;
- 2 explicit gaps.

## Next

The highest-value next binary is the Censo 2022 basic sector aggregate package, followed by sector income aggregates and sector geometry.

Once those are in custody, the robot can build actual `TERRITORY_PROFILE` rows and then reconcile the 69 schools.

## Guards

- school name != canonical identity when INEP code exists;
- CNEFE establishment text != official school roster;
- coordinate row != school coordinate until identity match is proven;
- school-location territory != student socioeconomic profile;
- missing geography != zero.
