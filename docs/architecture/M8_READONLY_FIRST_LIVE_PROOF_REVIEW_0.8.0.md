# M8 — revisão da primeira prova live read-only 0.8.0

## Resultado

A primeira prova live do gate `M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY` passou no run `33136736495`, job `98738273929`, sobre o `main` `8f80edcae45a373f85b84c03880842363661d870`.

A evidência canônica está em `docs/evidence/M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY_RUN_2_0.8.0.json`.

## O que foi provado

Antes de qualquer lookup/download no Drive, o workflow renovou o token dedicado e validou por tokeninfo o escopo efetivo exato `https://www.googleapis.com/auth/drive.readonly`. A prova de capability fez 2 requisições OAuth, zero chamadas à API do Drive, zero writes e não exibiu valores de secrets.

Depois da prova de capability, o gate realizou exatamente 9 lookups e 9 downloads dos Gold já persistidos de Limeira/SP, anos 2016–2024, com 2016=P1 e 2017–2024=P6. Não houve GET ao FNDE/SIOPE, write no Drive, publicação, persistência de remote file ID, retry, paginação, recorrência, schedule, imputação ou autorização de compliance.

O produto local contém 8 séries/AnswerContracts e 72 observações Gold. O artifact `9672319372`, digest `sha256:a3afeed9c1449ab4806127024d044d177e76e8097894786b0e68bbbfffc60b51`, contém `result.json` e sete arquivos de produto: JSON, report card, CSV, Markdown, HTML, PDF e manifest. Os hashes e tamanhos estão pinados na evidência e em testes fail-closed.

QA live: 1229/1229 testes unitários e 109/109 regressões históricas.

## Decisão de automação

A prova live remove o bloqueador `FIRST_LIVE_M8_READONLY_PRODUCT_GATE_NOT_YET_PROVEN`. Isso demonstra que o T1 possui credencial dedicada de menor privilégio e comportamento live compatível com o contrato read-only.

No entanto, **no-click continua BLOCK**. O `main` foi observado como `protected=false`; habilitar um trigger automático portador de secrets antes de estabelecer uma trust boundary protegida reduziria a defesa em profundidade. Além disso, o worker ainda não foi extraído para `workflow_call` com contrato explícito de secrets.

Bloqueadores atuais:

1. `CURRENT_WORKFLOW_REQUIRES_MANUAL_CONFIRMATION`;
2. `MAIN_BRANCH_NOT_PROTECTED_FOR_SECRET_BEARING_AUTOMATION`;
3. `NO_CLICK_REQUIRES_REUSABLE_WORKFLOW_AND_TRUSTED_ORCHESTRATOR_REVIEW`.

## Próxima etapa segura

A próxima etapa de engenharia é preparar a arquitetura reusable T1 e estabelecer proteção/ruleset de `main` antes de ativar um orquestrador no-click. O reusable worker deve manter `permissions: contents: read`, declarar somente os três secrets read-only dedicados e nunca usar `secrets: inherit`.

A remoção do clique deve ocorrer em mudança separada da mudança que estabelece/baixa bloqueadores, preservando a invariante `agent_may_lower_risk_tier_in_same_patch_that_enables_auto_execution=false`.

## O que esta revisão não autoriza

Esta revisão não publica o produto em `08_OUTPUTS`; não autoriza T2/T3; não abre 2015 ou anos anteriores; não autoriza future batch, retry, paginação, recorrência, schedule, overwrite/delete/replace, imputação ou conclusão automática de compliance MDE/Fundeb/auditoria fiscal.
