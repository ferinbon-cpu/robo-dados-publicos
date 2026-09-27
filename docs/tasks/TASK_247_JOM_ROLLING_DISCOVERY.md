# TASK 247 — JOM rolling bounded discovery

Issue: #821

## Objective

Convert the already-canonized 2026 Jornal Oficial discovery proof into the first **rolling delta-discovery carrier** for the Observatório, without reopening SIOPE and without silently enabling recurrence, persistence, serving, publication, or document download.

## Proven baseline

TASK217C already closed the historical discovery scope from 01/01/2026 through 08/09/2026:

- 9 monthly partitions;
- 99 official edition identities;
- September through 08/09 = 5 editions;
- September baseline editions = 7316, 7317, 7318, 7319, 7320;
- 9 index pages / 18 estimated remote GETs;
- canonical status `PASS_COMPLETE_DISCOVERY_CANONIZED`.

TASK247 does **not** repeat that work.

## New bounded window

The first rolling delta is fixed to:

- start: **09/09/2026**;
- end: **16/09/2026**;
- source: official Limeira Jornal Oficial index through the existing `JornalOficialLimeira` adapter;
- month query: September 2026 only;
- maximum index pages: 5;
- maximum estimated remote GETs: 10;
- PDF downloads: 0.

The executor first proves that the five canonical September baseline editions are still present. Any missing baseline edition or any additional pre-09/09 edition is treated as drift and stops the run. Only then are edition identities dated 09/09 through 16/09 emitted as the delta.

## Fail-closed boundaries

The carrier rejects:

- partial/pagination-incomplete discovery;
- baseline history regression or backfill drift;
- duplicate edition or source identity;
- edition outside September 2026;
- edition later than the authorized end date;
- non-HTTPS document route;
- document host outside the official declared ecrie host contract;
- request-budget breach;
- live run without owner authorization bound to the exact merged implementation SHA.

A successful result is metadata discovery only. It proves the identities exposed by the official portal in the exact observed window; it does not prove PDF contents and does not authorize inference about future editions.

## Runtime boundary

The workflow is inert on `main`. It can run only from branch `task-247-jom-rolling-discovery-runtime` when `runtime_triggers/task247_jom_rolling_discovery.run` changes. The runtime branch must descend from the exact implementation SHA named in `runtime/task247_owner_authorization.json`; only the authorization and trigger files may differ from that SHA.

The live authorization must keep all of these false:

- document download;
- Drive write;
- serving write;
- publication;
- promotion;
- recurrence;
- schedule.

No `schedule` trigger exists in TASK247.

## Outputs

Offline implementation materializes:

- `config/task247_jom_rolling_discovery.v1.json`;
- `robo_dados_publicos/research/task247_jom_rolling_discovery.py`;
- `.github/workflows/task247_jom_rolling_discovery.yml`;
- `scripts/github_task_247_jom_rolling_discovery_gate.py`;
- focused unit/mutation tests;
- `docs/evidence/TASK_247_JOM_ROLLING_DISCOVERY_CARRIER_0.8.0.json`.

A separately authorized live run may persist only a one-day sanitized GitHub Actions artifact containing the bounded discovery result.

## What remains separate

1. canonization of the live delta after a successful run;
2. PDF acquisition/redigest of newly discovered editions;
3. Drive/Bronze persistence;
4. serving/site update;
5. policy change for automatic recurrence/schedule.

Those steps are intentionally not bundled into TASK247. The purpose of this task is to bridge a solved historical discovery contract into a safe rolling observation primitive.
