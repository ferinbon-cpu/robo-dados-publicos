# TASK 219E — PNCP transport incident canonization

Issue: #699  
Parent issue: #691

TASK 219E converts the current PNCP obstacle into a permanent fail-closed rule for the robot. It performs no PNCP request.

## Why this task exists

The same official PNCP Consulta contracts endpoint has recently shown both successful and failed transport states in the canonical repository history.

- TASK 168B completed two HTTP 200 pages and 759 records.
- TASK 216 runtime 1 returned HTTP 200 on pages 1–3 and HTTP 502 on page 4. Pagination was incomplete and the scientific effect was explicitly NONE.
- TASK 216B then completed the same 2026 Limeira scope with 10 GETs across 9 partitions and 1,933 records.
- TASK 219C runtime 34364890448 later stopped on its first request with a read timeout, zero bytes, scientific effect NONE and absence inference false.

This history rules out treating the current failure as a data-absence observation. It also prevents us from prematurely declaring the endpoint deprecated: it has very recent successful complete observations.

## Deterministic response classes

TASK 219E introduces four transport/evidence states:

- `VALID_JSON_RESPONSE`: HTTP 200, at least one byte and valid JSON.
- `CONFIRMED_EMPTY_RESPONSE`: an explicit successful empty response, currently modeled by HTTP 204.
- `TRANSPORT_OR_EDGE_UNAVAILABLE`: no response/transport error, or HTTP 408/429/500/502/503/504.
- `INVALID_OR_INSUFFICIENT_RESPONSE`: any response that is not strong enough to establish a bounded source result.

The name `TRANSPORT_OR_EDGE_UNAVAILABLE` is intentionally conservative. A 502/503/504 or zero-byte timeout does not tell us whether the cause is the PNCP application backend, reverse proxy, WAF/CDN, upstream network, rate limiting, cloud-origin filtering or another transport component.

## Hard absence rule

`NO_MATCH` is semantically eligible only when:

1. the exact bounded scope is complete; and
2. every required page/partition ended as `VALID_JSON_RESPONSE` or `CONFIRMED_EMPTY_RESPONSE`.

Therefore:

- timeout is not NO_MATCH;
- zero bytes is not NO_MATCH;
- 502/503/504 is not NO_MATCH;
- incomplete pagination is not NO_MATCH;
- portal/index visibility does not substitute API/source proof;
- secondary evidence does not create procurement identity.

TASK 168B is retained as the positive example of a scientifically eligible bounded negative result. TASK 216 attempt 1 and TASK 219C are retained as negative examples that are incapable of proving absence.

## External context

The configuration records four diagnostic leads, all explicitly non-authoritative for procurement identity:

1. current official PNCP integration documentation;
2. the official 31 August 2026 deployment/maintenance notice;
3. a public dados.gov.br discussion reporting historical intermittent 504/ECONNABORTED behavior on the PNCP Consulta publication endpoint, including small pages;
4. an independent GitHub report of 2026 PNCP Consulta connectivity failures.

These leads justify investigation. They do **not** prove a current backend outage, rate limit, WAF/ASN blocking or causal link with the 31 August deployment.

Two 9 September operator observations (503/504 on a narrow daily lookup and 504 on a unit lookup) are also retained as `SUPPORTING_ONLY_NOT_CANONICAL_TRANSPORT_PROOF` because no raw runtime artifact was persisted.

## Future controlled probe

A later task may compare the exact same tiny known resource from two controlled origins while measuring separately:

- DNS resolution;
- TCP connection;
- TLS handshake;
- time to first byte;
- HTTP status;
- bytes received;
- content type.

The intended comparison is GitHub Actions versus a separately controlled non-cloud or Brazilian egress. That probe is not implemented or authorized here and cannot reuse a consumed authorization.

A proxy, mirror or commercial PNCP service may be useful as a diagnostic aid but can never become primary identity evidence.

## Scientific state

Coverage remains **34/38**.

Still blocked:

- CTRL_Q2
- PROC_Q1
- PROC_Q2
- PROC_Q3

The canonical current label is:

`PNCP_TRANSPORT_OR_EDGE_UNAVAILABLE_FOR_CURRENT_ATTEMPT_NOT_DATA_ABSENCE`

The next active route is primary municipal/TCE identity evidence. PNCP may be revisited later through a controlled multi-origin probe with fresh authorization.

No PNCP/TCE/Drive network, retry, serving, publication, scheduling, recurrence or question promotion occurs in TASK 219E.
