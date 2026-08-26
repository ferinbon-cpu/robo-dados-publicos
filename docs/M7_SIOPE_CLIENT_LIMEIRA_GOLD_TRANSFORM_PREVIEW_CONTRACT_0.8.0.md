# M7 — SIOPE Limeira Gold transform preview contract — 0.8.0

## Purpose

Create a deterministic, offline analytical preview from the exact Silver payload whose Drive readback was verified byte-for-byte. This gate does not write to Drive and does not authorize Gold persistence.

## Proven prerequisite

The pinned Silver readback run `33022961421` verified one remote file, one download, zero writes, exact byte identity, MD5, SHA-256, one record and 52 fields. The Silver payload SHA-256 is `072283e3d9e5f12e6a3a697d32e653b64e618f4665e28f53e553b35506ce68da`.

## Semantic boundary

The Gold preview is `DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS`. It may calculate ratios and per-capita values from the pinned public SIOPE record. It must not claim or infer:

- constitutional MDE compliance;
- Fundeb compliance;
- fiscal-audit conclusions;
- legal regularity;
- imputed values.

## Metrics

The preview computes exactly eight deterministic metrics:

1. realized revenue / updated revenue forecast (%);
2. paid total expenditure / updated total appropriation (%);
3. paid education expenditure / updated education appropriation (%);
4. education share of committed expenditure (%);
5. education share of liquidated expenditure (%);
6. education share of paid expenditure (%);
7. paid total expenditure per inhabitant;
8. paid education expenditure per inhabitant.

Percentages use `Decimal`, `ROUND_HALF_UP` and four decimal places. Per-capita values use `Decimal`, `ROUND_HALF_UP` and two decimal places.

## Fail-closed rules

The gate stops on config drift, Silver hash/size/contract drift, identity drift, schema drift, missing/non-numeric/non-finite/negative inputs, invalid positive denominators or population, or metric-set drift.

## Operational boundary

- source network: disabled;
- Drive network: disabled;
- Drive writes: zero;
- Gold persistence: disabled;
- overwrite/delete/replace: not present;
- processing authorization: false;
- recurrence: false;
- schedule: false.

A successful preview only authorizes an offline review of the preview evidence. A later create-only write into `03_GOLD` requires a separate reviewed gate.
