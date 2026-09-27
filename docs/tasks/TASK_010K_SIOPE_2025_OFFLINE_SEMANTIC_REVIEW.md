# TASK 010K — review semântico offline dos metadados SIOPE 2025

## Resultado

`KEEP_B1_B2_BLOCKED_CURRENT_2025_CONCEPTS_PINNED_ALIAS_IDENTITY_AND_NUM_POPU_SOURCE_VINTAGE_NOT_PROVEN`

A abertura reproduzível do pacote 2025 entregue por handoff humano resolveu a lacuna de **conteúdo dos metadados**, mas não autoriza promoção semântica. O review foi T0/offline, sem rede, sem execução de binários, sem persistência de XML decodificado e sem registrar valores financeiros municipais.

Artefato revisado, com proveniência preservada como `USER_MEDIATED_OFFICIAL_DOWNLOAD_CANDIDATE`: `Metadados_Mun_2025.zip`, SHA-256 `41511c141e1af025ae2b565085583d6a3ab7b4577862f8ebdc308605101c1e5b`, 6.586.598 bytes. O parser 010J já havia sido validado externamente em 146/146 containers. O review percorreu 156 membros internos, dos quais 144 são XML.

## Identidade do pacote

`Parametro.xml` identifica exercício 2025, tipo municipal, versão de metadados 333 e software `25.0.5.6`. A linha de parâmetro usa `NUM_PERI=1`; `Periodo.xml` identifica `1º Bimestre` e `IDN_ULTI_PERI_ANO=N`. Isso prova a identidade atual do pacote para o exercício 2025, mas **não** transforma o pacote em evidência de fechamento/finalidade do P6.

## S1 — `NUM_POPU`

O nome exato `NUM_POPU` está presente em `Dados_Municipio.xml`, dentro do pacote atual de 2025. A tabela contém 5.569 municípios; 5.568 linhas possuem o atributo e uma linha não o possui. O próprio XML, porém, declara apenas o campo/tipo/largura: não contém definição textual de população, fonte oficial nem regra temporal/vintage.

Assim, o review melhora a prova de **identidade estrutural atual do campo**, mas não satisfaz os quatro requisitos cumulativos de S1. Permanecem ausentes:

- definição semântica exata de `NUM_POPU`;
- fonte oficial da população;
- regra de vintage/data de referência.

Correspondências empíricas de valores com tabelas populacionais históricas continuam fora do critério de promoção. Resultado: `S1_NUM_POPU = NOT_PROVEN`.

## S2 — conceitos financeiros atuais

O pacote 2025 contém estruturas atuais inequívocas para os dez conceitos históricos:

- `Receita Total` (`COD_PAST=1`) e `Consolidado de Receita` (`COD_PAST=124`) expõem `PA = Previsão Atualizada` e `RR = Receitas Realizadas`;
- `Consolidado de Despesa` (`COD_PAST=125`) expõe `DA = Dotação Atualizada`, `DE = Desp. Empenhadas`, `DL = Desp. Liquidadas` e `DP = Desp. Pagas`;
- `Despesas com Educação` (`COD_PAST=27`) é a raiz de uma hierarquia de 715 pastas: 561 pastas operacionais usam o conjunto `DA/DE/DL/DP`, 153 são pastas de agrupamento sem colunas próprias e uma pasta especial do FUNDEB usa `DE/DL/DP` mais colunas específicas de restos/saldos.

Portanto, a lacuna antiga “os conceitos atuais existem?” está resolvida positivamente.

## O ponto que ainda bloqueia S2

Foi feita busca literal em **todos os 156 membros decodificados**. Nenhum dos dez nomes OData abaixo aparece no pacote:

`VAL_RECE_PREV_ATUA`, `VAL_RECE_REAL`, `VAL_DESP_DOTA_ATUA`, `VAL_DESP_EMPE`, `VAL_DESP_LIQU`, `VAL_DESP_PAGA`, `VL_DESP_DOTA_ATUA_EDU`, `VL_DESP_EMPE_EDU`, `VL_DESP_LIQU_EDU`, `VL_DESP_PAGA_EDU`.

Logo, temos `10/10` conceitos atuais presentes, mas `0/10` identidades alias→estrutura interna formalmente provadas. Fazer a ligação apenas pela semelhança lexical continuaria violando a regra fail-closed definida nas TASKs 007/009E.

### Matriz resumida

| Alias OData | estrutura 2025 candidata | código interno | conceito atual | status |
|---|---|---:|---|---|
| `VAL_RECE_PREV_ATUA` | Receita Total / Consolidado de Receita | `PA` | Previsão Atualizada | PARTIAL |
| `VAL_RECE_REAL` | Receita Total / Consolidado de Receita | `RR` | Receitas Realizadas | PARTIAL |
| `VAL_DESP_DOTA_ATUA` | Consolidado de Despesa | `DA` | Dotação Atualizada | PARTIAL |
| `VAL_DESP_EMPE` | Consolidado de Despesa | `DE` | Desp. Empenhadas | PARTIAL |
| `VAL_DESP_LIQU` | Consolidado de Despesa | `DL` | Desp. Liquidadas | PARTIAL |
| `VAL_DESP_PAGA` | Consolidado de Despesa | `DP` | Desp. Pagas | PARTIAL |
| `VL_DESP_DOTA_ATUA_EDU` | hierarquia Despesas com Educação | `DA` | Dotação Atualizada | PARTIAL |
| `VL_DESP_EMPE_EDU` | hierarquia Despesas com Educação | `DE` | Desp. Empenhadas | PARTIAL |
| `VL_DESP_LIQU_EDU` | hierarquia Despesas com Educação | `DL` | Desp. Liquidadas | PARTIAL |
| `VL_DESP_PAGA_EDU` | hierarquia Despesas com Educação | `DP` | Desp. Pagas | PARTIAL |

`PARTIAL` significa: o conceito oficial corrente está presente, mas a identidade determinística do alias OData com a estrutura interna não está publicada no pacote.

## EDU não é automaticamente MDE

O metadata 2025 separa explicitamente a raiz `Despesas com Educação` das estruturas de MDE. `ME_Indicador.xml` contém dez indicadores que nomeiam MDE explicitamente e existe uma tabela separada `ME_Valores_MDE.xml`. Isso é evidência atual suficiente para proibir a simplificação `EDU = MDE`.

Esse achado reduz a ambiguidade conceitual, mas ainda não prova que os quatro aliases `_EDU` apontam para um agregado específico da árvore `Despesas com Educação`.

## Estados preservados

- `0.7.0 = ACTIVE`;
- `0.8.0 = CANDIDATE`;
- `2025 = PROVEN_STRUCTURAL_RECENT`;
- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- `annual_closure_status = UNKNOWN`;
- `semantic_comparability_status = UNKNOWN`;
- `gold_metrics_status = UNKNOWN/BLOCKED`;
- série fechada = `2016–2024`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

## Próximo gate

Não repetir busca ampla já esgotada. A próxima promoção semântica exige **nova evidência específica**:

1. para S1: fonte oficial + definição + regra temporal/vintage de `NUM_POPU`;
2. para S2: ponte oficial/determinística, aplicável ao serviço OData corrente, entre cada um dos dez aliases e a estrutura interna 2025.

B3/finalidade 2025 continua sendo um blocker independente. Gold 2025 permanece bloqueado.
