# Release Notes — 0.6.3 ACTIVE

## Marco

M5 — observabilidade auditável e operacional promovida após gate ao vivo.

## Promoção

A candidata `0.6.3` foi validada no workflow manual `ROBO DADOS PUBLICOS`, run `32782732233`, sobre o commit `72734c5257718b7f879b10d218e7c41da6396df2`.

O gate concluiu com:

- `PASS_LIVE_PREFLIGHT` com 31/31 checks;
- 130/130 testes unitários;
- 109/109 regressões históricas;
- `PASS_GITHUB_LIVE_GATE` com 7/7 checks de runtime;
- `overall_health = HEALTHY`;
- `privacy_status = PASS`;
- estado remoto `REPLACED`;
- log append-only criado;
- `PASS_M5_OBSERVABILITY_RUNTIME_GATE`.

## Relatório operacional

O run publicou o artifact `observability-report-32782732233`, com 6 arquivos e 4.070 bytes:

- `report.md`;
- `report.json`;
- `cards/run.json`;
- `cards/source_execution.json`;
- `cards/metrics.json`;
- `cards/health.json`.

A revisão do pacote confirmou ausência de credenciais, tokens, chaves `remote_id` e chaves SHA/hash brutas. A evidência bruta do gate permaneceu somente no diretório temporário do runner.

A execução de fonte aparece como `NOT_CONFIGURED`, por desenho: esse gate não reabriu a coleta histórica. Isso não equivale a zero coletado nem a falha.

## Capacidades ativas

- `SOURCE_CARD`, `RUN_CARD` e `METRIC_CARD` tipados;
- saúde multidimensional sem escore composto oculto;
- distinção explícita entre zero, ausência esperada, vazio, desconhecido, incompleto, desatualizado e falha;
- GitHub Actions Summary legível por execução;
- artifact sanitizado por run, com retenção de 30 dias;
- propagação fail-closed do resultado do runtime após tentativa de diagnóstico.

## Segurança preservada

A promoção não habilita novas fontes, recorrência, agenda, reexecução dos gates históricos, reconciliação ampla ou promoção automática de identidade financeira. O TDA permanece bloqueado sem endpoint/export público comprovado.

## Próximo marco

`M6_PRODUCT_MINIMAL_OUTPUT_DESIGN_0_7_0`: desenhar a primeira saída de produto para leitura humana sem transformar a observabilidade em um aplicativo complexo prematuramente.
