# TASK 005 — avaliação offline de promoção estrutural do regime SIOPE 2025

## Escopo e decisão

A TASK 005 é estritamente `T0_OFFLINE`. Ela não executa acesso à fonte, Drive, persistência, publicação, nova autorização, retry, paginação ou alteração de workflow.

A evidência pinada da TASK 004C permite uma **promoção estreita e estrutural** de 2025. Ela não permite promover 2025 para a mesma classe semântica/fechada de 2017–2024.

Decisão canônica:

- `2025 status = PROVEN_STRUCTURAL_RECENT`;
- `P6 = PROVEN_AVAILABLE_CLOSURE_UNKNOWN`;
- recurso `Dados_Gerais_Siope = PROVEN` para a observação 2025;
- schema de 52 campos = `PROVEN_2025_P6_SCHEMA`;
- 11 campos necessários ao contrato Gold = presentes e provados **no P6 observado**;
- fechamento anual = `UNKNOWN`;
- comparabilidade semântica com 2017–2024 = `UNKNOWN`;
- elegibilidade para série anual fechada = não promovida; a série canônica permanece 2016–2024;
- 8 métricas Gold = `UNKNOWN`, não calculadas;
- 2026 = `UNPROVEN_CURRENT_YEAR`, fora do escopo.

## Evidência reconciliada

A evidência determinística é `docs/evidence/TASK_004C_SIOPE_2025_SECOND_LIVE_SUCCESS_0.8.0.json`, derivada do run `33204578436`, job `98962254951`.

Ela registra:

- P1, P2, P3, P4, P5 e P6 com identidade exata de Limeira/SP, HTTP 200, `application/json` e cardinalidade 1;
- um 7º GET condicional em P6, executado somente após P6 exato;
- schema P6 com exatamente 52 campos;
- SHA-256 dos nomes de campos `cd601ba7ee604df2e157028a2a18eefa226659fcbe0f2288937d3342d00e12a6`;
- presença dos 11 campos de entrada exigidos pelo contrato Gold;
- zero retry, redirect, paginação, `nextLink`, Drive, persistência de valores, B/S/G e publicação;
- resultado semântico do runner: `2025_P6_SCHEMA_EXACT_SEMANTICS_AND_CLOSURE_UNKNOWN`.

O timeout do primeiro live run da TASK 004B não produz observação válida conflitante: ele apenas registra uma tentativa P1 sem resposta dentro de 60 segundos. O segundo run é a evidência positiva válida.

## Matriz PROVEN / OBSERVED / UNKNOWN

| Aspecto | Estado TASK 005 | Interpretação |
| --- | --- | --- |
| Recurso `Dados_Gerais_Siope` em 2025 | PROVEN | O mesmo recurso oficial respondeu para P1–P6 com identidade exata |
| Disponibilidade P1–P6 | PROVEN | Os seis períodos responderam com cardinalidade 1 |
| Disponibilidade de P6 | PROVEN | P6 respondeu e habilitou a fase condicional de schema |
| Papel de P6 como período anual | OBSERVED_SUPPORTED_CANDIDATE | Estruturalmente compatível com 2017–2024, mas fechamento anual não foi provado |
| Schema P6 de 52 campos | PROVEN | Prova restrita à resposta P6 observada em 2025 |
| 11 inputs Gold em P6 | PROVEN_PRESENT | Presença de campos, não valores, semântica ou métricas |
| Fechamento anual 2025 | UNKNOWN | Disponibilidade de P6 não equivale a declaração final/fechada |
| Comparabilidade semântica 2017–2024 ↔ 2025 | UNKNOWN | Requer reconciliação de definições e fórmulas |
| Elegibilidade para série anual fechada | UNKNOWN / não promovida | `closed_annual_series.last_year` permanece 2024 |
| 8 métricas Gold | UNKNOWN | Nenhuma métrica é calculada nesta TASK |
| Compliance MDE/Fundeb | NOT_PROVEN_OUT_OF_SCOPE | Proibido inferir a partir desta evidência |
| Causalidade | NOT_PROVEN_OUT_OF_SCOPE | Fora do contrato |
| 2026 | UNPROVEN_CURRENT_YEAR | Sem promoção, fora do escopo |

## Por que P6 não vira “fechamento anual provado”

A TASK 004C provou que P6 **existe e responde** em 2025. Isso é suficiente para deixar de tratar P6 como mera hipótese de disponibilidade.

Não há, porém, evidência pinada que diferencie de modo explícito:

1. P6 disponível;
2. P6 transmitido/retificado;
3. P6 final/fechado para o exercício;
4. P6 semanticamente comparável ao consolidado usado em 2017–2024.

Por isso, o estado correto é `PROVEN_AVAILABLE_CLOSURE_UNKNOWN`, e não `PROVEN` no mesmo sentido dos anos históricos fechados.

## Evidência ainda necessária para fechamento anual

Uma promoção de `annual_closure_status` exige gate separado e evidência independente, por exemplo um indicador explícito do próprio SIOPE/FNDE ou documentação oficial pinada que prove que P6 é o estado final/fechado do exercício 2025, além de uma regra determinística que impeça confundir “P6 disponível” com “P6 fechado”.

Nenhum novo GET é autorizado pela TASK 005.

## Evidência ainda necessária para comparabilidade semântica

Antes de usar 2025 junto da série 2017–2024 para as 8 métricas Gold, é necessário reconciliar offline:

- definições dos 11 campos de entrada;
- numeradores e denominadores das 8 fórmulas;
- natureza contábil de previsão, realização, dotação, empenho, liquidação e pagamento;
- população usada nos indicadores per capita;
- eventuais alterações de regra, campo ou metodologia em 2025;
- tratamento de retificações e condição de fechamento.

A mera presença dos 11 campos não resolve essas questões.

## Mudanças de estado autorizadas nesta TASK

`config/siope_historical_regimes.v1.json` passa a registrar 2025 como `STRUCTURALLY_PROVEN_2025`, sem incluir 2025 em `closed_annual_series`.

`config/siope_historical_evidence_matrix.v1.json` passa a registrar a superfície, P6 estrutural e schema 52 como evidência interna estrutural provada, mantendo semântica e fechamento pendentes.

`config/siope_2025_regime_promotion_assessment.v1.json` é a matriz canônica da decisão desta TASK.

O gate `scripts/github_siope_2025_regime_promotion_gate.py` falha fechado se alguém tentar, dentro desta evidência, promover fechamento, Gold, 2026, future batch ou live execution.

## O que não muda

- `closed_annual_series = 2016–2024`;
- `future_batch_execution_authorized=false`;
- `live_discovery_authorized=false`;
- 2026 continua `UNPROVEN_CURRENT_YEAR`;
- nenhum workflow live é alterado;
- nenhuma autorização live é criada;
- nenhuma métrica financeira é calculada;
- nenhum valor financeiro novo é introduzido;
- nenhuma conclusão MDE/Fundeb/compliance/causal é produzida.

## Próximo gate

A próxima decisão lógica é separar dois trabalhos também fail-closed:

1. **prova de fechamento anual 2025**;
2. **revisão de comparabilidade semântica 2025 versus 2017–2024**.

Somente depois desses gates 2025 pode ser avaliado para entrada na série anual fechada e, em etapa ainda separada, para cálculo das 8 métricas Gold.
