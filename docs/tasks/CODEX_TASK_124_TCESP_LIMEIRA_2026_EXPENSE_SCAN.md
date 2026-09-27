# TASK 124 — TCESP Limeira 2026 detailed-expense bounded scan

This task uses exactly one official TCESP per-municipality ZIP as a discovery/corroboration source.

After preflight CI, the live gate may perform one GET of the exact ZIP. Local processing may validate ZIP safety, inspect CSV schema, and run exact lexical/code scans.

TCESP/Audesp is classified as SECONDARY_AGGREGATOR for research semantics. A matching row can identify a candidate accounting key or event, but cannot alone promote EITI financial or transaction identity to proven. Primary municipal verification remains mandatory.

No raw ZIP or CSV is committed or written to Drive.
