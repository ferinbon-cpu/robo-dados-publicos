# M7 SIOPE PUBLIC GET RUNTIME ROUTE DIAGNOSTICS 0.8.0

## Objetivo

Observar de forma fail-closed quais requisições dinâmicas o frontend da superfície pública `Dados Informados pelos Municípios` tenta emitir após carregar um exemplo GET já publicamente indexado pelo FNDE.

## Pré-condição

Este gate é sucessor lógico do `M7 SIOPE PUBLIC INDEXED GET CONTRACT GATE`. Ele não substitui a verificação anterior: o exemplo público indexado deve permanecer válido e sem desafio humano ativo antes de qualquer promoção operacional.

## Política de rede

O navegador pode continuar somente:

1. um único documento GET semanticamente idêntico ao exemplo público indexado já declarado no config; e
2. assets estáticos GET no host oficial `www.fnde.gov.br`, limitados a tipos `Script`, `Stylesheet`, `Image` e `Font` e extensões estáticas explicitamente allowlisted.

Qualquer outra requisição é interceptada em `Fetch.requestPaused` no estágio de request e recebe `Fetch.failRequest` antes de ir à rede.

## Evidência permitida

Para requisições bloqueadas, persistem apenas:

- método;
- `resourceType`;
- esquema;
- host;
- rota sem query;
- presença de query;
- nomes das chaves de query;
- contagem de ocorrências;
- booleanos de host oficial, candidatura dinâmica e bloqueio antes da rede.

Valores de query, headers, cookies, request body, response body, credenciais e conteúdo de CAPTCHA não são persistidos.

## Travas

Continuam proibidos:

- valores do piloto Limeira (`352690`);
- POST/form submit;
- envio de XHR/Fetch candidato;
- bypass ou resolução automática de CAPTCHA;
- autenticação;
- captura de cookies/credenciais;
- HEAD;
- download;
- escrita remota;
- coleta;
- processamento;
- recorrência;
- schedule.

## Critério de resultado

O gate pode terminar `PASS` mesmo com zero candidatas dinâmicas: seu papel é diagnóstico. Um eventual conjunto de candidatas apenas habilita revisão humana/arquitetural posterior; nenhuma rota observada é automaticamente promovida para coleta.

Se a interface indicar desafio humano ativo, se mais de um documento inicial for enviado, se qualquer rota dinâmica for marcada como enviada, se download deixar de estar negado ou se o limite de formas sanitizadas for excedido, o gate termina em STOP.
