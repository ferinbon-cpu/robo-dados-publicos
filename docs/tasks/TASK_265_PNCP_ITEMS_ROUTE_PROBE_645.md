# TASK 265 — probe da rota documentada de ITEMS

A TASK264 fechou 8/8 identidades JOM→PNCP. O Manual de Integração PNCP v2.6 documenta em produção o BASE_URL `https://pncp.gov.br/api/pncp` e GET `/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens`.

Como a rota DETAIL antiga informou migração para `/api/consulta/v1`, esta task não presume que ITEMS migrou do mesmo modo. Token 9 fará um único GET ao ITEMS documentado do controle 645, já saudável e exato.

HTTP 200 deve ser lista JSON. Só campos ITEM_ALLOW já usados na TASK167 podem ser persistidos. Resposta de migração/erro será apenas diagnóstico sanitizado. Sem retry, redirect, descoberta alternativa ou outro endpoint.
