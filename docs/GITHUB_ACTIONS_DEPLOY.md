# M4D — GitHub Actions

## Identidade preparada

- release ativa preservada: `0.5.8 ACTIVE`;
- candidata para o gate: `0.5.9 CANDIDATE`;
- `actions/checkout` fixada no SHA da release pública `v6.0.2`;
- `actions/setup-python` fixada no SHA da release `v7.0.0`;
- agendamento desabilitado até o primeiro PASS ao vivo.

## Objetivo
Executar `python main.py run --auth oauth-env` em infraestrutura GitHub-hosted, sem depender de PC ligado, Cloud Shell ativo ou sessão `gcloud`.

## Segurança
Os valores de OAuth não pertencem ao repositório. Devem existir somente como Repository Secrets com estes nomes exatos:

- `GOOGLE_DRIVE_CLIENT_ID`
- `GOOGLE_DRIVE_CLIENT_SECRET`
- `GOOGLE_DRIVE_REFRESH_TOKEN`

O workflow usa `permissions: contents: read`, `concurrency` para impedir sobreposição de runs, `persist-credentials: false` no Checkout e não imprime os valores dos secrets. Arquivos `.env`, tokens OAuth, bancos locais e credenciais JSON são excluídos pelo `.gitignore`.

O repositório deve ser criado como **privado** no primeiro gate. Os secrets devem ser cadastrados pela interface do GitHub; nunca copiar seus valores para issues, commits, logs, documentos ou conversa.

## Preflight sem GitHub

```bash
python scripts/github_preflight.py
python -m compileall -q .
python -m unittest discover -s tests -v
python main.py selftest
```

O preflight local esperado é `PASS_OFFLINE`. Ele valida a identidade `0.5.9 CANDIDATE`, preservação da ativa `0.5.8`, ausência de agendamento, confirmação obrigatória e pins imutáveis. Ele não simula credenciais nem declara o gate remoto como concluído.

## Primeiro gate: execução manual
O arquivo `.github/workflows/robo-dados-publicos.yml` nasce somente com `workflow_dispatch` ativo. Depois de cadastrar os três secrets, executar manualmente em **Actions → ROBO DADOS PUBLICOS → Run workflow** e marcar `confirm_persistence`.

Critérios de PASS:

1. compileall PASS;
2. testes unitários PASS;
3. regressão histórica 109/109 PASS;
4. preflight OAuth retorna `PASS_LIVE_PREFLIGHT` sem revelar valores;
5. `run --auth oauth-env` retorna `status: PASS`;
6. `software_version: 0.5.9` e `release_status: CANDIDATE`;
7. `state_source: REMOTE_EXISTING`;
8. `state_remote.mode: REPLACED`;
9. novo `ROBO_RUN_*.json` aparece em `07_LOGS`;
10. `scripts/github_run_gate.py` retorna `PASS_GITHUB_LIVE_GATE`.

## Segundo gate: agendamento
Somente depois do primeiro PASS manual, ativar `schedule`. O GitHub Actions aceita cron POSIX e `timezone` IANA. Exemplo para 03:17 em São Paulo:

```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: '17 3 * * *'
      timezone: 'America/Sao_Paulo'
```

O horário definitivo deve ser escolhido antes de habilitar esse bloco.

## Limites desta etapa
M4D automatiza o runtime de infraestrutura. A coleta de fontes permanece fora do escopo até o runtime agendado estar validado.

## Estado de bloqueio em 2026-08-23

A preparação offline está autorizada e não depende do acesso do usuário. A criação/conexão do repositório, o cadastro dos três secrets e o primeiro `workflow_dispatch` permanecem bloqueados até a recuperação do acesso ao GitHub. Nenhum arquivo em `06_BANCOS` ou `07_LOGS` deve ser alterado durante a preparação offline; o primeiro run real substituirá controladamente o estado em `06_BANCOS` e acrescentará um único log em `07_LOGS`, conforme o contrato acima.
