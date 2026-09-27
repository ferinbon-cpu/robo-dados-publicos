# SIOPE historical regime discovery — TASK 001

## Scope and decision

This deliverable is strictly `T0_OFFLINE`. It reconciles only versioned evidence and authorizes no source GET, Drive access, secret use, persistence, publication, retry, pagination, recurrence, schedule, or future batch. The machine-readable regime map is `config/siope_historical_regimes.v1.json`; the corresponding evidence matrix is `config/siope_historical_evidence_matrix.v1.json`. Unknown evidence remains `UNKNOWN` or `CANDIDATE`.

## Reconciled result

| Years | Regime conclusion | Resource/schema conclusion | Gold conclusion |
|---|---|---|---|
| 2000–2004 | `CANDIDATE_EXTERNAL_ONLY`; P1 is only an external hint | Unknown | All 8 unproven |
| 2005–2007 | `LEGACY_DOCUMENTED_CANDIDATE`; candidate P1 | Manuals/downloads concern the legacy system; current resource/schema unknown | All 8 unproven; adapter likely required |
| 2008–2015 | Officially documented annual P1 | Official analytical families do not prove the current `Dados_Gerais_Siope` 52-field resource | All 8 are only mathematically potential if fields and semantics are later proven |
| 2016 | Internally proven P1 | Current resource/schema proven | 8 arithmetic metrics proven |
| 2017–2024 | Internally proven P6 annual consolidation | Current resource/schema proven | 8 arithmetic metrics proven |
| 2025 | `UNPROVEN_RECENT`; period and closure unknown | Unknown | All 8 unproven |
| 2026 | `UNPROVEN_CURRENT_YEAR`; current/provisional and not closed | Unknown | All 8 unproven |

The period boundary is a regression invariant: `2016=P1` and `2017=P6`; the inverse assignments must STOP. Similar field names across regimes do not establish semantic comparability, and none of the arithmetic metrics is a conclusion about MDE, Fundeb, fiscal compliance, or causality.

## Evidence reconciliation

The evidence order is official primary material, internally pinned proof, then independent implementation. The FNDE 2019 dictionary and analytical-data catalog document annual P1 for 2008–2016, but do not prove that the present Olinda resource and its 52 fields exist unchanged for 2008–2015. The FNDE manuals and historical downloads identify 2005–2007 as a documented legacy area requiring manual/release-note reconciliation. The independent `tuffyli/RA_work` rule (`ano <= 2016` → P1 and loop `2000:2024`) corroborates the boundary but cannot promote 2000–2007.

The detailed, machine-validated matrix records the official document, surface/family, period confidence, field confidence, conditional metric calculability, semantic-break risk, and adapter/correction need for every range. Absence is recorded rather than converted into equivalence.

## Future live gates (design only; not authorized here)

1. Open a separate, bounded read-only discovery for **2025** with no persistence or publication.
2. Prove Limeira exists and enumerate the available periods without assuming P6.
3. Pin the resource schema and the fields needed by each of the 8 arithmetic metrics; STOP on missing, duplicate, alias, type, or semantic drift.
4. Establish annual closure independently before deciding whether 2025 can join the closed series.
5. Use a separate gate for **2026**, explicitly retaining current/provisional semantics and excluding it from the closed series.
6. Sample a small, explicitly bounded subset of 2008–2015 read-only to prove resource/schema and assess metric comparability before any batch design.
7. Only after that evidence, design year blocks and any required adapters for 2008–2015.
8. Give 2005–2007 a separate legacy gate after manuals, installers, downloads, release notes, period, schema, and semantic changes are reconciled.
9. Leave 2000–2004 blocked unless official evidence is pinned in addition to the external implementation.

Every future gate needs separate human/policy authorization. TASK 001 does not authorize live execution, T2/T3, or batch expansion.
