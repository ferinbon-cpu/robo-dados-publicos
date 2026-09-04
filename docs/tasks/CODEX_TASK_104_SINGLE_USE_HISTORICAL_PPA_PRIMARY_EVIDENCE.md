# TASK 104 — single-use live historical PPA primary evidence acquisition

Prospective owner authorization is the user's 2026-09-04 instruction `atorizado pra todoase essas etapas prossiga`, interpreted only for the staged sequence already described in the conversation. Existing fail-closed gates remain binding.

## Precondition

TASK 103 is merged on main and fixes the acquisition contract at:

`config/eiti_historical_ppa_primary_acquisition.v1.json`

Main before this task: `235c17e3cd7677f56c2ea50e56cea2ff6f50f0aa`.

## Exact live scope

Acquire primary planning evidence for exactly two periods:

1. PPA 2018–2021 / Lei Municipal 5.947/2017.
2. PPA 2022–2025 / Lei Municipal 6.659/2021.

For 2018–2021, first read only the official Prefeitura budget index and resolve the exact link whose anchor identifies Lei 5.947 and period 2018/2021. If that bounded official index does not expose one unambiguous link, record NO_MATCH and stop that period. Do not invent a URL or broaden the search automatically.

For 2022–2025, read only the official PDF candidate already pinned by TASK 103.

## Request budget

Maximum six HTTP requests total and maximum three per period, counting redirects. GET only. HTTPS only. Hosts are exactly those already allowlisted by TASK 103. Redirect destinations must remain allowlisted.

No retry, no pagination, no recurrence and no schedule.

## Primary evidence test

A period reaches PRIMARY_MATCH only when the downloaded PDF bytes:

- are actual PDF bytes;
- have a SHA-256 calculated before parsing;
- contain the expected law number in extracted PDF text;
- contain the expected historical planning signal;
- yield a typed one-based source-PDF page locator;
- yield a page-text SHA-256 and bounded direct-evidence excerpt.

A found signal without law identity is at most CANDIDATE_MATCH.

## Local parser

The live runner uses the runner image's preinstalled `pdftotext`. No package installation or third-party network is allowed. If `pdftotext` is unavailable or extraction fails, record a STOP state.

## Hard boundaries

No Google Drive, Bronze, Silver, Gold, StateRegistry, queue, serving or publication effects. No financial identity, transaction identity, implementation or causal effect may be created.

## Single-use workflow

The temporary workflow path is:

`.github/workflows/task-104-historical-ppa-live-once.yml`

It must trigger only when that workflow file itself is added on branch `task-104-historical-ppa-live-once`. It has contents:read only, no secrets and no schedule/workflow_dispatch/retry.

After the run, preserve the exact executed workflow source under docs/evidence and delete the live workflow before merge. No future execution is authorized.
