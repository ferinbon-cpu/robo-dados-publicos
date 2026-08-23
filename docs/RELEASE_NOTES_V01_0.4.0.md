# ROBO_DADOS_PUBLICOS SOFTWARE V01 — 0.4.0

## Marco
M4C — runtime preparado para execução não interativa, estado remoto persistente e agendamento em nuvem.

## Novidades
- comando único `run`;
- `cloud-preflight` para validar a topologia canônica da raiz;
- `ROBOT_STATE.sqlite` persistente em `06_BANCOS`;
- log JSON durável por execução em `07_LOGS`;
- registro de runs no SQLite;
- `EnvironmentAccessTokenProvider` para bridges controladas com token efêmero;
- `Dockerfile` e scripts de Cloud Run Job / Cloud Scheduler;
- separação explícita entre runtime de infraestrutura e coleta de fontes ainda não configurada.

## Gates
- raiz incompleta/duplicada → `STOP_REPOSITORY_LAYOUT`;
- estado remoto duplicado → STOP;
- regressão histórica falha → `STOP_QA_FAILED`;
- blocker analítico V17 é preservado.

## Escopo desta release
A 0.4.0 **não** afirma que o agendamento permanente já está implantado. Ela prepara e testa o runtime. A implantação permanente depende de billing habilitado e de uma credencial OAuth de longa duração armazenada fora do código.
