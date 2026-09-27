# TASK 013 — auditoria forense somente-leitura do R2 parcial

## Estado histórico observado

A execução única autorizada pela TASK 012 terminou em
`STOP_M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_REMOTE_OPERATION`. O resultado
sanitizado prova somente que um objeto remoto (a Sheet R2 parcial) foi criado,
que PDF e manifesto não foram criados e que não houve retry nem limpeza
automática. A telemetria histórica não registrou a proposição remota precisa;
portanto `historically_recorded_failure_stage` permanece
`UNKNOWN_REMOTE_OPERATION`. Ela não prova qual chamada falhou, nem que write,
readback ou validação semântica da Sheet original terminaram.

## Fronteira forense

A Sheet R2 existente é evidência forense imutável até decisão futura explícita
do owner. A TASK 013 usa exclusivamente a credencial dedicada com escopo OAuth
exato `drive.readonly`, uma única página limitada do inventário de `08_OUTPUTS`
e uma leitura read-only dos metadados da spreadsheet. Como a TASK 012 não definiu
um título canônico de aba, a auditoria exige exatamente uma worksheet `GRID` e
qualifica explicitamente a leitura como `'título da worksheet'!A:Z`. Zero,
múltiplas ou metadados ambíguos de worksheets terminam fail-closed antes da
leitura de valores. A leitura ocorre somente quando houver exatamente uma Sheet com o nome
canônico. Um `nextPageToken`, inventário ambíguo ou erro de leitura termina
fail-closed. IDs, pasta, URLs, tokens e corpos de exceção não integram o JSON
sanitizado.

O estado remoto provado agora é deliberadamente separado do estágio histórico.
Por exemplo, uma matriz canônica 9x7 prova que os valores existem no objeto no
momento forense; não prova que o readback da execução antiga teve sucesso.

## Evidência da execução forense histórica

A execução read-only `33330199393` provou o escopo OAuth exato
`https://www.googleapis.com/auth/drive.readonly`, zero mutações remotas e que o
inventário Drive limitado a uma página terminou sem paginação. O inventário
encontrou exatamente uma Sheet R2 com MIME type esperado, nenhum PDF R2 e
nenhum manifesto R2. A leitura da Sheet terminou fail-closed, mas essa execução
histórica **não registrou qual operação Sheets falhou**. Por isso, seu registro
continua sendo `historically_recorded_failure_stage =
UNKNOWN_REMOTE_OPERATION`; não há alegação sobre causa raiz.

A TASK 013R acrescenta somente observabilidade sanitizada para execuções
futuras: inventário Drive, `spreadsheets.get` de metadados e
`spreadsheets.values.get` passam a ter estágios distintos, com tipo de erro e,
quando disponível de forma segura, apenas o status HTTP numérico. Corpo da
resposta, texto opaco de exceção, URLs, IDs e credenciais não são serializados.
Essa melhoria não atribui retroativamente um estágio à execução `33330199393`
e não autoriza nova execução, retry ou repair.

## Autorizações que continuam ausentes

Esta tarefa não autoriza retry ou continuação da TASK 012, cleanup, repair in
place, delete, rename, replace, reutilização do nome R2, R3, novo PDF, novo
manifesto, publicação, recolha de fonte, recomputação, 2025 ou promoção 0.8.0.
A autorização one-shot anterior não é resetada nem reutilizada. Uma decisão
posterior poderá preservar R2 e considerar R3, ou seguir outro caminho aprovado
pela governança; a TASK 013 não escolhe essa decisão, que permanece pendente.

## Evidência deste PR

`LIVE_FORENSIC_REEXECUTION_NOT_PERFORMED_DURING_PR`

Implementação e CI executam zero operações Drive. Nenhum resultado futuro da
execução forense live é presumido ou fabricado neste documento.
