# TASK 184 — bundle real JOM and planning products into the local knowledge pack

## Objective

Enrich the TASK 183 local Observatório knowledge pack with real, already-custodied JOM and planning/normative evidence, while refusing to synthesize an ACCOUNTING_LEDGER when the real TCE rows were not persisted.

TASK 184 is T0/OFFLINE. It does not mutate Drive, Sheets, stable serving or publication.

## JOM_EVENT_INDEX

Source:

- Google Sheets stable serving: BI_JORNAL_EVENTOS__SERVING
- source snapshot id: d126c0df36075f759b687c05
- canonical matrix SHA-256: d126c0df36075f759b687c0554a7dbbf5a4e4897384707a588ddc5033697f252
- schema fingerprint SHA-256: 60d52f60d58785a357a7ffddefbc7a8f138c45e331e7a5af88ecf9f58a1bf1f1
- validated rows: 303
- source columns: 24

The 303 serving rows are captured as a sanitized JSONL evidence fixture. Event identity remains unchanged.

Semantic facets are recomputed with the current TASK 171/TASK 174 classifier rather than copied from an older serving schema.

Observed event types:

- EDITAL: 81
- PORTARIA: 79
- DECRETO: 66
- ATA_REGISTRO_PRECOS: 32
- CONTRATO: 20
- LEI: 8
- CONVENIO: 8
- TERMO_ADITIVO_CONTRATO: 5
- RESOLUCAO: 4

The old serving is semantically sparse. Current recomputation identifies 76 procurement-contract layer events, 5 infrastructure events, only 2 explicit education-domain events and no PERSONNEL layer event.

This is intentionally reflected in question answerability. The presence of 79 Portarias does not by itself prove personnel coverage.

Publication never proves implementation, accounting identity or payment.

## PLANNING_DOCUMENT_INDEX

Five real documents are represented by seven evidence segments.

### PPA 2026–2029

Source:
- Lei 7.213/2025 and annexes
- Drive id: 1btfxebkUxkjjVIrdsTT_W6WOSSbGCEbq
- 105 pages
- SHA-256: 3e5deb53448c2e5eea56217a4e5d7f20f7fc3859eff7fcb93a7de7eb17011c1a

Primary evidence includes:
- page 18, Programa 2001, including the indicator for students in integral education and annual targets;
- page 3, Art. 4, which limits the meaning of PPA financial estimates.

Role: PRIMARY_SUBSTANTIVE.

### LDO 2026

Source:
- Lei 7.141/2025
- Drive id: 1EyoQ69aaPx7u4_w7xkSg7-oWCx_vkJlX
- 37 pages
- SHA-256: 6f28017bb61fe6dbd7db44e2306bd1a48f813d8d40411d87c130fba78fca2406

Primary evidence includes:
- page 4, Art. 8 rules on limitation of commitment and protected education-related allocations;
- page 7, Art. 12 cost/result control based on liquidated expenditure.

Role: PRIMARY_SUBSTANTIVE.

### LOA 2026

Source:
- Lei 7.223/2025 and annexes
- Drive id: 1zoG37Ao-h5GSzxkwlvwki8LDHzuD_DmT
- 466 pages
- SHA-256: bc4c8bf4b2b1e8f59e880318c37ec7f7fbd4357a85a8b46c97750444dbf01d4b

Page 1 confirms the law and its 2026 budget scope.

TASK 184 does not claim a full substantive parse of the 466-page annex set. Therefore its role is PRIMARY_METADATA_ONLY and quality is PARTIAL.

The historical V10 PPA→LOA bridge remains derived context and cannot substitute primary LOA annex coverage.

### CME 02/2021

Source:
- official primary PDF under custody
- Drive id: 1H5XVqisjFvXJcL7uVrJxadiufLBk0d8X
- SHA-256: 5d01a883bd5ec721b9a9a8b0a0f2c985eea8958da23de8d475d7c73d3109c07c

Page 7 records the CME deliberation establishing basic guidelines for gradual implementation of the municipal full-time education policy and governance instances.

Role: PRIMARY_NORMATIVE.

### Decreto 118/2024

Source:
- official municipal primary PDF
- Drive id: 1zJ-D42f4pBtzEQAUfsTigIROgqkW3Kzt
- SHA-256: a534b99711652d437e1672dbaf39b9f56fe8f35c042f3648ae8483187c909b60

Page 1 states that the municipal executive institutes the Policy of Integral Education in Full Time in Limeira's municipal school network.

Role: PRIMARY_NORMATIVE.

Normative publication does not prove implementation or result.

## ACCOUNTING_LEDGER

TASK 172 observed 39,780 TCE-SP Limeira expense rows during the bounded live batch.

However:
- the raw source payload was not persisted;
- no real row-level TCE/accounting dataset was found in Drive;
- the small TASK 173 test fixture is synthetic and is forbidden as a substitute.

Therefore ACCOUNTING_LEDGER remains NOT MATERIALIZED in TASK 184.

Accounting gain in this task is exactly zero by construction.

A real bundle requires a new exact source retrieval/persistence or a separately supplied persisted row set.

## Content-aware answerability

TASK 184 extends TASK 183 so bundled-product presence alone is insufficient.

Product signals can require:
- minimum rows;
- row-level semantic criteria;
- exact document-type/evidence-role combinations;
- exact source-family/evidence-role combinations.

Consequences:
- JOM_RADAR can become answerable from 303 validated events;
- PERSONNEL remains partial because current JOM semantics contain zero PERSONNEL-layer rows;
- procurement becomes partial rather than complete while ACCOUNTING_LEDGER is missing;
- PPA/LDO/LOA planning questions remain partial because LOA is metadata-only in this task;
- school norms remain partial when old JOM semantics are too sparse, even though primary CME/Decreto evidence exists;
- public-policy questions may improve only when both JOM and primary normative evidence satisfy their criteria.

The report calculates independent gain for JOM, independent gain for planning, final combined gain, and accounting gain separately.

## Final pack shape

Substantive products:
- SCHOOL_INDICATOR_SERIES
- FISCAL_SERIES
- JOM_EVENT_INDEX
- PLANNING_DOCUMENT_INDEX

QUERY_PRODUCT_CATALOG is rebuilt from those four snapshots.

ACCOUNTING_LEDGER is absent and explicitly blocked.

## Hard guards

- JOM publication != implementation
- semantic facet != policy/accounting identity
- PPA != execution
- LDO rule != observed execution
- LOA authorization != accounting execution
- LOA custody metadata != substantive annex coverage
- CME/Decreto normative act != implementation result
- synthetic accounting fixture != real ledger
- LLM cannot fill missing numeric evidence

## Remote effects

- new source network: 0
- Drive write: 0
- serving mutation: 0
- publication: 0
- schedule: 0
- recurrence: 0

## Next

After this merge, the largest unresolved blocker is real ACCOUNTING_LEDGER row persistence. A separate bounded task should retrieve or persist the exact TCE expense dataset under the already-proven TASK 172/TASK 173 schema before any accounting questions are promoted.
