# TASK 010N-R-E-R — probe remoto one-shot do `$metadata` OData SIOPE 2025

## Resultado

`STOP_REMOTE_ACCESS_NO_EDMX`

A autorização one-shot `SIOPE2025-PUBLIC-CONTRACT-METADATA-20260829-01` foi usada para tentar acessar exclusivamente:

`https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/$metadata`

O ambiente de execução bloqueou o alvo por uma policy/safety boundary local antes de qualquer tráfego de rede. Uma segunda rota local de download do mesmo URL também foi recusada antes do GET pela mesma família de restrição de navegação. Não houve DNS, resposta HTTP, EDMX, valores municipais, autenticação, retry ou redirect.

Por política fail-closed, não foi feita busca para contornar a boundary, não foi usado host alternativo e não houve nova engenharia reversa.

## Efeito semântico

Nenhum.

Permanecem:

- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- evidência do contrato público = `PARTIAL_OFFLINE`;
- `2025 = PROVEN_STRUCTURAL_RECENT`;
- fechamento anual = `UNKNOWN`;
- comparabilidade semântica = `UNKNOWN`;
- Gold 2025 = `UNKNOWN/BLOCKED`;
- série anual fechada = `2016–2024`;
- `0.8.0 = CANDIDATE`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

## Contadores

- URL alvo: 1;
- tentativas de acesso no ambiente: 2;
- requests de rede emitidos: 0;
- respostas HTTP: 0;
- retries: 0;
- redirects: 0;
- consultas município/ano/período: 0;
- consultas financeiras: 0;
- autenticação/cookies/OAuth: 0;
- Drive: 0;
- Gold: 0;
- engenharia reversa: 0.

A autorização é tratada como consumida conservadoramente. Qualquer retry, nova rota, busca intermediária ou novo ambiente requer autorização separada do owner.
