# ROBO_DADOS_PUBLICOS_SOFTWARE_V01

Consolidação em software das capacidades metodológicas validadas nas versões V01–V17 do projeto.

## Estado desta release

**Software ativo:** 0.6.3 ACTIVE  
**Candidata corrente:** 0.7.0 CANDIDATE  
**Próximo gate:** M6 — desenho da publicação controlada em `08_OUTPUTS`  
**Dependências externas:** `pypdf==6.10.0` e `reportlab==5.0.0`  
**Python:** 3.11+

A 0.6.3 permanece a última release ativa validada. A 0.7.0 candidata acrescenta uma camada de produto local e determinística: `REPORT_CARD`, tabela compatível com o contrato de resposta e bundle com JSON, CSV, Markdown, HTML e PDF. O gate offline passou com 38/38 checks de preflight, 148/148 testes unitários, 13/13 testes específicos de produto e 109/109 regressões históricas. O CSV é a fonte planejada para futura importação como Google Sheets em `08_OUTPUTS`, mas esta candidata ainda não publica nada no Drive.

Agendamento, recorrência, novas fontes e execução ampla da fila permanecem desabilitados. TCE-SP, TDA, licitações e SIAVE ficam fora deste gate; o TDA continua bloqueado sem endpoint/export público comprovado. Uma eventual correspondência gera somente evidência documental `CANDIDATE_ONLY`, nunca identidade financeira automática.

## Testes

```bash
python3 -m pip install -r requirements.txt
python3 -m compileall -q .
python3 -m unittest discover -s tests -v
python3 main.py selftest
python3 main.py sources-validate --source-config config/sources.example.json
```

## M6 — Saída mínima de produto

O construtor local recebe respostas estruturadas e gera sete arquivos:

- `report.json` — conteúdo estruturado;
- `report_card.json` — contrato e estado do relatório;
- `table.csv` — tabela pronta para futura importação em Google Sheets;
- `report.md` — leitura rápida;
- `report.html` — leitura local em navegador;
- `report.pdf` — relatório portátil;
- `manifest.json` — inventário, bytes e SHA-256 dos seis artefatos de conteúdo.

As colunas preservam o contrato já existente: `status`, `DADO`, `CÁLCULO`, `CORRESPONDÊNCIA`, `INTERPRETAÇÃO`, `CAUTELA`, `FONTES`. A apresentação nunca é tratada como evidência. `NO_DATA`, `EVIDENCIA_INSUFICIENTE` e cautelas permanecem visíveis.

Exemplo local, sem Drive:

```bash
python scripts/build_product_output.py \
  --input answers.json \
  --output-dir runtime/product_output \
  --report-id RELATORIO_001 \
  --title "Relatório do robô" \
  --scope "Limeira/SP"
```

A geração local foi validada no CI, inclusive PDF real com `reportlab==5.0.0`. O destino futuro está configurado como `08_OUTPUTS`, mas a publicação remota e a conversão de `table.csv` para Google Sheets **não estão implementadas nem autorizadas nesta candidata**. O próximo gate trata especificamente dessa publicação controlada.

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
- evidência insuficiente permanece explicitamente insuficiente;
- apresentação ≠ evidência.

## Drive
A configuração canônica está em `config/cloud.json`. O preflight exige as camadas `00_DOCUMENTACAO` a `12_SOFTWARE` e `START_HERE_ROBO_DADOS_PUBLICOS`. `08_OUTPUTS` já é o destino reservado para saídas de produto, mas a 0.7.0 candidata ainda não escreve nessa pasta.

## Deploy
A rota corrente de execução remota permanece GitHub Actions (`docs/GITHUB_ACTIONS_DEPLOY.md`). Execute primeiro `python scripts/github_preflight.py`; o resultado esperado sem credenciais é `PASS_OFFLINE`. A coleta, o processamento, a primeira reconciliação controlada e a observabilidade operacional já foram validados. Novas fontes, repetição dos gates históricos, reconciliação ampla, recorrência e agenda continuam desabilitadas.

Os contratos históricos permanecem em `config/sources.jornal_oficial_7310_gate.json`, `config/processing.jornal_oficial_7310_gate.json` e `config/reconciliation.first_contract_gate.json`, mas o workflow não oferece `confirm_source_collection`, `confirm_processing` nem `confirm_reconciliation`.

Na candidata 0.7.0, o runtime persistente com OAuth continua bloqueado pelo preflight, mesmo quando credenciais estão presentes. A futura publicação em `08_OUTPUTS` ainda não está alcançável pelo workflow e será tratada em gate próprio.

## M5 — Observabilidade

A 0.6.3 ativa inclui `robo_dados_publicos/observability/` e não acrescenta escrita remota própria. O primeiro cartão de fonte está em `config/observability.jornal_oficial_7310.json`. Fontes `one_time_manual_gate` não recebem limiar artificial de atualização e não implicam recorrência.

Depois de cada runtime manual autorizado da release ativa, o workflow gera uma projeção sanitizada em dois lugares:

- **GitHub Actions → Summary:** visão humana imediata da saúde, gate, checks, fonte, métricas e privacidade;
- **GitHub Actions → Artifacts:** pacote `observability-report-<github.run_id>` por 30 dias, contendo `report.md`, `report.json` e cartões separados.

O gate de promoção foi concluído no run `32782732233` com `PASS_M5_OBSERVABILITY_RUNTIME_GATE`. A evidência bruta usada para montar o relatório permanece somente em `$RUNNER_TEMP` e não é enviada ao artifact. Secrets, hashes e identificadores remotos são excluídos por allowlist. Consulte `docs/OBSERVABILITY_RUNBOOK.md` para o caminho operacional completo.

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

A primeira tentativa ao vivo da 0.6.2 encontrou, com segurança, uma tarefa sem número de contrato nem fornecedor e encerrou com `STOP_MISSING_CONTRACT_OR_SUPPLIER_KEY`, `remote_writes: NONE`. Após o endurecimento do seletor, a execução manual nº 8 selecionou exatamente uma tarefa elegível de `LIMEIRA_CONTRATOS` e concluiu com `MATCH_CANDIDATE`. A evidência permanece `CANDIDATE_ONLY`; não houve promoção de identidade financeira nem alteração de TCE-SP, TDA, licitações ou SIAVE. Após a promoção, o caminho de repetição foi removido do workflow ativo.
