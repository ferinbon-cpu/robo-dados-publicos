# F02 known-family bundle adapter — 0.8.0

## Goal

Generalize the proven F02 MDE/FUNDEB pilots into a reusable **known-family bundle adapter**. New periods using an already-proven document shape must be supplied through an external manifest; they must not require a new parser, hard-coded period, or per-document PR.

## Why bundle-level maturity

The Drive metadata controller already recognizes RREO, FUNDEB and MDE. Those individual families remain `ROUTING_ONLY_SUPERVISED_EXECUTION` because one document alone is not enough to establish the F02 reconciliation semantics.

This adapter defines a narrower mature unit: a complete, manifest-pinned F02 bundle.

Supported modes:

- `RREO_ALIGNED`: exactly RREO_MDE + FUNDEB_LOCAL + MDE_25_LOCAL for the same period.
- `LOCAL_ONLY`: exactly FUNDEB_LOCAL + MDE_25_LOCAL for the same local monitoring period, with no official-MDE substitution.

## Runtime manifest

Each new batch is data, not code. The runtime manifest must pin:

- batch id and kind;
- reference-period start/end;
- exact source_id, family, role and stable Drive file ID;
- SHA-256, byte count and page count;
- a relative local snapshot path after separately authorized materialization.

The adapter refuses absolute paths and path traversal.

## Fail closed

Unknown/ambiguous family, missing/duplicate family, immutable source drift, parser/schema drift, or period mismatch is STOP. Upstream routing may quarantine unknown families.

## Promotion boundary

A passing adapter result is an offline deterministic candidate. It does not authorize Bronze, Silver, Gold, serving, publication, site, overwrite, delete, move, schedule, or recurrence.

A new period with the same known schema can therefore be processed with a new manifest and existing code, while remote persistence remains a separately authorized effect.


## Explicit blocked capabilities

The adapter is a **T0 offline-only** capability. A PASS does not authorize any of the following:

- remote Drive read;
- Bronze write;
- Silver write;
- Gold write;
- serving;
- publication;
- site mutation;
- overwrite, delete or move;
- schedule or recurrence;
- automatic acceptance of a new family or parser/schema shape.

The machine-readable boundary is pinned in `config/f02_known_family_bundle_gate.v1.json`. The only T0 execution privilege is reading already-materialized local snapshots inside the repository runtime boundary. Any remote materialization or persistence is a separate authorization.

## Security boundary for local files

Adapter config paths and snapshot paths must be repository-relative regular files. Absolute paths, `..`, symlink components, missing files and resolved paths outside the repository root fail closed.
