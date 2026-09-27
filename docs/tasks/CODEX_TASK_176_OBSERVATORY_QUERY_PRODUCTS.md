# TASK 176 — materialize unified observatory query products from existing custody

## Objective

Make TASK 175 query plans executable against deterministic, standardized query products without introducing a second source-of-truth layer.

The products are derived query/cache projections. Bronze/Silver/Gold, provenance, source hashes and source-role semantics remain authoritative.

## Architecture

TASK 176 reuses the existing BI principle already proven in `13_BI`:

- immutable/create-only snapshot identity;
- stable serving is a separate later gate;
- a timestamp is metadata, never identity;
- content hashes are deterministic;
- derived products never replace source custody.

No Drive, Sheets, serving or publication action occurs in TASK 176.

## Query products

### SCHOOL_INDICATOR_SERIES

Grain: one school/network scope x period x indicator.

Carries:

- scope level/id;
- school/network identifiers when present;
- indicator id/name/value/unit;
- source family;
- context and caution;
- source SHA-256 and provenance;
- snapshot and generation metadata.

Primary use: Censo Escolar, IDEB, SAEB, SARESP and municipal indicator series.

### JOM_EVENT_INDEX

Grain: one structured Jornal Oficial event.

Combines:

- TASK 174 event structure;
- TASK 171 policy/evidence/financial/topic facets;
- exact source locator;
- administrative identifiers when explicitly extracted.

Publication never becomes implementation or payment evidence.

### ACCOUNTING_LEDGER

Grain: one canonical accounting observation.

Reuses TASK 173 semantics:

- COMMITMENT;
- LIQUIDATION;
- PAYMENT;
- REVERSAL;
- OTHER_REVIEW.

Function, subfunction, program, action, source, application, element and accounting keys remain independent dimensions.

### FISCAL_SERIES

Grain: entity x period x metric x source family.

Target families:

- SICONFI/STN;
- SIOPE;
- FUNDEB;
- RREO;
- RGF;
- MDE.

The product carries explicit stage semantics so budget authorization is not confused with execution.

### PLANNING_DOCUMENT_INDEX

Grain: one documentary evidence segment.

Target sources:

- PPA;
- LDO;
- LOA;
- CME;
- municipal legislation;
- SIAVE.

Every document record must retain an exact locator. A documentary snippet without locator cannot be used as evidence.

### QUERY_PRODUCT_CATALOG

Grain: one product snapshot.

Records:

- product/schema;
- snapshot id;
- row count;
- coverage domains;
- source families;
- readiness;
- content SHA-256.

The catalog reports availability; it is not itself substantive truth.

## Deterministic materialization

`generated_at` must be supplied by the caller. The builder never calls the current clock.

Rows are normalized and ordered by the product primary key.

The canonical row matrix produces:

- full `content_sha256`;
- `snapshot_id = content_sha256[:24]`.

Changing row order alone does not change the snapshot.

## TASK 175 integration

The query API consumes `UNIFIED_OBSERVATORY_QUERY_PLAN_V1`.

Product selection begins with the canonical domain-product route and is automatically expanded when TASK 175 scenarios add source families.

Example: a school-transport question adds Censo Escolar and SIOPE to the plan. TASK 176 therefore adds SCHOOL_INDICATOR_SERIES and FISCAL_SERIES to the JOM/accounting products without hard-coding a second transport-specific router.

The evidence output is:

`OBSERVATORY_EVIDENCE_PACKET_V1`.

It contains:

- structured numeric records;
- documentary records with locators;
- catalog records;
- source/product gaps;
- upstream TASK 175 maturity gaps;
- snapshot ids;
- join semantics;
- answer contract.

## Coverage

Coverage is reported for all 15 observatory domains.

A product counts as available for a domain only when it contains at least one source family accepted by the TASK 175 plan for that domain. A generic materialized table is not enough.

This means a current local fixture bundle can truthfully show a gap, such as TERRITORY_CONTEXT when no IBGE/official-territory rows are present.

## Join guards

Strong:

- exact empenho;
- exact source expense identifier;
- exact contract/process id;
- exact PNCP control id;
- explicit CNPJ where the source exposes it.

Contextual:

- year;
- program;
- action;
- funding source;
- application;
- school/unit.

Weak only:

- amount;
- date proximity;
- object/history text;
- semantic similarity.

Weak evidence never creates identity.

## Acceptance scenarios

Offline tests cover:

- learning/IDEB;
- school reform;
- school transport;
- school meals;
- education financing;
- school norms;
- accounting stage preservation;
- product catalog;
- explicit missing-product gaps;
- all 15 domains.

## Remote effects

TASK 176 authorizes:

- network: 0;
- Drive reads/writes: 0;
- serving mutation: 0;
- publication: 0;
- schedule: 0;
- recurrence: 0.

A later task may materialize approved snapshots into stable serving tables only under a separate gate.
