# TASK 219C2 — half-month PNCP exact-identity fallback

Issue: #691

The first TASK 219C live runtime (run `34364890448`) stopped fail-closed on its first January request with a read timeout after 60 seconds. It received zero bytes, persisted only the sanitized stop record, and produced no scientific identity result. Token 4 was consumed by that authorized attempt and is never reused.

TASK 219C2 changes transport shape without changing the scientific identity model.

## Transport fallback

The exact 2026-01-01 through 2026-09-08 scope is divided into 18 contiguous non-overlapping windows, normally half-month windows. The final September interval is split into 1–4 and 5–8 September.

Each request uses:

- `tamanhoPagina=250`;
- at most 3 pages per partition;
- at most 54 remote GETs total;
- 120-second timeout;
- zero retry;
- zero redirects.

This is intentionally more conservative than the prior monthly page-size-500 shape. The old complete TASK 216B run needed only ten requests for 1,933 records, but a new live observation must not assume that the transport remains equally responsive.

## Identity model is unchanged

Input is the TASK 219B canonical set:

- 449 anchor rows;
- 303 unique exact administrative identities;
- 195 exact process identifiers;
- 108 exact contract identifiers.

A process match requires the exact normalized process identifier to resolve to exactly one PNCP purchase control ID. Supplier CNPJ cannot create or veto a process match.

A contract match requires an exact complete contract identifier on a typed PNCP contract record, one purchase control ID, and no known supplier conflict.

CNPJ alone, amount, date, object/history text, semantic similarity and incomplete identifiers remain forbidden as identity inputs.

## Runtime restrictions

The runtime can read only the bounded PNCP scope and can persist only one sanitized result artifact. It cannot query TCE, write Drive, serve, publish, promote questions, schedule, recur or reuse any prior authorization.

A fresh authorization pinned to the merged TASK 219C2 implementation SHA is required. The intended next consumable authorization is Token 5.
