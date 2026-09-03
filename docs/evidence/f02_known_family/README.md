# F02 known-family runtime manifest examples

These manifests pin **already-proven** April and May source identities. They are reference/runtime-input examples, not new ingestion authorizations.

The snapshot paths deliberately point to a transient `runtime/f02/...` area that is not committed. An execution environment must materialize the exact Drive objects there under a separately authorized content-read scope. The adapter then re-verifies SHA-256, bytes, pages and text-layer before parsing.

A future period uses the same schema and code, replacing only manifest identity/period/source pins. If the parser sees schema drift, the batch stops before Silver.
