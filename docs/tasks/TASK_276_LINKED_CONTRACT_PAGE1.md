# TASK 276 — consulta paginada correta de contratos/empenhos vinculados

A TASK275 provou que a produção exige o query parameter `pagina`, embora a seção 13.10 do Manual v2.6 o omita. O cliente OpenAPI gerado preservado publicamente mostra `pagina` obrigatório (mínimo 1), `tamanhoPagina` opcional (10–50) e retorno paginado em objeto.

Este carrier consulta somente `pagina=1&tamanhoPagina=50`. Não busca automaticamente páginas seguintes. Se a resposta indicar páginas restantes, o resultado é parcial e um novo gate será necessário.

A projeção exclui identificadores de fornecedor/subcontratado e `usuarioNome`. Zero registros, quando sustentado pelos metadados da página, significa apenas zero vínculos observados naquele instante.
