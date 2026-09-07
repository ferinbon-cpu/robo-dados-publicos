# TASK 199D — first canonical TERRITORY_PROFILE

TASK 199D promotes the first territorial query product after the official IBGE income dictionary was handed off and verified.

## Semantic closure

The exact dictionary defines V06004 as the nominal mean monthly income of responsible persons with income in occupied permanent private households, and V06006 as the corresponding nominal median monthly income.

The product never re-labels either value as student income, family income of enrolled pupils, or a vulnerability index.

## Product

TERRITORY_PROFILE becomes the eighth derived observatory product.

It materializes 67 rows:
- 11 municipal/sector-distribution summary rows;
- 56 rows for 14 strongly linked schools, four territorial metrics per school.

The full raw Limeira extracts remain preserved in Drive. The compact product is a query layer, not source truth.

## Answerability

The previous weak TERRITORY rule accepted any single population/income metric. TASK 199D applies the stricter design from TASK 199A.

TERR_Q1 and TERR_Q2 require a bundled TERRITORY_PROFILE with:
- MUNICIPAL_DEMOGRAPHY;
- CENSUS_SECTOR_CONTEXT;
- SECTOR_INCOME_CONTEXT.

EQUITY_Q1 additionally requires SCHOOL_TO_SECTOR_LINK_FULL_NETWORK. TASK 199D has only SCHOOL_TO_SECTOR_LINK_PARTIAL (14/69), so EQUITY_Q1 intentionally remains partial.

Expected matrix:
30 answerable / 6 partial / 2 gaps
→ 32 answerable / 6 partial / 0 gaps.

## Guards

School-location sector context is not the socioeconomic profile of enrolled students. The sector distribution is unweighted and is not a person-weighted municipal income estimate. No vulnerability index is fabricated.
