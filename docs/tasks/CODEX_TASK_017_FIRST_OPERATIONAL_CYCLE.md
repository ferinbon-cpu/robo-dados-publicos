# TASK 017 — first operational cycle preparation

This T0/offline contract composes the already-proven Jornal Oficial edition 7310 reference,
reconciliation constraints, observability, and the existing product builder. It does not
recollect or reprocess the source and does not execute reconciliation.

The eight stages are PREFLIGHT, SOURCE_SELECTION, ACQUISITION_OR_REUSE, PROCESSING,
RECONCILIATION, OBSERVABILITY, PRODUCT_BUILD, and OPERATIONAL_SUMMARY. Every stage emits
status, execution flag, input/output identities, evidence, warnings/stops, and remote effect
counts. A STOP makes every downstream stage `STOP_DEPENDENCY`.

The boundary remains 0.7.0 ACTIVE, 0.8.0 CANDIDATE, closed series 2016–2024, Gold 2025
UNKNOWN/BLOCKED, and B1/B2/B3 PENDING. TASK 018, under later owner authorization, is the
place for a first bounded live cycle; TASK 017 executes none of it.
