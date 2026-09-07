# TASK 199B — strong school-to-CNEFE sector seed

## Result

A first canonical **partial** school-to-census-sector seed is now materialized for 14 current municipal schools with years-initial coverage.

The join deliberately does not use a school name by itself.

Every promoted row requires four independent pieces to align:

1. INEP code and school identity from the pinned V08 roster;
2. current street and number from the official Limeira SME school list;
3. exact normalized street and number in the already-custodied CNEFE 2022 file;
4. a compatible named school establishment description at that CNEFE address.

The resulting CNEFE row supplies the IBGE 2022 census-sector code and coordinates.

## Coverage

- 14 strong rows;
- 14 unique INEP codes;
- 14 unique census-sector codes;
- denominator: 40 current schools in the pinned years-initial roster;
- seed coverage: 35%.

This is not a claim of 35% of the whole municipal network, because the network has 69 current units and this roster is the 40-school years-initial analytical subset.

## Fail-closed exclusions

Rows were not promoted when:

- only the school name matched;
- street matched but the number did not;
- the current SME address differed from the CNEFE school-name candidate;
- the exact address had a non-school or generic establishment description insufficient for automatic identity.

A key example is CEIEF Rafael Affonso Leite (INEP 35470600): the CNEFE text contains a similarly named establishment, but its CNEFE address differs from the current official SME address. The robot therefore keeps that school unlinked rather than silently inheriting the candidate sector.

## Semantics

This seed proves a **school-location-to-sector** relation for the 14 promoted rows.

It does not prove:

- socioeconomic characteristics of enrolled students;
- catchment area;
- residence of students;
- a complete 69-school crosswalk;
- territorial vulnerability;
- a complete TERRITORY_PROFILE.

Answerability therefore remains unchanged at 28 answerable / 8 partial / 2 explicit gaps.

## Why this matters

The GeoPackage is no longer a prerequisite for the first school-sector links: CNEFE already carries COD_SETOR with each address. Sector geometry remains valuable as a later spatial-QA layer.

The next high-value dependency is now the Censo 2022 sector aggregate tables (basic profile and income). Once those are ingested, the 14 proven school sectors can immediately receive factual territorial context without waiting for the full 69-school crosswalk.
