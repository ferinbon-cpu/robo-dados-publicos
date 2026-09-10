# TASK 219P — exact DSA6 response gate and identifier-layer correction

Issue #721. Second of the two large leaps authorized together by the owner.

## Goal

TASK 219P attempted to select the automatic `awsgetcontentareas.aspx` response object corresponding to the proven public Despesa area using exact identity only:

`returned v.id == AreaId ...DSA6`.

Only after that exact gate could an official action, and conditionally an Empenho lookup, occur.

## Result

The page again generated exactly **8 automatic POSTs** to `awsgetcontentareas.aspx`.

Across their returned JSON objects:

**count(returned v.id == ...DSA6) = 0**

The workflow therefore stopped before any interaction.

Executed:
- Despesa actions: 0
- text entries: 0
- query submits: 0
- Empenho lookups: 0

No retry or second browser session occurred.

## Important correction

Three upstream facts now reconcile cleanly:

1. TASK 219M proved that returned `LayerInfo.v.id` is the DOM destination used by the client.
2. TASK 219N proved that `SDT_TDAPortal.Layer.Area.AreaId = ...DSA6` is the area explicitly named **Despesa**.
3. TASK 219O found no stable top-level DOM node whose id is `...DSA6`.
4. TASK 219P found no automatic returned `v.id` exactly equal to `...DSA6`.

Therefore the previous implicit equality:

`SDT AreaId == returned LayerInfo.id`

is rejected for this runtime path.

The portal has at least two identifier layers, and their translation must be observed directly.

## Static GeneXus mediator

The already archived public generated client exposes the exact state that likely mediates this mapping:

- `vAREASTOREFRESH`
- `vAREAID`
- `vTHISAREAID`
- `vTHISAREAORIGIN`
- `vAREANAME`
- `vVPORTALACTION`
- `vVPORTALACTIONPARM`
- `vAUXPORTALACTIONPARM`
- `vAREALINK`
- `vLAYERLINK`

It also declares:

`MAINDIVPORTALCTL.DIVCLICKED`

with inputs:

`ClickedDivId` and `ClickedDivValue`.

This does not by itself prove the mapping, but it identifies the exact state family that a future passive capture should correlate.

## Next route

The next network step should be passive only:

- capture the eight returned safe `LayerInfo.id` values;
- capture the already-loaded public `vAREASTOREFRESH` collection with safe AreaId/AreaName/AreaOrigin fields;
- correlate call grouping/order and any explicit mediator identifiers;
- prove the deterministic mapping for **Despesa / DSA6**.

Only then should any action or Empenho `3286-2026` query be authorized.

## Provenance

Run `34422554312`  
Artifact `10131457417`

ZIP SHA-256:
`6078d840ddb4da0367adde798cdfb5c7272fcfc3c12621f770ade45d58cdb99b`

Result SHA-256:
`2f8a7f5f0886c5da0e4eeff017fb13b56692c72b8b419bfb264dd6c209214a65`

Coverage remains **34/38**.

The two-large-leap authorization is fully consumed by TASK 219O + TASK 219P.
