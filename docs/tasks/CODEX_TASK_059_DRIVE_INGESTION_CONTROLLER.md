# TASK 059 — Drive Ingestion Controller

## Objective
Replace the long-term file-by-file operating model with a fail-closed front controller for the existing ingestion pipeline.

The controller receives **metadata-only Drive inventory records** and routes each record to exactly one state:
- `AUTO_INGEST`: known family and supported metadata, eligible for a later authorized content/hash ingest;
- `REVIEW`: potentially useful, but ambiguous or requiring a rule/human decision;
- `QUARANTINE`: unknown, malformed, outside authorized scope, or policy-violating.

`AUTO_INGEST` is a routing decision only. TASK 059 does not read file content and does not create Bronze/Silver/Gold objects.

## Integration with existing architecture
The controller is placed before TASK 025-style supervised ingestion. It does not replace immutable hash/page validation, reconciliation, Bronze/Silver/Gold gates, BI materialization, or serving.

Future execution should reuse the existing source-integrity pattern: content hash becomes authoritative only after an explicitly authorized read. Same title or same size is never sufficient to prove duplication.

## Known families in v1
PPA, LDO, LOA, SIOPE, FUNDEB, RREO, RGF, MDE, detailed budget execution, SAEB, SARESP, Censo Escolar and IDEB.

## Fail-closed rules
- metadata phase may not hydrate content;
- unknown family goes to `QUARANTINE`;
- multiple family matches go to `REVIEW`;
- unsupported MIME for a known family goes to `REVIEW`;
- duplicate metadata file ID goes to `REVIEW`;
- out-of-scope record goes to `QUARANTINE`;
- no Drive write or data-layer promotion is authorized;
- no route may itself imply financial identity or Gold readiness.

## Relationship to F01
TASK 058, which would have opened `FUNDEB_LIMEIRA_2026_01.pdf`, is deferred and not executed. The EITI state remains unchanged.

## Next bounded gate
`TASK_060_DRIVE_INGESTION_CONTROLLER_METADATA_PILOT`: run the controller against one explicitly authorized Drive folder using metadata-only inventory. The pilot must return routing counts and candidate lists without reading content. A later execution authorization can then permit automatic digestion for known families.

Result: `PASS_TASK059_DRIVE_INGESTION_CONTROLLER_OFFLINE_READY_FOR_METADATA_PILOT`.
