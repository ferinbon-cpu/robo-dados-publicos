# TASK 239 — reconciliação do estado corrente 0.8.0

## Objetivo

Reconciliar a fotografia **corrente/canônica** da `0.8.0 CANDIDATE` após a conclusão de:

- território TASK199H / serving 69 de 69;
- B1 `NUM_POPU` resolvido por exclusão do uso analítico populacional;
- B2 fechado em 10 de 10 aliases ligados a conceitos oficiais;
- B3 fechado pela regra autoritativa dinâmica de seleção da declaração efetiva.

A tarefa não reescreve evidências históricas. Arquivos v1 e TASK011 continuam registrando corretamente o estado anterior em que protocolos estavam pendentes.

## Estado corrente materializado

### Território

- 69/69 escolas com vínculo forte a setor censitário IBGE 2022;
- 284 linhas em `TERRITORY_PROFILE`;
- 68/69 escolas com contexto numérico de renda setorial;
- INEP `35286229` com `SOURCE_EXPLICIT_X`, preservado como missingness e nunca convertido em zero;
- answerability 38/38.

### SIOPE 2025

- B1: `RESOLVED_BY_EXCLUSION_FROM_ANALYTICAL_POPULATION_SEMANTICS`;
- B2: `PROVEN_10_OF_10_ALIAS_TO_CONCEPT`;
- B3: `PROVEN_DYNAMIC_EFFECTIVE_SELECTION_RULE_WITH_PINNED_LIMEIRA_RECEIPT`;
- recibo anual efetivo na observação pinada: `428477-6` em `2026-08-30`;
- comparabilidade 2016–2025: `UNKNOWN_REQUIRES_TASK241`;
- Gold 2025: `BLOCKED_NOT_CALCULATED`;
- série anual fechada: `2016-2024`;
- release: `0.8.0 CANDIDATE`.

## Contratos correntes

- `config/release_0_8_0_readiness.v2.json`;
- `config/siope_2025_gold_prerequisites.v2.json`;
- `docs/evidence/TASK_239_CURRENT_0_8_0_STATE_0.8.0.json`.

Os arquivos v1 permanecem no repositório como snapshots históricos e são validados pelo gate da própria TASK239 para impedir reescrita retroativa.

## Próximo gate

`TASK 241 / #809 — semantic comparability 2016–2025`.

Nenhum Gold é calculado nesta tarefa. Nenhuma inclusão de 2025, promoção de release, coleta remota, escrita no Drive, publicação, schedule ou recorrência é autorizada.
