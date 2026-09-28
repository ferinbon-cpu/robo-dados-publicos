# TASK284 — aquisição unitária do testemunho de namespace

Issue #907. Esta PR registra separadamente o contrato, o preflight offline e a evidência sanitizada da única sessão manual já executada. **Não altera `config/automation_policy.v1.json`**; a revisão/registro de política T1 ocorre em PR própria empilhada sobre esta.

## Escopo

A TASK284 foi autorizada pelo prompt explícito do proprietário em 26/09/2026. Não autoriza execução automática, não consome TASK281 e não adiciona workflow.

O contrato limitou a sessão a uma navegação inicial, uma possível abertura determinística da área Despesa e uma única consulta alvo, somente após prova do binding da sessão. Zero retries, PNCP, paginação, batch, escrita na fonte ou persistência de cookies/tokens.

## Preflight

O módulo `task284_tda_binding_gate.py` é exclusivamente offline. Ele valida a forma de uma observação de DOM fornecida pelo operador e não implementa navegador, HTTP ou execução remota.

Um PASS desse módulo significaria apenas que o binding observado satisfaz o contrato para uma consulta manual. Não provaria identidade TDA–TCE nem autorizaria pagamento.

## Resultado histórico

A sessão autorizada terminou em:

`STOP_AREA_IDENTITY_NOT_PROVEN_BEFORE_TOP_ACTION`.

A página oficial carregou e quatro bindings inline da área Despesa convergiram para o mesmo destino, mas a identidade `AreaOrigin` não pôde ser comprovada na superfície DOM disponível.

Contadores observados:

- 1 sessão;
- 1 navegação inicial;
- 0 ações de área;
- 0 consultas;
- 0 atribuições a campos;
- 0 retries;
- 0 PNCP;
- 0 TCE live;
- 0 escrita na fonte.

A autorização daquela sessão foi consumida. Este registro **não autoriza retry** e não é evidência negativa da existência do empenho 3286/2026.

## Lacuna científica

Um eventual resultado de filtro que mostrasse `03286-01` para uma busca por `3286` ainda não seria suficiente por si só. A prova positiva continua exigindo documento oficial ou regra oficial aplicável que relacione:

- TDA `03286-01`;
- número contábil `3286`;
- exercício original `2026`;
- Prefeitura Municipal de Limeira.

A alternativa preferida permanece a Nota de Empenho original ou o extrato/crosswalk de integração municipal → AUDESP.

## Governança

Esta PR deliberadamente não registra a TASK284 na política de automação. A mudança de política é isolada em PR própria, conforme a exigência de revisão explícita do `AGENTS.md`.

Nenhum self-merge. A integração correta permanece encadeada após TASK282 e TASK283.
