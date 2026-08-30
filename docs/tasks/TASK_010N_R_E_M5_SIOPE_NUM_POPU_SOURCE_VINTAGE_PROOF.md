# TASK 010N-R-E-M5 — prova de fonte, definição e vintage de `NUM_POPU`

## Decisão S1

`KEEP_S1_NUM_POPU_NOT_PROVEN_DEFINITION_SOURCE_VINTAGE_MISSING`

Para SIOPE 2025/P6, Limeira/SP, nenhuma evidência oficial corrente disponível prova cumulativamente o significado exato de `NUM_POPU`, a fonte oficial que fornece o valor e a regra temporal/vintage aplicável. A presença do campo e seu tipo inteiro permanecem prova **estrutural**, não semântica.

## Inventário offline

Foram inspecionados TASK 007, 008, 010A, 010J, 010K, 010N, 010N-R, 010N-R-E-M/M2, a evidência corrente do pacote 2025 e do EDMX, o cliente SIOPE e a configuração histórica. A busca exata e conceitual incluiu todos os termos exigidos; caminhos, hashes e proposições estão pinados no evidence JSON.

O pacote 2025 prova 5.569 linhas municipais, 5.568 atributos `NUM_POPU` e a localização `Dados_Municipio.xml`. O EDMX prova `NUM_POPU: Edm.Int32`, porém contém zero annotations/descriptions. Nem esses artefatos, nem o cliente, fornecem definição, fornecedor ou regra temporal. Continuidade estrutural e valores observados em outros exercícios não promovem continuidade semântica.

## Descoberta documental bounded

Foram considerados somente documentos oficiais FNDE/SIOPE já pinados e tentadas três aberturas documentais oficiais públicas, sem autenticação, Drive ou chamada a endpoint municipal. O ambiente devolveu bloqueio de túnel HTTP 403 antes de resposta da origem; nenhum novo artefato foi baixado. O evidence registra URL, autoridade, título, versão/data disponível e o que cada fonte suporta ou não suporta. Hash é `null` quando bytes do documento não estão disponíveis; não se fabricou hash.

## Classificações separadas

- `NUM_POPU_2025_SEMANTICS = NOT_PROVEN_EXACT_SEMANTIC_DEFINITION_MISSING`.
- `NUM_POPU_2025_SOURCE = NOT_PROVEN_OFFICIAL_SOURCE_MAPPING_MISSING`.
- `NUM_POPU_2025_VINTAGE = NOT_PROVEN_REFERENCE_DATE_YEAR_VERSION_RULE_MISSING`.
- `NUM_POPU_2025_VALUE_RECONCILIATION = NOT_PERFORMED_SOURCE_AND_VINTAGE_RULE_NOT_PROVEN`.
- `NUM_POPU_2016_2024_CONTINUITY = NOT_PROVEN_NO_VERSIONED_HISTORICAL_SOURCE_AND_VINTAGE_RULE`.

A reconciliação de valor foi deliberadamente desabilitada: igualdade, inclusive exata, não pode inventar a regra. Após prova oficial dos três requisitos, o valor inteiro já autorizado para Limeira 2025/P6 poderá ser comparado ao vintage oficial por igualdade exata, nunca aproximada.

## Menor evidência restante

É necessário um único artefato oficial corrente FNDE/SIOPE — dicionário, layout, mapeamento de fonte ou rotina backend/import/view — que nomeie `Dados_Municipio.NUM_POPU` e declare definição semântica, fornecedor autoritativo e regra de data/ano/versão para 2025. O handoff deve preservar URL/proveniência e bytes/hash.

## Guardas

Permanecem: `0.7.0 = ACTIVE`, `0.8.0 = CANDIDATE`, S2 `NOT_PROVEN`, fechamento e comparabilidade global `UNKNOWN`, série fechada `2016-2024`, Gold 2025 `UNKNOWN/BLOCKED` e 2026 `UNPROVEN_CURRENT_YEAR`. Não houve persistência remota, publicação, Gold ou promoção de estado global.

## Validação

```bash
python scripts/github_task_010n_r_e_m5_siope_num_popu_source_vintage_gate.py
python -m unittest tests.test_task_010n_r_e_m5_siope_num_popu_source_vintage_gate -v
```
