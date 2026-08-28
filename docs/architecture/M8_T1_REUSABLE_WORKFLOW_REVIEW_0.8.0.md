# M8 — reusable workflow T1 read-only 0.8.0

## Objetivo

Separar o worker M8 T1 read-only do ponto de entrada manual, sem habilitar no-click e sem reduzir a classificação de risco.

## Arquitetura

O ponto de entrada humano continua sendo `.github/workflows/m8-siope-historical-gold-product-output-readonly-gate.yml`, exclusivamente `workflow_dispatch`, com confirmação booleana explícita e `permissions: contents: read`.

O trabalho bounded foi movido para `.github/workflows/m8-siope-historical-gold-product-output-readonly-reusable.yml`, que expõe somente `workflow_call`. O contrato declara explicitamente os três secrets dedicados:

- `GOOGLE_DRIVE_READONLY_CLIENT_ID`;
- `GOOGLE_DRIVE_READONLY_CLIENT_SECRET`;
- `GOOGLE_DRIVE_READONLY_REFRESH_TOKEN`.

O wrapper passa os três secrets nominalmente. `secrets: inherit` é proibido por teste e pelo gate de policy. O reusable não possui `workflow_dispatch`, `push`, `pull_request`, `workflow_run` ou `schedule`.

## Segurança preservada

O worker mantém `permissions: contents: read`, checkout sem persistência de credenciais, prova runtime de scope OAuth exatamente `drive.readonly` antes da primeira leitura do Drive, preflight dos nove Gold e todos os bloqueios já provados na primeira execução live.

A criação do reusable não executa M8 e não acrescenta caller automático. `auto_allowed` permanece `false` na policy. A primeira prova live pinada continua sendo o run `33136736495`, job `98738273929`, artifact `9672319372`.

## No-click continua bloqueado

A presença de `workflow_call` não constitui autorização de execução automática. Os bloqueadores remanescentes são:

1. o wrapper atual ainda exige confirmação humana;
2. `main` permanece sem trust boundary protegida (`protected=false` no último readback GitHub);
3. o trusted orchestrator ainda não foi desenhado/revisado em mudança separada.

Nenhum workflow automático portador dos secrets read-only é criado nesta etapa.

## Próxima fronteira

Estabelecer branch protection/ruleset para `main` antes de qualquer caller automático portador de secrets. Depois disso, desenhar e revisar um trusted orchestrator em PR separada. A mudança que habilitar execução no-click não deve ser a mesma que rebaixa/remova seus bloqueadores de policy.

Publicação em `08_OUTPUTS`, T2/T3, 2015 ou anteriores, future batch, retry, paginação, recorrência, schedule, overwrite/delete/replace, imputação e compliance automático continuam bloqueados.
