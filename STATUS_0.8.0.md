# STATUS 0.8.0

Este é o estado canônico corrente da `0.8.0 CANDIDATE`. Ele consolida a evidência já pinada e o roteamento posterior às TASK 242 e 243. Snapshots históricos permanecem preservados; este documento não reescreve o que era conhecido em etapas anteriores.

## 1. Fotografia corrente

- **Release ativa:** `0.7.0 ACTIVE`.
- **Release candidata:** `0.8.0 CANDIDATE`.
- **Main de entrada da TASK 244:** `094595b1ba8dd9d82596b918b621a2ae939aa204`.
- **Série anual SIOPE fechada:** `2016–2024`.
- **B1 / NUM_POPU:** `RESOLVED_BY_EXCLUSION_FROM_ANALYTICAL_POPULATION_SEMANTICS`.
- **B2 / aliases financeiros:** `PROVEN_10_OF_10_ALIAS_TO_CONCEPT`.
- **B3 / declaração efetiva:** `PROVEN_DYNAMIC_EFFECTIVE_SELECTION_RULE_WITH_PINNED_LIMEIRA_RECEIPT`.
- **Comparabilidade semântica 2016–2025:** `PARTIAL`.
- **Inputs financeiros:** `10/10 PARTIAL`.
- **Métricas financeiras Gold 1–6:** `6/6 PARTIAL`.
- **Métricas per capita Gold 7–8:** `2/2 NON_COMPARABLE` sob o contrato `NUM_POPU`.
- **Gold 2025:** `BLOCKED_NOT_CALCULATED`.

Gold 2025 permanece bloqueado e não calculado.

- **Inclusão de 2025 na série:** não autorizada.
- **Promoção da 0.8.0:** não autorizada.

## 2. Observatório territorial

A rede municipal mapeada permanece em **69/69** vínculos fortes escola→setor censitário IBGE 2022, `HELD=0`, `TERRITORY_PROFILE=284` linhas e contexto numérico de renda setorial para **68/69** escolas. A escola INEP `35286229` mantém missingness oficial `SOURCE_EXPLICIT_X`; `X != 0`. Cobertura contextual: **38/38**.

## 3. O que as TASK 241–243 provaram

A TASK 241 separou a comparabilidade em duas trilhas. Para os dez inputs financeiros e as métricas 1–6, mesma família `Dados_Gerais_Siope`, mesmos nomes e mesmas fórmulas são forte corroboração, mas não bastam para provar continuidade semântica longitudinal sob o padrão atual. Para as métricas per capita 7–8, o denominador histórico `NUM_POPU` não pode ser transportado para 2025 como população analítica.

A TASK 242 concluiu a auditoria offline da trilha financeira com o resultado:

`STOP_HISTORICAL_FINANCIAL_SEMANTIC_PROMOTION_PRIMARY_TEMPORAL_PUBLIC_CONTRACT_EVIDENCE_REQUIRED`.

Ela estabeleceu que o próximo passo deve buscar primeiro **evidência pública oficial FNDE/SIOPE com aplicabilidade temporal**, e que CML/XML/Delphi ou fórmula interna do backend não são requisitos por padrão.

A TASK 243 concluiu a auditoria offline do denominador com o resultado:

`STOP_IBGE_REBASE_SOURCE_CONTRACT_NOT_PINNED`.

Ela estabeleceu que Censo 2022 e estimativa 2025 isolados não formam uma série homogênea 2016–2025. A futura série comparável deve ser um produto separado, `SIOPE_PER_CAPITA_IBGE_REBASED_2016_2025`, preservando o Gold histórico original.

## 4. Estado de aquisição após TASK 244

As duas auditorias offline estão concluídas. Portanto, os próximos passos não são mais “abrir TASK 242/243”, mas executar dois gates bounded de evidência oficial:

### A — métricas financeiras 1–6

`BOUNDED_OFFICIAL_PUBLIC_CONTRACT_TEMPORAL_EVIDENCE_ACQUISITION_REQUIRES_EXPLICIT_AUTHORIZATION`

Objetivo: obter evidência pública primária FNDE/SIOPE suficiente para provar ou rejeitar continuidade semântica dos dez inputs financeiros nos regimes 2016–2024, incluindo identidade do campo/alias, conceito, unidade, fronteira de agregação, estágio orçamentário quando aplicável e vigência temporal/versionada.

**TASK245 — aquisição documental de 15/09/2026: PARTIAL.** Oito artefatos oficiais foram adquiridos e pinados por SHA-256. O catálogo associa o dicionário de 2019 aos consolidados 2008–2016/2017/2018/2019; a documentação Olinda v1 expõe os dez aliases com descrições vazias. Restam três proposições delimitadas por input: correspondência temporal dos campos, unidade/escala e continuidade das fronteiras de agregação. A especificação do menor documento oficial capaz de fechá-las está em `docs/tasks/TASK_245_SIOPE_TEMPORAL_CONTRACT_FINDINGS.md`. Os dez inputs e as seis métricas permanecem PARTIAL; B2/2025 e os snapshots anteriores estão preservados.

### B — métricas per capita 7–8

`BOUNDED_OFFICIAL_IBGE_POPULATION_SOURCE_CONTRACT_AND_SERIES_ACQUISITION_REQUIRES_EXPLICIT_AUTHORIZATION`

Objetivo: identificar e pinar o contrato oficial IBGE do denominador e uma cadeia 2016–2025 com conceito, município, período de referência, publicação/vintage, revisão e mudanças metodológicas explícitos. Mistura silenciosa de Censo e estimativas, imputação ou reaproveitamento de `NUM_POPU` permanecem proibidos.

**TASK246 — aquisição documental de 16/09/2026: NOT_COMPARABLE sob um único contrato direto 2016–2025.** O IBGE condiciona comparação de estimativas municipais à mesma revisão das projeções; a cadeia adquirida atravessa as revisões 2013, 2018 e 2024 e o Censo 2022. Há nove referências anuais oficiais, com 2023 explicitamente ausente: a relação TCU 2023 publica população censitária de 2022. O anexo de 2025 registra atualização territorial de Limeira em 2024–2025, sem discriminar seu impacto populacional. Foram pinados 34 artefatos e um inventário auditável, sem criar série de denominadores comparáveis. O artefato necessário para superar o bloqueio é uma série municipal oficial harmonizada, ou adaptação oficial com todos os inputs, incluindo referência real em 2023 e território comum. Ver `docs/tasks/TASK_246_IBGE_POPULATION_FINDINGS.md`. Nenhum cálculo per capita foi autorizado ou realizado.

Em **14/09/2026**, o usuário autorizou o grande salto completo, incluindo essas duas aquisições oficiais em modo bounded/read-only. Essa autorização **não** autoriza Gold 2025, cálculo da série rebased, inclusão de 2025, publicação, deploy, recorrência ou promoção da release.

## 5. Contratos correntes

Para leitura do estado atual, prevalecem:

- `config/release_0_8_0_readiness.v4.json`;
- `config/siope_2025_gold_prerequisites.v4.json`;
- `config/siope_2025_semantic_comparability.v1.json`;
- `config/siope_historical_financial_semantic_versioning.v2.json` (resultado documental TASK245; v1 histórica preservada);
- `config/ibge_population_denominator_rebase.v2.json` (resultado TASK246; v1 histórica preservada);
- `config/ibge_municipal_population_2016_2025.v1.json`;
- `config/ibge_municipal_population_acquisition.v1.json`;
- `docs/evidence/TASK_244_POST_TASK242_TASK243_ACQUISITION_READY_STATE_0.8.0.json`.
- `docs/evidence/TASK_245_SIOPE_OFFICIAL_TEMPORAL_CONTRACT_ACQUISITION_0.8.0.json` (resultado da aquisição financeira; sem promoção de readiness ou Gold).
- `docs/evidence/TASK_246_IBGE_MUNICIPAL_POPULATION_2016_2025_0.8.0.json` (resultado IBGE; inventário não habilita denominador homogêneo ou razão per capita).

Os arquivos v1–v3 de readiness/Gold e as evidências TASK005–TASK243 permanecem snapshots históricos e não devem ser reescritos retrospectivamente.

## 6. Readiness

```text
B1 ✅ RESOLVIDO
B2 ✅ RESOLVIDO
B3 ✅ RESOLVIDO
TASK242 auditoria offline ✅ concluída
TASK243 auditoria offline ✅ concluída
financeiro 1–6 ⚠ PARTIAL → TASK245: três proposições públicas temporais delimitadas
per capita 7–8 ⛔ NON_COMPARABLE → TASK246: cadeia IBGE NOT_COMPARABLE; harmonização oficial pendente
Gold 2025 ⛔ BLOCKED_NOT_CALCULATED
série fechada = 2016–2024
0.8.0 = CANDIDATE
```

A sequência fail-closed é:

```text
FNDE/SIOPE temporal evidence ┐
                             ├─> comparabilidade provada/rejeitada por métrica
IBGE denominator contract ───┘
                                      ↓
                    somente se suficiente: novo gate Gold 2025
                                      ↓
                            QA + regressão histórica
                                      ↓
                     decisão explícita de inclusão de 2025
                                      ↓
                              release-readiness
```

Nenhuma seta representa promoção automática.

## 7. Guardas

- `CURRENT_STATE_NE_HISTORICAL_EVIDENCE_REWRITE`;
- `TASK242_COMPLETION_NE_FINANCIAL_COMPARABILITY_PROVEN`;
- `TASK243_COMPLETION_NE_IBGE_SOURCE_CONTRACT_PROVEN`;
- `SAME_ALIAS_NE_TEMPORAL_SEMANTIC_CONTINUITY`;
- `NUM_POPU_NE_VALID_2025_POPULATION_DENOMINATOR`;
- `BOUNDED_SOURCE_ACQUISITION_NE_GOLD_AUTHORIZATION`;
- `NO_GOLD_2025_CALCULATION`;
- `NO_2025_SERIES_INCLUSION`;
- `NO_RELEASE_PROMOTION`;
- `NO_HISTORICAL_GOLD_REWRITE`;
- `NO_SILENT_CENSUS_ESTIMATE_MIX`;
- `NO_SILENT_IMPUTATION`;
- `NO_DRIVE_WRITE` na TASK 244;
- `NO_SCHEDULE_OR_RECURRENCE`.

## 8. Próximo marco

As aquisições TASK245/246 produziram decisões auditáveis: financeiro `PARTIAL`, denominador IBGE adquirido `NOT_COMPARABLE` sob um único contrato direto. O próximo marco exige o conteúdo oficial específico delimitado em cada evidência: G1/G2/G3 financeiros e série municipal harmonizada/adaptada com referência 2023 e território provados. Qualquer cálculo per capita permanece uma etapa separada com autorização própria. **Gold 2025 permanece bloqueado**.

## 9. Jornal Oficial — rolling discovery TASK247/TASK248

A TASK247 materializou um carrier bounded de descoberta incremental do Jornal Oficial e executou uma única prova live read-only vinculada ao `main` `3c3b59606ecafbd48fe634ef850543ac03c72bdc`. O GitHub Actions run `35151868669` terminou `success` e retornou `PASS_JOM_ROLLING_DELTA_DISCOVERY`.

A TASK248 canoniza esse resultado como `PASS_JOM_ROLLING_DELTA_CANONIZED`: a baseline permaneceu válida até 08/09/2026 e foram observadas quatro novas identidades oficiais na janela 09/09–16/09/2026 — edições **7321, 7322, 7323 e 7324**, publicadas respectivamente em **09, 10, 11 e 12/09/2026**. A execução consumiu uma página de índice e dois GETs remotos estimados, com **0 downloads de PDF, 0 writes Drive, 0 writes serving, 0 publicação, 0 promoção, 0 recurrence e 0 schedule**.

A prova é exclusivamente de identidade/rota documental. Conteúdo dos PDFs, eventos semânticos, ingestão Bronze/Drive, serving e recorrência continuam etapas separadas e não autorizadas por esta canonização. Evidência: `docs/evidence/TASK_248_JOM_LIVE_DELTA_CANONICAL_RESULT_0.8.0.json`.
