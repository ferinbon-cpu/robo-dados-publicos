# M4D — GitHub offline readiness — 2026-08-23

## Decisão

Preparar integralmente o repositório enquanto a conexão GitHub estiver indisponível, sem alterar a release ativa nem antecipar resultado do gate remoto.

## Achado corrigido

O pacote 0.5.8 apontava para `actions/checkout@v7`, mas a release pública corrente confirmada durante a auditoria era v6.0.2. A candidata 0.5.9 usa o SHA completo da v6.0.2. O `setup-python` v7.0.0 também foi fixado pelo SHA completo.

## Controles adicionados

1. trigger exclusivamente manual;
2. confirmação booleana obrigatória antes de qualquer persistência;
3. `contents: read` e `persist-credentials: false`;
4. preflight de identidade e segurança sem revelar secrets;
5. validação automática de `REMOTE_EXISTING`, `REPLACED` e criação de `ROBO_RUN_*`;
6. Dependabot semanal apenas para GitHub Actions;
7. `.gitignore` para tokens, credenciais, bancos e runtime local.

## Fronteira de evidência

`PASS_OFFLINE` prova somente que o repositório está pronto para publicação e execução. `PASS_GITHUB_LIVE_GATE` exige conexão, Repository Secrets válidos e um run hospedado pelo GitHub com persistência confirmada no Drive.

QA concluído: compileall PASS, 84/84 testes unitários PASS, 109/109 regressões históricas PASS, inventário de fontes PASS e preflight `PASS_OFFLINE`.

## Preservação

- 0.5.8 ACTIVE: imutável;
- 0.5.9: CANDIDATE;
- 06_BANCOS: sem escrita nesta etapa;
- 07_LOGS: sem escrita nesta etapa;
- TDA: bloqueado;
- identidade financeira: fail-closed.
