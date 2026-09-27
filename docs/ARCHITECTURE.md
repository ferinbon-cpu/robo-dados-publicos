# Arquitetura do Software V01

```text
CLI / Scheduler
      ↓
Orchestration Engine
      ↓
Ingest Gates → Schema Adapters → Silver → Gold
      ↓             ↓              ↓       ↓
  State/Hash     Quarantine       SQL    Evidence Graph
      ↓
QA / Regression Gates
      ↓
Storage remoto (M4)
      ↓
IA semântica opcional (M5)
```

## Regra estrutural

A IA será uma camada auxiliar. O núcleo de integridade, cálculo, estado, hash, schema, dependências e QA é determinístico.
