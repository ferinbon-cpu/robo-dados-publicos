# M7 — SIOPE export request-expression refinement gate — 0.8.0

## Context

The live call-site discovery run `32796782141` passed and observed five export-related call-sites and ten route-like literals. It did **not** request any candidate route or download the SIOPE artifact.

The previous gate intentionally used lexical proximity. Its evidence therefore contains both promising structural candidates — notably `/plataforma-antonieta-de-barros-api` and a dynamic `/{VAR}/{VAR}` pattern — and generic neighboring literals such as `/products`, `/directory`, `/legal` and `/payment`.

Lexical proximity is not sufficient proof of an artifact endpoint.

## Purpose

This gate refines the evidence by accepting a route candidate only when a route-like literal is syntactically attached to a request mechanism or request configuration in the context of a proven export identifier.

Observed mechanisms eligible for refinement are:

- `fetch(<literal>)`;
- `.get/.post/.put/.patch/.delete(<literal>)`;
- `url: <literal>` or `url = <literal>`;
- `baseURL: <literal>` or `baseURL = <literal>`;
- a local variable assigned a route literal and then passed directly to a request call.

When a `baseURL` and a direct relative request expression occur in the same export context, the gate also emits a composed candidate. Unbound neighboring strings are ignored.

## Safety contract

The workflow is manual only and requires explicit confirmation. It performs only read-only `GET` requests to the official product page and same-origin JavaScript files declared by that page.

It does not:

- call any candidate API route;
- issue `HEAD` requests;
- click the export control;
- execute browser automation;
- submit forms;
- bypass CAPTCHA;
- download the `.txt.gz` artifact;
- write to Drive;
- collect or process SIOPE data;
- authorize recurrence or schedule.

Query values are removed from sanitized route evidence.

## Decision rule

- `UNIQUE_REQUEST_ROUTE_EXPRESSION_OBSERVED_NOT_CALLED`: exactly one refined request route (preferably a composed `baseURL + endpoint`) remains. Next step is an **artifact-route verification design**, not collection.
- `REQUEST_ROUTE_EXPRESSIONS_OBSERVED_AMBIGUOUS_NOT_CALLED`: more than one refined request route remains. Next step is a constrained runtime-route probe design.
- `EXPORT_REQUEST_CONTEXT_OBSERVED_ROUTE_UNPROVEN`: export identifiers remain visible but no request-bound route can be proven statically. Next step is a constrained runtime-route probe design.

A pass from this gate never authorizes data collection.
