# TASK 256 — canonização do timeout TASK255 e diagnóstico curl no-follow

## Estado preservado

A TASK255 executou exatamente um GET no primeiro controle PNCP, no run `35297299432`, job `105452378888`, sobre o runtime head `532750f73c13c087882c75d6a36ebe6a2d9cfd60`.

O artifact sanitizado `10527918489` possui ZIP SHA-256 `bc1a12214ce35464b4e1d70674a4f0b93d4846beeac04050d5ae58c953d0440f` e resultado SHA-256 `52fbcbd4a06ba2a8c094bf8898a23ead52ce6aa18c214473cebe60bcf97af8d7`.

O resultado foi `TRANSPORT_UNRESOLVED` com `URL_ERROR:TimeoutError`, sem status HTTP, sem `Location` e sem bytes de resposta.

A autorização TASK255 foi consumida no runtime branch no commit `d10c3aa7209ced3f32f8875034fb7115d0fad00e`.

## Relação com a TASK254

A TASK254 observou um 3xx no mesmo URL, mas não persistiu o cabeçalho `Location`. A TASK255, em outra execução, expirou antes de receber status/cabeçalhos.

Essas duas observações permanecem separadas. Elas provam somente o que ocorreu em cada run; não provam destino de redirect, estabilidade do endpoint, ausência de registro PNCP ou comportamento dos sete controles ainda intocados.

## Carrier preparado

A TASK256 prepara um diagnóstico de transporte estritamente bounded com `curl` para o mesmo primeiro alvo:

`https://pncp.gov.br/api/pncp/v1/orgaos/45132495000140/compras/2026/646`

Limites:

- exatamente 1 GET;
- `curl` sem `--location`;
- zero retry;
- zero descoberta de URL alternativa;
- corpo descartado em `/dev/null`;
- nenhum dos sete controles restantes;
- zero ITEMS/HISTORY/contracts/TCE/Drive;
- zero Bronze/Silver/Gold/serving/publicação;
- zero schedule/recorrência.

O resultado futuro preservará somente metadados sanitizados de transporte: exit code/erro do curl, código HTTP, `redirect_url`, URL efetiva, IP/porta local e remota quando expostos, tempos de DNS/conexão/TLS/TTFB/total, content type e tamanho recebido.

O objetivo é separar quatro possibilidades observáveis sem inventar semântica: timeout sem resposta HTTP, resposta 3xx com destino, resposta HTTP não-redirect e drift inesperado da URL efetiva.

## Próximo gate

`OWNER_AUTHORIZED_SINGLE_PNCP_CURL_NOFOLLOW_TRANSPORT_DIAGNOSTIC_ON_MERGED_TASK256_SHA`.

A TASK256 não autoriza esse GET.
