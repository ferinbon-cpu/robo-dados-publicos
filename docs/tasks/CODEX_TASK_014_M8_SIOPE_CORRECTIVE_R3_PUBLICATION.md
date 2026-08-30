# TASK 014 — publicação corretiva R3 do produto histórico M8 SIOPE

## Escopo e estado preservado

A implementação permanece limitada ao produto SIOPE Limeira/SP 2016–2024, artefato GitHub Actions `9684264254`. Não recolhe FNDE/SIOPE, não recalcula Bronze/Silver/Gold, não inclui 2025 e não promove a release 0.8.0, que continua CANDIDATE; 0.7.0 continua ACTIVE.

## Evidência forense R2 imutável

A publicação R2 não foi concluída. Seu estágio histórico permanece exatamente `UNKNOWN_REMOTE_OPERATION`; o resultado histórico não é reclassificado. O run somente leitura TASK 013/013R `33337776345`, no SHA `ed958e2c724a2fdbfdc6710cb0c7516fbc95e260`, provou `SHEET_EMPTY`, PDF ausente e manifest ausente, com zero mutações. A disponibilidade posterior da Sheets API e o sucesso desse run somente leitura **não** provam retroativamente a causa da falha histórica.

A Sheet R2 é evidência forense imutável: nunca será escrita, reparada, apagada, movida, renomeada ou reutilizada. Na R3 ela serve somente como sentinel para um GET de metadata da Sheets API, com a mesma credencial OAuth de publicação, antes da primeira criação remota.

## Contrato R3

Gate: `M8_SIOPE_HISTORICAL_CORRECTIVE_PUBLICATION_0_8_0_R3`.

Nomes exatos novos:

- `SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R3_TABELA`
- `SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R3.pdf`
- `SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R3_publication_manifest.json`

A execução é manual, T3, create-only e one-shot. Não há overwrite, replace, delete, cleanup, repair, retry, paginação, recorrência, schedule ou autorização de lote futuro. Um inventário bounded de uma página exige zero colisões R3 e exatamente uma Sheet R2 com MIME correto; paginação ou ambiguidade causam STOP. Em seguida, o GET de metadata Sheets prova capacidade antes de qualquer mutação.

A fonte pinada é validada integralmente por tamanho/hash do ZIP, conjunto de membros, tamanho/hash de cada membro e matriz CSV canônica UTF-8 de 9 x 7. A Sheet R3 é criada vazia e recebe uma única escrita Sheets API `RAW`, em range explicitamente qualificado pela única worksheet. O readback `A:Z` exige matriz, header e digest exatos; assim H1, A10, worksheet adicional, truncamento e células extras falham antes do PDF. O PDF pinado só é criado após PASS semântico; o manifest é criado por último; o inventário e a semântica são verificados novamente no final.

Falhas remotas expõem somente estágio, classe da operação, tipo do erro, status HTTP seguro e `retryable=false`; bodies, tokens, URLs e IDs remotos não são serializados.

## Autorização e execução

A evidência `TASK_014_M8_CORRECTIVE_R3_OWNER_AUTHORIZATION_0.8.0.json` fica em `PENDING_OWNER_AUTHORIZATION`, com `authorized_implementation_sha=null`, neste PR. Uma PR futura, separada e apenas de autorização, deve piná-la ao SHA exato do merge da implementação. O runtime exige ancestralidade e que o diff implementação→execução contenha exatamente esse arquivo.

Nenhuma execução live foi feita nesta implementação:

`LIVE_R3_PUBLICATION_NOT_PERFORMED_DURING_IMPLEMENTATION_PR`
