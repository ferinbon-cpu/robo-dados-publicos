# TASK 010N-R-E-M6 — fechamento/finalidade anual SIOPE 2025 P6

## Decisão B3

`KEEP_ANNUAL_CLOSURE_UNKNOWN_RECEIPT_STATUS_SURFACE_FOUND_EFFECTIVE_SELECTION_RULE_AND_LIMEIRA_ANNUAL_STATUS_NOT_PINNED`.

O P6 é uma consolidação anual oficial e existe uma superfície operacional oficial de recibos/status. Ainda não está pinada a linha anual 2025 de Limeira nem uma regra oficial segundo a qual a linha exibida seja a versão vigente/mais recente quando há retificações ou supersessões. Sem essa regra, interpretar campos OData pelo nome ou transformar status de processamento em eficácia corrente seria inferência proibida. Não houve nova observação corrente.

## Modelo de prova de fechamento

Os conceitos são independentes:

1. **ANNUAL_CONSOLIDATION**: P6 agrega o exercício; provado.
2. **OFFICIAL_SIOPE_TRANSMISSION_RECEIPT_SURFACE**: a página oficial *SIOPE — Recibos de Transmissão* expõe `Período`, `Situação`, `Nº do Recibo`, `Data de Processamento`, `Data de Transmissão`, `Declaração Retificadora` e `MAVS`; exemplos oficiais indexados incluem `2025 - Anual` e `Declaração Retificadora = Sim/Não`.
3. **VALID_ANNUAL_SUBMISSION**: a superfície distingue status de processamento, recibo, timestamps, retificação e MAVS, mas a semântica normativa dos valores de `Situação` permanece parcial.
4. **CURRENTLY_EFFECTIVE_DECLARATION**: exige regra oficial de seleção da versão vigente/mais recente e observação correspondente; não provado.
5. **RECTIFICATION_POSSIBLE**: provado para P6 mediante autorização técnica. A possibilidade futura não torna automaticamente ineficaz a declaração corrente.
6. **RECTIFICATION_PENDING** e **SUPERSEDED_DECLARATION**: não provados. `Retificadora = Sim/Não` distingue o tipo da transmissão, mas não prova sozinho qual linha prevalece.
7. **SOURCE_FINAL/LOCKED_STATE**: imutabilidade não é exigida para o modelo de eficácia corrente e não está provada. `Processado com sucesso` ou `Retificadora = Não` não constituem lock.
8. **REPOSITORY_CLOSED_SERIES_ELIGIBILITY**: requer declaração anual atualmente eficaz e, separadamente, S1/S2/comparabilidade semântica.

## Reconciliação histórica

Para 2016, o repositório tratou P1 como anual; para 2017–2020 e 2021–2024, tratou P6 e os produtos do pipeline histórico como série fechada. A auditoria de continuidade caracteriza isso como convenção histórica, sem recibo, prazo, flag de status, supersessão ou lock pinado ano a ano. Trata-se da categoria **F: convenção do repositório sem prova explícita de finalidade da fonte**, e não de A–E.

O gate não rebaixa 2016–2024, mas também não herda a lacuna histórica para promover 2025. O padrão explícito daqui em diante é: papel anual + regra oficial de declaração atualmente eficaz + valor observado que satisfaça a regra. Retificação possível e eficácia corrente não são opostos.

## Inventário e evidência oficial

Os onze candidatos solicitados existem no schema de 52 campos, porém seus valores não foram preservados na observação autorizada e o acervo oficial pinado não lhes dá definição decisiva. O JSON de evidência registra individualmente presença, valor conhecido, definição, capacidade de distinguir original/retificadora, eficácia corrente e tipo de prova.

As fontes FNDE pinadas são o *Dicionário de Dados SIOPE 2019* (P6 como consolidação anual), o *Guia para Novos Prefeitos 2025* (recibo anual, prazo e transmissão/validação de P6), o *Tutorial Básico SIOPE 2024 v2* (retificação de P6 mediante autorização) e a página atual *SIOPE — Recibos de Transmissão*. Esta última prova a existência da superfície e suas colunas, mas não prova que uma linha seja vigente/mais recente, nem que sucesso de processamento seja fechamento do repositório. URLs, autoridade, versão, proposições e limitações constam no artefato machine-readable.

Os dois exemplos oficiais indexados fornecidos no handoff também são pinados por URL e proposição no JSON: ambos sustentam `2025 - Anual` e a distinção `Declaração Retificadora = Sim/Não`; ao menos um sustenta a ocorrência de `Sim`. São evidência indexada fornecida pela task, não bytes baixados pelo Codex, e não sustentam seleção vigente/mais recente, status de Limeira ou imutabilidade.

Uma busca documental oficial limitada pelos termos de recibo, situação, processamento, retificação, substituição, vigência, último recibo/transmissão, histórico e MAVS foi tentada em 2026-08-30. O acesso direto foi bloqueado pelo túnel com HTTP 403 e o conector de busca retornou HTTP 401. Não foi localizada/pinada uma regra de seleção ou supersessão; nenhum byte foi adquirido e nenhum hash foi fabricado.

## Observação mínima futura e estado resultante

O menor próximo passo é `USER_MEDIATED_OFFICIAL_RECEIPT_STATUS_HANDOFF`: consultar **Municipal / São Paulo / Limeira / exercício 2025 / Anual** e capturar somente cabeçalho/identidade, município e as sete colunas da superfície. Sem autenticação, Drive, valores financeiros, `NUM_POPU` ou publicação. Mesmo essa observação não promove B3 sem regra oficial sobre qual linha é vigente/mais recente quando existem retificações ou supersessões.

Estado resultante:

- `annual_closure_status = UNKNOWN`;
- `immutable_finality = NOT_PROVEN_NOT_REQUIRED_FOR_MODEL_BUT_EFFECTIVE_STATUS_RULE_MISSING`;
- `semantic_comparability_status = UNKNOWN`;
- `closed_series_2025_eligibility = BLOCKED_BY_B3_EFFECTIVE_SELECTION_AND_LIMEIRA_STATUS_PLUS_S1_S2_SEMANTIC_COMPARABILITY`;
- série fechada permanece `2016-2024`;
- S1, S2, Gold 2025, release 0.8.0 e 2026 permanecem bloqueados/inalterados.
