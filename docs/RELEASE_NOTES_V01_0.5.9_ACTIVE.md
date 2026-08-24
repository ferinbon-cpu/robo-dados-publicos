# SOFTWARE V01 0.5.9 ACTIVE — M4D GitHub live gate

## Promoção

A candidata 0.5.9 foi promovida após autorização do usuário e conclusão do gate GitHub ao vivo. O manifesto candidato original permanece preservado. A promoção altera a identidade operacional da release; ela não habilita coleta de fontes, agendamento ou promoção automática de identidade financeira.

## Evidência aceita

- workflow run `32678624194`, job `97476648260`, no commit `2ec69a5b054d209f6663ab4b8d442cd9bb0dc3d4`;
- preflight GitHub/OAuth: 14/14 verificações;
- testes no gate: 84/84;
- regressões históricas: 109/109;
- runtime: `PASS`, versão 0.5.9 candidata durante o gate;
- estado remoto preexistente substituído em `06_BANCOS/ROBOT_STATE.sqlite`;
- novo log append-only `ROBO_RUN_20260824T145325390316+0000_5.json` em `07_LOGS`;
- promoção revalidada localmente com 88/88 testes.

## Limites preservados

- o workflow permanece somente manual;
- a coleta de fontes está `NOT_CONFIGURED`;
- o Jornal Oficial está validado, mas `production_collection_enabled` continua `false`;
- TDA Limeira continua `BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN`;
- `MATCH_CANDIDATE` continua somente candidato à reconciliação;
- promoção automática para `financial_identity` continua proibida.

## Próxima ação

`M4E_FIRST_SOURCE_COLLECTION_GATE`: preparar e revisar um inventário explícito do Jornal Oficial para uma primeira coleta controlada, sem ativar agendamento automaticamente.
