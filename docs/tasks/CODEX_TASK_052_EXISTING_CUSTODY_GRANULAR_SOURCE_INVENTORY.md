# TASK 052 — Existing-custody granular source inventory

## Objective
Inventory, read-only, at most 25 existing-custody candidates for the granular EITI financial-evidence classes selected by TASK 051. The authorized boundary is metadata or manifest only: no source-content read, no public-source network request and no Drive write.

## Precondition cleanup
Before TASK 052, the owner authorized deletion of the accidental duplicate LOA Silver v2 Drive object `1l_q_iM8yIf76MjUAFi_ZvyLinLBYMJBv`. The canonical object `1sY2ysOroWzj-aNCXz2jU8EZQnbiDijPK` was preserved and the `02_SILVER` folder was re-read to verify the cleanup.

## Inventory finding before stop
Metadata search identified one concrete candidate whose title is potentially compatible with the preferred execution family:

- Drive id `1PTAnH-LL_8fvS7TsVuHSci5dBDKFLQTS`
- title `05 - Maio_despesa.pdf`
- candidate class: potential detailed budget execution / balancete

This classification is intentionally based only on the filename. No source-content fact is promoted by TASK 052.

## Boundary incident
While attempting to resolve location metadata for that candidate, a Drive `fetch` operation unexpectedly hydrated the source text rather than returning metadata only. That produced one source-content read, violating the TASK 052 contract `no_source_content_read=true`.

The task therefore fails closed. The hydrated text is not used to classify, reconcile or promote the candidate. No further source file was opened after the incident.

## Effects
- public-source network: 0
- Drive writes: 0
- OCR: 0
- Bronze/Silver/Gold writes: 0
- serving/publication: 0
- source-content reads: 1 (unexpected connector hydration)

## Controlled result
`STOP_TASK052_SOURCE_CONTENT_READ_BOUNDARY_BREACHED_NO_PROMOTION`

F01 remains `SILVER_SCOPED_PARTIAL_VALIDATED`; EITI financial identity remains `EVIDENCIA_INSUFICIENTE`; Gold, serving and publication remain blocked.

## Next gate
`TASK_053_METADATA_SAFE_CANDIDATE_INVENTORY_REDESIGN` should redesign the inventory so only search/list metadata surfaces are used and no `fetch` operation can hydrate source content. The candidate `1PTAnH-LL_8fvS7TsVuHSci5dBDKFLQTS` may be carried as a metadata seed, but any future source-content read requires a separate explicit authorization.
