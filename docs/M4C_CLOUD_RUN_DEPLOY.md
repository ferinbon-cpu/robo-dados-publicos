# M4C — execução não interativa e agendada

## Objetivo
A release 0.4.0 prepara o `ROBO_DADOS_PUBLICOS` para execução em Cloud Run Job com um único comando:

```bash
python3 main.py run --auth oauth-env
```

O comando faz preflight da raiz do repositório, recupera ou inicializa o estado SQLite persistente em `06_BANCOS`, executa as 109 regressões históricas, preserva blockers, persiste novamente o estado e grava um log JSON em `07_LOGS`.

## Segurança e autenticação
Em Cloud Run, não usar `gcloud auth login` dentro do container. As credenciais OAuth do usuário devem entrar apenas via Secret Manager nas variáveis:

- `GOOGLE_DRIVE_CLIENT_ID`
- `GOOGLE_DRIVE_CLIENT_SECRET`
- `GOOGLE_DRIVE_REFRESH_TOKEN`

Nunca gravar esses valores em código, Drive, logs, imagem Docker ou Git.

### Atenção ao status Testing
Para apps OAuth External em `Testing`, o Google emite refresh tokens que expiram em 7 dias (salvo exceções de escopos básicos de identidade). Para operação realmente autônoma, a credencial não pode depender desse token de teste de 7 dias. O app é de uso pessoal, mas deve ser tratado como implantação de produção antes do agendamento permanente.

O escopo atual `https://www.googleapis.com/auth/drive` é classificado pelo Google como **restricted**. A arquitetura futura deve reavaliar se `drive.file` pode atender ao repositório sem perder acesso aos arquivos já existentes. Até essa decisão, não reduzir o escopo às cegas.

## Billing
Cloud Run e Cloud Scheduler exigem projeto com faturamento habilitado. Isso não significa cobrança automática relevante no volume previsto: Cloud Run possui free tier e Cloud Scheduler oferece 3 jobs/mês sem custo por billing account, mas o projeto precisa estar vinculado a billing para implantação.

## Arquivos de implantação
- `Dockerfile`
- `deploy/cloudrun_job.sh`
- `deploy/create_scheduler.sh`

Os scripts não criam nem imprimem secrets.

## Ordem de implantação
1. Validar `python3 main.py run --auth gcloud` no Cloud Shell.
2. Definir estratégia OAuth persistente e criar secrets no Secret Manager.
3. Habilitar billing/APIs necessárias.
4. Implantar Cloud Run Job.
5. Executar o job manualmente e validar `07_LOGS` + `06_BANCOS/ROBOT_STATE.sqlite`.
6. Só então criar Cloud Scheduler.

## Regra de método
M4C é infraestrutura. Ele não cria V18 metodológica e não promove o blocker `FOMENTO_ETI_EXECUTION`: o status `STOP_DATA_DEPENDENCY` permanece até nova evidência substantiva.
