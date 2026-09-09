# TASK 219I — passive browser inspection of Limeira TDA

Issue: #707  
Parent: #691

## Why

Previous raw HTTP work had observed the official Limeira TDA entry route redirecting toward a logout/session surface. That was correctly classified as an access-surface limitation, not absence of public data.

After TASK 219H produced the exact accounting seed **Empenho 3286-2026**, TASK 219I executed the next engineering step already described in the repository research notes: one passive browser session against the public TDA client, without interacting with it.

## Browser boundary

Exactly one fresh headless browser session loaded:

`https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418`

The task performed:

- one initial navigation;
- zero clicks;
- zero typing;
- zero form submissions;
- zero manual fetch/XHR calls;
- zero authentication;
- zero cookie/storage injection;
- zero endpoint guessing;
- zero retries.

No response bodies or raw HAR were persisted. Query values were not persisted.

## What the browser proved

The browser reached the TDA client itself:

- final host: `transparencia.limeira.sp.gov.br`
- final path: `/tdaportalclient.aspx`
- title: **Prefeitura Municipal de Limeira**
- one form, five inputs and fifteen anchors were present.

A total of 111 network requests were observed:

- 95 to the municipal transparency host;
- 8 to `bi.etransparencia.com.br`;
- 4 to Google Maps;
- 3 to jsDelivr;
- one data-URL resource.

The vendor-host requests observed on `bi.etransparencia.com.br` were static images only. No vendor machine-data route was observed.

## New structural discovery

The public TDA page itself automatically issued **eight POST XHR requests** to the same municipal host:

`/awsgetcontentareas.aspx`

All eight returned:

- HTTP 200;
- MIME `text/html`;
- initiator type `script`.

This is the first browser-observed same-host content-service route canonized by the project.

## What this does not prove

TASK 219I did **not** capture request payload values, did not inspect response bodies, and did not directly call the discovered route.

Therefore `/awsgetcontentareas.aspx` is currently only:

**AUTOMATIC_REQUEST_INITIATED_BY_PUBLIC_TDA_PAGE / STRUCTURAL_DISCOVERY_ONLY**

It is not yet proven to be:

- an accounting endpoint;
- an API;
- a commitment lookup;
- a contract/procurement bridge.

The route cannot be manually queried under this task's authorization.

## Scientific consequence

The previous raw-HTTP `301 → logout.aspx` observation remains valid historical transport evidence, but it no longer justifies treating the whole TDA public workflow as browser-inaccessible. A clean browser session can load the public client without manual authentication and the page executes its own same-host content requests.

No commitment lookup occurred, no payment was attributed to Contract 45/2026 and no procurement identity was promoted.

Coverage remains **34/38**:

- CTRL_Q2
- PROC_Q1
- PROC_Q2
- PROC_Q3

## Runtime

Run: `34397753283`  
Execution head: `aef3ef949f40d408366cff25385fbbfa6e92d64f`  
Artifact: `10122191927`

Artifact ZIP SHA-256:

`c81c612f87796e5509004a26f50c72b3d8c63f27b5fa2221487d9c75650ac801`

Artifact member SHA-256:

`67edbb95b0f2c21dc433b2b8ed19bfef3f468018168ddf79ef6e87d2a1971b9a`

Executed workflow blob equals preserved historical workflow blob:

`488760470de4ba2c54c4e6388b4294ce6adf86ee`

The live workflow was removed immediately after execution in:

`68c5e77b08c3203ede4eea326036ce82e9ccee0a`

## Next future gate

A separately authorized future passive browser session may capture only the **sanitized field names and structural metadata** of the automatically generated `/awsgetcontentareas.aspx` POSTs. It must still avoid guessing fields or manually querying the endpoint until the page-generated request contract is proven.
