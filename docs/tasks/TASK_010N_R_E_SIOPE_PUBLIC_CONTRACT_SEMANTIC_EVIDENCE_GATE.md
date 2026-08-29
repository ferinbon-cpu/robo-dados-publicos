# TASK 010N-R-E — Gate offline de evidência semântica do contrato público SIOPE

## Resultado

**`PUBLIC_CONTRACT_EVIDENCE_PARTIAL_OFFLINE`.**

A evidência oficial já residente no repositório é semanticamente útil, mas não satisfaz o padrão P1 completo para nenhum dos 11 inputs Gold.

A TASK 007 e a discovery documental 009E-L provam que o dicionário oficial FNDE 2019 define os dez conceitos financeiros relevantes: previsão atualizada, receita realizada, dotação atualizada, despesa empenhada, liquidada e paga, inclusive os quatro conceitos de despesas com educação. Porém, essas fontes não ligam explicitamente os dez aliases OData atuais aos conceitos para o regime 2025 e não definem `NUM_POPU`, sua fonte populacional ou regra de vintage/referência temporal.

A TASK 010K acrescenta evidência atual do pacote de metadados 2025: os conceitos PA/RR/DA/DE/DL/DP existem em estruturas atuais e há uma árvore específica de `Despesas com Educação`, distinta das estruturas MDE. Isso fortalece a continuidade conceitual, mas não contém os dez aliases OData literais e não estabelece a agregação exata dos quatro aliases `_EDU`. `NUM_POPU` aparece nominalmente em `Dados_Municipio`, mas sua definição, fonte e vintage permanecem não provados.

A TASK 010L confirma que o instalador oficial não contém uma bridge OData literal observável no payload estático local; esse resultado não é interpretado como ausência da bridge no backend remoto. A TASK 010N-R já decidiu que ausência de source/internal identity não torna engenharia reversa um requisito epistemológico por padrão.

## Matriz 11/11

Resumo fail-closed:

- `PROVEN = 0`
- `PARTIAL = 11`
- `AMBIGUOUS = 0`
- `NOT_FOUND = 0`

Os dez campos financeiros são `PARTIAL` porque o alias existe estruturalmente no contrato observado e o conceito oficial correspondente existe na documentação FNDE, mas falta a ligação oficial atual alias→conceito, inclusive unidade, escopo/agregação e aplicabilidade temporal suficiente para o padrão reconciliado.

`NUM_POPU` também é `PARTIAL`: o nome do campo está presente no schema atual e no pacote 2025, porém definição oficial, fonte populacional, unidade semântica e regra de vintage/referência continuam ausentes.

## Aliases `_EDU`

Nenhuma equivalência `EDU = MDE` é autorizada. A evidência 2025 distingue `Despesas com Educação` de MDE. A documentação histórica define conceitos de despesas de educação, mas não fixa qual agregado atual alimenta cada alias `_EDU` no contrato OData.

## O que este gate prova

Ele prova apenas que:

1. existe documentação oficial primária relevante para 10/11 conceitos;
2. existe continuidade estrutural dos 11 nomes no contrato observado;
3. a evidência repo-resident não contém bridge oficial atual completa alias→conceito;
4. a ausência dessa bridge não autoriza concluir que uma bridge interna CML/XML/Delphi/backend seja necessária.

Portanto P1 continua não provado, P2 continua não demonstrado necessário e `STANDARD_NOT_YET_DETERMINABLE` permanece coerente com a 010N-R.

## Menor nova classe de evidência

A próxima evidência discriminante deve ser **primária, oficial e do contrato público**, nesta ordem:

1. EDMX/`$metadata` oficial com descrições/annotations semânticas suficientes;
2. documentação oficial FNDE/Olinda de campos ou aliases;
3. contrato oficial equivalente que relacione alias→conceito e cubra também `NUM_POPU`.

Uma eventual aquisição remota deve ser task separada, explicitamente autorizada pelo owner. Esta task não executa rede e não preserva autorização implícita para retry.

## Estados preservados

- `0.7.0 = ACTIVE`
- `0.8.0 = CANDIDATE`
- `2025 = PROVEN_STRUCTURAL_RECENT`
- `S1_NUM_POPU = NOT_PROVEN`
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`
- `annual_closure_status = UNKNOWN`
- `semantic_comparability_status = UNKNOWN`
- `gold_metrics_status = UNKNOWN/BLOCKED`
- closed annual series = `2016–2024`
- `2026 = UNPROVEN_CURRENT_YEAR`

Não há cálculo Gold 2025, expansão de série, promoção semântica, alteração de release, escrita no Drive, engenharia reversa adicional ou abertura da TASK 010O.
