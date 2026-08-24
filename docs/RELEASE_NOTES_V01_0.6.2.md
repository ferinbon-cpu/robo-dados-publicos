# Release 0.6.2 CANDIDATE

## Escopo

Preparar a primeira execução controlada da fila de reconciliação sem ampliar silenciosamente o runtime já validado na 0.6.1.

## Capacidade adicionada

- contrato fail-closed em `config/reconciliation.first_contract_gate.json`;
- seleção determinística por prioridade decrescente e `task_id` crescente;
- exatamente uma tarefa `READY_SEARCH` de `LIMEIRA_CONTRATOS`;
- resultados terminais permitidos: `MATCH_CANDIDATE` ou `NO_MATCH`;
- substituição do estado e log append-only somente após PASS integral;
- saída pública sanitizada, sem IDs remotos, identificadores de tarefas ou payloads candidatos.

## Proteções

- TCE-SP, TDA, licitações e SIAVE não são executados;
- o TDA permanece bloqueado sem endpoint/export público comprovado;
- `MATCH_CANDIDATE` gera apenas evidência documental `CANDIDATE_ONLY`;
- relação `financial_identity` é proibida;
- falha operacional preserva o estado remoto anterior e não cria log;
- coleta, processamento, recorrência e agendamento continuam desabilitados.

## QA offline

- compileall: PASS;
- testes unitários: 106/106 PASS;
- regressões históricas: 109/109 PASS;
- testes específicos do gate: 4/4 PASS;
- preflight: PASS_OFFLINE.

## Estado

O gate ao vivo ainda não foi executado. A 0.6.1 continua sendo a release ativa até uma execução manual bem-sucedida e uma promoção separada.
