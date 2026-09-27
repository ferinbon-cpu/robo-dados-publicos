# M7 — SIOPE runtime route all-types diagnostics 0.8.0

## Motivação

O primeiro diagnóstico runtime (`run 32799171860`) observou 104 requisições pós-clique abortadas antes da rede, porém apenas uma passou pelo filtro de `resourceType`: o favicon. Outras 103 foram excluídas exclusivamente pelo tipo de recurso.

## Objetivo

Inventariar de forma sanitizada todos os HTTP GET/POST pós-clique, independentemente do `resourceType`, sem alterar a política de rede do runtime probe.

## Evidência permitida

- método;
- resource type;
- scheme e host;
- rota sem query;
- nomes das chaves da query, nunca valores;
- ocorrências;
- contagens por método, tipo e host.

## Proibições preservadas

- nenhuma requisição pós-clique enviada;
- nenhum HEAD;
- nenhum download;
- nenhum request/response body;
- nenhum header ou cookie;
- nenhuma escrita remota;
- nenhuma coleta/processamento/recorrência;
- schedule desabilitado.

Este gate é diagnóstico. Ele não promove rota, não autoriza aquisição e não altera a release ativa 0.7.0.
