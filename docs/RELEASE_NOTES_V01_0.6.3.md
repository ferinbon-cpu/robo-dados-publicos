# Release Notes — 0.6.3 CANDIDATE

## Marco

M5 — observabilidade auditável e operacional, derivada do referencial acadêmico consolidado.

## Base

Última release ativa validada: `0.6.2 ACTIVE`.

## Incrementos

- novo pacote `robo_dados_publicos.observability`;
- `SOURCE_CARD` para documentação operacional de fontes;
- `RUN_CARD` para rastrear execução e latência;
- `METRIC_CARD` com fórmula e semântica explícita de nulos;
- saúde separada em atualidade, completude, consistência, coleta e latência;
- distinção entre zero, ausência esperada e falha;
- primeiro cartão para a edição 7310 do Jornal Oficial;
- relatório operacional sanitizado após o runtime gate;
- GitHub Actions Summary para leitura humana imediata;
- artifact `observability-report-<github.run_id>` com retenção de 30 dias;
- `report.md`, `report.json` e cartões separados para execução, fonte, métricas e saúde;
- falha do runtime é propagada depois da tentativa de geração do diagnóstico.

## Privacidade e segurança

A projeção operacional é allowlist-only. A evidência bruta do gate fica em `$RUNNER_TEMP` e não é publicada. Secrets, hashes e identificadores remotos não entram no artifact.

A observabilidade não adiciona escrita em Bronze/Silver/Gold/Bancos/Logs. O runtime já autorizado continua responsável somente pelo estado e log append-only previstos no gate.

Continuam desabilitados:

- agendamento;
- coleta recorrente;
- novas fontes;
- repetição dos gates históricos de coleta/processamento/reconciliação;
- reconciliação ampla;
- promoção automática de identidade financeira.

A 0.6.3 permanece `CANDIDATE`. A 0.6.2 continua a última versão `ACTIVE` validada.

## Gate offline consolidado

CI run `32782156537`, execução nº `48`, commit `9408783ff07ff0c85fd247a84486f2bc76411801`:

- preflight: `31/31 PASS`;
- compileall: `PASS`;
- unitários: `130/130 PASS`;
- contratos tipados de observabilidade: `9/9 PASS`;
- relatório operacional: `9/9 PASS`;
- regressões históricas: `109/109 PASS`.

## Próximo gate

`M5_OBSERVABILITY_RUNTIME_REPORT_GATE_0_6_3`.

A promoção para `ACTIVE` exige decisão e PR separados depois de uma execução manual controlada que comprove Summary, artifact e contrato de privacidade.
