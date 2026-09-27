# TASK 269 — HISTORY operacional, schema v2.6 e drift da allowlist

A TASK268 executou um único GET autorizado no HISTORY do controle 645 e recebeu HTTP 200 com uma lista de 3 eventos.

O achado central é estrutural: o schema atual observado não corresponde à allowlist herdada da TASK167. A interseção é apenas `justificativa`. Assim, a TASK268 provou rota, shape, contagem e inventário de chaves, mas não preservou informação suficiente para afirmar quais foram os três eventos.

O schema observado contém campos de manutenção (`logManutencao*`, `tipoLogManutencao*`, `categoriaLogManutencao*`), identidade da compra e referências numéricas a item, resultado e documento.

A próxima projeção sanitizada proposta cobre todos esses campos observados exceto `usuarioNome`, deliberadamente excluído para minimizar retenção de dado pessoal. Nenhum valor de evento é inventado nesta task.

Esta task é totalmente offline. Uma segunda observação do HISTORY exige nova autorização explícita posterior ao merge.
