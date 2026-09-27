# TASK 261 — segunda observação bounded dos três HTTP 500

A TASK260 resolveu exatamente quatro dos sete controles restantes e observou HTTP 500 com JSON válido de 341 bytes em 639, 648 e 654. HTTP 500 não equivale a ausência.

A TASK261 prepara uma única nova observação para cada um desses três controles, em ordem fixa, na rota oficial já provada. Se vier HTTP 200, a identidade deve coincidir exatamente. Caso contrário, somente metadados e escalares JSON sanitizados são persistidos. Corpo bruto permanece temporário.

Gate live: `OWNER_AUTHORIZED_TOKEN_6_EXACT_THREE_PNCP_OFFICIAL_ROUTE_REOBSERVATION_ON_MERGED_TASK261_SHA`.
