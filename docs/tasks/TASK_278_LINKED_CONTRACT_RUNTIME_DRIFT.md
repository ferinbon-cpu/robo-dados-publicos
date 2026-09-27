# TASK 278 — drift operacional da rota PNCP contrato/empenho

Para o controle 645, a rota oficial de contratos/empenhos passou por três estados observados: HTTP 400 sem `pagina`; HTTP 404 após correção da paginação; e, numa reobservação idêntica posterior, HTTP 503 em HTML.

A sequência impede promover o 404 anterior a ausência canônica de contrato/empenho. O estado correto é **unresolved por variabilidade da fonte/backend**.

O Manual v2.6 documenta a rota e os parâmetros de caminho, enquanto a API em produção exigiu adicionalmente `pagina`. Esta task não faz rede.

Próximo diagnóstico: observar em uma mesma execução um endpoint PNCP já provado saudável para o controle 645 (ITEMS) e a rota de contrato/empenho, um GET por rota e sem retry.
