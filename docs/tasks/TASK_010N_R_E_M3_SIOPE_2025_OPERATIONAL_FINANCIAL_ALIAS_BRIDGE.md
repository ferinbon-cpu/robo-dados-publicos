# TASK 010N-R-E-M3 — ponte operacional dos aliases financeiros SIOPE 2025

## Escopo e decisão

Este gate B2 valida **offline** a observação oficial mediada pelo usuário para `2025/P6/SP/352690/Limeira`. O fixture sanitizado contém somente as linhas necessárias; o validador não faz rede, não consulta nem grava Drive, não publica e não calcula Gold.

Decisão: `PROMOTE_S2_FINANCIAL_ALIAS_BRIDGE_CURRENT_2025_OPERATIONAL_SEMANTICS`.

A promoção é limitada à semântica corrente dos dez campos financeiros: `S2_FINANCIAL_ALIAS_BRIDGE = PROVEN_CURRENT_2025_OPERATIONAL_SEMANTICS`. Ela não afirma fechamento anual nem comparabilidade global.

## Reconciliação determinística

O gate usa `Decimal` a partir de strings com exatamente duas casas, exige identidade e unicidade exatas e falha fechado diante de linha ausente, duplicada, estágio inesperado ou valor alterado. Receita soma Correntes e Capital por estágio. Despesa geral usa os subtotais do RREO, somando separadamente a Reserva do RPPS apenas à dotação.

Para educação, `DES_SUBF=365` é subtotal duplicado e é excluído explicitamente. Na dotação educacional, a conta pai `3.2.00.00.00` entra uma única vez; a filha hierárquica `3.2.91.00.00`, com os mesmos `1000.00`, não é somada. A diferença exata entre o alias (`520399255.47`) e a linha 33 do RREO (`520398255.47`) é portanto `1000.00`. Esse campo recebe `PROVEN_SEMANTIC_CURRENT_WITH_DOCUMENTED_1000_RREO_VARIANCE`, jamais igualdade RREO exata. Os outros nove recebem `PROVEN_EXACT_OPERATIONAL`.

A matriz campo a campo, conceitos, fontes, valores, variâncias, status e razões está pinada no evidence JSON e é revalidada pelo gate.

## Limites preservados

- `semantic_comparability_status = UNKNOWN`: B2 isolado não basta; falta `B1_NUM_POPU_SOURCE_VINTAGE_AND_GLOBAL_COMPARABILITY_GATE`.
- `S1_NUM_POPU = NOT_PROVEN`; `annual_closure_status = UNKNOWN`; série fechada permanece `2016-2024`.
- 0.7.0 permanece `ACTIVE`; 0.8.0 permanece `CANDIDATE`.
- Gold 2025 permanece bloqueado; 2026 não é inferido.
- **EDU != MDE como identidade geral.** A prova cobre somente os aliases correntes e agregados oficiais observados, sem conclusão de compliance.

## Execução

```bash
python scripts/github_task_010n_r_e_m3_siope_2025_operational_financial_alias_bridge_gate.py
python -m unittest tests.test_task_010n_r_e_m3_siope_2025_operational_financial_alias_bridge_gate -v
```
