# TASK 010N-R — Reconciliação do padrão de prova SIOPE 2016–2025

## Decisão

**`INTERNAL_BRIDGE_STANDARD_REQUIRED`.**

A evidência versionada prova continuidade da identidade estrutural do contrato público — mesmo recurso `Dados_Gerais_Siope`, mesmo contrato parametrizado, 52 campos e os mesmos 11 aliases usados pelo Gold — mas não prova identidade semântica operacional. A ausência, em 2016–2024, de uma bridge versionada entre aliases OData e conceitos internos não pode ser convertida em prova positiva de significado. Por isso, um padrão público longitudinal não é suficiente para a promoção semântica; a reconciliação futura exige bridge interna, sem rebaixar agora os estados históricos.

Esta decisão reconcilia o padrão de **prova**, não os dados nem a série. Ela preserva integralmente os estados fixados pela TASK 010N.

## Escopo e base

- base Git exata: `d0e75e1dc47de6157e49864ca97bbcb640ba65df`;
- execução `T0_OFFLINE`, somente sobre artefatos versionados;
- zero rede e zero operações de Drive;
- nenhuma métrica Gold 2025 calculada;
- nenhuma promoção de 2025, de 0.8.0 ou da série fechada;
- nenhum rebaixamento automático de 2016–2024;
- 2026 permanece inalterado;
- TASK 010O não é aberta nem autorizada.

## Três camadas de identidade e limite interpretativo

1. **Identidade estrutural:** igualdade observável de recurso, forma do endpoint, contagem de campos e presença dos 11 aliases. Está sustentada longitudinalmente pelo contrato repo-resident.
2. **Identidade semântica operacional:** prova de que cada alias representa o mesmo conceito, população, unidade, escopo, agregação e estágio contábil no regime relevante. Não está suficientemente versionada para nenhum dos três blocos anuais.
3. **Bridge interna:** mapeamento determinístico, versionado e campo a campo do alias público para uma estrutura interna autoritativa, com definição, origem e vintage. É o padrão requerido para reconciliar a lacuna; não é criada nem presumida nesta task.
4. **Interpretação fiscal/legal:** conclusão de compliance, suficiência constitucional, auditoria ou efeito jurídico. Fica fora do contrato, mesmo que uma bridge futura seja provada.

Identidade estrutural não implica identidade semântica operacional; bridge interna não implica interpretação fiscal/legal.

## Comparação obrigatória

| Regime | Identidade estrutural | Identidade semântica operacional | Bridge interna | Estado preservado |
|---|---|---|---|---|
| 2016 / P1 | `Dados_Gerais_Siope`, contrato histórico de 52 campos e 11 inputs Gold; execução aritmética observada | nomes e fórmulas são conhecidos, mas definição/vintage de `NUM_POPU` e identidade campo a campo não foram fixadas | não há bridge equivalente versionada | `ALL_8_PROVEN`; não rebaixado |
| 2017–2024 / P6 | mesmo recurso/endpoint, contrato de 52 campos e mesmos 11 inputs; pipeline histórico validado | fórmulas/aliases não provam por si sós conceito, unidade, escopo e estágio contábil invariantes | não há bridge equivalente versionada para cada ano/regime | `ALL_8_PROVEN`; série 2016–2024 permanece fechada |
| 2025 / P6 | mesmo recurso/endpoint; 52 nomes e 11 inputs presentes foram fixados | `S1_NUM_POPU=NOT_PROVEN` e `S2_FINANCIAL_ALIAS_BRIDGE=NOT_PROVEN`; fechamento e comparabilidade continuam `UNKNOWN` | requerida, mas não provada | `PROVEN_STRUCTURAL_RECENT`; Gold `UNKNOWN/BLOCKED` |

A assimetria é probatória: 2025 está sujeito a uma exigência explícita que não foi registrada nas promoções históricas. Não foi encontrada ruptura semântica positiva, mas ausência de ruptura positiva também não prova continuidade semântica.

## Estados históricos que exigem futura reconciliação

Exatamente estes estados, sem qualquer alteração nesta task:

1. **2016 — `ALL_8_PROVEN`:** reconciliar a prova dos 11 inputs, incluindo definição, fonte e vintage de `NUM_POPU`, e a identidade operacional dos dez aliases financeiros.
2. **2017–2024 — `ALL_8_PROVEN`, ano a ano:** reconciliar a mesma prova para cada ano do regime P6; uma inferência agregada para o intervalo não substitui evidência por regime/ano.
3. **2016–2024 — comparabilidade semântica implícita da série Gold contínua:** reconciliar a alegação de comparabilidade com uma bridge interna versionada; isso não ordena apagar, recalcular ou reclassificar nenhum objeto existente.

Nenhum outro estado histórico é incluído. Em particular, 2025 não é histórico promovido, e 2026 permanece `UNPROVEN_CURRENT_YEAR`.

## Critério do próximo gate recomendado

Recomenda-se um gate separado **`TASK_010N_R_INTERNAL_BRIDGE_EVIDENCE_GATE`**, anterior e não equivalente à TASK 010O. Ele deve permanecer fail-closed até existir evidência repo-resident que, para os 11 inputs e para cada regime aplicável, fixe: alias exato; conceito interno autoritativo; definição; unidade; escopo; agregação; estágio contábil; fonte; vintage; período; e regra determinística de correspondência. Divergência, ausência ou ambiguidade deve resultar em `STOP`.

O gate não deve calcular Gold 2025, interpretar compliance fiscal/legal, rebaixar automaticamente 2016–2024, expandir a série, alterar 2026 ou promover a release.
