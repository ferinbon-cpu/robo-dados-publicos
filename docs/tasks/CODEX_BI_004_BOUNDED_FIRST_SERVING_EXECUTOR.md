# BI-004 — bounded first-serving executor

## Objetivo

Implementar e provar offline o executor bounded da primeira stable serving sheet, limitado a `BI_SIOPE_SERIES__SERVING`, derivada exclusivamente do snapshot BI-002 já materializado e validado.

## Base e classificação

- base obrigatória: `5b177c162a143e9265cec7492ab49cefda89c789`
- implementação: `T0_OFFLINE_IMPLEMENTATION_REVIEW`
- execução remota por este PR: **não autorizada**
- autorização T3 ativa embutida: **nenhuma**
- Looker: **fora de escopo e não autorizado**

## Snapshot pinado

- dataset: `BI_SIOPE_SERIES`
- snapshot_id: `1caaadc1d876a265817ad5d0`
- canonical_matrix_sha256: `1caaadc1d876a265817ad5d0c212fe4348ecbecad9f923f57e7b180220d1b380`
- schema_fingerprint_sha256: `26506e5e4680447b17d0f7c096e176ad55f763742a7350d109dae9fd988bdbf9`
- row_count: `72`
- serving: `13_BI/02_SERVING/BI_SIOPE_SERIES__SERVING`
- abas obrigatórias: `DATA`, `META`

## Fronteira do executor

O executor não importa cliente Google, não contém credenciais e não executa rede por conta própria. Toda interação remota futura deve entrar por transporte injetado e somente após validação de uma autorização T3 nova, explícita e pinada ao SHA exato da implementação auditada.

A primeira prova live fica limitada a dois estados:

1. `CREATE_INITIAL_SERVING`: nome remoto ausente; criar uma única planilha, escrever uma única atualização lógica `RAW`, reler semanticamente e, somente após readback válido, criar um manifesto create-only em `13_BI/00_MANIFESTS`.
2. `NO_CHANGE_IDEMPOTENT`: serving já existe e é semanticamente idêntica; apenas releitura e nenhum write.

Se a serving existente for válida porém diferente e o planner pedir `REPLACE_SERVING_FROM_NEW_SNAPSHOT`, a primeira prova deve parar. Replace não está autorizado nesta etapa.

## Limites obrigatórios

- discovery read: exatamente 1
- spreadsheet create: no máximo 1
- logical batch update: no máximo 1
- semantic readback: no máximo 1
- generation manifest create-only: no máximo 1 e apenas após create + readback válido
- retries: 0
- delete: 0
- cleanup automático: 0
- Looker publication: 0
- recorrência: 0
- schedule: 0

Falha ou ambiguidade após a criação inicial não autoriza retry, delete ou cleanup. O executor deve parar para decisão humana, preservando o estado remoto para auditoria.

## Contrato da futura T3

A futura autorização deverá usar:

- repository: `ferinbon-cpu/robo-dados-publicos`
- tier: `T3_MUTATING_OR_PUBLICATION`
- drive_root: `13_BI`
- parent_path: `13_BI/02_SERVING`
- task: `BI_004_FIRST_BOUNDED_SERVING_PROOF`
- scope: `BI_SIOPE_SERIES_CREATE_OR_IDEMPOTENT_READBACK_ONLY`
- selected_datasets: somente `BI_SIOPE_SERIES`
- selected_snapshots: somente o snapshot pinado acima
- `serving_mutation_authorized=true`
- `looker_publication_authorized=false`
- `first_live_proof_only=true`
- `replace_existing_authorized=false`
- `retry_authorized=false`
- `cleanup_authorized=false`
- `generation_manifest_create_only_authorized=true`
- `consumed=false`
- `test_only=false`
- `implementation_sha`: SHA-40 exato do head auditado/mesclado que será autorizado.

Autorizações T2 e T3 consumidas anteriormente não podem ser reutilizadas.

## Critério de aprovação offline

O gate BI-004 deve provar: pin exato ao snapshot SIOPE real, ausência de cliente remoto embutido, operação bounded, autorização SHA/snapshot/scope-bound, `REPLACE` bloqueado no primeiro live, serializer `RAW` herdado da BI-003, readback semântico obrigatório, manifesto create-only somente após sucesso e zero retry/delete/cleanup/Looker.
