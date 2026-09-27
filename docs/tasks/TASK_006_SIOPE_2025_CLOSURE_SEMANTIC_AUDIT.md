# TASK 006 — auditoria offline de fechamento e comparabilidade semântica SIOPE 2025

## Escopo

A TASK 006 é estritamente `T0_OFFLINE`. Ela usa somente evidências já persistidas no repositório. Não executa rede de fonte, Drive, workflow live, retry, redirect, paginação, nova autorização, cálculo Gold, persistência de valores ou publicação.

Ponto de partida: `main = ef48a62e0c047e9765905e16ee967d64dd0daba9`, após a TASK 005.

## Estado recebido da TASK 005

- 2025 = `PROVEN_STRUCTURAL_RECENT`;
- P6 = `PROVEN_AVAILABLE_CLOSURE_UNKNOWN`;
- P1–P6 disponíveis para Limeira/SP na observação pinada;
- schema P6 de 52 campos = provado para a observação 2025;
- 11 campos de entrada do contrato Gold = provados presentes;
- fechamento anual = `UNKNOWN`;
- comparabilidade semântica = `UNKNOWN`;
- série anual fechada = 2016–2024;
- oito métricas Gold 2025 = `UNKNOWN`;
- 2026 = `UNPROVEN_CURRENT_YEAR`.

## Gate A — fechamento anual 2025

**Resultado: `NOT_PROVEN`. Estado canônico permanece `UNKNOWN`.**

A evidência live pinada prova que P6 existe e respondeu com identidade exata, mas disponibilidade de P6 não prova que o registro observado esteja final/fechado para o exercício.

O histórico 2017–2024 prova o uso operacional de P6 na série já persistida. O material de pesquisa registra ainda a regra histórica de P6 como consolidação anual a partir de 2017 como fato de engenharia a verificar/pinar no documento oficial. Nenhum desses elementos, isolado ou em conjunto, fornece um indicador 2025-específico de estado final, encerramento ou ausência de retificação posterior.

Para promover fechamento seriam necessárias, em gate separado:

1. regra oficial pinada e aplicável a 2025 ou indicador oficial de estado que defina P6 como final/fechado;
2. regra determinística que diferencie `P6_AVAILABLE` de `P6_FINAL_CLOSED`;
3. se houver possibilidade de retificação ou mudança de estado, prova da condição de finalidade relevante.

## Gate B — comparabilidade semântica 2025 ↔ 2017–2024

**Resultado: `NOT_PROVEN`. Estado canônico permanece `UNKNOWN`.**

O contrato Gold existente registra oito fórmulas aritméticas para 2024/P6. A observação 2025 prova a presença dos mesmos 11 nomes de campos requeridos, mas nomes iguais não provam continuidade de significado contábil, regra de apuração ou denominador.

Para promover comparabilidade seriam necessárias, em gate separado:

1. definições oficiais aplicáveis a 2025 para os 11 campos de entrada;
2. reconciliação campo a campo com as definições do regime 2017–2024;
3. reconciliação semântica de numerador e denominador das oito fórmulas;
4. avaliação de continuidade das regras de declaração e retificação;
5. confirmação da definição de `NUM_POPU` usada nos indicadores per capita.

## Matriz final da TASK 006

| Item | Resultado |
| --- | --- |
| Estrutura 2025 | `PROVEN_STRUCTURAL_RECENT` |
| P6 disponível | `PROVEN_AVAILABLE_CLOSURE_UNKNOWN` |
| Fechamento anual 2025 | `NOT_PROVEN` / canônico `UNKNOWN` |
| Comparabilidade semântica | `NOT_PROVEN` / canônico `UNKNOWN` |
| Entrada de 2025 na série fechada | bloqueada |
| Série anual fechada | 2016–2024 |
| Oito métricas Gold 2025 | `UNKNOWN`, não calculadas |
| MDE/Fundeb/compliance | fora do escopo / não provado |
| Causalidade | fora do escopo / não provada |
| 2026 | `UNPROVEN_CURRENT_YEAR` |

## Gate fail-closed

`scripts/github_siope_2025_closure_semantic_audit_gate.py` valida deterministicamente que:

- TASK 006 fez zero GETs e zero Drive;
- a evidência normalizada continua declarando fechamento e comparabilidade como `UNKNOWN`;
- o histórico termina em 2024;
- o contrato Gold é aritmético e documentado para 2024/P6;
- o próprio mapa de pesquisa proíbe inferir equivalência semântica por nomes iguais;
- Gate A e Gate B permanecem `NOT_PROVEN`;
- série fechada, Gold, live, future batch, compliance, causalidade e 2026 não podem ser promovidos nesta TASK.

Os testes negativos em `tests/test_siope_2025_closure_semantic_audit.py` tentam violar essas fronteiras e exigem STOP fail-closed.

## Decisão

A TASK 006 não altera `config/siope_historical_regimes.v1.json`, porque nenhuma promoção adicional foi provada. O resultado correto de uma auditoria de suficiência pode ser ausência de promoção; registrar explicitamente essa ausência evita que similaridade estrutural seja confundida com prova semântica.

## Próxima ação

Antes de qualquer cálculo Gold 2025 ou inclusão de 2025 na série anual fechada, é necessário obter e pinar **evidência oficial de fechamento** e **definições oficiais aplicáveis a 2025**, em etapa separada. Essa necessidade não autoriza, por si só, novo acesso live nem future batch.
