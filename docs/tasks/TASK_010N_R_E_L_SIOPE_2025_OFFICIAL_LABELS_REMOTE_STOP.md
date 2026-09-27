# TASK 010N-R-E-L — rótulos semânticos oficiais Receita/Despesas SIOPE 2025

## Resultado

`STOP_REMOTE_ACCESS_NO_LABEL_EVIDENCE`

A partir do EDMX oficial user-mediated já pinado, foram autorizadas no máximo duas tentativas remotas distintas, sem `VAL_DECL`, para testar a superfície semântica pública dos recursos `Receita_Siope` e `Despesas_Siope` em 2025/P6/SP/Limeira.

Foram realizadas exatamente duas tentativas distintas:

1. `Receita_Siope`, selecionando somente campos de identidade/rótulo (`COD_MUNI`, `NOM_MUNI`, `COD_EXIB_FORMATADO`, `NOM_ITEM`, `IDN_CLAS`, `NOM_COLU`, `NUM_NIVE`, `NUM_ORDE`), sem valores declarados;
2. `Despesas_Siope`, selecionando somente campos de identidade/rótulo (`COD_MUNI`, `NOM_MUNI`, `NOM_PAST`, `TIP_PASTA`, `COD_EXIB`, `COD_EXIB_FORMATADO`, `COD_FONTE`, `NOM_ITEM`, `IDN_CLAS`, `NOM_COLU`, `NUM_NIVE`, `NUM_ORDE`), sem valores declarados.

Em ambos os casos, o ambiente de navegação retornou `503 Service Unavailable` interno antes de disponibilizar qualquer resposta HTTP utilizável do FNDE. `network_io_to_fnde_observed` permanece `UNKNOWN`.

Não houve retry, redirect follow voluntário, autenticação, Drive, Gold, write, engenharia reversa ou consulta a 2026.

## Interpretação fail-closed

Este STOP não prova que `Receita_Siope` ou `Despesas_Siope` estejam indisponíveis, não prova ausência de rótulos e não constitui evidência semântica negativa. O EDMX continua provando que ambos os recursos existem no contrato oficial e que expõem campos como `NOM_COLU`, `NOM_ITEM` e, para despesas, `NOM_PAST`.

A rota continua epistemicamente válida, mas precisa de execução em runtime externo ou handoff humano das respostas oficiais, sob nova autorização separada.

## Estados preservados

- `2025 = PROVEN_STRUCTURAL_RECENT`
- `S1_NUM_POPU = NOT_PROVEN`
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`
- fechamento anual = `UNKNOWN`
- comparabilidade semântica = `UNKNOWN`
- Gold 2025 = `UNKNOWN/BLOCKED`
- série fechada = `2016–2024`
- `0.8.0 = CANDIDATE`
- `2026 = UNPROVEN_CURRENT_YEAR`

Nenhuma promoção foi realizada.
