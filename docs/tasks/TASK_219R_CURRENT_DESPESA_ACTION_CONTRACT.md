# TASK 219R — exact current-session Despesa response binding

Issue #725.

## Result

TASK 219R successfully implemented the session-safe rule established by TASK 219Q.

A fresh public browser session first read `vSDT_TDAPORTAL`, then selected exactly one area by:

- `AreaName = Despesa`
- `AreaOrigin = 2_92_guestuser_207_6_DSL0_VIS1343`

Only after this did it obtain the current session's AreaId:

`d56383cbd82e47c39282ff168768bb58DSA6`

The page generated eight automatic POSTs to `/awsgetcontentareas.aspx`.

Exactly one request had:

`LayerInfo.id = d56383cbd82e47c39282ff168768bb58DSA6`

and its response returned exactly the same id.

Therefore:

**CURRENT-SESSION DESPESA -> EXACT LAYERINFO RESPONSE = PROVEN**

This eliminates the stale-AreaId problem from TASK 219P.

## What the selected info showed

The selected response `info` was:

- raw length: 11,305 characters
- raw SHA-256:
  `ad9f419a7da9a2cd9cfa7a43025d13b262b81a27da384975512b3d8a32f79195`
- raw value not persisted

Python `html.unescape` produced:

- 9,313 characters
- SHA-256:
  `4533468817eca88e292b98889272f92df2fba41598e6958ba8c73cac2a74cbd0`
- zero HTML interactive nodes
- zero recognized official actions
- zero literal accounting terms under the bounded term set.

## Important scientific qualification

This does **not** prove that the Despesa response has no official action.

TASK 219L already canonized all eight returned `info` fields as:

`QUERY_LIKE_DELIMITED_WITHOUT_SAFE_KEYS`

TASK 219M proves the public browser client applies its own:

`unescapeHTML(v.info)`

before rendering.

TASK 219R used Python `html.unescape`, and equivalence between these transformations is not proven.

Therefore the valid result is:

**DESPESA LAYERINFO RESPONSE EXACTLY BOUND; CLIENT INFO DECODER/ACTION CONTRACT STILL UNPROVEN**

not:

“Despesa has no action.”

## Boundary

One browser session, one initial navigation.

Zero:
- clicks;
- typing;
- form submissions;
- manual XHR/fetch;
- direct endpoint calls;
- PortalAction;
- LayerInfo replay;
- retries;
- Empenho 3286-2026 lookup.

## Provenance

Run: `34432594528`  
Artifact: `10135033287`

Artifact ZIP SHA-256:
`99f4682db21a96ab65d690a2136e845a196618029163f4d28aecfe11251cc060`

Result SHA-256:
`b0296358df8125ac907205376dcb93999a9ee93e1e92e110f11e9945a43ddf9c`

Live workflow removed after the run.

Coverage remains **34/38**.

## Next safe leap

In a fresh session:

1. resolve current Despesa by AreaName + exact AreaOrigin;
2. bind to its same-session LayerInfo response;
3. invoke/read only the already-loaded public client's actual `unescapeHTML` transformation on that `v.info`;
4. persist only transformation classification and sanitized actions/forms/controls;
5. execute nothing.

This should determine whether the remaining barrier is merely the client decoder or another portal-state layer.
