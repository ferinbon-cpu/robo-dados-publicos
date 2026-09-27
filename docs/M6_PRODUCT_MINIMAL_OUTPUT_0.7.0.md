# M6 — Saída mínima de produto candidata 0.7.0

## Objetivo

Transformar respostas estruturadas do robô em uma saída que uma pessoa consiga abrir, ler, conferir e compartilhar sem construir um aplicativo completo e sem apagar as fronteiras entre dado, cálculo, correspondência, interpretação, cautela e fonte.

A release ativa permanece `0.6.3`. A `0.7.0` é candidata.

## Decisão de arquitetura

O produto mínimo é um **bundle de arquivos**, não uma aplicação web.

O bundle contém:

1. `report.json` — conteúdo estruturado completo;
2. `report_card.json` — metadados e estado do relatório;
3. `table.csv` — visão tabular interoperável e futura fonte de Google Sheets;
4. `report.md` — leitura textual simples;
5. `report.html` — leitura local em navegador;
6. `report.pdf` — documento portátil;
7. `manifest.json` — inventário e hashes.

Isso permite testar utilidade e linguagem antes de assumir custo de UI, backend, autenticação e manutenção de um aplicativo.

## REPORT_CARD

Campos mínimos:

- `report_id`;
- `title`;
- `scope`;
- `software_version`;
- `generated_at` com timezone;
- `status`;
- `row_count`;
- `formats`;
- `limitations`;
- `notes`.

Estados permitidos:

- `READY`;
- `READY_WITH_CAUTION`;
- `EVIDENCIA_INSUFICIENTE`;
- `NO_DATA`.

## Contrato tabular

As colunas não inventam uma ontologia nova. Reutilizam o contrato já existente:

`status | DADO | CÁLCULO | CORRESPONDÊNCIA | INTERPRETAÇÃO | CAUTELA | FONTES`

Regras:

- `0` observado não pode virar ausência;
- `EVIDENCIA_INSUFICIENTE` não pode ser mascarada como resultado conclusivo;
- qualquer cautela torna o relatório `READY_WITH_CAUTION`;
- a apresentação não é evidência;
- referências de fonte mantêm proveniência, mas valores de parâmetros de URL associados a token, segredo, assinatura ou autenticação são redigidos.

## PDF

O PDF é gerado localmente com `reportlab==5.0.0` e usa fontes internas do PDF; não há distribuição de arquivos de fonte. Cada resposta é exibida como bloco legível em vez de uma tabela horizontal comprimida.

## Google Sheets e 08_OUTPUTS

`config/cloud.json` já contém `outputs_id` para a pasta `08_OUTPUTS`.

Nesta candidata:

- `table.csv` é declarado como `google_sheets_import_source`;
- `08_OUTPUTS` é declarado como `drive_target`;
- não existe publicação remota;
- não existe conversão para Google Sheets;
- o workflow de produção não chama o construtor de produto.

A publicação será implementada apenas depois do gate offline e deverá ter confirmação manual, allowlist de arquivos, tratamento de duplicidade e evidência de integridade.

## Gate de aceite offline

A candidata só pode avançar se:

1. `ReportCard` rejeitar timestamps sem timezone e estados inválidos;
2. estados `NO_DATA` e `EVIDENCIA_INSUFICIENTE` forem preservados;
3. cautela impedir `READY` limpo;
4. URLs de fonte com parâmetros sensíveis forem redigidas;
5. CSV preservar as sete colunas do contrato;
6. HTML escapar conteúdo;
7. PDF for gerado e tiver assinatura PDF válida;
8. manifesto conferir bytes e SHA-256;
9. nenhum código de publicação no Drive estiver alcançável pelo construtor local;
10. CI, compileall e regressões históricas permanecerem verdes.

## Fora do escopo desta candidata

- upload para `08_OUTPUTS`;
- criação real de Google Sheets;
- dashboard;
- aplicação web;
- autenticação de usuário final;
- agendamento;
- nova coleta;
- rerun dos gates históricos;
- GraphRAG.
