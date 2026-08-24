# Release Notes — 0.7.0 ACTIVE

## Marco

M6 — saída mínima de produto e primeira publicação controlada em `08_OUTPUTS` promovidas.

## Evidência de promoção

O gate manual `M6 PRODUCT OUTPUT PUBLICATION GATE` foi executado no run `32787729769`, job `97622956591`, sobre o commit `a8de99a8fbffc85e8e57b909a80fd701fe28fef7`, e concluiu com `PASS_M6_PRODUCT_OUTPUT_PUBLICATION_GATE`.

Antes da escrita real, a execução passou:

- preflight: 49/49 checks;
- compileall: PASS;
- suíte unitária: 163/163 PASS;
- regressões históricas: 109/109 PASS;
- dry-run do gate: PASS, sem rede e sem escrita remota.

## Saída validada

Foram criados exatamente três itens novos em `08_OUTPUTS`, sem overwrite:

1. `ROBO_DADOS_PUBLICOS_M6_GATE_0_7_0_TABELA` — Google Sheets nativo;
2. `ROBO_DADOS_PUBLICOS_M6_GATE_0_7_0.pdf` — PDF;
3. `ROBO_DADOS_PUBLICOS_M6_GATE_0_7_0_publication_manifest.json` — manifesto de conclusão, gravado por último.

A planilha foi relida e confirmou as sete colunas do contrato (`status`, `DADO`, `CÁLCULO`, `CORRESPONDÊNCIA`, `INTERPRETAÇÃO`, `CAUTELA`, `FONTES`) e uma linha técnica não vazia. O PDF foi baixado, renderizado e revisado visualmente, sem conteúdo vazio ou clipping. O manifesto confirmou `software_version=0.7.0`, `READY_WITH_CAUTION`, `overwrite_allowed=false` e `completion_marker_written_last=true`.

## Artifact GitHub

O run publicou apenas o artifact sanitizado `product-publication-gate-32787729769`, com `result.json`, 448 bytes, retenção de 30 dias e digest SHA-256 registrado no manifesto ACTIVE. Segredos e IDs remotos não foram expostos.

## Semântica

`READY_WITH_CAUTION` é intencional: o primeiro relatório é um artefato técnico de validação da camada de produto. Ele não representa conclusão substantiva sobre orçamento, contratos, fornecedores, pessoas, órgãos ou políticas públicas.

## Segurança preservada

- repetição do gate M6 bloqueada pela identidade ACTIVE da release;
- coleta de fontes histórica continua sem rerun no workflow;
- processamento e reconciliação históricos continuam sem rerun;
- agenda e recorrência continuam desabilitadas;
- reconciliação ampla continua desabilitada;
- promoção automática de identidade financeira continua proibida;
- TDA Limeira continua bloqueado sem endpoint/export público comprovado.

## Próximo gate

`M7_CONTROLLED_SOURCE_EXPANSION_DESIGN_0_8_0` — desenho da expansão controlada para 0.8.0. Isso não autoriza nova fonte, recorrência ou coleta automática por si só.
