# TASK290 — B08: preservar 9 PDFs oficiais a partir do artifact GitHub já validado

**10/10/2026.** O owner executou o lote B08 em [GitHub run #38076191781](https://github.com/ferinbon-cpu/robo-dados-publicos/actions/runs/38076191781), SUCCESS, artefato #11679565125 `jom2026-originais-B08-manifesto`, 326.670.529 bytes, SHA do ZIP `78f900478579313789015fbd0f5a6e973f04829b1c4d216836b70e2288fe7272`. Nove edições autorizadas e validadas: 7270–7273, 7283–7284, 7287–7289.

O Google Drive SME continua sem custódia de B08: o conector rejeita o artifact ZIP de 326,7 MB (HTTP 413; limite exato 104.857.600 bytes). O ambiente de processamento local ficou indisponível na sessão; isso não prova falha dos PDFs, nem autoriza contar B08 como salvo. Acervo anterior B01–B07: 81 identidades de 2026 preservadas de alguma forma, B08 **pendente**, B09 **não executado**.

## Remediação com limites explícitos

Workflow T2 estritamente manual, owner-confirmed, na `main`, primeira tentativa; **não tem schedule, push, workflow_run, repository_dispatch, Drive secrets nem sites oficiais**. Usa `GITHUB_TOKEN` com `actions:read` para recuperar exclusivamente o artifact preexistente da run B08. O script offline:

1. Confirma identidade de lote, SHA de origem, nove URLs pinadas do fixture TASK219A, quantidade e status.
2. Valida **todos os 9 originais antes de gravar outputs**: tamanho, SHA-256, PDF e capa, páginas, procedência.
3. Gera segmentos binários reversíveis, no máximo 90 MiB por segmento; PDFs menores continuam íntegros sem modificação.
4. Permite no máximo três segmentos por edição (27 artifacts no pior caso), cada um com `manifest_excerpt.json`, hash do original e do segmento, números e ordem.
5. Emite somente artifacts de 7 dias, nenhum GET municipal ou escrita Drive. Bronze continua create-only.

**Não executar até revisão, CI e merge por humano responsável:** abrir o PR, conferir os checks; após merge na `main`, Actions → `JOM B08 — reempacotar originais validados da run anterior` → `Run workflow` com `confirmar_b08=true` uma vez.

Após sucesso da run manual, baixar via conector os artifacts menores de 100 MiB, transferir individualmente para o Drive SME, preservar ambos originais e metadados, validar SHA-256 por readback, atualizar checkpoint. Usuário não precisa baixar/subir arquivos no computador; só a aprovação no GitHub é necessária para a emissão dos artifacts.

**Proibições:** não disparar automaticamente, não reinterpretar o run como autorização para B09, não repetir coleta, não fazer self-merge, não declarar B08 custodiado antes do QA no Drive. `PR #921 TASK289` é específico de B06 e não precisa ser executado para B08.
