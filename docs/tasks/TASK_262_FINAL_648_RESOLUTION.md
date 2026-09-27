# TASK 262 — controle PNCP final 648

A TASK261 resolveu 639 e 654 e deixou apenas 648 pendente. O PNCP retornou JSON explícito de `SQLTransientConnectionException` / HikariPool sem conexão disponível após 30001 ms. Isso prova falha transitória do backend naquele request, não ausência do registro.

A TASK262 prepara exatamente um GET adicional ao 648, na rota oficial `consulta/v1`, sem retry automático ou qualquer expansão. HTTP 200 exige identidade exata; qualquer outro resultado permanece unresolved e persiste somente diagnóstico sanitizado.

Gate live: `OWNER_AUTHORIZED_TOKEN_7_SINGLE_PNCP_FINAL_CONTROL_648_RESOLUTION_ON_MERGED_TASK262_SHA`.
