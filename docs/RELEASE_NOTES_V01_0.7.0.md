# Release Notes — 0.7.0 CANDIDATE

## Marco

M6 — saída mínima de produto para leitura humana.

## Base

Última release ativa validada: `0.6.3 ACTIVE`.

## Incrementos

- novo pacote `robo_dados_publicos.product`;
- `REPORT_CARD` com identificação, escopo, status, versão, data, contagem, formatos e limitações;
- preservação das colunas `status`, `DADO`, `CÁLCULO`, `CORRESPONDÊNCIA`, `INTERPRETAÇÃO`, `CAUTELA`, `FONTES`;
- estados explícitos `READY`, `READY_WITH_CAUTION`, `EVIDENCIA_INSUFICIENTE` e `NO_DATA`;
- bundle local com `report.json`, `report_card.json`, `table.csv`, `report.md`, `report.html`, `report.pdf` e `manifest.json`;
- manifesto com bytes e SHA-256 dos seis artefatos de conteúdo;
- PDF gerado por `reportlab==5.0.0`;
- parâmetros sensíveis em query strings de referências de fonte são redigidos;
- `table.csv` definido como fonte futura para importação em Google Sheets;
- `08_OUTPUTS` definido como destino futuro da camada de produto.

## Segurança

A candidata não publica nenhum arquivo no Drive e não adiciona rota de produto ao workflow de produção. O preflight confirma que `build_product_output.py` é local-only e que a camada de produto não está alcançável pelo workflow.

Coleta, processamento e reconciliação históricos permanecem sem rerun; agenda, recorrência e reconciliação ampla continuam desabilitadas; promoção automática de identidade financeira continua proibida.

## Semântica

A camada de apresentação não é evidência. Zero não é ausência. Evidência insuficiente continua marcada como tal, e cautelas impedem que o relatório seja classificado como `READY` limpo.

## Próximo gate

CI offline completo: preflight, compileall, testes unitários — incluindo a camada de produto — e regressões históricas. Somente depois será decidido o gate de publicação controlada em `08_OUTPUTS` e a conversão do CSV para Google Sheets.
