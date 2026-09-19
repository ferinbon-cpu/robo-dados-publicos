# TASK 275 — diagnóstico seguro do HTTP 400 da rota contrato/empenho

A TASK274 observou HTTP 400 JSON na rota documentada de contratos/empenhos vinculados à contratação 645. O resultado é `UNRESOLVED`, não ausência.

O Manual PNCP v2.6 confirma a rota e usa `Accept: */*` no exemplo oficial. Este carrier reproduz exatamente esse header e, se o retorno continuar sendo um objeto de erro, persiste apenas escalares genéricos previamente autorizados e um inventário de chaves. Corpo bruto e campos de fornecedor/usuário continuam bloqueados.

A execução é limitada a um GET e exige autorização pós-merge.
