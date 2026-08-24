# Release Notes — 0.6.3 CANDIDATE

## Marco

M5 — observabilidade auditável, derivada do referencial acadêmico consolidado.

## Base

Última release ativa validada: `0.6.2 ACTIVE`.

## Incrementos

- novo pacote `robo_dados_publicos.observability`;
- `SOURCE_CARD` para documentação operacional de fontes;
- `RUN_CARD` para rastrear execução e latência;
- `METRIC_CARD` com fórmula e semântica explícita de nulos;
- saúde separada em atualidade, completude, consistência, coleta e latência;
- distinção entre zero, ausência esperada e falha;
- primeiro cartão para a edição 7310 do Jornal Oficial.

## Segurança

A observabilidade é somente leitura. Não adiciona escrita remota, agendamento, coleta recorrente, novas fontes, processamento repetido, reconciliação repetida ou ampla, nem promoção automática de identidade financeira.

A 0.6.3 permanece `CANDIDATE` até gate separado. A 0.6.2 continua `ACTIVE`.

## Gate

Exige `PASS` em preflight offline, compileall, suíte unitária integral e regressões históricas. O resultado final do CI deve ser registrado nos manifestos de QA antes de qualquer promoção.
