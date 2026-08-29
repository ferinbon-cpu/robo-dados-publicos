# TASK 010N-R-E-M3 — ponte operacional dos aliases financeiros SIOPE 2025

## Escopo e decisão

Este gate B2 valida **offline** a observação oficial mediada pelo usuário para `2025/P6/SP/352690/Limeira`. O fixture sanitizado contém somente as linhas necessárias; o validador não faz rede, não consulta nem grava Drive, não publica e não calcula Gold.

Decisão: `KEEP_S2_NOT_PROVEN_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_MISSING`.

Nove aliases possuem pontes operacionais exatas. `VL_DESP_DOTA_ATUA_EDU` continua sem ponte definida pela fonte; portanto `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`.

## Reconciliação determinística

O gate usa `Decimal` a partir de strings com exatamente duas casas, exige identidade e unicidade exatas e falha fechado diante de linha ausente, duplicada, estágio inesperado ou valor alterado. Receita soma Correntes e Capital por estágio. Despesa geral usa os subtotais do RREO, somando separadamente a Reserva do RPPS apenas à dotação.

Para educação, o fixture preserva as dez linhas oficiais observadas, identificadas unicamente por `(NUM_ORDE, DES_SUBF)`. Para DE, DL e DP, o gate prova que as linhas 11 + 12 são iguais ao subtotal da linha 13 e soma todos os registros não-365 mais a linha 13, exatamente uma vez. Assim, componentes e subtotal nunca são contados juntos.

Na dotação educacional, a conta pai `3.2.00.00.00` e a filha `3.2.91.00.00` registram `1000.00`, e o total DA consolidado observado é `526804985.21`. A diferença exata entre o alias (`520399255.47`) e a linha 33 do RREO (`520398255.47`) é `1000.00`. Essa coincidência é uma **forte explicação candidata**, mas não prova uma regra da fonte/backend que inclua especificamente essa conta na linha do RREO. O campo recebe `PARTIAL_CURRENT_EXACT_1000_VARIANCE_NO_SOURCE_DEFINED_INCLUSION_RULE`, nunca um status `PROVEN`.

A matriz campo a campo, conceitos, fontes, valores, variâncias, status e razões está pinada no evidence JSON e é revalidada pelo gate.

## Limites preservados

- `semantic_comparability_status = UNKNOWN`: faltam a regra exata da fonte/backend para `VL_DESP_DOTA_ATUA_EDU` e `B1_NUM_POPU_SOURCE_VINTAGE_AND_GLOBAL_COMPARABILITY_GATE`.
- `S1_NUM_POPU = NOT_PROVEN`; `annual_closure_status = UNKNOWN`; série fechada permanece `2016-2024`.
- 0.7.0 permanece `ACTIVE`; 0.8.0 permanece `CANDIDATE`.
- Gold 2025 permanece bloqueado; 2026 não é inferido.
- **EDU != MDE como identidade geral.** A prova cobre somente os aliases correntes e agregados oficiais observados, sem conclusão de compliance.

## Execução

```bash
python scripts/github_task_010n_r_e_m3_siope_2025_operational_financial_alias_bridge_gate.py
python -m unittest tests.test_task_010n_r_e_m3_siope_2025_operational_financial_alias_bridge_gate -v
```
