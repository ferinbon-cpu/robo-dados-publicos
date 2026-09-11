# TASK 231 — fingerprint dos 50 relatórios FUNDEB/25%

## Objetivo

Resolver a última fila `INDEX_ONLY` da auditoria TASK 226 sem confundir quantidade de PDFs com quantidade de fatos novos. A TASK 231 materializa **proveniência e estrutura**, não valores financeiros novos.

## Universo

O MD_01.3B mapeia exatamente 50 documentos na categoria `FUNDEB / 25% Educação - relatórios do portal`:

- `DOC-020..DOC-040`: 21 arquivos `a_*`;
- `DOC-068..DOC-096`: 29 arquivos `fundeb25a_*`.

O config preserva os 50 nomes literais e os separa deterministicamente em `family`, `entity_token`, `selector_1`, `selector_2` e `filename_timestamp_token`.

## Famílias comprovadas

`a_*` corresponde ao título observado **APLICACAO COM RECURSOS DO FUNDEB**. Os relatórios amostrados expõem receitas/retenções do FUNDEB, apuração, profissionais da educação básica, complementações da União e estágios empenhado/liquidado/pago.

`fundeb25a_*` corresponde ao título observado **APLICACAO DOS RECURSOS PROPRIOS EM ENSINO - POR DATA**, com referência ao art. 256 da Constituição do Estado de São Paulo. O relatório acompanha receita de impostos, aplicação mínima de 25%, despesas próprias em Educação e retenções ao FUNDEB.

## Regra temporal principal

O bloco final de 14 dígitos do filename é somente `filename_timestamp_token`. **Não é tratado como data de geração, emissão, competência ou posição fiscal.**

O contraexemplo decisivo é `DOC-074` (`fundeb25a_137_0_4_13022026173134.pdf`): apesar do token `13022026173134`, o corpo do relatório imprime data `21/10/2025` e `POSICAO EM 30/09/2025`.

Além disso, `DOC-026`, `DOC-032` e `DOC-036` compartilham o token `13022026173759`, mas seus seletores diferentes apontam, no corpo dos relatórios, para posições 31/10/2025, 30/11/2025 e 31/12/2025. Isso prova que o token sozinho não resolve a posição contábil.

Portanto:

- `report_printed_date` só existe quando lida no corpo;
- `position_date` só existe quando lida no corpo;
- `selector_1` e `selector_2` permanecem opacos até existir contrato oficial que lhes dê significado.

## Não duplicação

Os snapshots de maio/2026 das duas famílias reproduzem métricas já conhecidas da camada F02 local-monitoring-only. Eles servem para corroborar proveniência, não para criar segunda contagem.

A TASK 190 continua sendo a camada oficial para o RREO Anexo 8 jan–abr/2026. A TASK 230 continua sendo a série oficial RREO B1/B2. Nenhum portal snapshot é equiparado automaticamente a essas camadas.

## Decisão de promoção

- fingerprints promovidos: **50**;
- amostras com data/posição comprovadas no corpo: **10**;
- fatos financeiros novos promovidos: **0**;
- mudança da cobertura contextual: **0**.

## Guardas

- `FILENAME_TIMESTAMP_TOKEN_NE_REPORT_PRINTED_DATE`
- `FILENAME_TIMESTAMP_TOKEN_NE_FISCAL_POSITION_DATE`
- `OPAQUE_SELECTOR_NE_SEMANTIC_DIMENSION`
- `PORTAL_SNAPSHOT_NE_NEW_FACT`
- `SAME_POSITION_SAME_METRIC_NE_NEW_CONTEXTUAL_COVERAGE`
- `CONFERENCE_MONITORING_REPORT_NE_OFFICIAL_PUBLISHED_COMPLIANCE_STATEMENT`
- `FUNDEB_PORTAL_NE_RREO_ANEXO8_BY_DEFAULT`
- `25PCT_PORTAL_NE_MDE_RREO_BY_DEFAULT`
- `COMMITTED_NE_LIQUIDATED_NE_PAID`
- `NO_DOUBLE_COUNT_WITH_F02_TASK190_TASK230`
- `NO_CONTEXTUAL_COVERAGE_CHANGE`

## Não efeitos

Sem aquisição de rede nova, sem escrita no Drive, sem serving/publicação, sem agenda e sem recorrência. A cobertura permanece 38/38.
