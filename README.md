# ROBO_DADOS_PUBLICOS_SOFTWARE_V01

Consolidação em software das capacidades metodológicas validadas no projeto ROBO_DADOS_PUBLICOS.

## Estado desta release

**Software ativo:** 0.7.0 ACTIVE  
**Candidata corrente:** 0.8.0 CANDIDATE  
**Série anual SIOPE fechada:** 2016–2024  
**Próximo gate:** TASK 241 — comparabilidade semântica 2016–2025  
**Dependências externas:** `pypdf==6.10.0` e `reportlab==5.0.0`  
**Python:** 3.11+

A 0.7.0 permanece a última release ativa validada. A 0.8.0 continua candidata: capacidade de engenharia, existência de dados e resolução de blockers individuais não equivalem a autorização de Gold, inclusão de 2025 na série, publicação, recorrência ou promoção de release.

### Fotografia corrente do Observatório

A camada territorial está completa para a rede municipal mapeada: **69/69** escolas possuem vínculo forte escola→setor censitário IBGE 2022, com **284** linhas no `TERRITORY_PROFILE`. Há contexto numérico de renda setorial para **68/69** escolas. A escola INEP `35286229` mantém missingness explícita `SOURCE_EXPLICIT_X`; `X` não é zero e não gera linha numérica sintética. A cobertura contextual permanece **38/38**.

No SIOPE 2025, os três blockers B1/B2/B3 foram resolvidos dentro de seus limites de prova:

- B1 `RESOLVED_BY_EXCLUSION_FROM_ANALYTICAL_POPULATION_SEMANTICS`: a resposta FNDE classifica `NUM_POPU` como campo legado/não analítico para análise populacional. O robô não deve usá-lo como população de 2025; análises populacionais devem usar fonte oficial IBGE com período de referência explícito.
- B2 `PROVEN_10_OF_10_ALIAS_TO_CONCEPT`: os dez aliases financeiros estão ligados aos conceitos oficiais aplicáveis. A fórmula interna de agregação do backend continua `NOT_PROVEN`; a diferença de R$ 1.000 observada não foi transformada em regra inventada.
- B3 `PROVEN_DYNAMIC_EFFECTIVE_SELECTION_RULE_WITH_PINNED_LIMEIRA_RECEIPT`: o FNDE confirmou que a declaração vigente é a última transmitida e recepcionada com sucesso e que a consulta pública de recibos mostra essa transmissão. Aplicada à observação já pinada de Limeira, a declaração anual efetiva é o recibo `428477-6` na fotografia de `2026-08-30`. Isso é estado dinâmico: uma retificação futura bem-sucedida substitui a anterior e exige nova observação.

A comparabilidade semântica 2016–2025 continua `UNKNOWN_REQUIRES_TASK241`. As seis métricas Gold puramente financeiras e as duas métricas per capita serão avaliadas separadamente. As métricas per capita não podem reutilizar `NUM_POPU` como denominador; a TASK 241 deve decidir a rota IBGE/rebase histórico. Gold 2025 permanece `BLOCKED_NOT_CALCULATED`, e a série anual fechada permanece **2016–2024**.

Os contratos correntes são `config/release_0_8_0_readiness.v2.json` e `config/siope_2025_gold_prerequisites.v2.json`. Os arquivos v1 e a evidência TASK 011 permanecem preservados como snapshots históricos do momento em que os protocolos FNDE ainda estavam pendentes.

Consulte **[`STATUS_0.8.0.md`](STATUS_0.8.0.md)** para o estado canônico corrente e os gates restantes.

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

O SIOPE/FNDE para Limeira/SP permanece o piloto da 0.8.0. Gates bounded demonstraram aquisição, Bronze/Silver, série histórica, Gold histórico e estrutura recente de 2025. Cada evidência conserva o limite do contrato que a produziu; nenhuma delas autoriza implicitamente rerun, recorrência, schedule, Gold 2025 ou publicação.

O gargalo corrente é **comparabilidade semântica 2016–2025**, formalizada na **TASK 241 / issue #809**. Para métricas 1–6, o gate deve reconciliar campo a campo e fórmula a fórmula a continuidade dos conceitos financeiros. Para métricas 7–8, deve resolver o denominador populacional por fonte oficial IBGE e decidir se uma série comparável exige rebase histórico. B1+B2+B3 resolvidos não promovem comparabilidade por inferência.

## M6 — Saída mínima de produto

O construtor recebe respostas estruturadas e gera sete arquivos locais:

- `report.json`;
- `report_card.json`;
- `table.csv`;
- `report.md`;
- `report.html`;
- `report.pdf`;
- `manifest.json`.

As colunas preservam o contrato `status`, `DADO`, `CÁLCULO`, `CORRESPONDÊNCIA`, `INTERPRETAÇÃO`, `CAUTELA`, `FONTES`. A apresentação nunca é tratada como evidência; `NO_DATA`, `EVIDENCIA_INSUFICIENTE` e cautelas permanecem visíveis.

Exemplo local:

```bash
python scripts/build_product_output.py \
  --input answers.json \
  --output-dir runtime/product_output \
  --report-id RELATORIO_001 \
  --title "Relatório do robô" \
  --scope "Limeira/SP"
```

A publicação histórica validada não autoriza nova publicação. Novos usos de publicação exigem gate próprio, nomes create-only e readback conforme o contrato aplicável.

## Execução persistente

Infraestrutura apenas:

```bash
python3 main.py run --auth oauth-env
```

Com coleta de fontes explicitamente configuradas:

```bash
python3 main.py run --auth oauth-env --source-config config/sources.json
```

Dry-run de fontes não consulta fontes externas nem escreve em Bronze/Quarentena. Para também suprimir persistência de estado/log:

```bash
python3 main.py run --auth oauth-env --source-config config/sources.json --dry-run-sources --no-persist --no-log
```

Enquanto a 0.8.0 estiver como `CANDIDATE`, o preflight com `--require-oauth` permanece bloqueado. A candidata não transforma validação técnica em autorização operacional.

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
- snapshot histórico ≠ estado corrente;
- estado efetivo dinâmico ≠ imutabilidade futura;
- B1+B2+B3 resolvidos ≠ comparabilidade provada;
- comparabilidade parcial ≠ autorização de Gold integral;
- elegibilidade para recorrência ≠ autorização de agenda.

## Drive

A configuração canônica permanece em `config/cloud.json`. O preflight exige as camadas `00_DOCUMENTACAO` a `12_SOFTWARE` e `START_HERE_ROBO_DADOS_PUBLICOS`. `08_OUTPUTS` é reservado para saídas de produto. Escritas históricas bounded/create-only permanecem evidência de gates específicos e não autorizam nova persistência.

## Deploy

A rota de execução remota permanece GitHub Actions (`docs/GITHUB_ACTIONS_DEPLOY.md`). Execute primeiro `python scripts/github_preflight.py`; o resultado esperado sem credenciais é `PASS_OFFLINE`. Coleta, processamento, reconciliação, observabilidade e produto possuem contratos próprios. Repetição de gates históricos, novas fontes, Gold 2025, inclusão de 2025, recorrência e agenda continuam desabilitados salvo autorização específica.

## M5 — Observabilidade

A observabilidade permanece integrada à base ativa. Após runtime manual autorizado, o workflow pode produzir projeção sanitizada no Summary e em artifacts conforme `docs/OBSERVABILITY_RUNBOOK.md`. Evidência bruta e secrets não são promovidos ao relatório por conveniência.

## M4E.1 — Portal discovery

```bash
python main.py portal-probe <URL>
```

Reconhecimento passivo e limitado: não resolve CAPTCHA, autentica, executa JavaScript arbitrário ou brute-força endpoints.

## M4E.2 — Jornal Oficial de Limeira

```bash
python3 main.py journal-discover --year 2026 --month 8
```

O software não adivinha URLs de PDF; só aceita rotas declaradas/validadas pelo índice oficial.

## M4E.3 — Processamento do Jornal Oficial

```bash
python3 main.py journal-process \
  --pdf runtime/edicao.pdf \
  --edition 7309 \
  --publication-date 2026-08-21 \
  --source-url 'https://.../edicao.pdf' \
  --out-dir runtime/jornal_7309
```

O comando gera manifesto, Silver redigida, eventos Gold e chunks RAG. PDF sem camada textual suficiente produz `STOP_OCR_REQUIRED`; OCR não é disparado silenciosamente.

## M4E.4 — Fila de reconciliação

O processamento do Jornal Oficial gera `reconciliation_tasks.jsonl`. Tarefas são ordens de investigação, não prova de identidade.

```bash
python3 main.py reconciliation-plan \
  --events-jsonl runtime/jornal_7309/events_gold.jsonl \
  --out runtime/jornal_7309/reconciliation_tasks.jsonl \
  --state-db runtime/robot_state.sqlite

python3 main.py reconciliation-status --state-db runtime/robot_state.sqlite
```

## M4E.5 — Execução da fila de reconciliação

Dry-run:

```bash
python3 main.py reconciliation-execute \
  --state-db runtime/robot_state.sqlite \
  --work-dir runtime/reconciliation \
  --dry-run
```

Execução limitada a resolvers implementados:

```bash
python3 main.py reconciliation-execute \
  --state-db runtime/robot_state.sqlite \
  --work-dir runtime/reconciliation \
  --target LIMEIRA_CONTRATOS \
  --target TCE_SP_DESPESAS \
  --limit 10
```

Estados como `MATCH_CANDIDATE`, `NO_MATCH`, `STOP_SCHEMA_UNKNOWN` e `STOP_CONTRACT_FORM_UNPROVEN` preservam a diferença entre candidato e identidade provada.
