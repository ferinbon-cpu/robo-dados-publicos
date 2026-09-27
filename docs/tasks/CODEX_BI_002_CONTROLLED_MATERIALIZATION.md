# BI-002 — materialização controlada de `13_BI` (implementação offline)

## Limite e resultado

BI-002 implementa exclusivamente o planner `T0_OFFLINE_IMPLEMENTATION_REVIEW`. O resultado esperado é `PASS_BI_002_CONTROLLED_MATERIALIZATION_IMPLEMENTATION_OFFLINE`: nenhum acesso à rede de fonte, Drive ou Looker; nenhuma pasta, Sheet ou publicação; nenhum schedule ou recorrência. `13_BI` é somente um nome futuro validado, não uma pasta criada. BI continua projeção derivada, nunca fonte da verdade.

Permanecem inalterados: release `0.7.0 = ACTIVE` e `0.8.0 = CANDIDATE`; B1/B2/B3 pendentes; TASK 023 intacta; TASK 024 não autorizada; SIOPE fechado em 2016–2024 (`2016=P1`, demais anos `P6`, sem Gold 2025); e `MATCH_CANDIDATE != financial_identity`.

## Estrutura e contratos futuros

O contrato planeja `13_BI/{00_MANIFESTS,01_SNAPSHOTS,02_SERVING}`. Em `01_SNAPSHOTS`, há uma subpasta conhecida para cada um dos seis datasets BI-001. Cada snapshot futuro será create-only, imutável e nomeado `<DATASET_ID>__snapshot__<SNAPSHOT_ID>.xlsx`; seu manifest terá o mesmo prefixo e sufixo `__manifest.json`. `SNAPSHOT_ID` deriva do SHA-256 da matriz canônica tipada, não de relógio ou aleatoriedade.

O planner valida primeiro pelo BI-001, recusa campo desconhecido/privado e PK duplicada, ordena apenas pela PK e projeta colunas na ordem contratual. A matriz JSON tipada preserva null, booleano, inteiro, número e texto. XLSX local tem uma aba, um header, tipos tabulares, zero fórmulas/merge/subtotais; propriedades e metadata ZIP são pinadas. O hash da matriz é a identidade semântica principal e `xlsx_sha256` registra a identidade física reproduzível.

## Gates T2 e T3, colisão e rollback

Uma futura criação de estrutura, snapshots e manifests é `T2_CREATE_ONLY` e requer autorização explícita do owner pinada ao SHA revisado. Antes da primeira escrita, o preflight exigirá raiz exatamente `13_BI`, allowlist/nome/schema/hash/manifest exatos, ausência de colisão e autorização T2. Qualquer objeto remoto com nome igual para em `STOP_BI_REMOTE_COLLISION_REQUIRES_READBACK`; nunca há overwrite, replace, delete ou renomeação automática.

A serving Sheet estável por dataset (`<DATASET_ID>__SERVING`) é fronteira distinta `T3_MUTATING_OR_PUBLICATION`, `GOVERNANCE_DECISION_REQUIRED`. Autorização T2 jamais a autoriza. Uma futura implementação deverá pinar snapshot e hash, provar schema, fazer escrita bounded e readback integral de dimensões, header, valores/tipos, PK e hash. Divergência será `STOP_BI_SERVING_READBACK_MISMATCH`, sem cleanup, retry, nova sobrescrita ou fallback. Looker exige autorização ainda explícita e permanece bloqueado aqui.

Rollback remoto não foi implementado. A política é preservar todo snapshot; eventual restauração da serving usa snapshot anterior validado sob nova autorização, nunca altera evidência, apaga snapshot, faz cleanup automático ou modifica Gold.

## Evidência e fixtures

As fixtures dos seis datasets são `SYNTHETIC_SANITIZED_TEST_ONLY`, não evidência operacional. O gate comprova contrato, tiers, determinismo, manifests, efeitos remotos zero e limites de release/task. A próxima ação após auditoria e merge é exclusivamente uma decisão do owner sobre uma primeira materialização create-only; este patch não concede tal autorização.
