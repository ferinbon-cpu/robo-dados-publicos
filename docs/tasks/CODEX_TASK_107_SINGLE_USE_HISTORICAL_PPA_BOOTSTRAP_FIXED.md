# TASK 107 — new single-use historical PPA acquisition with runner bootstrap fixed

## Why a new task

TASK 106 is not rerunnable. Its single-use workflow was consumed after pypdf preflight succeeded, but the runner failed at import time before the bounded HTTP client was instantiated.

Pinned TASK 106 source effects:

- official source HTTP requests: 0;
- primary-source bytes: 0;
- PPA 2018–2021 read: false;
- PPA 2022–2025 read: false;
- source-read scope consumed: false.

TASK 107 is therefore a NEW workflow boundary.

## Runner fix

The TASK 107 runner resolves the repository root from `__file__` and inserts it into `sys.path` before importing any `robo_dados_publicos` module.

It also supports:

    python scripts/run_task107_historical_ppa_live_once.py --preflight-only

This mode:

- proves project imports from a non-repository working directory;
- proves pypdf synthetic text extraction;
- instantiates no source client;
- emits zero source requests.

Offline CI must execute that preflight from a temporary non-repository directory before any live workflow is added.

## Live source contract

Exactly the TASK 103 contract remains in force:

- PPA 2018–2021 / Lei 5.947/2017;
- PPA 2022–2025 / Lei 6.659/2021;
- GET only;
- official Limeira allowlist only;
- max 6 source HTTP requests total;
- max 3 source HTTP requests per period;
- redirects count and remain allowlisted;
- no retry;
- no pagination;
- no recurrence;
- no schedule.

## Hard semantic boundaries

Planning evidence may close planning-document gaps only.

It may not create:

- financial identity;
- transaction execution identity;
- implementation proof;
- causal effect.

## Execution discipline

1. pass 5/5 offline PR checks;
2. add a NEW single-use workflow as final execution commit;
3. workflow proves runner bootstrap + pypdf before source read;
4. execute at most once;
5. pin result and exact executed workflow source;
6. remove workflow before merge.
