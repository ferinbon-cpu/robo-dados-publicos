# M4E — evidência do primeiro processamento controlado — 2026-08-24

## Resultado

- release durante o gate: `0.6.1 CANDIDATE`;
- run: `32761758504`;
- job: `97541993609`;
- commit: `f9bb9afad3d519376157f5acbdc4dc2cd18bec15`;
- duração total: 46 segundos;
- status: `PASS_GITHUB_JOURNAL_PROCESSING_GATE`;
- verificações: 16/16 PASS;
- identificadores remotos: não publicados;
- valores de secrets: não publicados.

## Contrato comprovado

- fonte: `LIMEIRA_JORNAL_OFICIAL_EDICAO_7310`;
- hash e tamanho do PDF: verificados contra a auditoria privada do Drive;
- extrator: `pypdf==6.10.0`;
- páginas: 76;
- caracteres extraídos: 195.540;
- eventos Gold: 53;
- chunks RAG: 148;
- tarefas de reconciliação: 68;
- origem pública chamada: não;
- estado remoto: substituído;
- log append-only: criado.

## Derivados sanitizados

- `edition_manifest.json`: criado;
- `pages_silver.jsonl`: criado;
- `events_gold.jsonl`: criado;
- `reconciliation_tasks.jsonl`: criado;
- `chunks_rag.jsonl`: criado.

Hashes, tamanhos e IDs privados permanecem apenas na auditoria do Drive e nos logs privados do workflow.

## Travas após o PASS

- repetição da coleta: desabilitada;
- repetição do processamento: desabilitada;
- agenda e recorrência: desabilitadas;
- execução automática dos resolvers: desabilitada;
- promoção automática de identidade financeira: proibida;
- TDA Limeira: bloqueado sem endpoint/export público comprovado.
