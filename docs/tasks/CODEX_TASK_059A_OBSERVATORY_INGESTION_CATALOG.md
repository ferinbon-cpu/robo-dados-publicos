# TASK 059A — Observatory-wide ingestion catalog

## Objective

Correct the scope of the Drive Ingestion Controller introduced by TASK 059 so it reflects the established architecture of the **Observatório de Dados Públicos Municipais de Limeira/SP**.

Education/SIOPE and the current EITI/F01 investigation are modules/use cases. They are not the global ingestion boundary.

## Scope

T0/offline only. Preserve `config/drive_ingestion_controller.v1.json` as historical evidence and add a v2 catalog.

The v2 catalog must cover the existing education/budget families and explicitly add municipal families already present in the architecture:

- Jornal Oficial;
- municipal contracts/aditivos/convenios/atas;
- procurement/licitações/editais;
- municipal legislation and administrative acts;
- CME documents;
- TCE-SP expense artifacts;
- TDA/Transparência de Limeira artifacts;
- SIAVE/Câmara artifacts.

## Maturity-aware routing

Recognition by title is not proof that a parser/schema is mature.

- `AUTO_INGEST`: routing eligibility only for mature/recurring families. It does not read content and does not promote a layer.
- `REVIEW`: known family requiring source-specific adapter/schema selection or human review.
- `QUARANTINE`: unknown, malformed, out-of-scope, or policy-violating input.

For v2, Jornal Oficial and established recurring education/fiscal data families may be `AUTO_INGEST`-eligible. Contracts, procurement, legislation/CME, TCE, TDA, SIAVE, PPA/LDO/LOA and generic budget execution remain `REVIEW` first.

A title matching more than one family must return `REVIEW` with `MULTIPLE_FAMILY_MATCHES`; no precedence may silently collapse a multi-role artifact into one family.

## Existing architecture to reuse

Do not create parallel source/reconciliation logic. The catalog must reference and remain compatible with:

- `config/sources.jornal_oficial_7310_gate.json`;
- `config/reconciliation_targets.json`;
- `config/operational_bootstrap.full.v1.json`;
- the shared Drive/manual-ingest integrity pipeline.

## EITI boundary

The controller must encode that EITI is an `ANALYTIC_USE_CASE_NOT_GLOBAL_INGESTION_FILTER`.

TASK 059A must not alter F01/EITI evidence status, calculate new financial identity, or use EITI terminology as a global inclusion/exclusion condition for files.

## Hard boundaries

TASK 059A authorizes none of the following:

- source network access;
- Drive source-content read;
- Drive write;
- OCR;
- Bronze/Silver/Gold writes;
- serving/publication;
- live workflow dispatch;
- recurrence/schedule.

## Expected result

`PASS_TASK059A_OBSERVATORY_WIDE_INGESTION_CATALOG_OFFLINE_READY`

The next gate is TASK 060: one explicitly scoped Drive folder, metadata-only, using the v2 catalog. Any content hydration is fail-closed and no content ingestion is authorized by TASK 059A.
