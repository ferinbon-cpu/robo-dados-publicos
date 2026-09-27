# TASK 053 — Metadata-safe candidate inventory redesign

## Objective

Redesign the existing-custody granular-source inventory so a future gate can discover and rank Drive candidates without hydrating or reading source content.

## Upstream condition

TASK 052 ended fail-closed with `STOP_TASK052_SOURCE_CONTENT_READ_BOUNDARY_BREACHED_NO_PROMOTION` after a metadata-resolution fetch unexpectedly hydrated source text. The candidate `05 - Maio_despesa.pdf` (`1PTAnH-LL_8fvS7TsVuHSci5dBDKFLQTS`) is retained only as a metadata-title seed. No hydrated source text from TASK 052 may be reused.

## Authorized scope for TASK 053

T0/offline redesign only.

- no Drive metadata search execution;
- no Drive list execution;
- no Drive fetch;
- no source-content read;
- no file download;
- no OCR;
- no public-source network;
- no Drive write;
- no Bronze/Silver/Gold write;
- no serving or publication.

## Redesigned future inventory boundary

A future execution gate may use only metadata-safe surfaces equivalent to:

- `DRIVE_SEARCH_METADATA_ONLY`;
- `DRIVE_LIST_METADATA_ONLY`.

It may retain at most 25 candidate records. Candidate classification must be based only on metadata returned by those surfaces. Source content must not influence classification.

Any operation that hydrates source content is a hard stop. `DRIVE_FETCH`, content reads, downloads and OCR are forbidden during metadata inventory.

## Future gate

`TASK_054_METADATA_SAFE_EXISTING_CUSTODY_INVENTORY_EXECUTION`

Preferred first family remains `DETAILED_EDUCATION_BUDGET_EXECUTION_OR_BALANCETE_EDUCACAO`.

TASK 054 may re-observe the known seed candidate using metadata-only surfaces. It still may not read its source content. A fresh explicit owner authorization is required before any later gate reads source content.

## Promotion

This redesign does not execute an inventory and does not promote data. F01 remains `SILVER_SCOPED_PARTIAL_VALIDATED`; EITI financial identity remains `EVIDENCIA_INSUFICIENTE`; Gold, serving and publication remain blocked.

Expected result: `PASS_TASK053_METADATA_SAFE_INVENTORY_REDESIGN_NO_SOURCE_READ`.
