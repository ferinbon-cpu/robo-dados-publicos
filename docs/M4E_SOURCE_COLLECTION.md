# M4E — Coleta de fontes públicas

## Objetivo
Adicionar aquisição automática sem misturar download com transformação analítica.

## Contrato do inventário
Arquivo JSON com `version` e `sources`. Cada fonte precisa de:
- `source_id` único;
- URL HTTPS;
- `logical_key`;
- `file_name`;
- `enabled`;
- tipos MIME esperados;
- cadência e observações opcionais.

O modelo está em `config/sources.example.json` e nasce desabilitado para impedir coleta de URL inventada ou não validada.

## Fluxo
1. validar inventário;
2. recuperar `ETag` / `Last-Modified` do estado;
3. fazer GET condicional;
4. se 304: registrar `NOT_MODIFIED`;
5. se payload novo: calcular SHA-256;
6. se hash já conhecido: `DUPLICATE_HASH`;
7. se tipo MIME divergir: enviar à quarentena e emitir STOP;
8. se contrato passar: gravar cópia imutável em Bronze e registrar proveniência.

## Comandos

```bash
python3 main.py sources-validate --source-config config/sources.example.json
```

O `run` só coleta quando um inventário é explicitamente informado:

```bash
python3 main.py run --auth oauth-env --source-config config/sources.json
```

O primeiro gate controlado usou `config/sources.jornal_oficial_7310_gate.json`. Esse inventário contém uma única edição histórica validada e não autoriza coleta recorrente. O gate concluiu em 2026-08-24 com `PASS_GITHUB_SOURCE_COLLECTION_GATE`; a opção `confirm_source_collection` foi então retirada do workflow ativo para impedir repetição acidental. Consulte `docs/M4E_FIRST_SOURCE_COLLECTION_EVIDENCE_2026-08-24.md`.

Para validar planejamento sem rede nem escrita:

```bash
python3 main.py run --auth oauth-env --source-config config/sources.json --dry-run-sources --no-persist --no-log
```

## Regra de ativação
Uma fonte oficial só pode ser marcada `enabled: true` depois que URL, formato, comportamento HTTP e tipo MIME forem observados em teste real. Páginas interativas que exigem parâmetros, sessão ou POST devem receber adaptador específico; não devem ser tratadas como arquivo direto por aproximação.

Para artefatos históricos imutáveis, `expected_sha256` e `expected_bytes` fecham adicionalmente o contrato. Divergência envia o arquivo observado à quarentena e interrompe a coleta.

## Jornal Oficial — separação descoberta/processamento
A descoberta do índice (`journal-discover`) e o processamento de uma edição (`journal-process`) são etapas distintas. O índice nunca autoriza, sozinho, uma rota de produção: a URL do documento e o tipo MIME precisam ser observados ao vivo. Depois da aquisição oficial, a 0.5.3 processa o PDF sem rede, preserva Bronze por hash e produz apenas derivados minimizados.


## M4E.4 — fila de reconciliação

Eventos Gold do Jornal Oficial agora geram tarefas determinísticas para cadastro municipal de contratos, TCESP, TDA, licitações e SIAVE. A fila pode ser persistida no SQLite e é idempotente por `task_id`. Ela não afirma identidade: cada resolver futuro deve coletar evidência e reaplicar os gates V16/V17. Consulte `docs/RECONCILIATION_QUEUE.md`.
