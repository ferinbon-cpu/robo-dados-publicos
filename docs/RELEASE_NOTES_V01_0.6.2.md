# Release 0.6.2 CANDIDATE

## Escopo

Preparar a primeira execução controlada da fila de reconciliação sem ampliar silenciosamente o runtime já validado na 0.6.1.

## Capacidade adicionada

- contrato fail-closed em `config/reconciliation.first_contract_gate.json`;
- elegibilidade fail-closed por número de contrato ou nome de fornecedor;
- seleção determinística por prioridade decrescente e `task_id` crescente entre tarefas elegíveis;
- exatamente uma tarefa `READY_SEARCH` pesquisável de `LIMEIRA_CONTRATOS`;
- execução vinculada ao `task_id` escolhido, sem nova seleção interna;
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
- testes unitários: 108/108 PASS;
- regressões históricas: 109/109 PASS;
- testes específicos do gate: 6/6 PASS;
- preflight: PASS_OFFLINE.

## Estado

A primeira tentativa ao vivo parou com segurança em `STOP_MISSING_CONTRACT_OR_SUPPLIER_KEY`, exit code 13 e `remote_writes: NONE`. O seletor foi corrigido para preservar e pular tarefas sem chave mínima antes da rede. A 0.6.1 continua sendo a release ativa; a 0.6.2 permanece candidata até uma nova execução manual bem-sucedida e uma promoção separada.
