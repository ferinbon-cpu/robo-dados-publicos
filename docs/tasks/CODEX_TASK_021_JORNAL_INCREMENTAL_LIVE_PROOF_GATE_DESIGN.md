# TASK 021 — desenho offline do gate de prova incremental live

## Escopo e base

A TASK 020 provou, com planner puro T0, `NO_CHANGE_IDEMPOTENT`, delta
`NEW_ITEMS_APPEND_ONLY` estritamente monotônico e os STOPs para checkpoint ou
discovery incompletos, duplicidade, desaparecimento, drift, regressão, excesso do
bound e identidade inválida. Sua saída continua sendo somente proposta e o
checkpoint só poderá avançar após todo downstream e readback final.

Uma prova live é separada porque rede de fonte muda o tier e requer autorização
do owner. A TASK 021 não realiza GET, não oferece transport e não cria workflow
live. O trust boundary futuro é: carregar e validar o checkpoint completo antes
da rede; fazer apenas discovery bounded read-only; exigir `PASS_DISCOVERY`;
normalizar as cinco propriedades canônicas; chamar o planner TASK 020; emitir uma
decisão; parar antes de download ou downstream.

## Checkpoint real: lacuna explícita

A closure sanitizada da TASK 018 registra 12 itens concluídos, porém não contém
as identidades individuais (`edition`, `publication_date`, `document_url`,
`source_id`, `logical_key`). Logo, ela não permite reconstruir auditavelmente o
checkpoint. A fonte canônica futura terá de ser um snapshot sanitizado,
versionado, com integridade pinada, status `COMPLETE`, as exatamente 12
identidades e proveniência para o run concluído da TASK 018. Até uma tarefa
separada piná-lo, o estado operacional é `STOP_REAL_CHECKPOINT_NOT_PINNED`.
`tests/fixtures/task_021_synthetic_checkpoint.json` prova somente o desenho e
nunca pode ser fallback ou autoridade operacional. Nenhum Drive foi consultado.

## Resultados e bloqueios

* `NO_CHANGE_IDEMPOTENT`: sucesso idempotente, zero GET de documento, Drive,
  processamento, publicação ou avanço de checkpoint.
* `NEW_ITEMS_APPEND_ONLY`: torna-se
  `NEW_ITEMS_DETECTED_EXECUTION_NOT_AUTHORIZED`; a lista pode ser informada, mas
  PDF, Bronze, processamento, reconciliação, publicação e checkpoint ficam
  bloqueados até nova autorização.
* `STOP_CHECKPOINT_NOT_COMPLETE`, `STOP_DISCOVERY_NOT_COMPLETE`,
  `STOP_DUPLICATE_EDITION`, `STOP_KNOWN_ITEM_MISSING`,
  `STOP_KNOWN_ITEM_DRIFT`, `STOP_NON_MONOTONIC_NEW_ITEM`,
  `STOP_NEW_ITEM_BOUND_EXCEEDED` e `STOP_BAD_ITEM_CONTRACT` são herdados sem
  enfraquecimento da TASK 020.
* O boundary acrescenta `STOP_REAL_CHECKPOINT_NOT_PINNED`,
  `STOP_LIVE_PROOF_NOT_AUTHORIZED`, `STOP_TASK_018_AUTHORIZATION_REUSE`,
  `STOP_TASK_021_DESIGN_ONLY` e `STOP_DOWNSTREAM_EXECUTION_NOT_AUTHORIZED`.

## Limites da prova futura

Antes de qualquer rede deverão estar fixados: somente HTTPS e
`www.limeira.sp.gov.br`; no máximo 8 páginas e 8 GETs; timeout de 20 segundos;
2.000.000 bytes por página; zero retry; zero redirect fora do host; nenhuma
paginação além do teto; `PASS_DISCOVERY`; e até 8 itens novos, preservando o
bound da TASK 020. Discovery não inclui download de PDF, Drive, T2 ou T3.

Uma autorização nova do owner, separada da autorização consumida da TASK 018,
deverá ser pinada ao SHA exato da implementação futura. TASK 021 não autoriza
`workflow_dispatch`, future batch, schedule, cron ou recurrence. Uma prova
bounded one-shot apenas decide; não seleciona cadência nem ativa recorrência.
