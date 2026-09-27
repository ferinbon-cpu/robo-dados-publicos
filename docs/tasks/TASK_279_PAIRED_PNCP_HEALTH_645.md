# TASK 279 — controle pareado de saúde PNCP

Compara, na mesma execução, o endpoint ITEMS do controle 645 (já provado saudável no projeto) e a rota paginada de contratos/empenhos vinculados à mesma contratação.

São exatamente dois GETs, um por URL, sem retry. O lado ITEMS persiste apenas metadados de transporte, hash e contagem de itens — nenhum conteúdo de item. O lado contrato mantém a projeção sanitizada já usada nas tasks anteriores.

O objetivo é distinguir indisponibilidade geral do PNCP de problema específico da rota de contrato/empenho. Mesmo um 404 sob contexto saudável não será convertido automaticamente em ausência permanente.
