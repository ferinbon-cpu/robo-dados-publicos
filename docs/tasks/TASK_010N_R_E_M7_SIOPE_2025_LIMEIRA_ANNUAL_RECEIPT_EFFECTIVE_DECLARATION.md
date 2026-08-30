# TASK 010N-R-E-M7 — recibo anual e declaração efetiva SIOPE 2025 de Limeira

## Decisão B3

`KEEP_ANNUAL_CLOSURE_UNKNOWN_VALID_ANNUAL_SUBMISSION_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING`.

O recibo oficial relatado pelo usuário prova que o formulário SIOPE 2025 Anual de Limeira foi entregue com sucesso. Assim, `VALID_ANNUAL_SUBMISSION = PROVEN`. A investigação documental, porém, não pinou regra oficial que determine que uma transmissão posterior substitui a anterior, nem que a superfície de recibos exibe exclusivamente a declaração válida mais recente. Por isso, `CURRENTLY_EFFECTIVE_DECLARATION = NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING` e `annual_closure_status = UNKNOWN`.

Imutabilidade futura não é requisito para reconhecer a entrega válida e permanece `NOT_PROVEN_NOT_REQUIRED`. Sucesso do processamento, disponibilidade para publicação e `Retificadora = Não`, isolados ou combinados sem regra de seleção, não provam eficácia corrente.

## Handoff oficial mediado pelo usuário

O manifesto normalizado preserva três classes distintas:

1. `USER_MEDIATED_OFFICIAL_RECEIPT_STATUS`: Municipal / São Paulo / Limeira, `2025 - Anual`, recibo superficial `428477`, transmissão `09/02/2026 14:10`, processamento `13/02/2026 12:47`, `Processado com sucesso / Com manifestação do CACS`, `Declaração Retificadora = Não` e MAVS `Histórico`.
2. `USER_MEDIATED_OFFICIAL_MAVS_HISTORY`: protocolo `831423` entrou no fluxo de validação e depois exigiu retransmissão; o protocolo distinto `832393` foi transmitido em `09/02/2026 14:10`, percorreu as validações e chegou a `Disponibilizada para Publicação` em `13/02/2026 11:33`.
3. `USER_MEDIATED_OFFICIAL_RECEIPT_PDF`: arquivo original informado `M352690_2025_6_428477.pdf`, município `352690 - Limeira`, período `2025 Anual`, recibo `428477-6`, versão `25.0.4.5`, código de validação pinado e a proposição literal de entrega bem-sucedida em `09/02/2026 às 14:10:26`.

Os bytes exatos do PDF oficial foram disponibilizados no handoff endurecido. O manifesto pina SHA-256 `41d5dba704d9de9309819ac1cb58a08bdbd85ae88d5dfdc3d1b936c654790e29`, tamanho `22133` bytes, media type `application/pdf`, versão PDF `1.3` e uma página. O binário não foi commitado; o conteúdo financeiro do recibo fica expressamente fora do B3.

## Reconciliação determinística

A identidade exigida é ano 2025, período Annual/P6, SP/Sao Paulo, código municipal 352690 e Limeira. O timestamp superficial e a transmissão MAVS do protocolo 832393 coincidem no minuto (`09/02/2026 14:10`), enquanto o PDF fornece segundos (`14:10:26`). O número superficial `428477` reconcilia com o número completo `428477-6` do PDF. O processamento (`13/02/2026 12:47`) ocorreu após o status MAVS de disponibilidade para publicação (`13/02/2026 11:33`).

`832393` é protocolo MAVS e `428477`/`428477-6` é número de recibo. O modelo os mantém como identificadores diferentes; não declara igualdade entre eles.

## Retransmissão não é retificação formal

O histórico sustenta uma progressão operacional: transmissão anterior → retransmissão exigida → nova transmissão → validações → disponibilidade para publicação. Ele não sustenta que o protocolo 831423 foi uma submissão final bem-sucedida nem que o protocolo 832393 seja uma `Declaração Retificadora = Sim`. Esta última inferência também contrariaria a observação superficial `Retificadora = Não`.

Portanto, `RETRANSMISSION_WORKFLOW` e `FORMAL_RETIFYING_DECLARATION` permanecem conceitos separados. A existência de retransmissão não fornece, por si, regra jurídica ou semântica de supersessão.

O *Tutorial Básico SIOPE 2024 v2*, na seção **4. Abrir Declaração**, exibe na aplicação oficial as colunas `RETIFICADORA`, `RECIBO` e `RECIBO ANTERIOR`. Isso constitui `PARTIAL_STRUCTURAL_RETIFICATION_CHAIN_EVIDENCE`: prova que o modelo da aplicação distingue indicador retificador, recibo corrente e recibo anterior. Não prova que toda retificação supersede a versão anterior em todas as superfícies, que a página pública exponha somente a versão vigente/mais recente, nem que o recibo `428477-6` seja imutável ou permanentemente final.

## Busca oficial de retificação/supersessão

A busca ficou limitada a `gov.br/fnde`, `fnde.gov.br` e `webservice.fnde.gov.br`, cobrindo termos de declaração retificadora, retificação, retransmissão, substituição, declaração anterior/vigente, última declaração/transmissão/recibo, novo recibo, cancelamento, sobrescrita, reabertura, anual/P6, recibo, publicação e MAVS.

As fontes oficiais já pinadas sustentam: P6 como consolidação anual; entrega/validação e recibo anual; possibilidade de retificar P6 mediante autorização; e existência da superfície operacional. Elas **não** sustentam que uma declaração posterior substitui a anterior, como se seleciona a declaração vigente, ou que a superfície mostra somente o recibo atual/mais recente.

Nesta execução, o acesso direto aos hosts oficiais falhou no túnel com HTTP 403 e o conector de busca oficial retornou HTTP 401. Nenhum novo byte foi adquirido. Logo, as respostas às perguntas primária e secundária são `NOT_FOUND_OR_PINNED`, não uma conclusão de que a regra inexiste.

## Estado resultante e limites

- `VALID_ANNUAL_SUBMISSION = PROVEN`;
- `CURRENTLY_EFFECTIVE_DECLARATION = NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING`;
- `annual_closure_status = UNKNOWN`;
- `closed_series_2025_eligibility = BLOCKED_BY_B3_EFFECTIVE_SELECTION_RULE_PLUS_S1_S2_SEMANTIC_COMPARABILITY`;
- série anual fechada permanece `2016-2024`;
- S1 e S2 permanecem `NOT_PROVEN` e comparabilidade semântica permanece `UNKNOWN`;
- aliases financeiros permanecem `9/10` exatos operacionais; o resultado contextual de `VL_DESP_DOTA_ATUA_EDU` permanece `PARTIAL_CURRENT_EXACT_1000_VARIANCE_NO_SOURCE_DEFINED_INCLUSION_RULE`, fora de `canonical_state`;
- Gold 2025 continua `UNKNOWN/BLOCKED`, 0.8.0 continua `CANDIDATE` e 2026 continua `UNPROVEN_CURRENT_YEAR`.

M7 avança somente a prova de submissão anual válida. Não revisita S1/S2, não incorpora indicadores financeiros e não autoriza leitura remota operacional, persistência, publicação ou merge automático.
