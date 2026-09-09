# TASK 219C — PNCP exact-identity bridge over the full 99-edition JOM corpus

Issue: #691

## Why this task exists

TASK 219B canonized 449 strong JOM anchor rows into 303 unique administrative identities:

- 195 exact process identifiers;
- 108 exact contract identifiers.

TASK 216 previously queried the complete PNCP contract scope for Limeira from 2026-01-01 through 2026-09-08, but it only had 42 unique JOM identities. TASK 219C repeats the same bounded PNCP source scope against the much larger 303-identity set.

## Exact identity rules

### Process identity

An exact normalized JOM process identifier may identify a PNCP purchase only when all exact PNCP records for that process resolve to one and only one `numeroControlePNCPCompra`.

Supplier identity does not create or veto a process match. A single procurement process may legitimately contain multiple suppliers, lots, contracts, or price-registry entries.

### Contract identity

A JOM contract identifier may match only a PNCP record classified as `CONTRATO`, with the complete exact contract number and exactly one purchase control ID.

If both sides expose supplier CNPJ and they conflict, the contract identity is rejected.

### Never identity

The following remain forbidden as join keys:

- supplier CNPJ alone;
- amount similarity;
- date proximity;
- object or history text;
- semantic similarity;
- incomplete administrative identifiers.

## Network boundary

The live carrier is read-only and bounded to:

- host: `pncp.gov.br`;
- endpoint: `/api/consulta/v1/contratos`;
- CNPJ órgão: `45132495000140`;
- dates: 2026-01-01 through 2026-09-08;
- nine non-overlapping partitions;
- page size: 500;
- at most two pages per partition;
- at most 18 GETs total;
- zero retry and zero redirects.

The prior complete run needed 10 GETs for 1,933 records. The larger cap exists only to fail closed if pagination has grown since that observation.

## Runtime output

The artifact may persist only sanitized information:

- exact accepted JOM↔PNCP identities;
- exact purchase siblings;
- typed PNCP empenho candidates for a later TCE crosswalk;
- conflicts;
- request metadata and completeness counts.

It may not persist raw PNCP pages or payloads.

TASK 219C does not query TCE, does not write Drive, does not serve or publish, and cannot promote any canonical question. A typed PNCP empenho is only a candidate for the later exact TCE join.

A fresh owner authorization pinned to the merged implementation SHA is mandatory before the live runtime. No prior authorization may be reused.
