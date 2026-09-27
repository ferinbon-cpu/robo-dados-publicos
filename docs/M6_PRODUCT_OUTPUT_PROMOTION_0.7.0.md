# M6 — Promoção da saída mínima de produto 0.7.0

## Gate ao vivo auditado

- workflow: `M6 PRODUCT OUTPUT PUBLICATION GATE`;
- run: `32787729769`;
- job: `97622956591`;
- commit: `a8de99a8fbffc85e8e57b909a80fd701fe28fef7`;
- resultado: `PASS_M6_PRODUCT_OUTPUT_PUBLICATION_GATE`;
- preflight: 49/49 PASS;
- unitários: 163/163 PASS;
- regressões históricas: 109/109 PASS;
- dry-run: sem rede e sem escrita remota;
- escrita real: exatamente 3 itens, sem overwrite.

## Evidência em 08_OUTPUTS

1. `ROBO_DADOS_PUBLICOS_M6_GATE_0_7_0_TABELA` — Google Sheets nativo;
2. `ROBO_DADOS_PUBLICOS_M6_GATE_0_7_0.pdf` — PDF;
3. `ROBO_DADOS_PUBLICOS_M6_GATE_0_7_0_publication_manifest.json` — manifesto JSON gravado por último.

A planilha contém as sete colunas do contrato de resposta e uma linha técnica não vazia. O PDF foi renderizado e revisado visualmente. O manifesto confirma `software_version=0.7.0`, `report_status=READY_WITH_CAUTION`, `overwrite_allowed=false` e `completion_marker_written_last=true`.

## Limite semântico

O primeiro relatório publicado é um artefato técnico de validação da camada de produto. Não constitui análise substantiva sobre orçamento, contratos, fornecedores, pessoas, órgãos ou políticas públicas.

## Segurança após promoção

O script do gate M6 exige `RELEASE_STATUS=CANDIDATE`, `ACTIVE_VALIDATED_VERSION=0.6.3` e `CURRENT_CANDIDATE_VERSION=0.7.0`. Depois da promoção para `0.7.0 ACTIVE`, uma nova tentativa é bloqueada antes de rede/escrita. Coleta, processamento, reconciliação ampla, agenda e recorrência permanecem fora do gate.

## Próximo marco

`M7_CONTROLLED_SOURCE_EXPANSION_DESIGN_0_8_0`.
