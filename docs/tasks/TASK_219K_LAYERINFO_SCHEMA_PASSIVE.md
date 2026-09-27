# TASK 219K — passive LayerInfo schema and response encoding

Issue: #711  
Parent: #691

## Result

TASK 219K executed one passive public-browser session against the Limeira TDA client and inspected only the requests the page itself generated.

No click, typing, form submission, authentication, manual XHR/fetch, endpoint replay or commitment lookup occurred.

## LayerInfo is JSON

The field `LayerInfo`, previously known only as a 3–4 KB text value, is now proven to contain valid JSON in all eight automatic calls.

Its stable top-level shape is:

`LIST[1] → OBJECT[17 fields]`

The 17 exact field names are:

- changetitle
- env
- filter
- filterarea
- id
- info
- isdebug
- isduplic
- ispreview
- maindebugid
- newdebugid
- perf
- refreshtime
- runafter
- showfilter
- title
- updatemain

All eight requests have the same key set, same types and same schema hash.

The stable type pattern includes booleans for control flags, integers for debug/refresh fields, and text for `env`, `filterarea`, `id`, `info`, `perf`, `runafter` and `title`.

No scalar value was persisted.

## Responses are JSON too

The endpoint declares `text/html`, but all eight observed response bodies are valid UTF-8 JSON.

Each response has the same top-level shape as the request:

`LIST[1] → OBJECT[17 fields]`

The response uses the same 17 keys and the same field types.

The canonical type-only schema SHA-256 is identical on request and all responses:

`e3140f95037307092e53805ee1cfc7a7b21caab8ebb03675281623537ef28d1b`

The eight response bodies are distinct because text-field sizes vary, but their typed envelope remains the same.

## Protocol interpretation

The strongest safe interpretation is now:

**browser sends a LayerInfo JSON state envelope → server returns a LayerInfo JSON state envelope with the same typed structure.**

This is consistent with a stateful content-layer round trip.

The large variable text fields `info` and sometimes `filterarea` are the most likely carriers of the actual layer content, but their internal encoding and meaning were not inspected in this task.

## What remains unproven

TASK 219K does not prove:

- which of the eight layers is the expense/accounting module;
- the internal schema of `info` or `filterarea`;
- that `/awsgetcontentareas.aspx` is specifically an accounting endpoint;
- a safe direct-call/replay contract;
- any lookup of Empenho 3286-2026;
- Contract 45/2026 identity;
- payment attribution.

No question was promoted. Coverage remains **34/38**.

## Runtime provenance

Run: `34407092854`  
Execution head: `4c9909afd30e8a8ff7ff34fcaaf0c6c282e2e671`  
Artifact: `10125750801`

Artifact ZIP SHA-256:

`7f351a5a3a467653c0c96877ea36ccd6f580631d4dfa0e98aeaacba3e89aa015`

Artifact member SHA-256:

`c37f8eef93ecb48c51672e4273a1a447963604ef5c9cacb679897e0e418cad89`

Executed workflow blob equals preserved historical source:

`fbfe325368e18a3afa862aa4aa0edcda3bc77d3d`

The live workflow was removed after execution in:

`ebd671fce47228e182f72f76e902fb002938a7dc`

## Next future gate

A separately authorized passive session can inspect only the nested serialization/schema of `info` and `filterarea`, without persisting their values, and compare the eight layers structurally.

Do not synthesize or replay LayerInfo and do not query Empenho 3286-2026 until the relevant layer and nested protocol are proven.
