# TASK 280 — dual 503 no controle pareado PNCP

Na mesma execução, o endpoint ITEMS 645 e a rota paginada de contratos/empenhos 645 devolveram HTTP 503, `text/html`, 107 bytes e o mesmo hash de corpo.

Isso elimina, naquele instante, a hipótese de que apenas a rota de contratos/empenhos estivesse indisponível. O que foi observado é uma indisponibilidade mais ampla no recorte PNCP testado.

A conclusão permanece limitada: isso não prova queda global de todos os serviços PNCP. Também não transforma o 404 anterior em ausência de contrato.

Nenhum novo GET é feito nesta task. O próximo gate é um único health check do ITEMS 645, somente para verificar recuperação da fonte.
