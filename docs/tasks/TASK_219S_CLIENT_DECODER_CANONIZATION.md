# TASK 219S — exact public-client decoder contract for Despesa

Issue: #727  
Parent: #691

## Goal

Resolve the current-session Despesa response exactly, then determine the exact client-side transformation used before the response `info` is injected into the portal.

## Runtime result

One fresh public browser session again proved the session-safe binding:

- `AreaName = Despesa`
- `AreaOrigin = 2_92_guestuser_207_6_DSL0_VIS1343`
- current-session AreaId: `159c60a8cace44f89c165511a12a724eDSA6`
- eight automatic POSTs to `/awsgetcontentareas.aspx`
- exactly one request matched the current AreaId.

The selected `info` was 11,305 characters and was retained only in memory. Its SHA-256 was:

`51cd1a5e70b65fb7b4fb7cb87719b9f81aaa08a08b953b7d59b26e2070b0aab8`

The predeclared probe for a callable global function named `unescapeHTML` returned:

- callable: false
- global candidates: 0
- transformed output: none.

No second browser session or retry was performed.

## Offline source reconciliation

The canonical TASK 219M artifact already contains the exact public JavaScript source that handled these same LayerInfo responses.

A literal search across its archived public scripts found **zero occurrences** of `unescapeHTML`.

The actual implementation is inside `window.appendAreasWS` in `aportalclientjs.aspx`.

At source line 680 the client computes the content string with the equivalent of:

`temporary textarea -> assign v.info as HTML -> read textarea text`

The exact archived expression is recorded in the TASK 219S static-source evidence file.

Then the client:

1. empties the DOM destination selected by `v.id`;
2. appends the decoded string into that destination;
3. applies the same temporary-textarea entity decoding pattern to `v.perf`;
4. applies the same pattern to `v.filterarea` when filters are present;
5. separately executes `eval(v.runafter)` when `v.runafter` is non-empty.

Therefore the earlier shorthand that the page called a function named `unescapeHTML(v.info)` is superseded.

## Canonical decoder model

The proven model is:

`LayerInfo response`
→ select exact same-session `v.id`
→ browser/jQuery HTML-entity decode through a temporary `textarea`
→ resulting string
→ jQuery `append()` into the `v.id` container
→ optional separate `runafter` evaluation.

This distinction matters because TASK 219R used Python `html.unescape`. Python equivalence to the exact browser/jQuery textarea transformation is **not proven** for the selected Despesa payload.

Consequently TASK 219R's zero parsed HTML nodes cannot be promoted to “Despesa has no action”.

## Scientific gain

Before TASK 219S, the remaining barrier was vaguely described as an unknown `unescapeHTML` function.

After TASK 219S, that uncertainty is removed:

- there is no such global function in the archived client;
- the exact transform expression and injection sequence are proven;
- the next carrier can reproduce the client's transformation literally in the same session.

The remaining unknown is now only the structure of the exact Despesa payload **after that exact textarea transformation**.

## Boundary

The authorized session performed:

- one browser session;
- one initial navigation;
- zero clicks;
- zero typing;
- zero form submissions;
- zero manual XHR/fetch;
- zero direct endpoint calls;
- zero PortalAction triggers;
- zero LayerInfo replay/synthesis;
- zero retries;
- zero Empenho `3286-2026` lookup.

The static fallback used only the already-canonical TASK 219M GitHub artifact and made no additional request to the municipal portal.

Coverage remains **34/38**.

## Provenance

TASK 219S run: `34478265183`  
Job: `102874304014`  
Artifact: `10152447866`

Artifact ZIP SHA-256:

`58b73b4dc98d617ae139cacb3e552756af799eefd50d549549cfbabc9afffcba`

Result member SHA-256:

`3ca6ec45734d2d02db9c18fb4ef106b2ecf43fe1541523aade747f30c7bfa6e1`

Executed workflow blob equals preserved historical workflow blob:

`eedf1a0cd2f61ba54a776c16a4ba4d6b70df4c35`

Live workflow removal commit:

`d780ae84e46161221887aa93e8b8e4431c03c23b`

TASK 219M public `aportalclientjs.aspx` SHA-256:

`f8ce8973c88faad20b81649ed0151e56f1de06347b3bb47993a0da9892bc8cd6`

## Next safe leap

In a new authorized session:

1. resolve current Despesa by `AreaName + AreaOrigin`;
2. select its same-session LayerInfo response;
3. reproduce exactly the client's temporary-textarea decode expression on `v.info` in memory;
4. inspect the result in a detached DOM;
5. persist only sanitized links, buttons, forms, controls and explicit action bindings;
6. do not execute any action unless a later authorization explicitly permits it.
