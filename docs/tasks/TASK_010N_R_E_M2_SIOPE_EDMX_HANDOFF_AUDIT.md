# TASK 010N-R-E-M2 — handoff humano do EDMX oficial SIOPE

## Resultado

`EDMX_OBTAINED_STRUCTURAL_CONTRACT_CONFIRMED_SEMANTIC_ANNOTATIONS_ABSENT`

O owner abriu manualmente o URL oficial `$metadata` do serviço SIOPE e forneceu no chat o conteúdo XML exibido pelo navegador. A auditoria desta task é T0/offline; nenhum novo acesso remoto foi executado.

## O que o EDMX prova

- OData `Version=4.0`.
- Namespace `br.gov.bcb.olinda.servico.DADOS_ABERTOS_SIOPE`.
- `EntityType Name="Dados_Gerais_Siope"` com exatamente 52 propriedades.
- Presença dos 11 inputs usados pelo Gold histórico.
- Tipos do contrato atual: `NUM_POPU=Edm.Int32`; seis aliases financeiros gerais em `Edm.String`; quatro aliases `_EDU` em `Edm.Decimal`.
- A função `Dados_Gerais_Siope` recebe `Ano_Consulta`, `Num_Peri` e `Sig_UF` e retorna coleção do EntityType correspondente.

## O que o EDMX NÃO prova sozinho

Não existem `Annotation`, `Annotations`, `Documentation`, `Description` ou termos semânticos no payload recebido. Portanto a presença e o tipo dos aliases não bastam, por si só, para promover:

- `S1_NUM_POPU`;
- `S2_FINANCIAL_ALIAS_BRIDGE`;
- comparabilidade semântica;
- Gold 2025;
- fechamento anual.

Não transformar nome de campo em equivalência semântica apenas por similaridade lexical.

## Novo achado de alto valor

O mesmo EDMX expõe recursos oficiais auxiliares:

### `Receita_Siope`

Inclui `NOM_ITEM`, `IDN_CLAS`, `NOM_COLU` e `VAL_DECL`.

### `Despesas_Siope`

Inclui `NOM_PAST`, `TIP_PASTA`, `NOM_ITEM`, `IDN_CLAS`, `NOM_COLU` e `VAL_DECL`.

### `Despesas_Funcao_Educacao_Siope`

Inclui `DES_SUBF`, `VAL_DESP_EMPE`, `VAL_DESP_LIQU` e `VAL_DESP_PAGA`.

Esses recursos criam uma rota oficial que não depende de CML/XML/Delphi: um gate remoto separado e bounded pode consultar somente os campos necessários e testar se rótulos oficiais e valores do próprio serviço reconciliam operacionalmente com os aliases de `Dados_Gerais_Siope`.

Essa futura correspondência deve ser provada por regras explícitas; coincidência de nome ou um único valor isolado não deve bastar.

## Proveniência do handoff

- URL informado e aberto pelo owner: `https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/$metadata`
- bruto recebido: 15.965 bytes; SHA-256 `e4970d18e593b0edc88dac23c711f2d9e1df6d9c79ae76d9fc67f869f310b307`
- XML a partir de `<edmx:Edmx>`: 15.586 bytes; SHA-256 `6bf6a37ef190389db9420a6e6cd26f2ec7967c8920bcf61799252a017cdb30ca`
- classe de proveniência: `USER_MEDIATED_DIRECT_OFFICIAL_URL_EDMX_CANDIDATE`

## Estados preservados

- `0.7.0 = ACTIVE`
- `0.8.0 = CANDIDATE`
- `2025 = PROVEN_STRUCTURAL_RECENT`
- `S1_NUM_POPU = NOT_PROVEN`
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`
- `annual_closure_status = UNKNOWN`
- `semantic_comparability_status = UNKNOWN`
- `gold_metrics_status = UNKNOWN/BLOCKED`
- série anual fechada = `2016–2024`
- `2026 = UNPROVEN_CURRENT_YEAR`

## Próximo gate recomendado

`OFFICIAL_AUXILIARY_RESOURCE_LABEL_TO_ALIAS_OPERATIONAL_BRIDGE`

Deve ser separado e explicitamente autorizado. A prioridade é consultar os recursos oficiais auxiliares com escopo mínimo, preferencialmente primeiro rótulos sem valores e depois, apenas se necessário, uma reconciliação determinística de valores públicos para provar a correspondência operacional.