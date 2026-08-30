# TASK 012 — publicação corretiva M8 SIOPE com readback semântico

## Escopo e estado

Esta mudança prepara, mas **não executa**, uma publicação T3 corretiva e
manual do produto histórico validado de Limeira (2016–2024). A execução futura
exige `workflow_dispatch`, confirmação booleana, branch `main` e autorização
explícita separada do owner em
`docs/evidence/TASK_012_M8_CORRECTIVE_R2_OWNER_AUTHORIZATION_0.8.0.json`, com
status autorizado e `authorized_main_sha` idêntico ao SHA executado. O arquivo
permanece `PENDING_POST_MERGE_OWNER_AUTHORIZATION` neste PR, portanto a
confirmação booleana isolada para antes de OAuth/Drive. O estado de release permanece `0.7.0 = ACTIVE` e
`0.8.0 = CANDIDATE`.

Os objetos V0_8_0 existentes são imutáveis. A correção usa somente estes nomes:

1. `SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R2_TABELA`;
2. `SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R2.pdf`;
3. `SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R2_publication_manifest.json`.

## Transporte tabular independente de locale

O CSV pinado é aberto em UTF-8 (aceitando BOM), com `newline=""` e parser
`csv.reader(..., dialect="excel", delimiter=",")`. Não há detecção de locale
nem conversão/importação CSV pelo Drive. O gate cria uma planilha vazia e
envia a matriz explicitamente a `spreadsheets.values.update` no range `A1:G9`,
com `valueInputOption=RAW` e `majorDimension=ROWS`.

O readback usa `spreadsheets.values.get` no range amplo e limitado `A:Z`,
`majorDimension=ROWS` e
`valueRenderOption=UNFORMATTED_VALUE`. A matriz retornada deve conter exatamente
9 linhas, 7 colunas em cada linha e igualdade célula a célula com a matriz
canônica. Ambas também recebem SHA-256 da serialização JSON canônica. Assim,
colapso de delimitador, reordenação, truncamento, células extras/ausentes e
reinterpretação de fórmulas falham de modo fechado. Como toda a matriz usada
retornada para `A:Z` deve ser exatamente 9x7, valores em `H1`, `A10` ou qualquer
outra linha/coluna extra também falham.

## Ordem e falha fechada

Antes da primeira escrita, o gate valida o contrato, o ZIP e todos os membros
pinados (incluindo `table.csv`, `report.pdf` e `manifest.json`) e faz um único
inventário para colisão dos três nomes R2. Cada inventário usa exatamente uma
requisição Drive com `pageSize=1000`; qualquer `nextPageToken` é STOP, pois
paginação não é autorizada. Qualquer colisão ou drift implica
zero escrita.

A única sequência mutante é:

1. criar uma Sheet vazia;
2. escrever a matriz com semântica RAW;
3. realizar e validar o readback semântico 9x7;
4. criar e verificar por download/hash o PDF;
5. criar o completion manifest por último;
6. verificar por download/hash o manifest e fazer o inventário final.

Se o readback da Sheet falhar, o processo encerra com exatamente uma criação
parcial possível. Não cria PDF ou manifest, não cria segunda Sheet, não tenta
novamente e não apaga nem altera a Sheet. A evidência de falha registra apenas
contagens e flags sanitizadas, nunca IDs remotos ou secrets.

## Capacidades que permanecem bloqueadas

Overwrite, replace, delete, retry, schedule, recorrência, recolhimento de fonte,
rerun de processamento/reconciliação, inclusão de 2025, promoção de release e
promoção de conclusão de compliance estão declarados como `false` no contrato.
O dry-run é totalmente local, com `network_called=false` e `drive_writes=0`.

Os estados semânticos existentes não mudam: `S1_NUM_POPU = NOT_PROVEN`,
`S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`, `VALID_ANNUAL_SUBMISSION = PROVEN`,
`CURRENTLY_EFFECTIVE_DECLARATION = NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING`,
`annual_closure_status = UNKNOWN`, `semantic_comparability_status = UNKNOWN`,
Gold 2025 permanece `UNKNOWN/BLOCKED` e 2026 permanece
`UNPROVEN_CURRENT_YEAR`.
