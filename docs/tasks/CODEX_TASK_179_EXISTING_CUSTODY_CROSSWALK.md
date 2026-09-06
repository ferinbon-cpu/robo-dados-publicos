# TASK 179 — existing-custody corpus registry and product-ingestion crosswalk

## Objective

Exploit the substantial corpus already owned by the user before collecting more external data.

TASK 179 is T0/OFFLINE only. It does not copy full corpus bodies into the repository and does not mutate Drive, Sheets, serving or source systems.

## Existing custody mapped

### Indicators collection

The synchronized 2026 publication triad is treated as a rich documentary/technical source:

- Volume I V07 — network diagnosis and integrated analyses;
- Volume II V06 — school-by-school compendium for 69 active 2025 units;
- Volume III V07 — technical tables, series, QA, provenance and reproduction rules.

The publication itself identifies Base Mestra Limeira V05 as canonical and CAMADA_ANALITICA_V06_40_ESCOLAS_V08 as an auditable operational extension.

Because those structured base files are referenced but are not currently runtime-accessible, the publication is ready for document indexing and partial structured extraction, but not for full canonical school-row materialization.

School numeric precedence is therefore:

Base Mestra V05 -> CAMADA_ANALITICA V08 -> Volume III technical tables -> Volume II school profiles -> Volume I narrative.

Volume I is explanatory context, not a replacement numeric database. The preferred school identity key is Inep code. Not applicable, missing and zero remain different states.

### Normative brain

The discovered Cérebro Normativo de Gestão Escolar is ready for document indexing and operational topic routing.

Its hierarchy is preserved: official normative document -> extracted/document corpus -> normative synthesis -> free interpretation. The brain never becomes legal proof by itself. Historical/revoked material remains contextual.

### Fiscal-budget brain

MD_01.2 is treated as a consolidated fiscal-budget technical dossier plus documentary annex. It is ready for document indexing and partial structured extraction of explicit tables when period, metric, source and semantic role are retained.

Fiscal precedence remains: official structured TCE/SIOPE/SICONFI/FUNDEB -> exact underlying document/corpus -> MD_01.2 tables -> MD_01.2 interpretation -> MD_00 methodology.

MD_01.3B is referenced by MD_00 as a deduplicated/transcribed corpus of 194 unique documents, but the file itself is not currently runtime-accessible. It is therefore a handoff target.

### Methodology/reference documents

MD_00 V17 and MD_00.1 V02 are governance/methodological inputs. They do not become empirical query evidence.

## Mapping into TASK 176 products

- SCHOOL_INDICATOR_SERIES: READY_PARTIAL_ONLY; full canonical row materialization requires Base Mestra V05; CAMADA_ANALITICA V08 is the preferred second handoff.
- PLANNING_DOCUMENT_INDEX: READY_FROM_EXISTING_CUSTODY; normative brain and MD_01.2 can populate document-index records; MD_01.3B would enrich exact locators.
- FISCAL_SERIES: READY_PARTIAL_ONLY; MD_01.2 may contribute explicit table rows, while official structured source precedence remains unchanged.
- JOM_EVENT_INDEX: NO_NEW_CUSTODY_INPUT_REQUIRED; normative brain may enrich routing/topics, not event identity.
- ACCOUNTING_LEDGER: NO_NEW_CUSTODY_INPUT_REQUIRED; TCE remains primary and MD fiscal content is context only.
- QUERY_PRODUCT_CATALOG: READY_FROM_EXISTING_CUSTODY.

## Coverage

The crosswalk maps existing custody or already-operational system products to 14 of the 15 observatory domains. The only explicit gap is TERRITORY_CONTEXT. This is intentional: school context indicators are not silently promoted into a general territorial-statistics source.

## Handoff priority

1. Base Mestra Limeira V05
2. CAMADA_ANALITICA_V06_40_ESCOLAS_V08
3. MD_01.3B corpus
4. a newer Cérebro Normativo version if one exists beyond the currently discovered v0.1

The first handoff gives the largest immediate product gain because it unlocks full SCHOOL_INDICATOR_SERIES materialization across the 69-unit network.

## Effect on TASK 178

TASK 178 remains open but is noncanonical for now. The project should map and ingest existing custody before using the first remote OBS serving proof.

## Remote effects

- network: 0
- Drive write: 0
- serving: 0
- publication: 0
- schedule: 0
- recurrence: 0
