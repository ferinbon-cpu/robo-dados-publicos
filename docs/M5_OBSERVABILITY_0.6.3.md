# M5 — Observabilidade candidata 0.6.3

## Objetivo

A candidata `0.6.3` adiciona uma camada somente leitura para tornar fontes, execuções e métricas explicitamente observáveis antes de qualquer expansão de coleta, agendamento ou painel de produto.

A release ativa permanece `0.6.2`. Esta candidata não promove versão, não repete coleta/processamento/reconciliação e não habilita recorrência.

## Contratos introduzidos

- `SOURCE_CARD`: instituição, URL, formatos, periodicidade, escopo, campos, licença, riscos, responsável e limiar de atualização quando aplicável.
- `RUN_CARD`: execução, versão, início/fim, status, artefatos, contagens, avisos, motivo de falha e latência calculada.
- `METRIC_CARD`: definição, fórmula, unidade, campos de origem, semântica de nulos, limitações e exemplo.
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

`config/observability.jornal_oficial_7310.json` descreve a edição 7310 do Jornal Oficial, já utilizada nos gates M4E. URL, formato e periodicidade devem continuar coerentes com `config/sources.jornal_oficial_7310_gate.json`.

## Gate de aceite da candidata

A `0.6.3` só pode avançar após:

1. testes de cartões e saúde aprovados;
2. suíte unitária integral aprovada;
3. regressões históricas aprovadas;
4. `compileall` aprovado;
5. preflight offline aprovado;
6. confirmação de que workflow continua sem agenda, recorrência e reruns dos gates históricos;
7. confirmação de que a release ativa continua `0.6.2` até decisão separada de promoção.

## Base acadêmico-metodológica

O desenho deriva da matriz consolidada `MD_00_1_REFERENCIAL_ACADEMICO_E_MATRIZ_DE_INCORPORACAO_V02.md`, especialmente das contribuições de Data Cards, completude de dados abertos, dimensões de qualidade de metadados e práticas de metadados. A literatura fundamenta requisitos e critérios de aceite; não é tratada como prova de capacidade implementada sem teste.

## Fora do escopo

- painel web ou Google Sheets;
- relatório PDF/HTML de produto;
- novas fontes;
- agendamento;
- coleta recorrente;
- reconciliação ampla;
- promoção automática de identidade financeira;
- GraphRAG ou mineração avançada.
