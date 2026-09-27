# TASK 281 — gate de recuperação PNCP

Carrier inerte para um único GET futuro no endpoint ITEMS do controle 645. O objetivo é apenas verificar se a fonte voltou a responder.

Não há retry automático nem consulta à rota de contrato/empenho nesta task. Um HTTP 200 com lista prova recuperação do health control e libera somente a preparação de um gate separado para contrato/empenho. Um novo 503 mantém o bloco remoto pausado.
