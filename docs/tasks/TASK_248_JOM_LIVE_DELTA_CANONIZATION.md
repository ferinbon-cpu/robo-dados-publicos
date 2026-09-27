# TASK 248 — canonização do delta live do JOM e fila bounded inert

## Objetivo

A TASK248 transforma a execução live bem-sucedida da TASK247 em evidência canônica do repositório e produz uma fila determinística, estritamente offline, com as quatro novas identidades documentais observadas. Ela **não** baixa os PDFs e **não** habilita recorrência.

## Entrada comprovada

- implementação TASK247 no `main`: `3c3b59606ecafbd48fe634ef850543ac03c72bdc`;
- runtime: `cbaa17bb14a90bf171c10f090e9f596896120368`;
- GitHub Actions run: `35151868669`, conclusão `success`;
- artifact: `10469402153`, `task-247-jom-rolling-sanitized-discovery`;
- digest do ZIP: `sha256:bea443dcec80cd271e6902c3f16cdf0ee65dea0468a90a5d35d14b013ccdbb7f`;
- SHA-256 do resultado sanitizado: `28701eb442dee5bc74e34fe9c7c5a21cec27ffcbae680fe0988ef4a64c978b6d`.

O hash acima é recalculável a partir do JSON live após remover somente o campo anexado `result_sha256` e serializar o restante com `sort_keys=True`, `ensure_ascii=False` e separadores canônicos.

## Resultado live canonizado

O baseline de 99 edições permanece válido até 08/09/2026. O delta observado contém:

| edição | data | source_id |
|---:|---|---|
| 7321 | 09/09/2026 | `LIMEIRA_JO_07321` |
| 7322 | 10/09/2026 | `LIMEIRA_JO_07322` |
| 7323 | 11/09/2026 | `LIMEIRA_JO_07323` |
| 7324 | 12/09/2026 | `LIMEIRA_JO_07324` |

A execução consultou uma página de índice, estimou 2 GETs remotos, baixou zero PDFs e efetuou zero escritas.

## Semântica

`PASS_JOM_ROLLING_DELTA_DISCOVERY` prova as quatro identidades observadas no estado consultado do índice. Não prova conteúdo dos PDFs. Não autoriza concluir ausência de edições em 13–16/09 e não autoriza inferência sobre edições futuras.

A fila `config/task248_jom_bounded_ingestion_queue.v1.json` é um produto T0/offline. Todos os seus efeitos remotos são `false`.

## Próximo gate

Qualquer ingestão dos PDFs 7321–7324 exige tarefa separada com autorização explícita, budget, persistência e efeitos definidos antes do primeiro GET documental. Recorrência/schedule continuam fora da TASK248.

## Validação

O gate `scripts/github_task_248_jom_live_delta_queue_gate.py`:

- pina proveniência do run/artifact;
- recalcula o hash do resultado;
- verifica o contrato TASK247;
- prova fila exata de quatro itens, única e sem sobreposição ao baseline;
- valida HTTPS e host `ecrie.com.br`;
- falha fechado se qualquer efeito remoto da TASK248 for habilitado.

A suíte `tests/test_task_248_jom_live_delta_queue.py` cobre o caminho nominal e mutações de hash, duplicidade, host e efeitos remotos.
