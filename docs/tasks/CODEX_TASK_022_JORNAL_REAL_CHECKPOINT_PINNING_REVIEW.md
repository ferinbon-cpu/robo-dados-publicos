# TASK 022 — pinning offline do checkpoint real do Jornal Oficial

## Resultado: PASS com checkpoint real pinado

A TASK 021 ficou corretamente em `STOP_REAL_CHECKPOINT_NOT_PINNED` no momento do seu desenho: a closure resumida da TASK 018 prova 12 itens descobertos/processados, mas não expõe as cinco propriedades de identidade por item. `count=12` sozinho não permite detectar desaparecimento, drift ou duplicidade.

Na revisão independente do PR #292, o artifact histórico sanitizado já produzido pela TASK 018 foi lido em modo histórico read-only: `task-018-sanitized-operational-evidence`, artifact `9758450652`, run `33392616951`. O digest do ZIP foi recomputado e coincidiu exatamente com a closure: `sha256:f4eacabeed66e3b2ca0801140efa3a495e5a9e294cfaa61953cb2dc27e6628cd`. O membro `operational_result.json` tem 349383 bytes e SHA-256 `aad99f2644b6580b1734ab75e02c969095c24c95c3e393f1f3f096a72e19a5bd`.

Esse `operational_result.json` contém diretamente 12 entradas em `items`, cada uma com `edition`, `publication_date`, `url`, `source_id` e `logical_key`. Não houve consulta ao site do Jornal Oficial, Drive, PDFs ou nova execução. Para o snapshot canônico, `url` foi apenas renomeado para `document_url`; os demais quatro campos foram copiados literalmente.

## Checkpoint canônico

Foi criado `docs/evidence/TASK_018_JORNAL_COMPLETED_CANONICAL_CHECKPOINT_0.8.0.json` com exatamente as 12 identidades reais, edições 7304–7315, em ordem determinística. A sequência não foi presumida: cada edição e cada data/URL foram observadas diretamente no artifact histórico.

A serialização canônica considera somente as cinco propriedades de identidade, com JSON UTF-8, `sort_keys=true` e separadores compactos. Resultado: 2797 bytes e SHA-256 `64e78c27a2c233468d76bc94c5719a35ed68ff7455cfac36d958d922c4ece5db`.

O validador exige 12 itens, `source_id=LIMEIRA_JO_{edition:05d}`, `logical_key=limeira/jornal_oficial/edicao/{edition}`, data ISO, HTTPS em `ecrie.com.br`, ausência de duplicidades, proveniência real e integridade exata.

## Limites preservados

A TASK 022 permanece estritamente `T0_OFFLINE`. A leitura do artifact histórico é evidência já produzida e não é nova coleta da fonte pública. Os efeitos operacionais desta task permanecem zero: source network, Drive reads/writes, source document downloads, processamento, publicação, workflow dispatch, schedule, recurrence e future batch.

TASK 018 continua `CLOSED_SUCCESS_AUTHORIZATION_CONSUMED`, não rerodável. TASK 021 permanece como evidência histórica correta do estado de desenho anterior; ela não é retroativamente alterada.

O resultado desta TASK é `PASS_REAL_CHECKPOINT_PINNED_OFFLINE` / `COMPLETE_PINNED`. Isso **não** autoriza a prova incremental live. Qualquer próxima prova live bounded exige task/implementação e autorização separadas, pinadas a um SHA exato do owner.
