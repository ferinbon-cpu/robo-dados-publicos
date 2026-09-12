# STATUS 0.8.0

Este é o documento canônico de estado corrente da release `0.8.0 CANDIDATE`. Ele consolida a evidência já pinada no repositório e **não** autoriza coleta, Gold 2025, inclusão de 2025 na série, publicação, deploy, persistência recorrente, schedule ou promoção de release.

## 1. Fotografia canônica

- **Release ativa:** `0.7.0 ACTIVE`.
- **Release candidata:** `0.8.0 CANDIDATE`.
- **Base da TASK 241:** `2d898e99bd8681ec6f020430bead20df7ac3d370`.
- **Série anual SIOPE fechada:** `2016–2024`.
- **Comparabilidade semântica 2016–2025:** `PARTIAL`.
- **Inputs financeiros:** `10/10 PARTIAL`.
- **Métricas financeiras Gold 1–6:** `6/6 PARTIAL`, não autorizadas para Gold 2025.
- **Métricas per capita Gold 7–8:** `2/2 NON_COMPARABLE` sob o contrato `NUM_POPU`; rebase IBGE requerido.
- **Gold 2025:** `BLOCKED_NOT_CALCULATED`.
- **2026:** `UNPROVEN_CURRENT_YEAR`.

Os blockers B1/B2/B3 permanecem resolvidos dentro dos limites de suas provas. A TASK 241 mostrou que o bloqueio restante se divide em duas trilhas: **pinagem histórica financeira sob padrão semântico versionado equivalente** e **contrato populacional IBGE homogêneo para 2016–2025**.

## 2. Observatório territorial

A evidência TASK199H fecha a cobertura geográfica da rede municipal mapeada:

- vínculo forte escola→setor censitário IBGE 2022: **69/69**;
- `HELD geography`: **0**;
- `TERRITORY_PROFILE`: **284 linhas**;
- contexto numérico de renda setorial: **68/69** escolas;
- uma escola, INEP `35286229`, possui missingness oficial `SOURCE_EXPLICIT_X`;
- `X != 0` e nenhuma renda numérica é fabricada para esse setor;
- cobertura contextual: **38/38**.

Cobertura geográfica integral não equivale a renda numérica integral e renda do setor não equivale a renda dos estudantes ou das famílias matriculadas.

## 3. SIOPE 2025 — blockers resolvidos

### B1 — `NUM_POPU`

B1 = `RESOLVED_BY_EXCLUSION_FROM_ANALYTICAL_POPULATION_SEMANTICS`.

A resposta oficial do FNDE classifica `NUM_POPU` como campo legado, cujo conteúdo foi replicado de exercícios anteriores e cuja referência temporal atual não é assegurável. O FNDE recomenda desconsiderá-lo para análise populacional e usar bases oficiais do IBGE diretamente.

Consequências canônicas:

- `NUM_POPU` não é população 2025;
- `NUM_POPU` não pode ser usado como denominador analítico de 2025;
- métricas per capita precisam de fonte IBGE e período de referência explícitos;
- compatibilidade dos denominadores históricos não pode ser inferida;
- eventual rebase deve criar nova série comparável e preservar o Gold histórico original.

Evidência principal: `docs/evidence/TASK_010N_R_E_M6_SIOPE_NUM_POPU_FNDE_DISPOSITION_0.8.0.json`.

### B2 — aliases financeiros

B2 = `PROVEN_10_OF_10_ALIAS_TO_CONCEPT`.

Os dez aliases financeiros de 2025 estão ligados aos conceitos oficiais aplicáveis. O alias `VL_DESP_DOTA_ATUA_EDU` foi ligado ao conceito de despesa com Educação/Função 12 — dotação atualizada.

Limites preservados:

- `backend_aggregation_formula = NOT_PROVEN`;
- a diferença observada de R$ 1.000 não foi convertida em regra de inclusão/exclusão inventada;
- `RREO line 33 != definição obrigatória do alias`;
- `EDU != MDE` como identidade geral;
- B2 prova semântica **atual** dos aliases, não continuidade histórica 2016–2025 por si só.

Evidência principal: `docs/evidence/TASK_195C_SIOPE_FUNCAO12_ALIAS_BRIDGE_0.8.0.json`.

### B3 — declaração anual efetiva

B3 = `PROVEN_DYNAMIC_EFFECTIVE_SELECTION_RULE_WITH_PINNED_LIMEIRA_RECEIPT`.

A resposta oficial FNDE ao NUP `23546.111502/2026-41` estabelece que, para o mesmo ente, exercício e período:

1. declaração retificadora posterior substitui a anterior;
2. a declaração vigente é a última transmitida e recepcionada com sucesso;
3. a consulta pública `Recibos de Transmissão` apresenta o recibo correspondente a essa última transmissão bem-sucedida;
4. o comportamento é uma regra implementada no SIOPE, ainda que não exista manual técnico específico descrevendo-a.

Aplicada à evidência já pinada de Limeira, o recibo anual efetivo na observação de `2026-08-30` é **`428477-6`**. Essa prova é temporal e dinâmica: futura retificação transmitida e recebida com sucesso substitui a versão anterior e exige refresh. Nenhuma imutabilidade futura foi inferida.

Evidência principal: `docs/evidence/TASK_240_SIOPE_2025_EFFECTIVE_ANNUAL_DECLARATION_0.8.0.json`.

## 4. TASK 241 — comparabilidade semântica

A TASK 241 foi executada usando apenas evidência já materializada. O resultado global é:

`PARTIAL_FINANCIAL_CONTINUITY_HISTORICAL_VERSIONING_GAP_PER_CAPITA_REQUIRES_IBGE_REBASE`.

### 4.1 Dez inputs financeiros

Os dez aliases de 2025 têm conceitos oficiais provados e o histórico 2016–2024 usa a mesma família `Dados_Gerais_Siope`, o mesmo contrato de 52 campos e os mesmos nomes dos inputs Gold. A documentação FNDE e a evidência operacional oferecem **forte corroboracão de continuidade**.

Entretanto, a própria auditoria TASK010N registrou:

- `HISTORICAL_PROOF_STANDARD_INSUFFICIENT`;
- `NO_POSITIVE_BREAK_EVIDENCE_FOUND`;
- `2025_STRICTER_THAN_HISTORICAL`.

Isso significa que a ausência de ruptura conhecida é corroborativa, mas o histórico 2016–2024 não está pinado sob o mesmo padrão semântico **versionado, ano a ano**, hoje exigido para 2025. Por isso:

- `PROVEN_COMPARABLE = 0`;
- `PARTIAL = 10`;
- `NON_COMPARABLE = 0`.

### 4.2 Métricas financeiras 1–6

As seis fórmulas conservam exatamente os pares de numerador/denominador esperados e usam apenas os dez aliases financeiros. Mesmo assim, **mesma fórmula não equivale a continuidade semântica**. Como seus inputs permanecem `PARTIAL`, as seis métricas também são classificadas como `PARTIAL`.

Consequência: **nenhuma das métricas 1–6 está autorizada para Gold 2025 neste estado**.

### 4.3 Métricas per capita 7–8

As duas métricas históricas per capita usam `NUM_POPU`. Como B1 excluiu esse campo do uso populacional analítico atual e a compatibilidade temporal dos denominadores históricos não foi provada, as métricas 7–8 são:

`NON_COMPARABLE` sob o contrato atual.

A rota obrigatória é:

`IBGE_HOMOGENEOUS_DENOMINATOR_REBASE_2016_2025`.

Isso deve produzir uma **nova série comparável** com fonte IBGE e período de referência explícitos, preservando os Gold históricos existentes como artefatos históricos.

**Gold 2025 permanece bloqueado e não calculado.**

## 5. Contratos correntes e snapshots históricos

Para leitura de **estado corrente**, prevalecem:

- `config/release_0_8_0_readiness.v3.json`;
- `config/siope_2025_gold_prerequisites.v3.json`;
- `config/siope_2025_semantic_comparability.v1.json`;
- `docs/evidence/TASK_241_SIOPE_2016_2025_SEMANTIC_COMPARABILITY_0.8.0.json`.

Continuam preservados, sem reescrita retrospectiva:

- `config/release_0_8_0_readiness.v1.json` e `.v2.json`;
- `config/siope_2025_gold_prerequisites.v1.json` e `.v2.json`;
- `docs/evidence/TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING_0.8.0.json`;
- evidências intermediárias TASK005–TASK240.

Esses arquivos antigos registram corretamente o que era conhecido **naquele momento**. Eles não devem ser alterados para parecer que já continham evidências posteriores.

## 6. Readiness da 0.8.0

Estado corrente:

```text
B1 ✅ RESOLVIDO
B2 ✅ RESOLVIDO
B3 ✅ RESOLVIDO
comparabilidade financeira 1–6 ⚠ PARTIAL
per capita 7–8 ⛔ NON_COMPARABLE no contrato NUM_POPU
Gold 2025 ⛔ não calculado / não autorizado
inclusão de 2025 na série ⛔
0.8.0 = CANDIDATE
```

A sequência correta agora é bifurcada:

```text
A) ponte semântica financeira histórica versionada 2016–2024
                         ┐
                         ├─> somente após prova suficiente: novo gate Gold 2025
B) contrato IBGE/rebase populacional 2016–2025
                         ┘
                                      ↓
                              QA + regressão histórica
                                      ↓
                       decisão explícita de inclusão de 2025
                                      ↓
                              release-readiness
```

Nenhuma seta representa promoção automática.

## 7. Guardas atuais

- `CURRENT_STATE_NE_HISTORICAL_EVIDENCE_REWRITE`;
- `FULL_NETWORK_GEOGRAPHY_NE_COMPLETE_NUMERIC_INCOME`;
- `SOURCE_EXPLICIT_X_NE_ZERO`;
- `NUM_POPU_NE_VALID_2025_POPULATION_DENOMINATOR`;
- `B2_ALIAS_CONCEPT_PROOF_NE_BACKEND_FORMULA`;
- `B3_EFFECTIVE_STATE_NE_IMMUTABLE_FINALITY`;
- `SAME_FIELD_NAME_NE_SEMANTIC_COMPARABILITY`;
- `SAME_FORMULA_NE_SEMANTIC_COMPARABILITY`;
- `NO_POSITIVE_BREAK_FOUND_NE_CONTINUITY_PROVEN`;
- `B1_B2_B3_NE_SEMANTIC_COMPARABILITY_BY_INFERENCE`;
- `PARTIAL_COMPARABILITY_NE_GOLD_AUTHORIZATION`;
- `IBGE_REBASE_NE_HISTORICAL_GOLD_REWRITE`;
- `NO_GOLD_2025_CALCULATION`;
- `NO_2025_SERIES_INCLUSION`;
- `NO_RELEASE_PROMOTION`;
- `NO_REMOTE_SOURCE_COLLECTION` na TASK 241;
- `NO_DRIVE_WRITE` na TASK 241;
- `NO_SCHEDULE_OR_RECURRENCE`.

## 8. Próximos passos canônicos

Abrir gates separados para:

1. **`HISTORICAL_FINANCIAL_SEMANTIC_VERSIONED_BRIDGE_2016_2024`** — provar, sob padrão compatível com 2025, a continuidade histórica dos dez conceitos financeiros antes de qualquer promoção das métricas 1–6;
2. **`IBGE_POPULATION_DENOMINATOR_REBASE_CONTRACT_2016_2025`** — definir fonte/vintage/período IBGE homogêneos e construir nova série per capita comparável sem reescrever o Gold histórico.

Somente depois de evidência suficiente nesses gates deve existir um novo gate de cálculo Gold 2025.
