# STATUS 0.8.0

Este é o documento canônico de estado da release `0.8.0 CANDIDATE`. Ele consolida
evidência já pinada no repositório; não autoriza nova coleta, persistência,
publicação, recorrência ou promoção de dados.

## 1. Estado da release

- **Release ativa:** `0.7.0 ACTIVE`.
- **Release candidata:** `0.8.0 CANDIDATE`.
- **Base auditada:** `f4688f5ac8ab23d54758e84c0d296f21ce025b93` (`main`
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
| Bridge dos dez aliases financeiros atuais | `NOT_PROVEN` | Nomes atuais foram observados, mas não existe bridge oficial suficiente, alias por alias, para os conceitos históricos. Similaridade nominal não é prova. |
| Comparabilidade semântica com 2016–2024 | `UNKNOWN` | Schema e documentação histórica não provam continuidade semântica atual. |
| Fechamento/finalidade anual | `UNKNOWN` | P6 disponível não prova que o exercício esteja final e fechado. |
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

Falta evidência primária oficial atual que prove conjuntamente definição, fonte e
regra temporal. Estado: `NOT_PROVEN`.

### B2 — bridge semântico dos aliases financeiros recentes

Falta evidência oficial aplicável ao regime atual que ligue individualmente os
dez aliases financeiros aos conceitos usados pelo Gold histórico. Estado:
`NOT_PROVEN`.

### B3 — fechamento/finalidade anual de 2025

Falta prova independente de que o P6 observado representa estado anual
suficientemente final para a série fechada. Estado: `UNKNOWN`.

### B4 — Gold determinístico 2025

Depende de **B1 + B2 + B3** e de um gate separado que autorize cálculo e valide
os inputs. Até lá, Gold 2025 permanece `UNKNOWN` / `BLOCKED`.

### B5 — regressão/comparabilidade 2016–2025

Depende de Gold 2025 elegível e de QA/regressão explícitos. Só então pode haver
decisão formal, separada, sobre incluir 2025 na série.

Fluxo de dependências:

```text
B1 + B2 -> semântica suficiente
semântica suficiente + B3 -> elegibilidade para um gate de Gold 2025
Gold 2025 autorizado + B5 -> decisão formal sobre inclusão de 2025
decisão de inclusão + gates de release -> possível promoção de 0.8.0 CANDIDATE
```

Nenhuma seta representa promoção automática.

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
| `README.md` antes desta consolidação | **totalmente superado** no resumo M7; **necessita atualização** | Ainda dizia rota/schema 2025 `UNPROVEN` e coleta SIOPE não autorizada, apesar das provas posteriores. Atualizado para apontar este status. |
| `docs/RELEASE_NOTES_V01_0.8.0.md` | **parcialmente superado; necessita atualização futura** | Preserva corretamente o desenho inicial da candidata, mas sua fotografia `CONTRACT_VALIDATED` antecede TASKs 004–009E. Mantido como nota histórica, não como status canônico. |
| `docs/M7_NEXT_GATE_0.8.0.md` e documentos M7 de gates individuais | **parcialmente ou totalmente superados como “próximo gate”** | Continuam úteis como trilha de auditoria. Não devem ser lidos como roadmap corrente; este documento prevalece para estado. |
| TASKs 004A–004B | **totalmente superadas quanto ao estado recente; ainda válidas como histórico** | O timeout/`UNPROVEN_RECENT` foi sucedido pela observação 004C e pela promoção estrutural da TASK 005. Não apagar. |
| TASKs 004C–009E | **ainda válidas**, com gates intermediários consumidos/superados | Formam a cadeia de evidência recente; a conclusão 009E mantém S1/S2 `NOT_PROVEN`. |
| Issue GitHub `#183` | **necessita auditoria; classificação de mérito não observada** | O ambiente não disponibilizou conteúdo autenticado da issue e a tentativa pública foi bloqueada. Ela não foi fechada nem declarada superada. Recomenda-se ler corpo/comentários no GitHub e só então relacioná-la nominalmente às TASKs/commits substitutos. |

A impossibilidade de observar a issue #183 é tratada de forma fail-closed: a
proximidade cronológica com trabalhos posteriores não basta para concluir que seu
escopo foi cumprido.
