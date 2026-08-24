# M4D — GitHub Actions

## Identidade ativa

- release ativa: `0.6.0 ACTIVE`;
- candidata corrente: `0.6.1 CANDIDATE`;
- `actions/checkout` fixada no SHA da release pública `v6.0.2`;
- `actions/setup-python` fixada no SHA da release `v7.0.0`;
- agendamento desabilitado até decisão explícita sobre cadência e fontes.

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

O preflight local esperado é `PASS_OFFLINE`. Ele valida a identidade ativa `0.6.0 ACTIVE`, a candidata `0.6.1 CANDIDATE`, ausência de agendamento, bloqueio da repetição do gate de fonte, o contrato exato do primeiro processamento e os pins das actions. Ele não simula credenciais.

## Gate manual concluído
O arquivo `.github/workflows/robo-dados-publicos.yml` permanece somente com `workflow_dispatch` ativo. O primeiro gate persistente foi executado no run `32678624194`, job `97476648260`.

Critérios de PASS:

1. compileall PASS;
2. testes unitários PASS;
3. regressão histórica 109/109 PASS;
4. preflight OAuth retorna `PASS_LIVE_PREFLIGHT` sem revelar valores;
5. `run --auth oauth-env` retorna `status: PASS`;
6. no gate de promoção, `software_version: 0.5.9` e `release_status: CANDIDATE`;
7. `state_source: REMOTE_EXISTING`;
8. `state_remote.mode: REPLACED`;
9. novo `ROBO_RUN_*.json` aparece em `07_LOGS`;
10. `scripts/github_run_gate.py` retorna `PASS_GITHUB_LIVE_GATE`.

Todos os dez critérios passaram e sustentaram a promoção da 0.5.9.

## Gate de primeira coleta controlada concluído

A candidata 0.6.0 adicionou temporariamente o input `confirm_source_collection`. Ele foi marcado junto com `confirm_persistence` no workflow manual nº 3 e passou explicitamente `config/sources.jornal_oficial_7310_gate.json` ao runtime.

O gate comprovou:

1. `software_version: 0.6.0` e `release_status: CANDIDATE`;
2. `mode: SOURCE_COLLECTION_ENABLED`;
3. exatamente uma fonte habilitada;
4. PDF da edição 7310 com tipo, tamanho e SHA-256 esperados;
5. resultado `DOWNLOADED_NEW` com `remote_id` em Bronze;
6. estado remoto substituído e novo log append-only;
7. `PASS_GITHUB_SOURCE_COLLECTION_GATE`.

O resultado foi `PASS_GITHUB_SOURCE_COLLECTION_GATE`, com 16/16 verificações aprovadas. Após a promoção, `confirm_source_collection` e a passagem do inventário de uso único foram retirados do workflow ativo. Evidência: `docs/M4E_FIRST_SOURCE_COLLECTION_EVIDENCE_2026-08-24.md`.

## Próximo gate: primeiro processamento controlado

A candidata 0.6.1 adiciona o input manual `confirm_processing`. Ele não repete a aquisição: o runtime recupera do estado a referência privada do PDF já preservado, baixa apenas do Drive e reconfirma SHA-256 e tamanho antes de gerar qualquer derivado.

Para executar o gate uma única vez:

1. abrir `Actions` no repositório;
2. selecionar `ROBO DADOS PUBLICOS`;
3. escolher `Run workflow` na branch `main`;
4. marcar `confirm_persistence`;
5. marcar `confirm_processing`;
6. acionar `Run workflow` uma vez.

O PASS exige 76 páginas, 195.540 caracteres extraídos, 53 eventos Gold, 148 chunks RAG e 68 tarefas, além dos hashes dos cinco derivados, estado remoto substituído e log append-only. O resumo público não contém IDs do Drive. Consulte `docs/M4E_FIRST_SOURCE_PROCESSING_GATE_0.6.1.md`.

## Gate futuro: agendamento
Nenhum PASS habilita agendamento automaticamente. Antes de ativar `schedule`, ainda é necessário escolher a cadência e aprovar um inventário recorrente separado. O inventário da edição 7310 é de uso único e não pode ser convertido silenciosamente em rotina. O GitHub Actions aceita cron POSIX e `timezone` IANA. Exemplo ainda não ativo para 03:17 em São Paulo:

```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: '17 3 * * *'
      timezone: 'America/Sao_Paulo'
```

O horário definitivo deve ser escolhido antes de habilitar esse bloco.

## Limites desta etapa
M4D prova o runtime de infraestrutura; o primeiro M4E provou uma única coleta histórica; a candidata 0.6.1 limita-se ao processamento desse Bronze. Novas fontes, repetição da coleta, recorrência e agendamento permanecem desativados.

## Evidência em 2026-08-24

O repositório privado foi conectado, os três secrets foram cadastrados e o gate de infraestrutura concluiu com `PASS_GITHUB_LIVE_GATE`. Em seguida, o workflow nº 3 coletou a edição 7310 no Bronze e concluiu com `PASS_GITHUB_SOURCE_COLLECTION_GATE`. O estado em `06_BANCOS` foi substituído controladamente e um novo log foi acrescentado em `07_LOGS`. Nenhum valor de secret foi registrado no repositório ou nas evidências.
