# TASK 277 — significado seguro do HTTP 404 na rota contrato/empenho

A TASK276 corrigiu paginação e recebeu HTTP 404 JSON. Este carrier repete uma única vez exatamente a mesma consulta e persiste somente escalares genéricos seguros do envelope de erro.

Se a fonte retornar 200, o mesmo carrier entende o objeto paginado e preserva apenas a projeção de contrato/empenho sem identificadores de fornecedor.

HTTP 404 só poderá ser interpretado como zero vínculos observados se a mensagem sanitizada da própria fonte sustentar isso. A conclusão nunca será convertida em ausência permanente.
