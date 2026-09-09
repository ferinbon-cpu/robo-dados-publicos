# TASK 219M — public TDA client JavaScript static mining

Issue: #715  
Parent: #691

## Why this task changed the route

After TASK 219L, the remaining plan was to correlate the eight LayerInfo responses to DOM containers experimentally.

TASK 219M showed that this experiment is unnecessary.

The public client source already documents the binding.

## Bounded acquisition

Exactly six public same-host resources previously observed by the browser were acquired:

- `/aportalclientjs.aspx`
- `/tdaportalclient.js`
- `/mp_tda.js`
- `/gxcfg.js`
- `/gxgral.js`
- `/gxtimezone.js`

There were exactly six GET requests, zero redirects followed, zero retries, zero POSTs and no browser session.

All six returned HTTP 200.

Full third-party source exists only in the ephemeral runtime artifact and is not vendored into the repository.

## The key source: aportalclientjs.aspx

Only `/aportalclientjs.aspx` contains both:

- `LayerInfo`
- `awsgetcontentareas.aspx`

It defines `window.appendAreasWS(pinfo)`.

Static source proves the transport contract:

- route: `awsgetcontentareas.aspx`
- method: POST
- form field: `LayerInfo`
- field value: the `pinfo` argument.

The success handler parses the response as JSON and iterates the returned area objects.

## Exact DOM binding is now proven

For each returned object `v`, the public source uses `v.id` as the destination identity.

Structurally it binds:

- `v.info` → content container identified by `v.id`;
- `v.filterarea` → `AREAFILTER_<v.id>`;
- `v.title` → `<v.id>_title`;
- `v.perf` → `<v.id>_icoperf`.

When `v.refreshtime > 0`, the client schedules:

`AUTOREFRESH` with the same `v.id`.

When `v.runafter` is non-empty, the client executes that returned post-render script.

Therefore the prior planned generic DOM-correlation task is no longer needed.

## Portal action bridge

The same public script defines a generic portal action helper.

It serializes actions as:

`action#parm`

into a DOM handle called:

`PortalActionHandle`

and triggers a click.

Static action names include:

- `NEWLINK`
- `AREALINK`
- `AUTOREFRESH`

The generated GeneXus client also exposes the `MAINDIVPORTALCTL` W5DivHelper control and its `DivClicked` server event. This is consistent with the portal-action bridge, although TASK 219M does not claim the entire server-side action dispatch contract from static source alone.

## Generated GeneXus model

`/tdaportalclient.js` identifies itself as a GeneXus C# generated client:

- GeneXus 15.0.12 build 126726;
- generated 27 June 2024;
- server class `tdaportalclient`;
- package `TDA.Programs`;
- full AJAX enabled;
- AJAX events enabled;
- AJAX security token enabled.

Most importantly, it exposes:

`vSDT_TDAPORTAL` → type `SDT_TDAPortal`

with top-level fields:

- MainId
- MainDivId
- MainEnvironment
- MainOrientation
- Layers

It also exposes a typed area object:

`SDT_TDAPortal.Layer.Area`

with fields including:

- AreaId
- AreaDivId
- AreaType
- AreaFormat
- AreaAgg
- AreaDashOrder
- AreaOriginalType
- AreaShowingType
- AreaName
- AreaOrigin
- AreaLayerJson
- AreaFilterRendered
- AreaNewDebugId
- AreaShowButtonFilter
- AreaExternal
- AreaShowFilter
- AreaDuplicate
- Map
- Parms
- Links

The generated client also names controls such as:

- `vTHISAREAJSON`
- `vAREASTOREFRESH`
- `vLAYERNAME`
- `vAREANAME`
- `vTHISAREAID`

## What this means

The best next target is no longer a generic DOM inspection.

The public client already tells us where the portal keeps its structured state:

**`vSDT_TDAPORTAL`**

A future passive browser session can read the already-loaded public state and sanitize:

`Layers → Areas → AreaId / AreaName / AreaOrigin / AreaType / AreaLayerJson metadata`

If that runtime state names or structurally identifies the Despesas area, the robot can select the correct area without guessing from payload size or ordinal.

## Negative result

None of the six generic client scripts contains explicit occurrences of:

- despesa
- empenho
- empenhado
- credor
- fornecedor
- pagamento
- liquidação

Therefore module identity is not statically embedded in these six generic scripts.

It is more likely carried in runtime portal state or server-generated area content.

## Provenance

Run: `34413105966`  
Execution head: `c43b95a0301db4d18dc05484064bcfb3a506ebde`  
Artifact: `10128000020`

Artifact ZIP SHA-256:

`6053ea0e936e8f4d451f11c7335a6bbdede80b04f0bc0f051ae85479f8e9278a`

Result member SHA-256:

`9571188548cf0fc57c11a24b3ca91618d621b1a54d321e6a22ff16cbe3f77fab`

The executed workflow blob equals the preserved historical workflow blob:

`f180645fc3dfce13d5db1638a4ad08865f4402df`

The live workflow was removed after execution in:

`0b5ed0ac004592c4e94e8e98a8dec915af6d0ea3`

## Coverage

Coverage remains **34/38**.

Still blocked:

- CTRL_Q2
- PROC_Q1
- PROC_Q2
- PROC_Q3
