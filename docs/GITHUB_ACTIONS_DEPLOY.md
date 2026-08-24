# M4D — GitHub Actions

## Identidade ativa

- release ativa: `0.6.1 ACTIVE`;
- candidata corrente: `0.6.2 CANDIDATE`;
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

O preflight local esperado é `PASS_OFFLINE`. Ele valida a identidade `0.6.1 ACTIVE` + `0.6.2 CANDIDATE`, ausência de agendamento, bloqueio da repetição dos gates de fonte e processamento, o contrato estrito da reconciliação e os pins das actions. Ele não simula credenciais.

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

## Gate de primeiro processamento controlado concluído

A candidata 0.6.1 adicionou temporariamente o input manual `confirm_processing`. Ele não repetiu a aquisição: o runtime recuperou do estado a referência privada do PDF já preservado, baixou apenas do Drive e reconfirmou SHA-256 e tamanho antes de gerar qualquer derivado.

O run `32761758504`, job `97541993609`, concluiu com `PASS_GITHUB_JOURNAL_PROCESSING_GATE` e comprovou:

1. `pypdf==6.10.0`;
2. 76 páginas e 195.540 caracteres extraídos;
3. 53 eventos Gold, 148 chunks RAG e 68 tarefas;
4. cinco derivados criados com hashes auditáveis;
5. estado remoto substituído e log append-only criado;
6. origem pública não chamada;
7. nenhum ID remoto ou secret publicado.

Após a promoção, `confirm_processing` e a chamada de `scripts/github_processing_gate.py` foram retirados do workflow ativo. Consulte `docs/M4E_FIRST_SOURCE_PROCESSING_EVIDENCE_2026-08-24.md`.

## Próximo gate preparado: primeira execução controlada da reconciliação

As tarefas estão persistidas, mas a candidata 0.6.2 permite executar somente uma tarefa pesquisável. A primeira tentativa parou com `STOP_MISSING_CONTRACT_OR_SUPPLIER_KEY` e `remote_writes: NONE`; a correção preserva e pula a tarefa incompleta antes da rede. Para repetir após a publicação da correção, no formulário manual do workflow:

1. mantenha a branch `main`;
2. marque `confirm_persistence`;
3. marque `confirm_reconciliation`;
4. clique em `Run workflow` uma única vez;
5. não marque nem procure opções de coleta ou processamento, pois elas continuam removidas.

O gate seleciona a primeira tarefa `READY_SEARCH` de `LIMEIRA_CONTRATOS` que tenha número de contrato ou fornecedor, segundo prioridade decrescente e `task_id` crescente. Ele executa exatamente esse `task_id`, aceita somente `MATCH_CANDIDATE` ou `NO_MATCH` e mantém TCE-SP, TDA, licitações e SIAVE intocados. Uma correspondência continua sendo evidência `CANDIDATE_ONLY`, insuficiente para identidade financeira. Detalhes: `docs/M4E_FIRST_RECONCILIATION_EXECUTION_GATE_0.6.2.md`.

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
M4D prova o runtime de infraestrutura; os dois primeiros gates M4E provaram uma única coleta histórica e seu processamento controlado. A candidata 0.6.2 prepara apenas uma reconciliação manual e unitária. Novas fontes, repetição da coleta, repetição do processamento, recorrência, reconciliação ampla/automática e agendamento permanecem desativados.

## Evidência em 2026-08-24

O repositório privado foi conectado, os três secrets foram cadastrados e o gate de infraestrutura concluiu com `PASS_GITHUB_LIVE_GATE`. Em seguida, a edição 7310 foi coletada com `PASS_GITHUB_SOURCE_COLLECTION_GATE` e processada no run `32761758504` com `PASS_GITHUB_JOURNAL_PROCESSING_GATE`. Nenhum valor de secret ou identificador privado foi registrado no repositório ou nas evidências públicas.
