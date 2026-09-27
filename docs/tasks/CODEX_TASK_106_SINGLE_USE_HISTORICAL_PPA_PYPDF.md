# TASK 106 — new single-use historical PPA acquisition with proven pypdf parser

Prospective owner authorization is the user's 2026-09-04 instruction `atorizado pra todoase essas etapas prossiga`, followed by `prossiga`. It is interpreted only for the previously described staged sequence. All fail-closed gates remain binding.

## Preconditions

- TASK 103 bounded acquisition contract is merged.
- TASK 104 consumed its workflow mechanism but emitted zero official-source HTTP requests and read zero primary-source bytes.
- TASK 105 proved deterministic PDF text extraction with the project-pinned `pypdf==6.10.0` dependency.
- Main before TASK 106: `c8ec0f968fb947899d5ee29c9b3e973cd95f2f95`.

## Exact source-read scope

Exactly two historical PPA periods:

1. PPA 2018–2021 / Lei Municipal 5.947/2017.
2. PPA 2022–2025 / Lei Municipal 6.659/2021.

The TASK 103 live contract remains authoritative: GET only, allowlisted Limeira official hosts, six source requests maximum total, three maximum per period, redirects counted and allowlisted, no retry and no pagination.

## Parser

TASK 106 uses `pypdf==6.10.0`, already pinned in `requirements.txt` and `pyproject.toml`.

The live workflow may install this exact pinned runtime dependency before any source request. Dependency installation is not counted as an official-source request and is operationally separate from the bounded Limeira source client. No source URL is contacted until the local parser proof succeeds in that run.

The runner must locally create a synthetic PDF and recover its marker with pypdf before invoking the source client.

## Primary-evidence threshold

PRIMARY_MATCH remains unchanged from TASK 104:

- actual PDF bytes;
- exact source SHA-256;
- law identity in extracted PDF text;
- expected historical planning signal;
- one-based source-PDF page locator;
- page-text SHA-256;
- bounded direct-evidence excerpt.

No planning match creates financial identity, transaction execution identity, implementation proof or causal effect.

## Execution discipline

The PR must pass offline CI before the live workflow file is added.

The live workflow is a new workflow, not a rerun of TASK 104. It is path-scoped to its own addition and has no workflow_dispatch, schedule, retry or recurrence.

After execution, preserve exact executed workflow source and result evidence, delete the workflow path, and merge only the inert closure state.
