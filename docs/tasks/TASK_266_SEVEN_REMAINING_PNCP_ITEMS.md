# TASK 266 — ITEMS dos sete controles restantes

A TASK265 provou com HTTP 200 que a rota documentada de ITEMS em `/api/pncp/v1/.../itens` está operacional para o controle 645.

A TASK266 prepara o último token da franquia (10/10) para os sete controles ainda não consultados: 646, 639, 648, 655, 653, 654 e 069. O conjunto é fixo, um GET por alvo, sem retry, redirect, descoberta alternativa ou subrotas. Corpos são temporários; apenas ITEM_ALLOW e metadados/hash são persistidos. Falha local permanece unresolved e nunca vira ausência.
