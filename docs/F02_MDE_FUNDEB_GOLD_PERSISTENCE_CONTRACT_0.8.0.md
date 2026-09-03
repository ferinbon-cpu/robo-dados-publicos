# F02 MDE/FUNDEB Gold create-only persistence contract — 0.8.0

## Purpose

Persist exactly one already-reviewed deterministic F02 Gold payload into `03_GOLD` and then record one compact execution manifest in `07_LOGS`.

This contract does not authorize serving, publication, site mutation, source collection, overwrite, delete, move, schedule or recurrence.

## Owner authorization chain

Owner instruction: **"tome 10 tokens de autorização, bote o deepseek pra fritar no trabalho"**.

Authorization model: ten sequential bounded gates.

This contract is materialized during token 7. The actual remote persistence is reserved for token 10 and must not occur before:
1. this contract and its verifier are merged;
2. CI is green on the exact PR head;
3. automatic DeepSeek review of the persistence PR has no concrete blocking finding;
4. the merge is pinned and verified.

## Pinned Gold candidate

- schema: `F02_MDE_FUNDEB_GOLD_PREVIEW_V1`
- logical content SHA-256: `38232ab8e02a3afc5444d3ef8f6276f056f29a001d62b2b2dc1d571a0a79e90d`
- rendered JSON bytes: `4231`
- rendered SHA-256: `e2ef3f4eef403730f54c8f8ddfd5dcbf3facd5131a6cedd0cb356ffce7354fe1`
- exact observations: `24.27`, `23.60`, `88.67`, `96.99`

The candidate must be rebuilt offline from the two exact Silver snapshots already pinned by the Gold preview config. No manually reconstructed substitute is allowed.

## Target

Gold folder:
- name: `03_GOLD`
- Drive folder ID: `1hAmQNBnY6MNBtyr14ACfVfRkmWhsoRq4`

Gold filename:
- `F02_MDE_FUNDEB_2026_GOLD__38232ab8e02a__gold_v1.json`

Execution-log folder:
- name: `07_LOGS`
- Drive folder ID: `1H2ggRDWZ3Zf5LF_ze8po8zU_Uf_IbvoU`

Manifest filename:
- `F02_MDE_FUNDEB_2026_GOLD_PERSISTENCE__38232ab8e02a__manifest_v1.json`

## Exact allowed remote effects for token 10

- pre-write existence lookup in the exact target folder: allowed;
- Gold create-only writes: exactly **1** if and only if no file with the target name/hash already exists;
- Gold readback: exactly **1**;
- log manifest create-only writes: exactly **1**, only after successful Gold readback;
- log manifest readback: exactly **1**.

If an identical Gold object already exists, STOP as `ALREADY_PRESENT` and do not create a duplicate.

## Required readback

The Gold readback must prove:
- exact byte length 4231;
- exact SHA-256 `e2ef3f4eef403730f54c8f8ddfd5dcbf3facd5131a6cedd0cb356ffce7354fe1`;
- parsed `content_sha256` equals `38232ab8e02a3afc5444d3ef8f6276f056f29a001d62b2b2dc1d571a0a79e90d`;
- schema and four observation identities unchanged.

The execution manifest must record the Gold Drive ID returned by the write and the verified readback identity. It may not claim serving/publication.

## Forbidden effects

- Silver mutation;
- Bronze mutation;
- source/network collection;
- more than one Gold create;
- overwrite/replace/update existing Gold;
- delete/move;
- serving;
- publication;
- site mutation;
- schedule/recurrence;
- compliance promotion beyond the typed claims already in the Gold payload.

Any drift is STOP.
