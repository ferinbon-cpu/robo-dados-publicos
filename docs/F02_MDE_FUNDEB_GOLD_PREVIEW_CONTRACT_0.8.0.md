# F02 MDE/FUNDEB Gold preview contract — 0.8.0

## Purpose

Build a deterministic offline Gold **preview** from two already-promoted, byte-verified F02 Silver artifacts. The preview curates typed observations; it does not persist Gold.

## Pinned Silver inputs

The config pins exact Drive IDs, byte sizes, file SHA-256, logical content SHA-256, schema and status for:
- Jan–Apr/2026 F02 Silver with same-period RREO;
- Jan–May/2026 F02 local-monitoring Silver without same-period RREO.

Any drift is a STOP.

## Semantic boundary

Gold is not a license to erase provenance. The preview emits exactly four observations:

1. MDE Jan–Apr official partial RREO observation;
2. MDE Jan–May local monitoring observation;
3. FUNDEB professionals Jan–Apr official partial RREO observation;
4. FUNDEB professionals Jan–May local monitoring observation.

Every observation must retain exact period, authority, claim class, source Silver identity, source metric and value.

The following are forbidden:
- treating Jan–May local MDE as official MDE;
- annual compliance conclusions from partial data;
- combining Jan–Apr and Jan–May as the same period;
- combining RREO authority with local-monitoring authority;
- imputation, forward fill or inferred May RREO;
- replacing an observation with a derived comparison across incompatible periods/authorities.

## Fail-closed rules

STOP on:
- Silver file hash, byte length, logical hash, schema or status drift;
- missing expected normalized family;
- missing/non-numeric/non-finite/negative metric;
- source period drift;
- authority drift;
- observation-set drift;
- duplicated observation IDs;
- any semantic-policy permission becoming true;
- any remote/write/persistence/serving/publication/site/delete/move/overwrite/recurrence/schedule permission becoming true.

## Operational boundary

This gate is offline only. It makes zero Drive calls and zero writes.

A passing preview authorizes only review of the Gold candidate and its evidence. A create-only write into `03_GOLD` requires a later, separately reviewed owner gate.
