# TASK 010N-R — Reconciliação do padrão de prova SIOPE 2016–2025

## Decisão revisada

**`STANDARD_NOT_YET_DETERMINABLE`.**

Não há evidência repo-resident suficiente para decidir entre:

- **P1 — `UNIFORM_PUBLIC_CONTRACT_STANDARD_JUSTIFIED`:** identidade semântica operacional demonstrada por evidência primária oficial do próprio contrato público; e
- **P2 — `INTERNAL_BRIDGE_STANDARD_REQUIRED`:** necessidade de identidade com uma estrutura interna CML/XML/Delphi/backend.

A revisão anterior demonstrou uma lacuna semântica, mas não demonstrou que uma bridge interna seja epistemicamente necessária para claims Gold estritamente aritméticos. Em princípio, documentação oficial FNDE/Olinda, EDMX/`$metadata`, descrição oficial dos campos ou outro contrato oficial alias→conceito pode provar `OPERATIONAL_SEMANTIC_IDENTITY` sem provar `SOURCE_INTERNAL_IDENTITY`. Fixar P2 antes de testar essa classe de evidência confundiria identidade semântica do contrato público com identidade da implementação interna.

## Escopo e estados preservados

Base exata: `d0e75e1dc47de6157e49864ca97bbcb640ba65df`. Esta reconciliação é `T0_OFFLINE`: zero rede, zero Drive e nenhum cálculo Gold 2025.

Permanecem integralmente: 0.7.0 `ACTIVE`; 0.8.0 `CANDIDATE`; 2025 `PROVEN_STRUCTURAL_RECENT`; S1 e S2 `NOT_PROVEN`; fechamento anual e comparabilidade semântica `UNKNOWN`; Gold 2025 `UNKNOWN/BLOCKED`; série fechada 2016–2024; e 2026 `UNPROVEN_CURRENT_YEAR`. Não há promoção, rebaixamento histórico, expansão da série ou abertura da TASK 010O.

## P1 — padrão público longitudinal

P1 não se reduz a continuidade estrutural. Ele seria justificável se evidência primária oficial do contrato público fixasse, de modo não ambíguo, para os 11 inputs:

1. o alias OData exato;
2. o conceito operacional correspondente;
3. definição, unidade, escopo, agregação e estágio contábil;
4. definição, fonte e vintage de `NUM_POPU`;
5. aplicabilidade temporal/regime a 2016/P1, 2017–2024/P6 e 2025/P6; e
6. compatibilidade com as fórmulas Gold estritamente aritméticas, sem conclusão fiscal/legal.

Esses critérios poderiam ser satisfeitos por EDMX/`$metadata` oficial suficientemente descritivo, documentação oficial de campos, documentação oficial alias→conceito ou contrato oficial equivalente. A evidência atual não permite dizer quais anos os satisfazem: **nenhum ano possui, no repositório, o conjunto completo de prova acima**. Isso não rebaixa `ALL_8_PROVEN` de 2016–2024; apenas descreve a lacuna do padrão reconciliado.

## P2 — bridge interna

P2 exigiria demonstração adicional de que a semântica necessária ao claim aritmético não pode ser estabelecida no contrato público, ou de que existe ambiguidade/incompatibilidade que só a estrutura interna autoritativa resolve. Nenhuma evidência repo-resident demonstra essa insuficiência epistemológica da documentação/metadata oficial.

Logo, a ausência atual de alias bridge não prova P2. Engenharia reversa de CML/XML/Delphi/backend não é o próximo passo automático. `SOURCE_INTERNAL_IDENTITY` só se torna requisito se a futura evidência discriminante mostrar que P1 é insuficiente.

## Evidência oficial repo-resident da TASK 007

`docs/evidence/TASK_007_SIOPE_2025_OFFICIAL_DOCUMENTARY_EVIDENCE_0.8.0.json` registra que o dicionário oficial FNDE 2019 define os dez conceitos financeiros usados pelo Gold. Porém, ele não define os aliases OData atuais e não define `NUM_POPU`; por isso, fixa zero identidades de alias OData 2025 e classifica a bridge como `PARTIAL_NOT_PROVEN`.

Essa evidência é primária e semanticamente relevante, mas não fecha P1: conceito financeiro definido sem vínculo oficial alias→conceito não prova a identidade operacional do campo observado. Também não fecha P2: a limitação do documento consultado não prova que todo contrato público oficial seja insuficiente.

## Comparação obrigatória

| Regime | Identidade estrutural | Identidade semântica operacional | Source/internal identity | Estado preservado |
|---|---|---|---|---|
| 2016 / P1 | contrato histórico de 52 campos e 11 inputs; execução aritmética observada | critérios P1 completos não versionados | não exigida nem dispensada ainda | `ALL_8_PROVEN` |
| 2017–2024 / P6 | mesmo recurso/endpoint e mesmos 11 inputs; pipeline histórico validado | dicionário 2019 cobre dez conceitos, mas não vincula aliases atuais nem define `NUM_POPU` | não exigida nem dispensada ainda | `ALL_8_PROVEN`; série fechada preservada |
| 2025 / P6 | 52 nomes e 11 inputs presentes fixados | S1/S2 continuam `NOT_PROVEN`; evidência oficial é parcial | não provada e ainda não demonstrada necessária | `PROVEN_STRUCTURAL_RECENT`; Gold `UNKNOWN/BLOCKED` |

Identidade estrutural, identidade semântica operacional, source/internal identity e interpretação fiscal/legal são camadas distintas. Nenhuma decisão P1 ou P2 autoriza automaticamente conclusão de compliance, auditoria ou efeito jurídico.

## Menor nova classe de evidência discriminante

A menor classe capaz de decidir P1 versus P2 é **evidência primária oficial do contrato público alias→conceito**, aplicável aos regimes relevantes e cobrindo os 11 inputs. Prioridade:

1. EDMX/`$metadata` oficial com descrições semânticas dos campos; ou
2. documentação oficial FNDE/Olinda de campos/aliases; ou
3. contrato oficial equivalente que ligue cada alias ao conceito, incluindo `NUM_POPU`.

O próximo gate recomendado é `TASK_010N_R_PUBLIC_CONTRACT_SEMANTIC_EVIDENCE_GATE`, separado, T0 sobre artefato previamente pinado e fail-closed. Ele deve decidir:

- **P1**, se a fonte oficial satisfizer todos os critérios mínimos sem depender de source/internal identity;
- **P2**, somente se evidência positiva demonstrar que o contrato público é insuficiente e que a estrutura interna resolve a lacuna; ou
- **indeterminável**, se faltar cobertura, autoridade, vínculo alias→conceito ou aplicabilidade temporal.

Esse gate não abre TASK 010O, não executa rede, não inicia engenharia reversa e não altera qualquer estado canônico.
