# TASK 219Q — current-session SDT AreaId ↔ LayerInfo.id mapping

Issue #723.

## Major correction

TASK 219P had concluded that the SDT `AreaId` and returned `LayerInfo.id` appeared to be distinct identifier layers because a full AreaId captured in TASK 219N did not occur in a later browser session.

TASK 219Q proves the actual mechanism:

**the 32-character LayerId/AreaId prefix changes between browser sessions.**

Within one session, however:

**SDT AreaId == request LayerInfo.id == response LayerInfo.id**

for all eight automatically loaded areas.

## Exact passive proof

One clean public browser session loaded both:

- `vSDT_TDAPORTAL`
- `vAREASTOREFRESH`

Both contained the same eight public areas.

The page issued exactly eight automatic POSTs to `/awsgetcontentareas.aspx`.

For every request:

1. the current AreaId appeared exactly in `LayerInfo.id` and inside `LayerInfo.info`;
2. the exact full AreaOrigin appeared inside `LayerInfo.info`;
3. exactly one Area object claimed that request;
4. the returned response `LayerInfo.id` equaled the request `LayerInfo.id`.

Thus all **8/8 areas were mapped one-to-one** without using ordinal or size as identity.

## Despesa

Current-session public state:

- AreaName: **Despesa**
- AreaOrigin: `2_92_guestuser_207_6_DSL0_VIS1343`
- current AreaId: `89edf10f97084b6988c50aeb868f6067DSA6`
- current LayerInfo.id: `89edf10f97084b6988c50aeb868f6067DSA6`

The exact AreaOrigin occurs in that request's `$.info`.

The exact AreaId occurs in:
- `$.id`
- `$.info`

The response repeats the same id.

Therefore:

**CURRENT-SESSION DESPESA → LAYERINFO.ID MAPPING = PROVEN**

## Why TASK 219P failed

TASK 219N, in an earlier browser session, had:

`0e1483cd46954696a3e9b01c5be19e23DSA6`

TASK 219Q has:

`89edf10f97084b6988c50aeb868f6067DSA6`

The stable public origin remains:

`2_92_guestuser_207_6_DSL0_VIS1343`

and the observed suffix remains:

`DSA6`.

TASK 219P reused the full prior-session AreaId as a future literal. It therefore correctly found zero matches, but the interpretation that this represented two identifier namespaces is now superseded.

## Correct runtime rule

Never persist a complete AreaId from one session and expect it to identify the same area in a future session.

Instead:

1. read the current `vSDT_TDAPORTAL`;
2. identify **Despesa** from explicit `AreaName` plus exact stable `AreaOrigin`;
3. obtain that session's current AreaId;
4. select the automatic `LayerInfo` request/response whose id equals that same-session AreaId.

## Conditional response inspection

The one-shot workflow had been written before the session-prefix behavior was known and used the prior TASK 219N full AreaId as the conditional selector for the Despesa response.

Consequently, although the mapping itself was proved during the run, that conditional branch did not retain the corresponding response `info` for structural inspection.

A second browser session/retry was outside this task authorization and was not performed.

This limitation does not reduce the mapping proof.

## Boundary

Zero:
- clicks;
- typing;
- forms;
- manual XHR/fetch;
- direct endpoint calls;
- PortalAction;
- LayerInfo replay/synthesis;
- retries;
- Empenho lookup.

Coverage remains **34/38**.

## Provenance

Run: `34427037950`  
Artifact: `10133051856`

ZIP SHA-256:
`42d6425d66709a5d48cce550c973afdec145b22ea0053ee166eef39b009cd824`

Result SHA-256:
`794c559421f7fb22906a2add293791ddd748f5e15ce8a96f261385d00eb6df41`

Live workflow removed in:
`f1f06a03f58a5d675a2108182f6c03c1fbef430b`

## Next safe leap

In a fresh session, determine the current Despesa AreaId from `AreaName=Despesa` + exact `AreaOrigin=...VIS1343`, immediately bind it to that same session's LayerInfo response, and inspect the returned `info` for its official public action contract.

Do not pin the 32-character prefix across sessions.
