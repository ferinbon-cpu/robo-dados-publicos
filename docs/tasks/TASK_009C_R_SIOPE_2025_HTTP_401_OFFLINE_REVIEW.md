# TASK 009C-R — revisão offline do HTTP 401 no caminho resolvido

## Escopo e observação pinada

Esta revisão é estritamente `T0_OFFLINE`: usa somente material já versionado e a observação sanitizada fornecida pelo proprietário, posteriormente conferida contra o GitHub Actions. Nenhuma rede de fonte SIOPE/FNDE, Drive, persistência, publicação, OAuth, cookie, credencial ou tentativa de login foi usada nesta revisão.

O workflow manual real foi confirmado como run ID `33221146589`, `run_number=1`, `run_attempt=1`, evento `workflow_dispatch`, workflow ID `344981895`, head `0e70495e5ae8ccdf45aff7e2c76fd302d1294b0c`, iniciado em `2026-08-28T23:39:27Z`. O run emitiu o único GET permitido ao caminho resolvido, recebeu `HTTP 401` e terminou com `STOP_SIOPE_2025_METADATA_RESOLVED_PATH_PROBE_HTTP_401` / exit code 13. Nenhuma resposta ou arquivo foi persistido. A evidência sanitizada está em `docs/evidence/TASK_009C_SIOPE_2025_RESOLVED_PATH_PROBE_RUN_1_HTTP_401_0.8.0.json`.

## Autorização consumida

A autorização `SIOPE2025-METADATA-DIRECT-PROBE-20260828-01` era one-shot e foi **consumida** após exatamente um source GET. Rerun, retry, reuso e qualquer nova chamada estão bloqueados. O 401 não autoriza autenticação, login, cookies, tokens, credenciais, OAuth, bypass ou exploração.

## Inventário estático das rotas já documentadas

| Material local | Classificação | Limite da evidência |
|---|---|---|
| Página oficial FNDE Downloads (`https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/downloads`) | `PUBLIC_ROUTE_CANDIDATE` | É landing page oficial já pinada; não prova uma rota binária pública atual. |
| Short/share URL SharePoint pinada na TASK 009A/009B | `PUBLIC_ROUTE_CANDIDATE` / `UNPROVEN_CANDIDATE` | A observação existente prova somente redirect, não entrega pública do ZIP. |
| `Location` relativo observado na TASK 009B | `UNKNOWN` / `UNPROVEN_CANDIDATE` | É referência relativa, não rota pública independente comprovada. |
| Caminho direto resolvido na TASK 009C | `REQUIRES_AUTHENTICATION` | O request autorizado observado recebeu 401; isso não prova mecanismo nem autoriza autenticação. |

Não há no repositório evidência de outra URL oficial para o mesmo pacote. Em especial, esta revisão não acrescenta `?download=1`, não presume `_layouts/15/download.aspx` público e não deriva nem inventa URL.

## Conclusão e desenho da TASK 009D

A próxima rota pública para o pacote permanece `UNKNOWN`. Falta um href oficial FNDE pinado localmente, ou documentação oficial pinada, que identifique uma rota distinta de entrega pública não autenticada para o mesmo pacote municipal de metadados 2025.

Uma eventual TASK 009D permanece `KEEP_BLOCKED`. Antes de qualquer execução ela exigiria: (1) essa nova evidência oficial; (2) contrato bounded separado, fail-closed e revisado; e (3) nova autorização humana explícita e one-shot. Este documento e o assessment não autorizam request algum.

## Guardas semânticas e efeitos

- `annual_closure_status`: `UNKNOWN`;
- `semantic_comparability_status`: `UNKNOWN`;
- Gold 2025: `UNKNOWN`;
- série anual fechada: 2016–2024;
- 2026: não provado/não autorizado;
- source GET nesta revisão: 0;
- Drive read/write: 0/0;
- persistência e publicação: não.
