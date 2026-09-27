# TASK 255 — canonização do STOP TASK254 e probe no-follow de Location

## Estado preservado

A TASK254 foi executada uma única vez no run 35296079277. O primeiro controle PNCP consumiu exatamente 1 GET e o carrier encerrou fail-closed com `TASK254_REDIRECT_STATUS_OBSERVED`. Nenhum dos sete controles restantes foi requisitado.

O artifact sanitizado 10527683320 tem ZIP SHA-256 `3238e7eb162833d821f8116c36460278584f18f2fb3afa31c5c92b78393344fc` e resultado SHA-256 `d408b5c4d98b40d3c7e6b9d90c94c2180b6f31bea56c7502190189beda645e0c`.

Nada nesse STOP autoriza concluir ausência no PNCP ou invalidar o PNCP ID publicado no JOM.

## Lacuna

O transporte TASK254 bloqueou corretamente o redirect, mas descartou o cabeçalho `Location`. Assim, a existência do redirect foi provada, porém seu destino ficou `UNOBSERVED_NOT_PERSISTED`.

## Probe futuro

Somente o primeiro alvo:

`45132495000140-1-000646/2026`

URL:

`https://pncp.gov.br/api/pncp/v1/orgaos/45132495000140/compras/2026/646`

Limites:

- exatamente 1 GET;
- zero follow de redirect;
- zero retry;
- zero busca/paginação/fallback;
- zero consulta aos outros sete IDs;
- zero PNCP ITEMS/HISTORY/contracts;
- zero TCE/Drive.

O probe persiste somente metadados sanitizados: status, Location, Content-Type, bytes e hash do corpo limitado, quando existir.

Se houver 3xx, `Location` deve existir e ser URL HTTPS absoluta. Caso contrário, STOP.

Mesmo com Location válida, a TASK255 não promove esse destino aos outros sete controles. Essa transformação exigirá adjudicação posterior.

## Próximo gate

`OWNER_AUTHORIZED_SINGLE_NOFOLLOW_PNCP_REDIRECT_LOCATION_PROBE_ON_MERGED_TASK255_SHA`.
