# TASK 009A — bounded route probe preparation for the official SIOPE 2025 metadata package

## Classification

Current execution: `T0_OFFLINE`.

Future target: `T1_REMOTE_READONLY`, only after a separately merged one-shot authorization artifact and explicit owner authorization.

## Why a route probe comes before archive acquisition

TASK 008 proved that FNDE publishes the **Municipal — Metadados de 2025** package, but the official link is hosted at `fnde.sharepoint.com` and the current documentary tools could not inspect the binary. We do not yet have a trustworthy package byte size or a pre-approved redirect destination set.

Authorizing a full ZIP download without those facts would require guessing the response bound and redirect trust boundary. TASK 009A therefore prepares a narrower first observation.

## Exact source

Official index:

`https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/downloads`

Pinned package URL:

`https://fnde.sharepoint.com/:u:/s/SIOPE/EeP0ArdsxWJLuWyg3LQHt2IBKEWEhLDvDk2_7k1vbAx0tQ?download=1&e=UiD081`

Initial host: `fnde.sharepoint.com`.

## Future one-shot route probe contract

The prepared live gate, if separately authorized, permits exactly:

- one `GET`;
- exact pinned package URL only;
- `Range: bytes=0-4095`;
- at most 4 KiB of response body;
- timeout 60 s;
- one attempt;
- no retry;
- no redirect following;
- no pre-authorized redirect hosts.

If the initial SharePoint URL redirects, the gate records only the sanitized destination scheme/host/path and stops. Query values/tokens are never emitted. A new authorization is required before contacting any redirect destination.

If the server returns direct partial package bytes, the gate may record HTTP/content metadata, `Content-Length`, total size from `Content-Range` when exposed, ZIP magic presence and SHA-256 of the bounded sample. The sample body is never persisted or printed.

If Range is ignored and the declared/direct response exceeds 4 KiB, the gate stops. It does not turn the route probe into an implicit archive download.

## Authorization boundary

The actual authorization path is fixed:

`config/siope_2025_metadata_package_route_probe_authorization.v1.json`

TASK 009A intentionally does **not** create that file. The template remains `authorized:false`.

A future authorization must be:

- explicit owner authorization;
- one-shot;
- bound to an exact `main` base SHA;
- bound to an exact workflow run number, attempt 1 and `refs/heads/main`;
- introduced by an authorization-only commit/PR;
- time bounded;
- identical to the prepared request/effects/semantic contract.

## Effects prohibited

The gate does not authorize:

- SIOPE fiscal/OData data collection;
- Limeira receipt/status query;
- Drive read/write;
- response/archive persistence;
- Bronze/Silver/Gold creation;
- publication;
- recurrence/schedule/batch;
- Gold 2025 promotion;
- annual closure/finality promotion;
- MDE/Fundeb/compliance inference;
- 2026 promotion.

## Interpretation

A successful route probe still proves **no field semantics**. It only supplies enough transport evidence to design the subsequent bounded acquisition gate without guessing size or redirect trust.

Until a later archive acquisition/inspection proves otherwise, the canonical state remains:

- closed annual series: 2016–2024;
- 2025: `PROVEN_STRUCTURAL_RECENT`;
- P6 annual-consolidation role proven, finality `UNKNOWN`;
- 2025 alias bridge `NOT_PROVEN`;
- `NUM_POPU` definition/source/vintage `NOT_PROVEN`;
- semantic comparability `UNKNOWN`;
- Gold 2025 `UNKNOWN`;
- 2026 `UNPROVEN_CURRENT_YEAR`.
