# TASK 270 — HISTORY v2.6 com projeção segura

A TASK268 provou a rota HISTORY e observou 3 eventos. A TASK269 canonizou que a allowlist antiga da TASK167 não corresponde ao schema atual.

Esta task prepara uma única reobservação do mesmo controle 645, agora usando os 15 campos v2.6 observados considerados necessários para interpretar os eventos.

O campo `usuarioNome` fica estruturalmente fora da projeção e do artifact, mesmo que seja retornado pela fonte. A execução valida CNPJ, ano e sequencial quando esses campos aparecem.

O workflow permanece inerte no main. Ele aceita somente uma nova autorização pós-merge, um GET, sem retry, redirects, descoberta alternativa ou travessia de referências a documentos/resultados/itens.
