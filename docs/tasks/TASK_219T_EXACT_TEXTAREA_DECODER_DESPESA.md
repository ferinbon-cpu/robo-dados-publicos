# TASK 219T — exact textarea decoder on the current-session Despesa response

Issue: #729  
Parent: #691

## Context

TASK 219R had already proved how to bind the current-session public `Despesa` area to the exact automatic `LayerInfo` response.

TASK 219S then corrected the remaining decoder hypothesis from static public client source. There is no callable global function named `unescapeHTML`. The real client code inside `appendAreasWS` performs:

`$('<textarea />').html(v.info).text()`

and then injects the resulting string into the current `v.id` container.

TASK 219T applies that exact expression in the actual loaded public page.

## Boundary

Exactly one public browser session and one initial navigation.

Zero:
- clicks;
- typing;
- form submissions;
- manual XHR/fetch;
- direct endpoint calls;
- PortalAction triggers;
- LayerInfo replay/synthesis;
- retries;
- Empenho 3286-2026 lookup.

The task does not persist raw `v.info`, full transformed HTML, page source, HAR, cookies or tokens.

## Same-session Despesa binding

The task first read the current `vSDT_TDAPORTAL` and selected exactly one area by:

- `AreaName = Despesa`
- `AreaOrigin = 2_92_guestuser_207_6_DSL0_VIS1343`

Current-session AreaId:

`6aa0e2f44c2340988888297491c30038DSA6`

The page produced exactly eight automatic POSTs to `/awsgetcontentareas.aspx`.

Exactly one request matched that current AreaId, and the returned response repeated the same id.

Thus:

**current AreaId = request LayerInfo.id = response LayerInfo.id**

for the selected Despesa response.

## Exact decoder runtime proof

Inside the already-loaded public page, jQuery was available as version `3.2.1`.

The task executed the exact expression:

`$('<textarea />').html(v.info).text()`

on the selected Despesa `v.info`.

Input:
- length: 11,305 characters;
- SHA-256: `9a0c8549684e8735fde8537f4e5e7dcf9dba2e44bf6d03814dd155e3be41bab4`;
- raw value not persisted.

Output:
- type: string;
- length: 9,313 characters;
- SHA-256: `d23b729e8bb56d325d73d0ed8ace53127a15e4916800b729e74faad68c057f84`;
- raw output not persisted.

Therefore:

**THE EXACT PUBLIC-CLIENT TEXTAREA DECODER IS NOW PROVEN AT RUNTIME.**

The Python `html.unescape` approximation is no longer needed as the canonical decoder model.

## Decoded structure

The output is real HTML-like content.

A detached inert `<template>` parse found 52 elements:

- 29 `div`;
- 4 `img`;
- 4 `script`;
- 5 `style`;
- 1 `table`;
- 1 `tbody`;
- 4 `td`;
- 4 `tr`.

The inert parse found:

- forms: 0;
- inline interactive nodes: 0;
- explicit public actions: 0;
- `runafter`: absent.

Plain-text length was 6,684 characters.

No exact bounded accounting term from the task set appeared in that plain text.

## Important fail-closed correction

The runtime carrier's provisional rule initially marked action absence because the decoded output was HTML-like and contained zero inline interactive nodes.

That provisional absence flag is **not canonical**.

The transformed HTML contains four `<script>` elements, while the detached `<template>` was intentionally inert and executed neither scripts nor handlers.

Therefore zero interactive nodes in this pre-script inert DOM cannot prove that the normally rendered post-script DOM contains no action surface.

Canonical result:

**EXACT DESPESA DECODER PROVEN; HTML BASE HAS NO INLINE INTERACTIVE SURFACE; POST-RENDER ACTION SURFACE STILL UNPROVEN.**

## Why this also supersedes TASK 219O

TASK 219O searched the DOM using a complete AreaId captured in an earlier session.

TASK 219Q later proved that the 32-character AreaId prefix changes between sessions.

Thus TASK 219O's top-level DOM-negative result does not answer the correct question.

The proper next probe must:

1. read the current session `vSDT_TDAPORTAL`;
2. identify Despesa by explicit `AreaName` plus exact stable `AreaOrigin`;
3. obtain that session's current AreaId;
4. wait for the public page's normal automatic rendering;
5. inspect the **live DOM node whose id equals that same-session AreaId**, including its rendered descendants and public action/control metadata;
6. execute nothing.

This route observes the actual post-render DOM rather than an inert pre-script template.

## Provenance

Run: `34485958452`  
Job: `102900169628`  
Execution head: `4abf82b41bd2cd4b00b010e9247c8168d50db3df`  
Artifact: `10155617848`

Artifact ZIP SHA-256:

`e7f1d44cd8afa8db290fb0139c5f505069ce29158530b5d6e2b48ab60b4abf1a`

Executed single-use workflow blob equals preserved historical workflow blob:

`9b1b4a616770ef0816a941bb001e805b7190d824`

The live workflow was removed after execution in commit:

`4357ee33df128f5c4efd33d8405a9423c7e3cd8b`

## Coverage

Coverage remains **34/38**.

Still blocked:
- CTRL_Q2
- PROC_Q1
- PROC_Q2
- PROC_Q3

The task did not query Empenho `3286-2026` and did not attribute any payment to Contract `45/2026`.
