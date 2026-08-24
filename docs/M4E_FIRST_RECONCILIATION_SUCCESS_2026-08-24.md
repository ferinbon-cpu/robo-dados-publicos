# Evidência da primeira reconciliação bem-sucedida — 2026-08-24

## Identidade da execução

- release durante o gate: `0.6.2 CANDIDATE`;
- workflow: `M4E reconciliation gate 0.6.2`;
- sequência manual: 8;
- commit de origem: `bca696c4792fe8e6a87be716b26855f450c22459`;
- duração total informada pelo GitHub Actions: 33 segundos;
- status do wrapper: `PASS_GITHUB_RECONCILIATION_EXECUTION_GATE`;
- status do runtime persistente: `PASS_CLOUD_RECONCILIATION_EXECUTION_GATE`.

## Resultado sanitizado

- alvo permitido: somente `LIMEIRA_CONTRATOS`;
- tarefas `READY_SEARCH` no alvo permitido: 5;
- tarefas elegíveis com chave mínima: 2;
- tarefas selecionadas e executadas: 1;
- resultado terminal: `MATCH_CANDIDATE`;
- arestas de evidência candidata: 1;
- relações `financial_identity`: 0;
- estado remoto: `REPLACED`;
- log append-only: criado em `07_LOGS`;
- origem pública da coleta: não chamada.

Todos os checks de seleção e execução passaram. A tarefa escolhida continha chave mínima, foi exatamente a tarefa entregue ao executor e permaneceu dentro do alvo autorizado. TCE-SP, TDA, licitações e SIAVE não foram alterados.

## Limite probatório

`MATCH_CANDIDATE` não significa identidade jurídica ou financeira confirmada. A única aresta criada permanece `CANDIDATE_ONLY` e precisa de revisão separada sob as regras V16/V17. Nenhuma promoção automática foi autorizada.

## Privacidade e auditoria

Secrets, IDs remotos, identificadores de tarefas e payloads candidatos não foram publicados. Os identificadores, hashes e detalhes do candidato permanecem somente na auditoria privada do Drive.

## Encerramento do gate

Com o PASS, a candidata 0.6.2 pode ser promovida separadamente. A promoção remove `confirm_reconciliation` e a chamada do gate de uso único do workflow ativo. Reconciliação ampla, repetição automática, novas fontes, recorrência e agendamento continuam desabilitados.
