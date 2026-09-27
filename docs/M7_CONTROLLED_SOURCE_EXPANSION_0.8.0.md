# M7 — Expansão controlada de fontes 0.8.0

## Objetivo

Provar que o robô consegue incorporar uma fonte nova por meio de estados explícitos e gates separados, sem confundir descoberta pública com autorização de coleta.

## Fonte-piloto

A única fonte-piloto desta candidata é o Sistema de Informações sobre Orçamentos Públicos em Educação (SIOPE), do Fundo Nacional de Desenvolvimento da Educação (FNDE), na superfície pública `Dados Informados pelos Municípios`.

Superfícies oficiais verificadas em 24/08/2026:

- `https://webservice.fnde.gov.br/siope/dadosInformadosMunicipio.do`
- `https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope`

A página institucional informa que o SIOPE dissemina e dá acesso público às informações orçamentárias da educação e que o cidadão pode consultar dados detalhados de receitas e despesas, MDE e Fundeb sem necessidade de senha.

Esta verificação comprova somente a existência e a finalidade da superfície pública. Ela **não** comprova um endpoint/export de aquisição, parâmetros estáveis, content-type ou schema.

## Recorte proposto

- município: Limeira/SP;
- código municipal de referência: `352690`;
- exercício: 2024;
- condição: exercício fechado proposto para o futuro gate de aquisição;
- temas: receitas, despesas, MDE e Fundeb.

A escolha de um exercício fechado reduz volatilidade durante a primeira prova de aquisição. O código e o período ainda deverão ser confirmados contra a própria rota oficial no próximo gate antes de qualquer coleta.

## Ciclo de vida

1. `DISCOVERED` — a existência da fonte/superfície é conhecida.
2. `CONTRACT_VALIDATED` — instituição, domínio, escopo, cautelas e requisitos do próximo gate foram validados offline.
3. `ONE_TIME_AUTHORIZED` — somente depois de rota, content-type e schema comprovados e de autorização explícita para uma coleta.
4. `LIVE_VALIDATED` — um payload real, único e delimitado passou pelo contrato imutável.
5. `RECURRENCE_ELIGIBLE` — a fonte demonstrou estabilidade suficiente para ser avaliada para recorrência.

`RECURRENCE_ELIGIBLE` não equivale a recorrência autorizada. O schedule continua exigindo uma decisão separada.

## Estado da 0.8.0 candidata

O SIOPE–Limeira para em `CONTRACT_VALIDATED`.

- `acquisition_route_status = UNPROVEN`
- `schema_status = UNPROVEN`
- `content_type_status = UNPROVEN`
- `collection_authorization = PROHIBITED`
- `recurrence_authorization = PROHIBITED`
- `schedule = DISABLED`

O gate de desenho (`scripts/github_source_expansion_design_gate.py`) não usa rede e não escreve remotamente.

## Semântica financeira

A 0.8.0 não autoriza interpretação automática de campos financeiros. Antes de processamento, o próximo gate deverá documentar:

- nome do campo de origem;
- definição oficial;
- unidade e escala monetária;
- período de referência;
- natureza receita/despesa;
- estágio orçamentário quando aplicável;
- semântica de zero;
- semântica de vazio/nulo/ausente;
- correspondência para conceitos analíticos usados pelo robô;
- cautelas que impeçam tratar dotação, empenho, liquidação, pagamento, saldo ou receita como equivalentes.

## Critérios para o próximo gate

`M7_SIOPE_LIMEIRA_ROUTE_DISCOVERY_GATE_0_8_0` somente poderá avançar se:

1. a rota oficial for observada a partir da superfície pública, sem adivinhar URL;
2. parâmetros necessários forem identificados de forma reprodutível;
3. content-type de uma resposta candidata for comprovado;
4. schema e cabeçalhos forem inspecionados;
5. nenhuma credencial, bypass ou automação de desafio humano for necessária;
6. um único recorte 2024/Limeira puder ser fixado;
7. nenhuma escrita no Drive ocorrer durante descoberta;
8. nenhuma recorrência ou schedule for habilitado.

Mesmo após essa descoberta, a coleta ao vivo deverá exigir outro gate/autoridade explícita `ONE_TIME_AUTHORIZED`.
