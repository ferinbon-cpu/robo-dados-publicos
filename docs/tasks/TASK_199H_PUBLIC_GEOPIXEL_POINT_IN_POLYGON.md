# TASK 199H — fechamento 69/69 por ponto municipal oficial × setor IBGE 2022

## Objetivo

Fechar os cinco vínculos escola→setor que permaneceram `HELD` após a TASK 199G, usando a rota preferencial já definida pelo projeto: **coordenada oficial atual da escola → point-in-polygon → malha oficial de setores censitários de 2022**.

A TASK não altera a regra de cautela territorial: localização da escola não é residência dos estudantes nem perfil socioeconômico da clientela.

## Fonte municipal de pontos

O portal público Limeira Geo expõe o visor `Geopixel Cidades`. A leitura estática do próprio front-end provou o contrato operacional, sem adivinhação de endpoints:

- `configurations.json` → `serverPath=https://limeira.geopixel.com.br/geopixelcidades3_server`;
- acesso público embutido no produto: `POST /public/anonymousLogin`;
- perfil público único: `id=2`, `Público`;
- temas do perfil: `GET /themes/getThemeByProfile?profileId=2`;
- tema `1234` = **Escola Municipal**;
- layer WMS = `limeira:escola_municipal_limeira`;
- chave = `gid`; geometria = `geom`; SRID = 3857;
- busca nominal usada pelo próprio visor: `GET /data/quickSearch?themeId=1234&value=<nome>&queryExpiredData=false`.

Nenhuma credencial, cadastro ou login regular foi utilizado. O token de sessão anônima existiu apenas em memória no runner e nunca foi persistido.

## Identidades municipais recuperadas

Cinco unidades foram reconciliadas com a camada municipal oficial:

| INEP | Unidade | gid | Endereço retornado pelo GeoPortal |
|---|---|---:|---|
| 35208437 | EMEIEF Ismael Pereira Lago, Pastor | 49 | Av Luis Vaz De Camoes 330 Jd Caieira |
| 35286229 | EMEIEF Maurício Sebastião Ferreira, Padre | 67 | R: João Pompeu Filho, 571 Jardim Do Lago |
| 35004773 | EMEIEF Raquel Aparecida Gonçalves Franceschi, Profa. | 76 | Rua Sebastião Teixeira, 200, Residencial Rubi |
| 35099569 | CI Neusa Francisco Correa da Silva | 26 | Rua Olivia Sacco Iaquinta, S/N - Vila Labak |
| 35241885 | EMEI Theresa Veronesi D Andrea | 80 | Rua Manoel Rato, 25, Jardim Parque Novo Mundo |

Para Theresa, o visor retorna também uma feição separada explicitamente marcada **`(Extensão)`**, gid 38, Rua Senador Vergueiro, 1309. A TASK seleciona a unidade principal apenas porque a feição gid 80 é a feição nomeada sem `Extensão` e coincide com o endereço corrente Manoel Rato, 25. A extensão permanece registrada e não é apagada.

Para Neusa, a divergência entre `Mário Alves Ferraz, 185` no diretório da SME e `Olivia Sacco Iaquinta, S/N` no GeoPortal municipal permanece explícita. O ponto do GeoPortal é usado apenas como **local atual nomeado pela própria Prefeitura** para a interseção espacial; não se afirma que esse era o sítio da escola em 2022.

## Malha IBGE

A execução efêmera adquiriu diretamente a fonte oficial:

`SP_setores_CD2022.gpkg`

- bytes: `182128640`;
- SHA-256: `07affc966f82292d6f9a359adccc49e69ed55d2075936ef6d1e9c346b29a04bc`;
- feature table: `SP_setores_CD2022`;
- código: `CD_SETOR`;
- geometria: `POLYGON`;
- SRS: EPSG:4674;
- setores de Limeira: `735`;
- geometrias de Limeira parseadas: `735`;
- erros de parsing: `0`.

O binário foi apagado ao final do runner. Apenas hash, metadados e resultados sanitizados são canonizados.

## Resultado do point-in-polygon

Todos os cinco pontos municipais caíram no **interior de exatamente um setor**, sem ponto em borda:

| INEP | Setor 2022 |
|---|---|
| 35208437 | 352690205000447 |
| 35286229 | 352690205000913 |
| 35004773 | 352690205000850 |
| 35099569 | 352690205000593 |
| 35241885 | 352690205000232 |

Com isso, o crosswalk passa de **64/69 para 69/69**.

## Métricas territoriais

Os setores foram reconciliados com os CSVs IBGE já sob custódia e hashados. Quatro setores possuem V06004/V06006 numéricos. O setor `352690205000913`, do Padre Maurício, contém `X` em V06001–V06006 no arquivo oficial de renda.

Esse `X` é preservado como missingness, nunca convertido para zero. Por isso a nova versão do `TERRITORY_PROFILE` acrescenta:

- 4 linhas por escola para Ismael, Raquel, Neusa e Theresa;
- apenas `SECTOR_POPULATION` para Padre Maurício;
- total novo = `17` linhas;
- produto: `267 → 284` linhas;
- escolas com vínculo: `64 → 69`;
- `held = 0`;
- capacidade `SCHOOL_TO_SECTOR_LINK_FULL_NETWORK` = presente;
- renda setorial completa = **não** declarada.

O percentil V06004 mantém a fórmula histórica: `count(V06004 <= valor) / 718 × 100`, arredondado a uma casa decimal.

## Estado semântico

`SCHOOL_TO_SECTOR_LINK_FULL_NETWORK` significa apenas que todas as 69 unidades do roster municipal ativo possuem um vínculo territorial forte para a geometria setorial de 2022.

Ele **não** significa:

- que a escola ocupava o mesmo sítio em 2022;
- que o setor descreve o domicílio dos estudantes;
- que a renda do setor é a renda dos alunos;
- que todas as variáveis de renda existem para todos os setores;
- que há um índice sintético de vulnerabilidade.

A answerability permanece `38/38`; a TASK melhora a qualidade geográfica, não cria uma nova pergunta canônica.
