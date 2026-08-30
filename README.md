# ROBO_DADOS_PUBLICOS_SOFTWARE_V01

Consolidação em software das capacidades metodológicas validadas nas versões V01–V17 do projeto.

## Estado desta release

**Software ativo:** 0.7.0 ACTIVE  
**Candidata corrente:** 0.8.0 CANDIDATE  
**Série anual SIOPE fechada:** 2016–2024<br>
**Próximo gate:** respostas oficiais FNDE para B1/B2/B3; protocolos pendentes até 2026-09-21<br>
**Dependências externas:** `pypdf==6.10.0` e `reportlab==5.0.0`  
**Python:** 3.11+

A 0.7.0 permanece a última release ativa validada. O motor principal já demonstrou coleta controlada, Bronze/Silver/Gold histórico, reconciliação, observabilidade, persistência create-only, gates e geração de produtos JSON/CSV/MD/HTML/PDF. A 0.8.0 continua candidata porque capacidade de engenharia não equivale a autorização operacional nem a suficiência semântica.

Para 2025, P1–P6, o schema P6 de 52 campos e a presença estrutural dos 11 inputs do pipeline foram observados. O estado é `PROVEN_STRUCTURAL_RECENT`. Nove dos dez aliases financeiros são `PROVEN_EXACT_OPERATIONAL`; `VL_DESP_DOTA_ATUA_EDU` permanece parcial, sem regra de inclusão/agregação definida pela fonte. `VALID_ANNUAL_SUBMISSION` é `PROVEN`, mas a declaração atualmente efetiva, B1, B2 e a comparabilidade continuam não provadas. Gold 2025 segue `UNKNOWN/BLOCKED`, e a série anual fechada permanece **2016–2024**.

As solicitações FNDE pendentes são B3 `23546.111502/2026-41`, B1 `23546.111503/2026-95` e B2 `23546.111504/2026-30`. A existência desses protocolos não promove qualquer estado. Os gates TASK 011 mantêm B4, B5 e a prontidão da 0.8.0 deterministicamente bloqueados.

Consulte **[`STATUS_0.8.0.md`](STATUS_0.8.0.md)** para o estado canônico, a cadeia de evidências, os bloqueios de promoção, a matriz de maturidade e a auditoria de resíduos documentais.

A expansão segue o ciclo `DISCOVERED → CONTRACT_VALIDATED → ONE_TIME_AUTHORIZED → LIVE_VALIDATED → RECURRENCE_ELIGIBLE`. Chegar a `RECURRENCE_ELIGIBLE` não liga agenda por si só; recorrência e schedule exigem autorização separada.

## Testes

```bash
python3 -m pip install -r requirements.txt
python3 scripts/github_preflight.py
python3 scripts/github_source_expansion_design_gate.py
python3 -m compileall -q .
python3 -m unittest discover -s tests -v
python3 main.py selftest
python3 main.py sources-validate --source-config config/sources.example.json
```

## M7 — Expansão controlada de fontes

O SIOPE/FNDE para Limeira/SP permanece o piloto único da 0.8.0. Desde o desenho inicial, gates bounded demonstraram a rota, o pipeline histórico e a estrutura recente de 2025. Cada evidência conserva o limite do contrato que a produziu: não há autorização implícita para rerun, recorrência, schedule, Gold 2025 ou publicação.

Os gargalos correntes são a definição/fonte/vintage de `NUM_POPU`, a regra oficial de inclusão/agregação do alias financeiro restante e a regra que seleciona a declaração anual atualmente efetiva. As três respostas oficiais estão pendentes. Veja o [`STATUS_0.8.0.md`](STATUS_0.8.0.md); os documentos M7 individuais permanecem como histórico auditável dos gates.

## M6 — Saída mínima de produto

O construtor recebe respostas estruturadas e gera sete arquivos locais:

- `report.json` — conteúdo estruturado;
- `report_card.json` — contrato e estado do relatório;
- `table.csv` — tabela compatível com importação em Google Sheets;
- `report.md` — leitura rápida;
- `report.html` — leitura local em navegador;
- `report.pdf` — relatório portátil;
- `manifest.json` — inventário, bytes e SHA-256 dos seis artefatos de conteúdo.

As colunas preservam o contrato já existente: `status`, `DADO`, `CÁLCULO`, `CORRESPONDÊNCIA`, `INTERPRETAÇÃO`, `CAUTELA`, `FONTES`. A apresentação nunca é tratada como evidência. `NO_DATA`, `EVIDENCIA_INSUFICIENTE` e cautelas permanecem visíveis.

Exemplo local:

```bash
python scripts/build_product_output.py \
  --input answers.json \
  --output-dir runtime/product_output \
  --report-id RELATORIO_001 \
  --title "Relatório do robô" \
  --scope "Limeira/SP"
```

O gate controlado M6 publicou exatamente três itens em `08_OUTPUTS`: `ROBO_DADOS_PUBLICOS_M6_GATE_0_7_0_TABELA`, `ROBO_DADOS_PUBLICOS_M6_GATE_0_7_0.pdf` e `ROBO_DADOS_PUBLICOS_M6_GATE_0_7_0_publication_manifest.json`. A planilha foi verificada com as sete colunas do contrato, o PDF foi renderizado e revisado visualmente, e o manifesto foi confirmado como o último item criado. Não houve overwrite. Após a promoção, a repetição desse gate é bloqueada pela identidade da release.

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

Enquanto a 0.8.0 estiver como `CANDIDATE`, o preflight com `--require-oauth` encerra com `STOP_CANDIDATE_PERSISTENT_RUNTIME_NOT_AUTHORIZED`, mesmo que as credenciais estejam presentes. Isso impede que o novo desenho de expansão seja confundido com autorização operacional.

## Princípios preservados
- Bronze imutável por hash;
- schema/contrato desconhecido → STOP/QUARENTENA;
- aquisição separada de transformação;
- LLM não é motor de verdade numérica;
- receita ≠ despesa; saldo ≠ gasto; dotação ≠ execução;
- correspondência temática ≠ identidade jurídica/financeira;
- evidência insuficiente permanece explicitamente insuficiente;
- apresentação ≠ evidência;
- superfície pública comprovada ≠ rota de aquisição comprovada;
- elegibilidade para recorrência ≠ autorização de agenda.

## Drive
A configuração canônica está em `config/cloud.json`. O preflight exige as camadas `00_DOCUMENTACAO` a `12_SOFTWARE` e `START_HERE_ROBO_DADOS_PUBLICOS`. `08_OUTPUTS` é o destino reservado para saídas de produto. A primeira publicação controlada da 0.7.0 foi validada no run `32787729769`; novos usos de publicação exigirão um gate próprio e não reutilizam silenciosamente o M6.

A candidata não autoriza escrita por padrão. Escritas históricas bounded/create-only ocorreram somente em gates próprios já pinados; nova persistência ou publicação exige autorização separada.

## Deploy
A rota corrente de execução remota permanece GitHub Actions (`docs/GITHUB_ACTIONS_DEPLOY.md`). Execute primeiro `python scripts/github_preflight.py`; o resultado esperado sem credenciais é `PASS_OFFLINE`. Como a release corrente é candidata, `--require-oauth` permanece bloqueado. Coleta, processamento, primeira reconciliação controlada, observabilidade e saída mínima de produto já foram validados. No SIOPE, apenas execuções bounded explicitamente autorizadas foram realizadas; repetição dos gates históricos, novas fontes, Gold 2025, reconciliação ampla, recorrência e agenda continuam desabilitados.

Os contratos históricos permanecem em `config/sources.jornal_oficial_7310_gate.json`, `config/processing.jornal_oficial_7310_gate.json`, `config/reconciliation.first_contract_gate.json` e `config/product_output.first_publication_gate.json`. O workflow principal não oferece `confirm_source_collection`, `confirm_processing`, `confirm_reconciliation`, publicação de produto nem `confirm_source_expansion`.

## M5 — Observabilidade

A observabilidade foi promovida inicialmente na 0.6.3 e permanece integrada à base ativa. O primeiro cartão de fonte está em `config/observability.jornal_oficial_7310.json`. Fontes `one_time_manual_gate` não recebem limiar artificial de atualização e não implicam recorrência.

Depois de cada runtime manual autorizado de uma release ativa, o workflow gera uma projeção sanitizada em dois lugares:

- **GitHub Actions → Summary:** visão humana imediata da saúde, gate, checks, fonte, métricas e privacidade;
- **GitHub Actions → Artifacts:** pacote `observability-report-<github.run_id>` por 30 dias, contendo `report.md`, `report.json` e cartões separados.

O gate original de promoção da observabilidade foi concluído no run `32782732233` com `PASS_M5_OBSERVABILITY_RUNTIME_GATE`. A evidência bruta usada para montar o relatório permanece somente em `$RUNNER_TEMP` e não é enviada ao artifact. Secrets, hashes e identificadores remotos são excluídos por allowlist. Consulte `docs/OBSERVABILITY_RUNBOOK.md` para o caminho operacional completo.

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

O processamento do Jornal Oficial gera também `reconciliation_tasks.jsonl`. As tarefas são apenas ordens de busca/reconciliação; não representam prova de identidade.

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
