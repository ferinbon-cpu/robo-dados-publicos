# TASK 268 — carrier do HISTORY PNCP para o controle 645

O Manual de Integração do PNCP v2.6, de 31/08/2026, documenta o serviço **Consultar Histórico da Contratação** em:

`GET /v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/historico`

com BASE_URL de produção `https://pncp.gov.br/api/pncp`.

A documentação descreve o serviço como consulta aos eventos da contratação específica, incluindo eventos de itens, resultados e documentos/arquivos.

A TASK268 só prepara o carrier. O `main` permanece sem rede. Um live futuro fica limitado ao controle exato `45132495000140-1-000645/2026`, um GET, retry zero, sem redirects ou descoberta alternativa e sem seguir qualquer referência encontrada no histórico.

Em HTTP 200, a resposta deve ser uma lista JSON. A persistência é sanitizada pelos campos HISTORY_ALLOW já usados na TASK167 e por inventário de chaves/hash/contagem. Corpo bruto não é persistido.

A franquia anterior de 10 autorizações está esgotada e não é reutilizada. O próximo GET exige autorização nova e posterior ao SHA mesclado da TASK268.
