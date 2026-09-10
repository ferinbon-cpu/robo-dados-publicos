# TASK 010N-R-E-M6 — disposição oficial FNDE para `NUM_POPU`

## Achado primário

Foi fornecida pelo operador a resposta oficial do FNDE/SIOPE ao Fala.BR NUP `23546.111503/2026-95`, documento SEI `5787039`.

O FNDE informa que `Dados_Municipio.NUM_POPU`:

- é um campo legado;
- vem tendo seu conteúdo replicado de exercícios anteriores do SIOPE;
- teve, na carga original, referência em dados do IBGE;
- não é usado nos cálculos do SIOPE;
- não é usado nos relatórios do SIOPE, exceto para exibição em `Municípios Transmitidos por UF`;
- não possui, para o exercício de 2025, correspondência temporal que o FNDE possa assegurar como estimativa populacional de 2025, Censo ou outro recorte temporal específico;
- deve ser desconsiderado em consultas, análises ou validações populacionais, usando-se diretamente as bases oficiais do IBGE com fonte e período adequados.

## Mudança do estado científico

A TASK 010N-R-E-M5 estava correta ao manter `NUM_POPU` como `NOT_PROVEN` na ausência de fonte primária. A nova resposta não prova um vintage exato de 2025; em vez disso, resolve a questão operacional de forma mais forte: **o próprio FNDE manda não usar o campo para análise populacional**.

Novo estado:

`PROVEN_LEGACY_NON_ANALYTIC_FIELD_DO_NOT_USE_FOR_POPULATION_ANALYSIS`

com:

- referência original a IBGE: provada;
- vintage exato do valor 2025: indeterminado;
- reconciliação do valor 2025 com uma estimativa IBGE: não deve ser executada;
- rota analítica correta: consultar IBGE diretamente e declarar explicitamente o período de referência.

## Efeito sobre gates

O antigo B1 `NOT_PROVEN_DEFINITION_SOURCE_VINTAGE_MISSING` deixa de ser uma busca aberta por um número equivalente. Ele passa a ser resolvido por **exclusão do campo da semântica analítica de população**.

Isso não promove a release 0.8.0 nem libera Gold 2025 sozinho. B2, B3 e comparabilidade continuam independentes.

## Custódia

O PDF bruto não é commitado. O repositório persiste apenas SHA-256, identidade documental e proposições delimitadas da resposta oficial. Nenhuma aquisição de fonte foi feita pelo robô nesta task.
