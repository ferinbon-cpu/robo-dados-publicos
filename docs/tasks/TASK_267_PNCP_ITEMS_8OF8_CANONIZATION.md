# TASK 267 — snapshot PNCP ITEMS 8/8

Os 10 tokens de autorização foram integralmente consumidos. A cadeia fechou 8/8 controles JOM→PNCP e, em seguida, 8/8 consultas de ITEMS com HTTP 200/lista JSON.

Contagens de itens: 646=9; 639=1; 645=1; 648=1; 655=8; 653=10; 654=1; 069=9. Total: 40.

Como QA, a soma de `valorTotal` dos itens coincide exatamente com `valorTotalEstimado` do detalhe em sete controles. No 653 (aquisição de livros), ITEMS soma R$ 657,71 e o detalhe registra R$ 17.579,33, diferença de -R$ 16.921,62. A TASK267 preserva isso como `OPEN_DIAGNOSTIC_NO_CAUSE_INFERRED`: não corrige fonte, não inventa item faltante e não conclui erro do PNCP.

Nenhuma leitura HISTORY, resultado de item, fonte orçamentária, contrato ou TCE foi autorizada. Qualquer nova rede exige autorização explícita nova.
