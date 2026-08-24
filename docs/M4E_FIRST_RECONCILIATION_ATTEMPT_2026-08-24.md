# Evidência da primeira tentativa de reconciliação — 2026-08-24

## Resultado observado

- versão: `0.6.2 CANDIDATE`;
- alvo permitido: `LIMEIRA_CONTRATOS`;
- tarefas selecionadas: 1;
- resultado: `STOP_MISSING_CONTRACT_OR_SUPPLIER_KEY`;
- status do gate: `STOP_RECONCILIATION_EXECUTION_CONTRACT`;
- exit code: 13;
- escrita remota: `NONE`;
- relações `financial_identity`: 0;
- origem pública da coleta: não chamada.

## Interpretação

O bloqueio foi correto: a tarefa prioritária não possuía número de contrato nem nome de fornecedor, e uma busca ampla por objeto não é autorizada. O estado remoto e o log append-only não foram alterados.

A tentativa revelou que o seletor considerava apenas status, alvo e prioridade, enquanto o resolver também exigia uma chave mínima. A candidata foi endurecida para:

1. testar a chave mínima antes da rede;
2. preservar e pular tarefas incompletas;
3. ordenar somente as tarefas elegíveis por prioridade decrescente e `task_id` crescente;
4. transmitir ao executor exatamente o `task_id` selecionado;
5. continuar parando sem escrita se nenhuma tarefa elegível existir.

## QA da correção

- compileall: PASS;
- testes unitários: 108/108 PASS;
- testes específicos do gate: 6/6 PASS;
- regressões históricas: 109/109 PASS;
- preflight offline: PASS.

Uma nova execução manual do mesmo gate permanece necessária. Nenhum agendamento, recorrência, nova coleta ou novo processamento foi habilitado.
