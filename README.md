# ROBO_DADOS_PUBLICOS_SOFTWARE_V01

Consolidação em software das capacidades metodológicas validadas nas versões V01–V17 do projeto.

## Estado desta release

**Software ativo:** 0.6.1 ACTIVE  
**Candidata corrente:** 0.6.2 CANDIDATE  
**Próximo gate:** M4E primeira execução ao vivo de uma única tarefa `LIMEIRA_CONTRATOS`  
**Dependências externas:** `pypdf==6.10.0` para processamento textual determinístico de PDFs  
**Python:** 3.11+

A 0.6.1 permanece ativa após o primeiro processamento controlado. A candidata 0.6.2 seleciona deterministicamente uma única tarefa `READY_SEARCH` e pesquisável de `LIMEIRA_CONTRATOS`: é obrigatório haver número de contrato ou nome de fornecedor. Tarefas incompletas são preservadas e puladas; o executor recebe exatamente o `task_id` selecionado. O gate aceita apenas `MATCH_CANDIDATE` ou `NO_MATCH` e só substitui o estado remoto após todos os checks passarem.

Agendamento, recorrência, novas fontes e execução ampla da fila permanecem desabilitados. TCE-SP, TDA, licitações e SIAVE ficam fora deste gate; o TDA continua bloqueado sem endpoint/export público comprovado. Uma eventual correspondência gera somente evidência documental `CANDIDATE_ONLY`, nunca identidade financeira automática.

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
A rota corrente de execução remota permanece GitHub Actions (`docs/GITHUB_ACTIONS_DEPLOY.md`). Execute primeiro `python scripts/github_preflight.py`; o resultado esperado sem credenciais é `PASS_OFFLINE`. A coleta e o processamento M4E da edição 7310 já foram validados. A candidata 0.6.2 expõe apenas um gate manual e limitado de reconciliação; novas fontes, repetição da coleta, repetição do processamento, recorrência e agenda continuam desabilitadas.

Os contratos históricos permanecem em `config/sources.jornal_oficial_7310_gate.json` e `config/processing.jornal_oficial_7310_gate.json`, mas o workflow não oferece `confirm_source_collection` nem `confirm_processing`. A 0.6.2 acrescenta `confirm_reconciliation`, que somente funciona junto da confirmação de persistência e aplica `config/reconciliation.first_contract_gate.json`.


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

O gate remoto da edição 7310 foi concluído pela 0.6.1 com `PASS_GITHUB_JOURNAL_PROCESSING_GATE`. Ele usou `journal-process-cloud` por meio de `scripts/github_processing_gate.py`, leu a cópia imutável do Drive e comprovou o contrato exato documentado em `docs/M4E_FIRST_SOURCE_PROCESSING_GATE_0.6.1.md`. Esse caminho não está mais exposto no workflow ativo.


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

Na candidata 0.6.2, o workflow manual usa `scripts/github_reconciliation_gate.py` para executar no máximo uma tarefa pesquisável de `LIMEIRA_CONTRATOS`. A primeira tentativa ao vivo encontrou, com segurança, uma tarefa prioritária sem número de contrato nem fornecedor e encerrou com `STOP_MISSING_CONTRACT_OR_SUPPLIER_KEY`, `remote_writes: NONE`. O seletor foi endurecido para pular esse tipo de tarefa sem alterá-la e passar ao executor exatamente o `task_id` elegível escolhido. Qualquer resultado fora de `MATCH_CANDIDATE`/`NO_MATCH`, qualquer alteração em alvos protegidos ou qualquer tentativa de gerar `financial_identity` continua impedindo a substituição do estado e a criação do log.
