# ROBO_DADOS_PUBLICOS_SOFTWARE_V01

Consolidação em software das capacidades metodológicas validadas nas versões V01–V17 do projeto.

## Estado desta release

**Software ativo:** 0.6.0 ACTIVE  
**Candidata corrente:** 0.6.1 CANDIDATE  
**Próximo gate:** M4E primeiro processamento controlado do Bronze  
**Dependências externas:** `pypdf==6.10.0` para processamento textual determinístico de PDFs  
**Python:** 3.11+

A 0.6.0 está ativa após o gate GitHub ao vivo coletar somente a edição 7310 do Jornal Oficial, declarada pelo índice oficial e travada por tipo MIME, SHA-256 e tamanho. O arquivo foi criado no Bronze com `DOWNLOADED_NEW`, o estado remoto foi substituído e o log append-only foi criado. A opção de repetir essa coleta foi retirada do workflow.

A 0.6.1 é candidata ao primeiro processamento controlado desse mesmo PDF. O gate localiza o Bronze pela referência privada do estado, baixa somente do Drive, reconfirma hash, tamanho e versão exata do extrator (`pypdf==6.10.0`) e produz derivados Silver, Gold, Documentos e RAG. Ele não chama a origem pública, não recria o Bronze, não executa resolvers e não imprime identificadores remotos. Agendamento, recorrência e novas fontes permanecem desabilitados. O TDA continua bloqueado sem endpoint/export público comprovado e nenhuma correspondência é promovida automaticamente a identidade financeira.

## Testes

```bash
python3 -m pip install -r requirements.txt
python3 -m compileall -q .
python3 -m unittest discover -s tests -v
python3 main.py selftest
python3 main.py sources-validate --source-config config/sources.example.json
```

## Execução persistente

Infraestrutura apenas:

```bash
python3 main.py run --auth oauth-env
```

Com coleta de fontes explicitamente configuradas:

```bash
python3 main.py run --auth oauth-env --source-config config/sources.json
```

Dry-run de fontes não consulta as fontes externas nem escreve em Bronze/Quarentena. Para também suprimir persistência de estado/log no teste, use `--no-persist --no-log`:

```bash
python3 main.py run --auth oauth-env --source-config config/sources.json --dry-run-sources --no-persist --no-log
```

## Princípios preservados
- Bronze imutável por hash;
- schema/contrato desconhecido → STOP/QUARENTENA;
- aquisição separada de transformação;
- LLM não é motor de verdade numérica;
- receita ≠ despesa; saldo ≠ gasto; dotação ≠ execução;
- correspondência temática ≠ identidade jurídica/financeira;
- evidência insuficiente permanece explicitamente insuficiente.

## Drive
A configuração canônica está em `config/cloud.json`. O preflight exige as camadas `00_DOCUMENTACAO` a `12_SOFTWARE` e `START_HERE_ROBO_DADOS_PUBLICOS`.

## Deploy
A rota corrente de execução remota permanece GitHub Actions (`docs/GITHUB_ACTIONS_DEPLOY.md`). Execute primeiro `python scripts/github_preflight.py`; o resultado esperado sem credenciais é `PASS_OFFLINE`. A primeira coleta M4E foi validada e está documentada em `docs/M4E_SOURCE_COLLECTION.md`. O gate seguinte processa somente o Bronze validado; novas fontes, repetição da coleta, recorrência e agenda continuam desabilitadas até gates próprios.

O inventário histórico do primeiro gate está preservado em `config/sources.jornal_oficial_7310_gate.json`, mas o workflow ativo não oferece mais `confirm_source_collection`. O contrato do processamento seguinte está em `config/processing.jornal_oficial_7310_gate.json` e só pode ser acionado com as confirmações manuais `confirm_persistence` e `confirm_processing`.


## M4E.1 — Portal discovery

Use `python main.py portal-probe <URL>` for a single-page, robots-aware passive reconnaissance. It never solves CAPTCHA, submits forms, authenticates, executes JavaScript, or brute-forces endpoints.


## M4E.2 — Jornal Oficial de Limeira

Descoberta de um mês do índice público (sem baixar PDFs):

```bash
python3 main.py journal-discover --year 2026 --month 8
```

Para emitir um inventário desabilitado, que ainda exige validação de rota/content-type antes de produção:

```bash
python3 main.py journal-discover --year 2026 --month 8 --emit-inventory runtime/jornal_2026_08_sources.json
```

O software não adivinha URLs de PDF; só aceita rotas declaradas pelo índice oficial.


## M4E.3 — Processamento do Jornal Oficial

Depois de obter um PDF por uma rota oficial já validada:

```bash
python3 main.py journal-process \
  --pdf runtime/edicao.pdf \
  --edition 7309 \
  --publication-date 2026-08-21 \
  --source-url 'https://.../edicao.pdf' \
  --out-dir runtime/jornal_7309
```

O comando gera manifesto, Silver redigida, eventos Gold e chunks RAG. PDF sem camada textual suficiente produz `STOP_OCR_REQUIRED`; nenhum OCR é disparado silenciosamente.

Para o gate remoto da edição 7310, a candidata 0.6.1 usa `journal-process-cloud` por meio de `scripts/github_processing_gate.py`. Esse caminho lê a cópia imutável do Drive e exige, antes e depois do processamento, o contrato exato documentado em `docs/M4E_FIRST_SOURCE_PROCESSING_GATE_0.6.1.md`.


## M4E.4 — Fila de reconciliação

O processamento do Jornal Oficial agora gera também `reconciliation_tasks.jsonl`. As tarefas são apenas ordens de busca/reconciliação; não representam prova de identidade.

Persistir a fila no SQLite:

```bash
python3 main.py reconciliation-plan \
  --events-jsonl runtime/jornal_7309/events_gold.jsonl \
  --out runtime/jornal_7309/reconciliation_tasks.jsonl \
  --state-db runtime/robot_state.sqlite
```

Consultar a fila:

```bash
python3 main.py reconciliation-status --state-db runtime/robot_state.sqlite
```

O alvo TDA permanece `BLOCKED_CONNECTOR_DISCOVERY` até que endpoint/export público estável seja comprovado. Consulte `docs/RECONCILIATION_QUEUE.md`.


## M4E.5 — Execução da fila de reconciliação

Dry-run, sem rede e sem alterar o status das tarefas:

```bash
python3 main.py reconciliation-execute \
  --state-db runtime/robot_state.sqlite \
  --work-dir runtime/reconciliation \
  --dry-run
```

Executar somente resolvers já implementados:

```bash
python3 main.py reconciliation-execute \
  --state-db runtime/robot_state.sqlite \
  --work-dir runtime/reconciliation \
  --target LIMEIRA_CONTRATOS \
  --target TCE_SP_DESPESAS \
  --limit 10
```

Estados como `MATCH_CANDIDATE`, `NO_MATCH`, `STOP_SCHEMA_UNKNOWN` e `STOP_CONTRACT_FORM_UNPROVEN` são persistidos no SQLite. `MATCH_CANDIDATE` significa somente que a fonte-alvo retornou registros compatíveis com as chaves de busca; não significa que o gasto pertença ao contrato/ato publicado.
