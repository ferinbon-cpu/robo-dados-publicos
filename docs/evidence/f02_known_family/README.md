# F02 known-family runtime manifest examples

The JSON files in this folder are **synthetic examples only**. They intentionally do not duplicate real Drive IDs, source hashes, financial values, or custody identifiers.

A production-period manifest is runtime data and must be materialized outside the public repository under a separately authorized scope. It pins the real source identity, SHA-256, bytes, pages, role and period for that one bounded execution.

Snapshot paths point to transient `runtime/f02/...` locations. `runtime/` is already ignored by Git. The adapter rejects absolute paths, `..`, symlinks, and any resolved path that escapes the repository root.

A new period with an already-proven document shape changes the runtime manifest, not the parser. Unknown family, schema drift, immutable-byte drift, incomplete bundle or period mismatch stops before Silver.
