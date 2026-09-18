# TASK 274 — probe de contratos/empenhos vinculados ao controle 645

O Manual PNCP v2.6 documenta o GET de contratos/empenhos de uma contratação em `/v1/orgaos/{cnpj}/contratos/contratacao/{anoContratacao}/{sequencialContratacao}`.

Esta task prepara um único GET para o controle 645. O elo `numeroControlePNCPCompra` valida que qualquer linha retornada pertence à contratação exata.

Por minimização de dados, identificadores de fornecedor/subcontratado, `usuarioNome` e `informacaoComplementar` ficam fora do artifact. Nenhum contrato retornado é seguido para detail/history.

Lista vazia é observação temporal de zero contratos vinculados naquele instante, não ausência permanente.
