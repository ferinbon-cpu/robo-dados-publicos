# TASK 199H — full-network official school point → IBGE 2022 sector closure

## Result

TASK 199H closes the remaining geography-quality gap from TASK 199G.

- before: 64/69 strong school→sector links;
- after: 69/69 strong links;
- held: 5 → 0;
- `SCHOOL_TO_SECTOR_LINK_FULL_NETWORK`: proven;
- question answerability remains 38/38 and is not the same claim as geographic completeness.

## Municipal point source

The public Limeira Geo front-end exposed the public anonymous-session contract used by the map. The successful bounded runtime used the municipal `Escola Municipal` layer (theme 1234) and recovered nominative school features and geometries without user credentials, registration, regular login or token persistence.

The final five municipal points were matched by explicit named feature identity. Theresa's main unit at Rua Manoel Rato, 25 (gid 80) was used; the separately named `Extensão` at Rua Senador Vergueiro, 1309 (gid 38) remains explicitly excluded from the main-unit link. Neusa's conflict between the GeoPortal address and another current SME address source is preserved rather than erased.

## IBGE geometry

The exact official `SP_setores_CD2022.gpkg` was downloaded ephemerally in GitHub Actions:

- bytes: 182,128,640;
- SHA-256: `07affc966f82292d6f9a359adccc49e69ed55d2075936ef6d1e9c346b29a04bc`;
- Limeira sector polygons: 735;
- raw GPKG persisted: no.

Every one of the five municipal points falls in exactly one Limeira 2022 census-sector polygon and none lies on a polygon boundary.

## Final five links

| INEP | School | Sector |
|---|---|---|
| 35208437 | EMEIEF Ismael Pereira Lago, Pastor | 352690205000447 |
| 35286229 | EMEIEF Maurício Sebastião Ferreira, Padre | 352690205000913 |
| 35004773 | EMEIEF Raquel Aparecida Gonçalves Franceschi, Profa. | 352690205000850 |
| 35099569 | CI Neusa Francisco Correa da Silva | 352690205000593 |
| 35241885 | EMEI Theresa Veronesi D Andrea | 352690205000232 |

## TERRITORY_PROFILE

The existing 267 rows are preserved and TASK 199H adds 17 rows:

- population for all five newly linked schools;
- mean income, median income and V06004 percentile for four sectors with numeric income values;
- no numeric income rows for Padre Maurício's sector because the official income extract reports `X` for V06001–V06006.

New total: **284 rows**.

This distinction is deliberate:

- school→sector geography = 69/69;
- numeric sector-income context = 68/69;
- `X` is explicit source missingness, never zero.

## Semantic guards

- school-location context is not student socioeconomic profile;
- census-sector income is not enrolled-household income;
- full geographic coverage does not imply income availability for every sector;
- no synthetic vulnerability index is created;
- no third-party geocoder is used for canonical promotion;
- address conflicts and extension/main-unit distinctions remain visible.

## Runtime provenance

- public school-point recovery run: `34657846719`, artifact `10286022415`;
- point-in-polygon run: `34658013353`, artifact `10286108922`;
- successful runtime did not use TinyFish.

The temporary discovery workflow/script are not part of the canonical implementation and must not be merged into `main`.
