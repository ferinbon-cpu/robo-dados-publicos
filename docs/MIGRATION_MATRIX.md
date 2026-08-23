# Matriz V01–V17 → Software V01

| Legado | Capacidade | Módulo atual |
|---|---|---|
| V03–V04 | hash, dedupe, série SIOPE, totais oficiais | `storage.hashing`, `ingest.gates`, `analytics.siope` |
| V05 | schema drift TNR | `schema.tnr` |
| V06–V07 | RAG/SQL/HYBRID | `router.rules` (núcleo); RAG completo fica para M5 |
| V08 | grafo de evidências | `evidence.graph` |
| V09 | resposta controlada | `answers.contracts` |
| V10–V11 | blockers e arquitetura madura | contratos + regressão |
| V12–V13 | Drive-first / Inbox | `storage.drive_rest`, `ingest.gates`, `orchestration.cloud_runner` |
| V14 | incrementalidade | `incremental.planner` |
| V15 | temporalidade | `temporal.rules` |
| V16 | identidade de política | `policy.identity` |
| V17 | identidade contábil / execução | `accounting.identity` |

## O que deliberadamente ainda não foi consolidado

- adaptadores oficiais completos para cada fonte pública;
- parser PDF robusto/OCR;
- índice RAG completo;
- chamada a modelo de IA;
- execução agendada ao vivo validada no GitHub Actions;
- notificações.

O cliente Drive, runtime persistente e infraestrutura genérica de coleta HTTP já existem. Fontes oficiais só serão ativadas após teste real do contrato, e os itens restantes não devem ser simulados como prontos.
