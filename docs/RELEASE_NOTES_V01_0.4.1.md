# ROBO_DADOS_PUBLICOS SOFTWARE V01 — 0.4.1 CANDIDATE

## Marco
M4D — adaptação do runtime 0.4.0 para GitHub Actions após bloqueio de billing do Google Cloud.

## Novidades
- workflow GitHub Actions com `workflow_dispatch`;
- execução em Python 3.12;
- OAuth por `GOOGLE_DRIVE_CLIENT_ID`, `GOOGLE_DRIVE_CLIENT_SECRET` e `GOOGLE_DRIVE_REFRESH_TOKEN` via repository secrets;
- `permissions: contents: read`;
- `concurrency` sem cancelamento da execução persistente em andamento;
- gate explícito para secrets ausentes sem imprimir valores;
- compileall + unit tests + 109 regressões antes do `run` remoto;
- `.gitignore` reforçado contra arquivos de credenciais;
- documentação do gate manual e do agendamento posterior;
- correção de `robo_dados_publicos.__version__` para acompanhar a release.

## Estado
**CANDIDATE**. Não promover para ATIVO antes de um run real pelo GitHub Actions com persistência no Drive confirmada.
