# M4E — Primeira execução controlada de reconciliação — 0.6.2

## Objetivo

Executar uma única busca no cadastro municipal de contratos e comprovar que o ciclo `checkout local → processar → validar → replace controlado` preserva as regras V16/V17 de identidade.

## Contrato obrigatório

1. estado remoto existente em `06_BANCOS`;
2. exatamente uma tarefa `READY_SEARCH` pesquisável, com número de contrato ou nome de fornecedor;
3. alvo único `LIMEIRA_CONTRATOS`;
4. tarefas sem a chave mínima são preservadas e puladas antes de qualquer chamada de rede;
5. entre as tarefas elegíveis, seleção por prioridade decrescente e `task_id` crescente;
6. o executor recebe exatamente o `task_id` escolhido pelo gate, sem segunda seleção independente;
7. resultado final somente `MATCH_CANDIDATE` ou `NO_MATCH`;
8. TCE-SP, TDA, licitações e SIAVE sem alteração;
9. zero relações `financial_identity`;
10. evidências, quando existirem, somente `CANDIDATE_ONLY`;
11. estado substituído e log append-only criados apenas após PASS integral;
12. saída sanitizada sem secrets, IDs remotos, IDs de tarefa ou dados dos candidatos.

## Primeira tentativa ao vivo

A primeira execução encontrou uma tarefa `LIMEIRA_CONTRATOS` sem número de contrato nem nome de fornecedor. O resolver retornou `STOP_MISSING_CONTRACT_OR_SUPPLIER_KEY`; o gate encerrou com exit code 13 e `remote_writes: NONE`. Nenhum estado remoto ou log foi gravado.

Essa evidência revelou uma divergência entre o seletor do gate e a pré-condição do resolver. A correção mantém a tarefa incompleta em `READY_SEARCH`, filtra a elegibilidade sem rede e vincula o executor ao `task_id` selecionado.

## Execução bem-sucedida

A execução manual nº 8, sobre o commit `bca696c`, concluiu em 33 segundos com `PASS_GITHUB_RECONCILIATION_EXECUTION_GATE` e comprovou:

1. cinco tarefas `READY_SEARCH` no alvo permitido e duas elegíveis;
2. seleção e execução exata de uma tarefa `LIMEIRA_CONTRATOS` com chave mínima;
3. resultado terminal `MATCH_CANDIDATE`;
4. uma aresta de evidência `CANDIDATE_ONLY` e zero relações `financial_identity`;
5. alvos protegidos inalterados;
6. estado remoto `REPLACED` e log append-only criado;
7. nenhum secret, identificador remoto, `task_id` ou payload candidato exposto.

## STOP

Qualquer falha operacional, ausência de tarefa elegível, seleção ampliada, resultado não permitido, alteração de alvo protegido ou tentativa de promoção financeira produz STOP. Nesse caso, o arquivo remoto de estado não é substituído e nenhum log de reconciliação é criado.

## Estado após promoção

O workflow permanece somente manual, mas `confirm_reconciliation` e a chamada de `scripts/github_reconciliation_gate.py` foram removidos após a promoção. Nenhum PASS habilitou repetição do gate, reconciliação ampla, recorrência ou agendamento.
