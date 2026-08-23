# RELEASE NOTES — SOFTWARE V01 0.5.9

## Status

`CANDIDATE`. A release ativa continua sendo `0.5.8 ACTIVE` e não foi modificada.

## Nova capacidade comprovável offline

- validação fail-closed do primeiro run GitHub;
- bloqueio do job sem confirmação explícita de persistência;
- `actions/checkout` fixada no SHA `de0fac2e4500dabe0009e67214ff5f5447ce83dd` da release v6.0.2;
- `actions/setup-python` fixada no SHA `5fda3b95a4ea91299a34e894583c3862153e4b97` da release v7.0.0;
- credenciais de checkout não persistidas;
- preflight local que valida identidade, manifesto, workflow, `.gitignore` e presença dos secrets sem imprimir valores;
- wrapper do run persistente que só aceita PASS quando estado remoto existente é substituído e um novo log append-only é criado.

## Limites

O run real não foi executado porque o acesso GitHub do usuário está indisponível. Não houve escrita em `06_BANCOS` ou `07_LOGS`. O TDA permanece `BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN`; produção continua opt-in e a promoção automática de identidade financeira permanece proibida.

## QA offline

- compileall: PASS;
- testes unitários: 84/84 PASS;
- regressões históricas: 109/109 PASS;
- source inventory: PASS;
- preflight GitHub: PASS_OFFLINE;
- secret scan: PASS.

## Próxima ação

`M4D_GITHUB_LIVE_GATE_0_5_9`.
