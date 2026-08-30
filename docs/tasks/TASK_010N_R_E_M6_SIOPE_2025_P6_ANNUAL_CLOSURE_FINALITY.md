# TASK 010N-R-E-M6 — fechamento/finalidade anual SIOPE 2025 P6

## Decisão B3

`KEEP_ANNUAL_CLOSURE_UNKNOWN_EFFECTIVE_STATUS_RULE_MISSING`.

O P6 é uma consolidação anual oficial, mas nenhuma evidência oficial pinada define um campo/valor do recurso `Dados_Gerais_Siope` que identifique a declaração atualmente eficaz, uma retificação pendente, uma declaração substituída ou um estado final/bloqueado. Sem essa regra, interpretar `IDN_DECL_RETI`, `IDN_TIPO_DECL`, `DAT_DECL` ou `NUM_RECI` pelo nome seria inferência proibida. Não houve nova observação corrente.

## Modelo de prova de fechamento

Os conceitos são independentes:

1. **ANNUAL_CONSOLIDATION**: P6 agrega o exercício; provado.
2. **VALID_ANNUAL_SUBMISSION**: transmissão/validação e recibo anual aparecem na documentação, mas nenhum valor decisivo foi pinado na observação.
3. **CURRENTLY_EFFECTIVE_DECLARATION**: exige regra oficial de seleção da versão vigente e observação correspondente; não provado.
4. **RECTIFICATION_POSSIBLE**: provado para P6 mediante autorização técnica. A possibilidade futura não torna automaticamente ineficaz a declaração corrente.
5. **RECTIFICATION_PENDING** e **SUPERSEDED_DECLARATION**: não observados e sem campos oficialmente definidos no acervo pinado.
6. **SOURCE_FINAL/LOCKED_STATE**: nenhum conceito explícito foi localizado. Imutabilidade futura não é exigida pelo modelo, mas também não pode ser presumida.
7. **REPOSITORY_CLOSED_SERIES_ELIGIBILITY**: requer declaração anual atualmente eficaz e, separadamente, S1/S2/comparabilidade semântica.

## Reconciliação histórica

Para 2016, o repositório tratou P1 como anual; para 2017–2020 e 2021–2024, tratou P6 e os produtos do pipeline histórico como série fechada. A auditoria de continuidade caracteriza isso como convenção histórica, sem recibo, prazo, flag de status, supersessão ou lock pinado ano a ano. Trata-se da categoria **F: convenção do repositório sem prova explícita de finalidade da fonte**, e não de A–E.

O gate não rebaixa 2016–2024, mas também não herda a lacuna histórica para promover 2025. O padrão explícito daqui em diante é: papel anual + regra oficial de declaração atualmente eficaz + valor observado que satisfaça a regra. Retificação possível e eficácia corrente não são opostos.

## Inventário e evidência oficial

Os onze candidatos solicitados existem no schema de 52 campos, porém seus valores não foram preservados na observação autorizada e o acervo oficial pinado não lhes dá definição decisiva. O JSON de evidência registra individualmente presença, valor conhecido, definição, capacidade de distinguir original/retificadora, eficácia corrente e tipo de prova.

As fontes FNDE pinadas são o *Dicionário de Dados SIOPE 2019* (P6 como consolidação anual), o *Guia para Novos Prefeitos 2025* (recibo anual, prazo e transmissão/validação de P6) e o *Tutorial Básico SIOPE 2024 v2* (retificação de P6 mediante autorização). Nenhuma define versão vigente ou lock no recurso público. Seus URLs, autoridade, versão, proposições positivas, limitações e ausência de hash de bytes constam no artefato machine-readable.

Uma busca documental oficial limitada foi tentada em 2026-08-30, mas o conector retornou HTTP 401 antes de fornecer resultados. Nenhum claim novo foi adotado, nenhum byte foi adquirido e nenhum hash foi fabricado.

## Observação mínima futura e estado resultante

Uma nova consulta agora não resolveria a semântica: primeiro deve ser pinada a regra oficial que defina os campos e valores decisivos. Só então caberia uma autorização separada para um GET único de 2025/P6/Limeira (`COD_MUNI=352690`), selecionando apenas identidade e os campos comprovadamente decisivos, sem paginação, retry, redirect, Drive, persistência ou publicação.

Estado resultante:

- `annual_closure_status = UNKNOWN`;
- `immutable_finality = NOT_PROVEN_NOT_REQUIRED_FOR_MODEL_BUT_EFFECTIVE_STATUS_RULE_MISSING`;
- `semantic_comparability_status = UNKNOWN`;
- `closed_series_2025_eligibility = BLOCKED_BY_B3_AND_S1_S2_SEMANTIC_COMPARABILITY`;
- série fechada permanece `2016-2024`;
- S1, S2, Gold 2025, release 0.8.0 e 2026 permanecem bloqueados/inalterados.
