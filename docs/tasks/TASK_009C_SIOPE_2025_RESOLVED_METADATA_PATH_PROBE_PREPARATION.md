# TASK 009C — resolved SIOPE 2025 metadata path probe preparation

## Scope

This task is T0/offline preparation only. It creates no authorization for live execution and performs zero source GETs.

The previous bounded TASK 009B observation returned HTTP 302 with relative `Location`:

`/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip`

Offline RFC-style relative URL resolution against the pinned HTTPS SharePoint origin yields the candidate target:

`https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip`

That resolved target has not yet been contacted.

## Future T1 contract

A later separately authorized run may issue exactly one GET to the exact resolved URL with `Range: bytes=0-4095`, read at most 4096 bytes, use a 60-second timeout, perform one attempt, never retry and never follow redirects. A redirect is sanitized and stops the run. A large range-ignored response stops without archive persistence.

The future observation may establish only response class, sanitized further redirect, exposed package size, and ZIP magic in the bounded sample. It cannot establish full package integrity, alias semantics, `NUM_POPU`, annual finality, Gold 2025, MDE/Fundeb compliance, or any 2026 status.

## Guards

The live authorization artifact `config/siope_2025_metadata_resolved_path_probe_authorization.v1.json` must be absent from this preparation PR. Only the `authorized:false` template is added. The manual workflow has `contents: read`, no schedule/push trigger, no secrets and stops before transport without a separately merged authorization-only artifact.

2025 annual closure, semantic comparability and Gold remain `UNKNOWN`; the closed annual series remains 2016–2024.
