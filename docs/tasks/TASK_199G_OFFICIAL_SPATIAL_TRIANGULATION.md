# TASK 199G — official spatial triangulation for five held schools

## Goal

Advance the school-to-census-sector crosswalk using only multi-anchor official evidence. No third-party geocoder is used for canonical promotion.

## Before

- strong school links: 59/69
- held: 10
- TERRITORY_PROFILE rows: 247
- EQUITY_Q1: MATERIALIZED_PARTIAL

## Promotions

### CEIEF Rafael Affonso Leite — sector 352690205000136

Current Prefeitura service card locates the school on Rua Antonio Alves de Oliveira, in front of no. 250. The CNEFE contains 64 exact no. 250 address rows and all map to sector 136P. The exact named CNEFE school record also maps to 136P, about 94.9 m from the representative no. 250 point.

### EMEIEF Alfredo Christiano Stahlberg — sector 352690205000652

Current SME directory states Via Martim Lutero, KM 10, Sítio Santa Rosa, Frades. CNEFE has an exact route no. 10 row in DOS FRADES at sector 652P and the named school record at route no. 9 in the same locality and sector. The older Prefeitura properties page still says KM 13; this conflict is preserved, not erased, and the current operational SME directory is used as the current address.

### EMEIEF Major José Levy Sobrinho — sector 352690205000094

A newer Prefeitura elections publication dated 2026-09-01 gives Rua Francisco Benedito Gonçalves de Oliveira, 38, Jardim Esteves. That exactly matches the named CNEFE school row at no. 38, sector 094P. The older SME directory number 3 is preserved as superseded conflicting data.

### EMEIEF Martim Lutero — sector 352690205000375

Current Prefeitura properties data give Via Martim Lutero KM 3, Bairro dos Pires do Meio de Cima. CNEFE has the named school in sector 375P plus two route-number-3 points in the same sector.

### CI Ary Levy Pereira — sector 352690205000554

Current SME directory gives Rua Ademar Marcolino 215, Jardim Glória. Câmara Indicação 355/2016 explicitly identifies Centro Infantil Prefeito Ary Levy Pereira at Rua Ademar Marcolino s/n, Jardim Glória. CNEFE has exactly one generic CRECHE MUNICIPAL on that street/locality at s/n, sector 554P. This is treated as a temporal identity bridge, not a name-only match.

## Still held

Five schools remain unresolved:

- EMEIEF Ismael Pereira Lago
- EMEIEF Padre Maurício Sebastião Ferreira
- EMEIEF Profa. Raquel Aparecida Gonçalves Franceschi
- CI Neusa Francisco Correa da Silva
- EMEI Theresa Veronesi D Andrea

Reasons include one-sided address evidence, duplicated street numbering across sectors, current-vs-2022 site change, or an old CNEFE unit inconsistent with the current site.

## After

- strong links: 64/69 = 92.8%
- held: 5
- TERRITORY_PROFILE rows: 267
- full-network capability: false
- EQUITY_Q1 remains MATERIALIZED_PARTIAL
- current observatory answerability remains 37/38.

The remaining valid route is official point/parcel/geometry evidence for the final five, preferably Limeira Geo or an equivalent municipal GIS source.
