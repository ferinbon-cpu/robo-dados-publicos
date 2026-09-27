# TASK 165 — Direct JSON first source discovery policy

## Purpose

Generalize a practical lesson from the PNCP work:

> when an authorized source already exposes a structured JSON/API URL, retrieve that machine-readable resource directly before considering HTML/DOM/JavaScript/path reverse engineering.

This is a source-discovery and acquisition rule, not an analytical-methodology rule.

## Preferred strategy

1. direct official JSON/API GET;
2. direct authorized machine-readable GET with explicit source role;
3. documented API or declared download route;
4. HTML/DOM/JS/internal-path reverse engineering only as fallback.

The fallback must record why the machine-readable strategies were unavailable.

## Authorization reuse

The robot must not ask the owner for authorization once per page or once per equivalent URL when an existing authorization explicitly covers:

- the same source family;
- the same authorized host;
- the same research purpose;
- read-only GET/download;
- pagination/filter variations within scope;
- no mutation.

A new authorization is required when the operation leaves that scope, including a new unauthorized host/source family, widened purpose, write/mutation, new privileged access, or revocation/supersession.

For future live sources, the preferred interaction is therefore **one clear source-scope read-only authorization with boundaries**, rather than many per-URL authorizations.

This rule does not infer broad permission from a narrow authorization.

## PNCP reference case

TASK 161 records:

- owner instruction: `Autorizado pn p irrestrito`;
- interpreted scope: `PNCP_LIVE_READ_DISCOVERY_ONLY`;
- metering: `UNMETERED_WITHIN_PNCP_SCOPE_UNTIL_REVOKED_OR_SUPERSEDED`.

Once the exact public consultation JSON endpoint was known, pages and filters within that scope should be retrieved directly from the JSON endpoint. Re-discovering the web application's internals or requesting authorization for every page is unnecessary.

## Evidence guards

Direct JSON does not weaken evidence discipline:

- entity identity must still match;
- schema/key semantics must be validated;
- raw anomalies remain raw;
- transport failure is `SOURCE_TRANSPORT_UNAVAILABLE`, never `NO_MATCH`;
- exhaustive negatives require complete pagination;
- raw payload persistence remains governed separately.

## Scope

This task changes policy only. It performs no new live source request, Drive access, serving or publication.
