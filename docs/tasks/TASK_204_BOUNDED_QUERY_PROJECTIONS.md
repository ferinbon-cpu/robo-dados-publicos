# TASK 204 — bounded query projections from pinned ledger snapshots

## Goal

Close the eleven local renderability gaps identified by TASK 203 without copying the 39,783-row accounting ledger or the 2,286-row revenue ledger into GitHub.

The projection layer is a derived query surface, not a replacement source layer.

## Source verification

TASK 204 read the two already-custodied gzip snapshots from Drive and verified their exact bytes before deriving any value.

Accounting:
- snapshot 64503339d8352a2f61e1ee85;
- 39,783 rows;
- gzip 7,845,217 bytes;
- SHA-256 5447581813677855ac8edcc70e6a90164ef1caa7799df544cc0a08d62ada25b0.

Revenue:
- snapshot fd110fa5c0c2a2583c475a19;
- 2,286 rows;
- gzip 246,707 bytes;
- SHA-256 02c644bfaf35a70a981967afdc15e0d0e548ed7df30a6da54e21435b17564847.

## Accounting projection semantics

For TCESP education transactions:

`empenhado líquido = Empenhado + Reforço - Anulação`

Liquidation and payment use the signed source rows directly.

Through April 2026:
- net committed: R$ 319,000,956.31;
- liquidated: R$ 138,279,835.79;
- paid: R$ 104,176,664.15.

Through July 2026:
- net committed: R$ 368,762,412.07;
- liquidated: R$ 262,452,288.06;
- paid: R$ 227,797,802.44.

The projection also carries bounded program/action, funding/application, expense-element, formal-procurement supplier, commitment-control and RREO-rests views.

Selected lists are explicitly non-exhaustive. Their source counts remain visible (22 program/action pairs, 39 funding/application pairs and 93 expense elements).

## Revenue projection semantics

Revenue uses the signed net sum of official TCESP rows.

Jan-Jul 2026:
- education-application revenue: R$ 241,960,964.18;
- treasury-classified education application: R$ 109,552,581.52;
- state transfers: R$ 119,045,512.07;
- federal transfers: R$ 13,362,870.59;
- FUNDEB-linked: R$ 118,066,203.65.

Revenue is not expenditure and does not prove expenditure destination.

## Renderability layer

TASK 203 remains historically reproducible:
- 27 RECORD_BACKED;
- 8 MIXED_RECORD_AND_CAPABILITY;
- 3 CAPABILITY_ONLY.

TASK 204 does not rewrite that baseline. It adds `OBSERVATORY_RENDERABLE_PACKET_V1`, combining the existing evidence packet with one or more bounded projection views for exactly the eleven backlog questions.

Expected current ontology-summary surface:
- 27 LOCAL_RECORD_BACKED;
- 11 BOUNDED_SOURCE_PINNED_PROJECTION_BACKED;
- 38/38 ontology questions renderable as bounded summaries.

This does not mean arbitrary ledger drilldown is locally complete. A drilldown outside the bounded projection must continue to use the pinned source snapshot or report the limitation.

## Privacy and guards

Formal procurement contained 28 person-supplier rows. Their names and public identifiers are not persisted in the projection; only one redacted aggregate is retained.

No serving, publication, schedule or recurrence is enabled.
