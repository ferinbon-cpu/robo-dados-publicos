# STATUS 0.8.0

Este é o documento canônico de estado corrente da release `0.8.0 CANDIDATE`. Ele consolida a evidência já pinada no repositório e **não** autoriza coleta, Gold 2025, inclusão de 2025 na série, publicação, deploy, persistência recorrente, schedule ou promoção de release.

## 1. Fotografia canônica

- **Release ativa:** `0.7.0 ACTIVE`.
- **Release candidata:** `0.8.0 CANDIDATE`.
- **Base reconciliada:** `07952f63c6ec86a5dd9ce316cc2516c8e4225580`.
- **Série anual SIOPE fechada:** `2016–2024`.
- **Próximo gate:** **TASK 241 / issue #809 — comparabilidade semântica 2016–2025**.
- **Gold 2025:** `BLOCKED_NOT_CALCULATED`.
- **2026:** `UNPROVEN_CURRENT_YEAR`.

Os três blockers externos B1/B2/B3 já foram resolvidos dentro dos limites de suas provas. O bloqueio corrente deixou de ser “esperar resposta FNDE” e passou a ser **provar comparabilidade semântica antes de qualquer Gold 2025**.

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

A resposta oficial do FNDE classifica `NUM_POPU` como campo legado, cujo conteúdo foi replicado de exercícios anteriores e cuja referência temporal atual não é assegurável. O próprio FNDE recomenda desconsiderá-lo para análise populacional e usar bases oficiais do IBGE diretamente.

Consequências canônicas:

- `NUM_POPU` não é população 2025;
- `NUM_POPU` não pode ser usado como denominador analítico de 2025;
- métricas per capita precisam de fonte IBGE e período de referência explícitos;
- a decisão sobre eventual rebase histórico pertence à TASK 241, não a B1.

Evidência principal: `docs/evidence/TASK_010N_R_E_M6_SIOPE_NUM_POPU_FNDE_DISPOSITION_0.8.0.json`.

### B2 — aliases financeiros

B2 = `PROVEN_10_OF_10_ALIAS_TO_CONCEPT`.

Os dez aliases financeiros necessários ao contrato atual estão ligados aos conceitos oficiais aplicáveis. O alias `VL_DESP_DOTA_ATUA_EDU` foi ligado ao conceito de despesa com Educação/Função 12 — dotação atualizada.

Limites preservados:

- `backend_aggregation_formula = NOT_PROVEN`;
- a diferença observada de R$ 1.000 não foi convertida em regra de inclusão/exclusão inventada;
- `RREO line 33 != definição obrigatória do alias`;
- `EDU != MDE` como identidade geral.

Evidência principal: `docs/evidence/TASK_195C_SIOPE_FUNCAO12_ALIAS_BRIDGE_0.8.0.json`.

### B3 — declaração anual efetiva

B3 = `PROVEN_DYNAMIC_EFFECTIVE_SELECTION_RULE_WITH_PINNED_LIMEIRA_RECEIPT`.

A resposta oficial FNDE ao NUP `23546.111502/2026-41` estabelece que, para o mesmo ente, exercício e período:

1. declaração retificadora posterior substitui a anterior;
2. a declaração vigente é a última transmitida e recepcionada com sucesso;
3. a consulta pública `Recibos de Transmissão` apresenta o recibo correspondente a essa última transmissão bem-sucedida;
4. o comportamento é uma regra implementada no SIOPE, ainda que não exista manual técnico específico descrevendo-a.

Aplicada à evidência já pinada de Limeira, o recibo anual efetivo na observação de `2026-08-30` é **`428477-6`**. Essa prova é temporal e dinâmica: uma futura retificação transmitida e recebida com sucesso substituirá a versão anterior e exigirá refresh. Nenhuma imutabilidade futura foi inferida.

Evidência principal: `docs/evidence/TASK_240_SIOPE_2025_EFFECTIVE_ANNUAL_DECLARATION_0.8.0.json`.

## 4. Gate restante — comparabilidade 2016–2025

A comparabilidade permanece `UNKNOWN_REQUIRES_TASK241`.

B1+B2+B3 resolvidos **não** provam continuidade semântica da série por inferência. A TASK 241 deve avaliar três níveis separadamente:

1. **10 inputs financeiros** — continuidade conceitual e de estágio entre o histórico e 2025;
2. **métricas Gold 1–6** — continuidade de numerador e denominador financeiros;
3. **métricas Gold 7–8 per capita** — rota de denominador IBGE e necessidade ou não de rebase histórico homogêneo.

O contrato Gold histórico contém oito métricas. As seis primeiras são financeiras. As duas últimas usam população no denominador. Como B1 excluiu `NUM_POPU` do uso analítico, é proibido concluir `8/8 comparable` apenas pela permanência dos nomes dos campos ou das fórmulas.

Resultados possíveis da TASK 241 incluem prova integral, prova parcial ou, por exemplo, `PROVEN_FINANCIAL_6_OF_8_PER_CAPITA_REQUIRES_IBGE_REBASE`. O resultado será determinado pela evidência.

**Gold 2025 permanece bloqueado e não calculado.**

## 5. Contratos correntes e snapshots históricos

Para leitura de **estado corrente**, prevalecem:

- `config/release_0_8_0_readiness.v2.json`;
- `config/siope_2025_gold_prerequisites.v2.json`;
- `docs/evidence/TASK_239_CURRENT_0_8_0_STATE_0.8.0.json`.

Continuam preservados, sem reescrita retrospectiva:

- `config/release_0_8_0_readiness.v1.json`;
- `config/siope_2025_gold_prerequisites.v1.json`;
- `docs/evidence/TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING_0.8.0.json`;
- evidências intermediárias TASK005–TASK240.

Esses arquivos antigos registram corretamente o que era conhecido **naquele momento**. Eles não devem ser alterados para parecer que já continham evidências posteriores.

## 6. Readiness da 0.8.0

Estado corrente:

```text
B1 ✅ RESOLVIDO
B2 ✅ RESOLVIDO
B3 ✅ RESOLVIDO
comparabilidade 2016–2025 ❓ TASK 241
Gold 2025 ⛔ não calculado
inclusão de 2025 na série ⛔
0.8.0 = CANDIDATE
```

A sequência correta é:

```text
TASK 241 — comparabilidade
        ↓ somente se a evidência autorizar
Gold 2025 determinístico em gate próprio
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
- `B1_B2_B3_NE_SEMANTIC_COMPARABILITY_BY_INFERENCE`;
- `PARTIAL_COMPARABILITY_NE_FULL_GOLD_AUTHORIZATION`;
- `NO_GOLD_2025_CALCULATION`;
- `NO_2025_SERIES_INCLUSION`;
- `NO_RELEASE_PROMOTION`;
- `NO_REMOTE_SOURCE_COLLECTION` nesta reconciliação;
- `NO_DRIVE_WRITE` nesta reconciliação;
- `NO_SCHEDULE_OR_RECURRENCE`.

## 8. Próximo passo canônico

Executar **TASK 241 / #809** usando primeiro apenas evidência já materializada. Se a comparabilidade financeira puder ser provada mas as métricas per capita exigirem uma série populacional homogênea, abrir um contrato separado para **IBGE/rebase populacional**, preservando o Gold histórico original como histórico e construindo uma nova série comparável em vez de reescrever retroativamente os artefatos antigos.
