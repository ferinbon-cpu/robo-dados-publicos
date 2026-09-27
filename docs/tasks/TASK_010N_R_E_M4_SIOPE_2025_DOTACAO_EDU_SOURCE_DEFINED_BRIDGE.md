# TASK 010N-R-E-M4 — ponte source-defined da dotação educacional SIOPE 2025

## Decisão

`KEEP_S2_NOT_PROVEN_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_MISSING`

O inventário offline não encontrou regra oficial corrente que defina a construção de `VL_DESP_DOTA_ATUA_EDU`. Portanto o campo permanece `PARTIAL_CURRENT_EXACT_1000_VARIANCE_NO_SOURCE_DEFINED_INCLUSION_RULE`, somente 9/10 aliases financeiros permanecem `PROVEN_EXACT_OPERATIONAL` e `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`.

Nenhuma requisição de rede de fonte foi feita: esta task T0 não autoriza uma nova aquisição remota.

## Inventário executado

Foram pesquisados no repositório os termos exigidos, incluindo os dois nomes do alias, os rótulos de dotação/educação, a linha total do RREO, as contas `3.2.00.00.00` e `3.2.91.00.00` e ambos os valores observados. O evidence JSON pina termos, caminhos, hashes e achados.

- M3 e seu fixture preservam os valores oficiais correntes e a diferença exata, mas classificam a conta de R$ 1.000,00 apenas como explicação candidata.
- O EDMX oficial corrente de M2 expõe o campo como `Edm.Decimal`, sem annotations, descriptions, fórmula ou relação de origem.
- O pacote 2025 resumido em 010K prova a existência de DA e da hierarquia `Despesas com Educação`, mas sua varredura dos 156 membros decodificados não encontrou nenhum dos dez aliases.
- A inspeção estática 010L não encontrou serializer, SQL, view ou rotina de exportação que construa o campo.
- A busca documental oficial anterior não encontrou definição corrente explícita do alias.

## Por que os candidatos não bastam

`520398255.47 + 1000.00 = 520399255.47` é verdadeiro em `Decimal`, mas não define uma regra da fonte. A observação isolada não informa se o backend inclui a conta pai, a filha, ambas, alguma outra rubrica ou um componente de outra superfície. Pai e filha repetem o mesmo valor e não podem ser somados sem uma regra oficial de hierarquia.

O nome do alias, o tipo EDMX e os conceitos DA/educação não fornecem inclusões ou exclusões. Documentação histórica não prova o backend 2025. Similaridade lexical também não autoriza identidade semântica. **EDU != MDE como identidade geral.**

## Menor próxima evidência

Basta um artefato oficial corrente que nomeie `VL_DESP_DOTA_ATUA_EDU` e defina deterministicamente sua construção: preferencialmente o SQL/view/serializer/backend mapping; alternativamente um layout, dicionário ou especificação corrente com categorias incluídas/excluídas. A regra deve explicar expressamente o tratamento de `3.2.00.00.00` e `3.2.91.00.00`, sem ser deduzida da coincidência de R$ 1.000,00.

Essa evidência deve chegar por handoff humano ou aquisição separada, bounded e explicitamente autorizada.

## Guardas preservadas

- `0.7.0 = ACTIVE`; `0.8.0 = CANDIDATE`; `2025 = PROVEN_STRUCTURAL_RECENT`.
- `S1_NUM_POPU = NOT_PROVEN`; fechamento anual e comparabilidade semântica permanecem `UNKNOWN`.
- A série fechada permanece `2016-2024`; Gold 2025 permanece `UNKNOWN/BLOCKED`.
- `2026 = UNPROVEN_CURRENT_YEAR`; não há persistência, publicação ou cálculo Gold.

## Validação

```bash
python scripts/github_task_010n_r_e_m4_siope_2025_dotacao_edu_source_defined_bridge_gate.py
python -m unittest tests.test_task_010n_r_e_m4_siope_2025_dotacao_edu_source_defined_bridge_gate -v
```
