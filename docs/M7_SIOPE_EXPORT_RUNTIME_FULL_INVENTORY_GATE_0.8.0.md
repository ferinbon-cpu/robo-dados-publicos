# M7 SIOPE — Runtime Full Inventory Gate 0.8.0

## Motivo

O live run `32799171860` do diagnóstico runtime anterior passou, mas mostrou que 103 de 104 requisições pós-clique foram excluídas exclusivamente pelo filtro de `resourceType`. A única forma elegível foi `favicon.ico`, portanto nenhuma rota de exportação foi provada.

## Objetivo

Inventariar todas as requisições HTTP pós-clique observadas pelo mesmo runtime Chrome/CDP, sem restringir por `resourceType`, mantendo todas abortadas no estágio `Fetch.requestPaused` antes da rede.

## Evidência permitida

Somente:
- método;
- `resourceType`;
- scheme e host;
- rota sem query;
- nomes das chaves de query, sem valores;
- contagem de ocorrências;
- marcador de provável asset estático;
- marcadores textuais de exportação presentes na rota;
- flags `network_sent=false` e `intercepted_before_network=true`.

## Proibições preservadas

- nenhum request pós-clique enviado;
- nenhum download;
- nenhum HEAD;
- nenhum header, cookie, request body ou response body capturado;
- nenhuma escrita em Drive;
- nenhuma coleta ou processamento da fonte;
- nenhuma recorrência ou schedule.

## Semântica

- `ONE_MARKER_BOUND_ROUTE_SHAPE_OBSERVED_NOT_SENT`: uma única forma de rota contém marcador diretamente aderente ao contrato de exportação; ainda não foi chamada.
- `FULL_POST_CLICK_HTTP_INVENTORY_OBSERVED_REVIEW_REQUIRED`: há formas não estáticas ou potencialmente relevantes, mas exigem revisão.
- `ONLY_STATIC_POST_CLICK_HTTP_SHAPES_OBSERVED`: o clique não produziu forma HTTP de exportação; próximo passo é diagnosticar o controle DOM efetivamente clicado.

Nenhum destes estados autoriza aquisição, coleta, processamento ou recorrência.
