# M5 — Observabilidade candidata 0.6.3

## Objetivo

A candidata `0.6.3` adiciona uma camada de observabilidade auditável antes de qualquer expansão de coleta, agendamento ou painel de produto.

A release ativa validada permanece `0.6.2`. A `0.6.3` é `CANDIDATE` e não reabre os gates históricos de coleta, processamento ou reconciliação.

## Contratos introduzidos

- `SOURCE_CARD`: instituição, URL, formatos, periodicidade, escopo, campos, licença, riscos, responsável e limiar de atualização quando aplicável;
- `RUN_CARD`: execução, versão, início/fim, status, artefatos, contagens, avisos, motivo de falha e latência calculada;
- `METRIC_CARD`: definição, fórmula, unidade, campos de origem, semântica de nulos, limitações e exemplo;
- avaliação de saúde multidimensional: atualidade, completude, consistência, coleta e latência.

Não há escore composto oculto. Cada dimensão permanece visível para auditoria.

## Semântica operacional

A observabilidade distingue explicitamente:

- `0`: valor ou contagem observada igual a zero;
- `EXPECTED_ABSENCE`: ausência legítima prevista pelo contrato;
- `EMPTY`: execução esperava registros, mas recebeu zero;
- `UNKNOWN`: não há denominador ou contagem suficiente para avaliar;
- `INCOMPLETE`: saída menor que a entrada conhecida;
- `STALE`: última execução excede o limiar configurado;
- `FAIL`: falha de coleta ou consistência.

Para uma fonte `one_time_manual_gate`, o limiar de atualização permanece `null` por desenho. Isso evita transformar um artefato histórico validado em fonte recorrente sem autorização.

## Primeiro cartão de fonte

`config/observability.jornal_oficial_7310.json` descreve a edição 7310 do Jornal Oficial, já utilizada nos gates M4E. URL, formato e periodicidade permanecem coerentes com `config/sources.jornal_oficial_7310_gate.json`.

## Camada operacional consolidada

A `0.6.3` também gera uma projeção operacional sanitizada após o runtime gate:

- **GitHub Actions Summary** para leitura imediata;
- `observability-report-<github.run_id>` como artifact por execução;
- `report.md` para leitura humana;
- `report.json` para consumo estruturado futuro;
- cartões separados de execução, fonte, métricas e saúde.

A evidência bruta do gate permanece somente em `$RUNNER_TEMP` e não é enviada ao artifact. A projeção usa allowlist explícita: secrets, hashes e identificadores remotos não são propagados.

O workflow tenta produzir o relatório mesmo quando o runtime gate termina em erro e, em seguida, propaga a falha original. Observabilidade não transforma falha operacional em sucesso.

Consulte `docs/OBSERVABILITY_RUNBOOK.md` para o caminho exato na interface.

## Gate offline consolidado

Resultado validado no CI offline, run `32782156537` / execução nº `48`, commit `9408783ff07ff0c85fd247a84486f2bc76411801`:

- preflight: `31/31 PASS`;
- `compileall`: `PASS`;
- testes unitários: `130/130 PASS`;
- testes dos contratos tipados de observabilidade: `9/9 PASS`;
- testes do relatório operacional: `9/9 PASS`;
- regressões históricas: `109/109 PASS`.

## Próximo gate

`M5_OBSERVABILITY_RUNTIME_REPORT_GATE_0_6_3`.

O gate deve comprovar, em uma execução manual controlada:

1. runtime gate aprovado;
2. Summary gerado;
3. artifact `observability-report-<run_id>` criado;
4. `report.md` e `report.json` legíveis;
5. contrato de privacidade `PASS`;
6. ausência de secrets, hashes e identificadores remotos no pacote;
7. nenhuma reabertura de coleta, processamento ou reconciliação históricos;
8. nenhum `schedule` ou recorrência.

Somente depois desse gate uma promoção da `0.6.3` para `ACTIVE` pode ser considerada em PR separado.

## Base acadêmico-metodológica

O desenho deriva da matriz consolidada `MD_00_1_REFERENCIAL_ACADEMICO_E_MATRIZ_DE_INCORPORACAO_V02.md`, especialmente das contribuições de Data Cards, completude de dados abertos, dimensões de qualidade de metadados e práticas de metadados. A literatura fundamenta requisitos e critérios de aceite; não é tratada como prova de capacidade implementada sem teste.

## Fora do escopo

- painel web próprio ou Google Sheets como camada principal;
- relatório PDF/HTML de produto;
- novas fontes;
- agendamento;
- coleta recorrente;
- reconciliação ampla;
- promoção automática de identidade financeira;
- GraphRAG ou mineração avançada.
