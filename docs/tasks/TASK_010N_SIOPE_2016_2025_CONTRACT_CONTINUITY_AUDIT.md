# TASK 010N — Auditoria de continuidade contratual SIOPE 2016–2025

## Resultado executivo

**Classe B — `HISTORICAL_PROOF_STANDARD_INSUFFICIENT`.**

A busca repo-resident não encontrou evidência positiva de ruptura semântica de 2024 para 2025: **`NO_POSITIVE_BREAK_EVIDENCE_FOUND`**. Isso não promove 2025. A auditoria encontrou outra assimetria: 2016–2024 receberam `ALL_8_PROVEN` com prova de recurso, período, schema, presença dos inputs e execução aritmética, mas sem uma bridge versionada, campo a campo, entre aliases OData e CML/XML/Delphi equivalente à exigida agora para 2025. Portanto, o padrão corrente é **`2025_STRICTER_THAN_HISTORICAL`** e os estados históricos de prova semântica precisam de reconciliação — sem apagar ou recalcular dados.

O próximo gate não é aberto por esta task. Antes de `TASK_010O_SEMANTIC_PROMOTION_DECISION`, recomenda-se um gate separado de reconciliação do padrão histórico.

## Escopo e método fail-closed

Esta foi uma leitura T0 exclusivamente de arquivos versionados. Foram feitas zero chamadas de rede, zero leituras/escritas de Drive, zero cálculo Gold 2025 e zero publicação. Ausência de documentação foi classificada como `UNKNOWN`/lacuna, nunca como mudança positiva.

O artefato machine-readable canônico desta auditoria é `docs/evidence/TASK_010N_SIOPE_2016_2025_CONTRACT_CONTINUITY_AUDIT_0.8.0.json`. Ele contém a matriz anual, a comparação 2024×2025, as referências e todos os guards.

## Cadeia histórica reconstruída

### Regime 2016

- Recurso: `Dados_Gerais_Siope`, contrato OData parametrizado por ano, período e UF.
- Período anual aceito: P1.
- Schema registrado: `DADOS_GERAIS_SIOPE_52_FIELDS`; os 11 inputs Gold constam do contrato histórico.
- Evidência operacional: o bounded batch fixado observou um registro, schema com 52 chaves e produziu oito métricas para 2016; a revisão agregada registra Bronze/Silver/Gold.
- Regra decisória registrada: schema/pipeline determinísticos e fórmulas aritméticas dos oito Gold; sem conclusão de compliance.
- Lacuna: a evidência agregada não fixa lista ordenada/tipos por ano e não registra bridge OData→estrutura interna nem definição/vintage independente de `NUM_POPU`.

### Regime 2017–2020

- Mesmo recurso e endpoint; P6.
- O bounded batch fixado registra um GET e um registro por ano, 52 chaves, oito métricas e os objetos de pipeline.
- A promoção histórica usa o mesmo contrato de 11 inputs e a mesma regra aritmética.
- A mesma lacuna de identidade semântica/alias bridge permanece.

### Regime 2021–2024

- Mesmo recurso e endpoint; P6.
- A revisão pós-generalização registra pilotos verticais em 2021–2024, série contínua e oito métricas por ano. Evidências específicas de full-schema/payload existem para parte desses anos, mas a revisão agregada não fixa uma enumeração/tipagem anual completa para todos.
- A decisão `ALL_8_PROVEN` está registrada no mapa de regimes e na matriz histórica.
- Não foi localizada bridge explícita equivalente à exigência criada para 2025.

### Regime 2025 (estado preservado)

- Recurso e endpoint têm o mesmo nome/formato contratual.
- P1–P6 foram observados; P6 é `PROVEN_AVAILABLE_CLOSURE_UNKNOWN` e seu papel é `P6_ANNUAL_CONSOLIDATION_PROVEN_FINALITY_UNKNOWN`.
- A resposta P6 fixou exatamente 52 nomes (hash e ordem no JSON), incluindo os mesmos 11 inputs.
- A revisão offline encontrou os conceitos internos atuais, mas não a identidade determinística dos dez aliases financeiros; `NUM_POPU` permanece sem definição, fonte e vintage provadas.
- Nenhuma métrica, fechamento, comparabilidade ou elegibilidade para série fechada foi promovida.

## Matriz anual resumida

| Ano | Período | Recurso/schema | 11 inputs | Prova semântica/aliases | Fechamento | Regra Gold |
|---|---:|---|---|---|---|---|
| 2016 | P1 | `Dados_Gerais_Siope`; 52 campos | contrato histórico: presentes | fórmulas e nomes; sem bridge interna equivalente | tratado como anual histórico | `ALL_8_PROVEN` pelo pipeline aritmético |
| 2017 | P6 | idem | idem | idem | tratado como anual histórico | idem |
| 2018 | P6 | idem | idem | idem | tratado como anual histórico | idem |
| 2019 | P6 | idem | idem | idem | tratado como anual histórico | idem |
| 2020 | P6 | idem | idem | idem | tratado como anual histórico | idem |
| 2021 | P6 | idem | idem | idem | tratado como anual histórico | idem |
| 2022 | P6 | idem; payload versionado | presentes | sem bridge interna equivalente | tratado como anual histórico | idem |
| 2023 | P6 | idem; payload versionado | presentes | sem bridge interna equivalente | tratado como anual histórico | idem |
| 2024 | P6 | idem | presentes pelo contrato | sem bridge interna equivalente | fechado no mapa histórico | idem |
| 2025 | P6 disponível | mesmo nome; 52 nomes fixados | `PROVEN_PRESENT_2025_P6` | S1/S2 `NOT_PROVEN` | `UNKNOWN` | `UNKNOWN/BLOCKED` |

“Presente” não equivale a “semanticamente identificado”. O JSON distingue evidência anual direta de afirmação do contrato agregado.

## Comparação 2024 × 2025

| Aspecto | Classificação | Fundamentação |
|---|---|---|
| resource name | `IDENTICAL` | `Dados_Gerais_Siope` |
| endpoint contract | `IDENTICAL` | mesma função OData parametrizada |
| número de campos | `IDENTICAL` | 52 em ambos os contratos registrados |
| nomes exatos | `COMPATIBLE` | os 11 inputs coincidem; a lista 2025 é fixada, a lista anual 2024 não está enumerada na evidência agregada |
| 11 inputs Gold | `IDENTICAL` | mesmos aliases |
| ordenação | `UNKNOWN` | ordenação 2024 por ano não fixada na revisão agregada |
| tipos observados | `UNKNOWN` | não há tipagem versionada suficiente para ambos |
| identidade municipal | `COMPATIBLE` | Limeira/SP; 2025 fixa `COD_MUNI=352690` |
| P6 | `COMPATIBLE` | disponível em ambos; só 2025 mantém fechamento desconhecido |
| regime de período | `COMPATIBLE` | P6 anual histórico versus P6 disponível/finalidade desconhecida |
| documentação semântica | `NOT_COMPARABLE` | bases probatórias diferentes/incompletas |
| alias bridge | `NOT_COMPARABLE` | não versionada historicamente; não provada em 2025 |
| fechamento/finalidade | `NOT_COMPARABLE` | 2024 é estado histórico fechado; 2025 permanece desconhecido |
| autorização Gold | `CHANGED` | 2025 exige provas adicionais que não aparecem na promoção histórica |

Nenhuma classificação `CHANGED` acima prova mudança do significado dos dados: ela descreve mudança da **regra de autorização/prova**.

## Busca de ruptura positiva

Não foi localizada evidência versionada de mudança de significado, fonte, unidade ou aggregate de qualquer dos 11 campos; nem de alteração de escopo de `_EDU`, definição de `NUM_POPU` ou substituição conceitual da fonte. Resultado: **`NO_POSITIVE_BREAK_EVIDENCE_FOUND`**.

A falta de uma bridge nova não é ruptura. Também não autoriza inferir continuidade semântica plena.

## Consistência do padrão de prova e reconciliação

Classificação: **`2025_STRICTER_THAN_HISTORICAL`**.

Estados que precisam de reconciliação explícita:

1. `2016: ALL_8_PROVEN` — falta bridge equivalente e prova própria de `NUM_POPU`.
2. `2017–2024: ALL_8_PROVEN` — mesma lacuna para cada ano/regime.
3. A comparabilidade semântica implícita na série Gold contínua 2016–2024 — o repo prova execução aritmética/estrutural, não registra a identidade interna campo a campo hoje exigida.

Isso não revoga automaticamente os estados, não apaga Bronze/Silver/Gold e não autoriza recálculo. A decisão sobre como reconciliar deve ocorrer em gate separado.

## Prior art (contexto, não prova primária)

Conforme o contexto fornecido para esta auditoria, implementações independentes — `StrategicProjects/tesouror`, `StrategicProjects/tesouropy`, `BrenoNsm/painelEduca` e `tuffyli/RA_work` — usam o contrato SIOPE longitudinalmente, inclusive `Dados_Gerais_Siope`, períodos 1..6, união de campos ou a fronteira 2016=P1/depois=P6. Nenhum repositório externo foi consultado nesta task. Esse prior art não é documentação oficial FNDE e, isoladamente, não promove B1/B2.

## Estados e guards preservados

- 2025 = `PROVEN_STRUCTURAL_RECENT`.
- P6 = `PROVEN_AVAILABLE_CLOSURE_UNKNOWN` / `P6_ANNUAL_CONSOLIDATION_PROVEN_FINALITY_UNKNOWN`.
- `S1_NUM_POPU = NOT_PROVEN`; `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`.
- fechamento e comparabilidade = `UNKNOWN`; Gold = `UNKNOWN/BLOCKED`.
- série anual fechada = 2016–2024; 2026 = `UNPROVEN_CURRENT_YEAR`; 0.8.0 = `CANDIDATE`.
- rede remota, escrita Drive, Gold 2025, promoção semântica, expansão anual, promoção de release e 2026: todos não autorizados.
