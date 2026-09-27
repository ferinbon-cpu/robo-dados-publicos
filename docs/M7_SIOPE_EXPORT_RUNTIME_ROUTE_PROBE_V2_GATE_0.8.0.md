# M7 SIOPE EXPORT RUNTIME ROUTE PROBE V2 GATE 0.8.0

## Motivo

O diagnóstico all-types do run 32835798761 mostrou que as 104 requisições interceptadas após a mudança de fase eram 101 scripts, 2 stylesheets e 1 favicon do front-end da Plataforma Antonieta de Barros. O bloqueio anterior era seguro, mas impedia o carregamento dos chunks necessários para o botão `Exportar artefato` progredir até a requisição de exportação.

## Estratégia V2

O V2 mantém CDP `Fetch.requestPaused` no estágio `Request` e mantém downloads negados. Após o clique, somente requisições que satisfaçam simultaneamente todos os critérios abaixo podem continuar:

- HTTPS;
- host exato `www.fnde.gov.br`;
- caminho iniciado por `/plataforma-antonieta-de-barros/assets/`;
- método GET;
- `resourceType` Script ou Stylesheet.

Qualquer outra requisição pós-clique é abortada antes da rede e registrada apenas de forma sanitizada: método, tipo de recurso, scheme/host, rota sem query e nomes das chaves de query. Valores de query, headers, cookies e bodies são proibidos.

## PASS/STOP

- PASS somente se houver exatamente uma rota não-estática pós-clique interceptada e não enviada.
- STOP se não houver nenhuma rota não-estática.
- STOP se houver múltiplas rotas não-estáticas; nesse caso a evidência sanitizada é submetida a revisão antes de qualquer novo gate.

## Proibições preservadas

- download do artefato;
- HEAD;
- envio da rota candidata;
- captura de request/response body;
- captura de headers ou cookies;
- escrita remota;
- Drive/OAuth;
- coleta e processamento da fonte;
- recorrência e schedule.

## Próximo estágio

Somente após PASS com rota única: `M7_SIOPE_ANTONIETA_ARTIFACT_ROUTE_VERIFICATION_DESIGN_0_8_0`.
