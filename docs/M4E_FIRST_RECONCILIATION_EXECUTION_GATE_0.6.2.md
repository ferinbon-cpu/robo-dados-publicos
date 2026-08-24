# M4E — Primeira execução controlada de reconciliação — 0.6.2

## Objetivo

Executar uma única busca no cadastro municipal de contratos e comprovar que o ciclo `checkout local → processar → validar → replace controlado` preserva as regras V16/V17 de identidade.

## Contrato obrigatório

1. estado remoto existente em `06_BANCOS`;
2. exatamente uma tarefa `READY_SEARCH`;
3. alvo único `LIMEIRA_CONTRATOS`;
4. seleção por prioridade decrescente e `task_id` crescente;
5. resultado final somente `MATCH_CANDIDATE` ou `NO_MATCH`;
6. TCE-SP, TDA, licitações e SIAVE sem alteração;
7. zero relações `financial_identity`;
8. evidências, quando existirem, somente `CANDIDATE_ONLY`;
9. estado substituído e log append-only criados apenas após PASS integral;
10. saída sanitizada sem secrets, IDs remotos, IDs de tarefa ou dados dos candidatos.

## STOP

Qualquer falha operacional, seleção vazia ou ampliada, resultado não permitido, alteração de alvo protegido ou tentativa de promoção financeira produz STOP. Nesse caso, o arquivo remoto de estado não é substituído e nenhum log de reconciliação é criado.

## Acionamento

O workflow permanece somente manual. A execução ao vivo exige marcar `confirm_persistence` e `confirm_reconciliation`. Nenhum PASS habilita recorrência ou agendamento.
