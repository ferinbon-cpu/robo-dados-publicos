# TASK 120 — exact SIOPE-MAVS binary identity closure

TASK 056 already contains the semantic read of the selected SIOPE-MAVS/FUNDEB report, but the original PDF SHA-256 was not versioned. TASK 120 closes only that binary-provenance gap.

After offline preflight, one exact metadata read and one exact raw-media read of the already-selected Drive file are permitted. The temporary bytes may be materialized only to compute SHA-256 and byte count and verify PDF magic.

No text extraction, OCR, ontology scan or semantic interpretation is allowed. The TASK 056 findings remain the semantic authority. No Drive write or derived persistence is allowed.

The resulting sanitized evidence will bind TASK 056 findings to an exact source SHA before the SIOPE research-digest adapter is built.
