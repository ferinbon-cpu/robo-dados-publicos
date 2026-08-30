# STATUS 0.8.0

Este é o documento canônico de estado da release `0.8.0 CANDIDATE`. Ele consolida
evidência já pinada no repositório; não autoriza nova coleta, persistência,
publicação, recorrência ou promoção de dados.

## 1. Estado da release

- **Release ativa:** `0.7.0 ACTIVE`.
- **Release candidata:** `0.8.0 CANDIDATE`.
- **Base auditada:** `09145411be5fe5c8552047038270c39d3f5d24e7` (`main`
  canônico informado para esta consolidação).
- **Escopo da candidata:** expansão controlada do motor para o SIOPE/FNDE de
  Limeira/SP, incluindo aquisição limitada, Bronze, Silver, Gold histórico,
  série histórica e produto, sem converter capacidade técnica em autorização
  recorrente.

O motor principal já foi demonstrado. A promoção da release, porém, permanece
bloqueada pelos gates semânticos e de fechamento de 2025 descritos abaixo.

## 2. Capacidades já provadas

| Capacidade | Limite da prova | Evidência no repositório |
| --- | --- | --- |
| Coleta/ingestion controlada | Execuções bounded e autorizadas; não autoriza recorrência | [`docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_RUN_1_0.8.0.json`](docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_RUN_1_0.8.0.json), [`config/automation_policy.v1.json`](config/automation_policy.v1.json) |
| Bronze imutável e Silver | Piloto e histórico SIOPE, com persistência create-only nos gates próprios | [`docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json`](docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json), [`docs/M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_VERIFICATION_GATE_0.8.0.md`](docs/M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_VERIFICATION_GATE_0.8.0.md) |
| Gold determinístico histórico | Fórmulas aritméticas delimitadas; não prova compliance e não inclui 2025 | [`docs/references/M7_SIOPE_LIMEIRA_GOLD_ARITHMETIC_SCOPE_0.8.0.md`](docs/references/M7_SIOPE_LIMEIRA_GOLD_ARITHMETIC_SCOPE_0.8.0.md), [`docs/SIOPE_HISTORICAL_REGIME_DISCOVERY_V1.md`](docs/SIOPE_HISTORICAL_REGIME_DISCOVERY_V1.md) |
| Série SIOPE histórica | Série anual fechada exatamente em `2016–2024` | [`config/siope_historical_regimes.v1.json`](config/siope_historical_regimes.v1.json), [`docs/research/SIOPE_HISTORICAL_REGIME_EVIDENCE_V1.md`](docs/research/SIOPE_HISTORICAL_REGIME_EVIDENCE_V1.md) |
| Reconciliação | Planejamento, evidência e estados fail-closed; candidato não equivale a identidade | [`docs/RECONCILIATION_QUEUE.md`](docs/RECONCILIATION_QUEUE.md), [`robo_dados_publicos/reconciliation/gate.py`](robo_dados_publicos/reconciliation/gate.py) |
| Observabilidade | Relatórios e cartões sanitizados, sem promover evidência bruta | [`docs/OBSERVABILITY_RUNBOOK.md`](docs/OBSERVABILITY_RUNBOOK.md), [`robo_dados_publicos/observability/report.py`](robo_dados_publicos/observability/report.py) |
| Persistência controlada | Bronze append-only e gates de escrita/publicação separados | [`docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_RUN_1_0.8.0.json`](docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_RUN_1_0.8.0.json), [`config/automation_policy.v1.json`](config/automation_policy.v1.json) |
| Produto | JSON, CSV, Markdown, HTML, PDF e manifesto; apresentação não é evidência | [`docs/M6_PRODUCT_MINIMAL_OUTPUT_0.7.0.md`](docs/M6_PRODUCT_MINIMAL_OUTPUT_0.7.0.md), [`scripts/build_product_output.py`](scripts/build_product_output.py) |
| GitHub Actions e gates | Workflows manuais/limitados e políticas validadas fail-closed | [`.github/workflows`](.github/workflows), [`scripts/github_automation_policy_gate.py`](scripts/github_automation_policy_gate.py) |
| QA e regressão | Suíte unitária, selftest, manifests e gates específicos | [`tests`](tests), [`QA_SOFTWARE_V01_0.8.0.json`](QA_SOFTWARE_V01_0.8.0.json) |

Essas provas têm o alcance dos respectivos contratos. Elas não ligam schedule,
não autorizam rerun e não promovem hipótese semântica a fato.

## 3. Estado do SIOPE 2025

| Aspecto | Estado canônico | O que a evidência permite afirmar |
| --- | --- | --- |
| Estrutura recente de 2025 | `PROVEN_STRUCTURAL_RECENT` | P1–P6 foram observados; o P6 observado expôs schema exato de 52 campos e os 11 nomes de inputs requeridos pelo pipeline. |
| Disponibilidade/papel de P6 | `PROVEN_AVAILABLE_CLOSURE_UNKNOWN` / `P6_ANNUAL_CONSOLIDATION_PROVEN_FINALITY_UNKNOWN` | P6 existe e seu papel documental de consolidação anual foi provado; existência e papel não provam finalidade/imutabilidade. |
| `NUM_POPU` | `NOT_PROVEN` | Presença estrutural não prova significado oficial, fonte da população nem regra de ano/data de referência. |
| Bridge dos dez aliases financeiros atuais | `NOT_PROVEN_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_MISSING` | `9/10` aliases são `PROVEN_EXACT_OPERATIONAL`. `VL_DESP_DOTA_ATUA_EDU` é `PARTIAL_CURRENT_EXACT_1000_VARIANCE_NO_SOURCE_DEFINED_INCLUSION_RULE`; o resultado permanece contexto, não promoção canônica. |
| Comparabilidade semântica com 2016–2024 | `UNKNOWN` | Schema e documentação histórica não provam continuidade semântica atual. |
| Submissão e efetividade anual | `VALID_ANNUAL_SUBMISSION = PROVEN`; `CURRENTLY_EFFECTIVE_DECLARATION = NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING`; fechamento `UNKNOWN` | O recibo oficial prova entrega anual válida, não a regra de seleção/supersessão da declaração atualmente efetiva. |
| Gold 2025 | `UNKNOWN` / `BLOCKED` | Não calculado, não persistido e não autorizado. |
| Entrada na série anual fechada | `BLOCKED` | A série permanece **exatamente `2016–2024`**. |
| 2026 | fora do escopo fechado | `UNPROVEN_CURRENT_YEAR`; nenhuma promoção. |

As decisões e os limites estão pinados em
[`docs/tasks/TASK_005_SIOPE_2025_REGIME_PROMOTION_ASSESSMENT.md`](docs/tasks/TASK_005_SIOPE_2025_REGIME_PROMOTION_ASSESSMENT.md),
[`docs/tasks/TASK_007_SIOPE_2025_OFFICIAL_DOCUMENTARY_PROOF.md`](docs/tasks/TASK_007_SIOPE_2025_OFFICIAL_DOCUMENTARY_PROOF.md),
[`docs/tasks/TASK_008_SIOPE_2025_ALIAS_FINALITY_AUDIT.md`](docs/tasks/TASK_008_SIOPE_2025_ALIAS_FINALITY_AUDIT.md) e
[`docs/tasks/TASK_009E_L_R_SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_REVIEW.md`](docs/tasks/TASK_009E_L_R_SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_REVIEW.md).

## 4. Bloqueios para promoção da 0.8.0

### B1 — semântica de `NUM_POPU`

Estado: `NOT_PROVEN_DEFINITION_SOURCE_VINTAGE_MISSING`. Faltam conjuntamente a
definição, a fonte autoritativa e a regra de data/ano/versão. Aguarda resposta
FNDE do protocolo `23546.111503/2026-95`.

### B2 — bridge semântico dos aliases financeiros recentes

Estado: `NOT_PROVEN_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_MISSING`. Nove de dez
aliases estão provados de modo exato e operacional. Resta a regra definida pela
fonte para inclusão/agregação de `VL_DESP_DOTA_ATUA_EDU`, aguardando o protocolo
FNDE `23546.111504/2026-30`.

### B3 — fechamento/finalidade anual de 2025

`ANNUAL_CONSOLIDATION = PROVEN` e `VALID_ANNUAL_SUBMISSION = PROVEN`, com recibo
`428477-6` pinado pelo SHA-256
`41d5dba704d9de9309819ac1cb58a08bdbd85ae88d5dfdc3d1b936c654790e29`.
Contudo, `CURRENTLY_EFFECTIVE_DECLARATION =
NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING` e `annual_closure_status = UNKNOWN`.
A evidência estrutural `RETIFICADORA` / `RECIBO` / `RECIBO ANTERIOR` não prova
seleção nem supersessão. Aguarda o protocolo FNDE `23546.111502/2026-41`.

### B4 — Gold determinístico 2025

Estado: `BLOCKED_BY_B1_B2_B3`. O gate preparado também exige comparabilidade
semântica `PROVEN`, separadamente; B1+B2+B3 não a provam por inferência. Decisão
atual: `STOP_GOLD_2025_PREREQUISITES_NOT_PROVEN`. Gold 2025 permanece
`UNKNOWN/BLOCKED` e não foi calculado.

### B5 — regressão/comparabilidade 2016–2025

Estado: `BLOCKED_BY_B4`. Depende de Gold 2025 autorizado/computado, evidência
determinística validada, comparabilidade, QA/regressão e decisão explícita de
inclusão. Decisão atual: `STOP_2025_SERIES_INCLUSION_GOLD_NOT_ELIGIBLE`.

Fluxo de dependências:

```text
B1 + B2 + B3 + comparabilidade explícita -> B4 pode ser executado
B4 autorizado/computado + evidência + QA + decisão explícita -> B5 pode passar
decisão de inclusão + gates de release -> possível promoção de 0.8.0 CANDIDATE
```

Nenhuma seta representa promoção automática.

## 4.1 Solicitações FNDE e prontidão da release

As solicitações foram apresentadas em `2026-08-30`, têm autoridade `FNDE` e
prazo `2026-09-21`. Os protocolos são evidência apenas da atividade de aquisição:
B3 `23546.111502/2026-41`, B1 `23546.111503/2026-95` e B2
`23546.111504/2026-30`. Enquanto pendentes, têm efeito de promoção `NONE`.

O gate de release-readiness decide
`KEEP_0_8_0_CANDIDATE_BLOCKERS_REMAIN`. A release `0.8.0` permanece
`CANDIDATE`; prontidão futura será apenas avaliação e não publicação, deploy,
schedule ou recorrência.

## 5. Roadmap pós-0.8.0

Os itens abaixo são posteriores e **não são requisitos implícitos** para promover
a 0.8.0:

- persistência recorrente e atualização autorizada;
- recorrência e schedule, sujeitos a política e autorização próprias;
- expansão para SAEB, SARESP, Censo Escolar e demais indicadores;
- produto consolidado entre fontes;
- dashboard ou outra interface humana.

## 6. Matriz de maturidade

| Área | Estado | Evidência | Próximo gate |
| --- | --- | --- | --- |
| Engenharia base | `PROVEN` nos contratos existentes | Bronze/Silver/Gold histórico, reconciliação, observabilidade, produto, QA | Manter regressão e limites operacionais |
| Histórico SIOPE | `PROVEN` | Série fechada `2016–2024` | Nenhum para o escopo histórico atual |
| SIOPE 2025 estrutural | `PROVEN_STRUCTURAL_RECENT` | P1–P6, P6/52 campos, 11 inputs presentes | Preservar evidência pinada |
| SIOPE 2025 semântico | `UNKNOWN` / `NOT_PROVEN` | TASKs 007–009E | B1 e B2 com fonte oficial aplicável |
| Fechamento 2025 | `UNKNOWN` | Consolidação anual provada; finalidade não provada | B3 independente |
| Gold 2025 | `UNKNOWN` / `BLOCKED` | Nenhum Gold autorizado | B4 após B1–B3 |
| Automação recorrente | `BLOCKED` fora dos gates elegíveis | Política canônica de automação | Autorização/tier separado; sem schedule implícito |
| Outras fontes | Pós-0.8.0 | Contratos históricos não autorizam expansão automática | Gate próprio por fonte |
| Produto/interface | Produto em arquivos `PROVEN`; dashboard fora do escopo | M6/M8 | Roadmap separado |

## 7. Auditoria de resíduos documentais e issue #183

| Item | Classificação | Diagnóstico/ação |
| --- | --- | --- |
| `README.md` | `CURRENT` após atualização canônica | Resume 9/10 aliases, submissão válida, os três protocolos pendentes e os gates bloqueados. |
| `STATUS_0.8.0.md` | `CANONICAL_UPDATE_REQUIRED` antes da TASK 011; `CURRENT` após este patch | A fotografia genérica B1/B2/B3 foi substituída pelo estado pós-M7 e pela cadeia B4/B5/readiness. |
| `docs/RELEASE_NOTES_V01_0.8.0.md` | `SUPERSEDED_BUT_HISTORICAL` | Preserva o desenho inicial `CONTRACT_VALIDATED`; recebeu rótulo explícito e não foi reescrita como se conhecesse evidência posterior. |
| `docs/M7_NEXT_GATE_0.8.0.md` e documentos M7 de gates individuais | **parcialmente ou totalmente superados como “próximo gate”** | Continuam úteis como trilha de auditoria. Não devem ser lidos como roadmap corrente; este documento prevalece para estado. |
| TASKs 004A–004B | **totalmente superadas quanto ao estado recente; ainda válidas como histórico** | O timeout/`UNPROVEN_RECENT` foi sucedido pela observação 004C e pela promoção estrutural da TASK 005. Não apagar. |
| TASKs 004C–009E | **ainda válidas**, com gates intermediários consumidos/superados | Formam a cadeia de evidência recente; a conclusão 009E mantém S1/S2 `NOT_PROVEN`. |
| Issue GitHub `#183` — `[CODEX] TASK 004 — primeiro discovery live SIOPE 2025 bounded T1` | **totalmente superada como task ativa; válida como histórico** | Seus objetivos operacionais foram consumidos pela execução/revisão do primeiro live bounded na TASK 004B e pelo segundo live bounded bem-sucedido na TASK 004C. A TASK 005 formalizou a promoção estritamente estrutural resultante, e os estados posteriores passaram a ser governados pelas TASKs 005–009E. Recomenda-se o fechamento administrativo da issue, preservando seu histórico. |

A classificação da issue #183 não altera o estado do SIOPE 2025: estrutura
recente permanece `PROVEN_STRUCTURAL_RECENT`; semântica, finalidade,
comparabilidade e Gold permanecem nos estados fail-closed registrados na seção 3.
