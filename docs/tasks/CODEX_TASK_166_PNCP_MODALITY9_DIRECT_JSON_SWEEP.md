# TASK 166 — PNCP modality 9 direct JSON sweep

This task applies the robot-wide DIRECT_JSON_FIRST policy to the official PNCP public consultation endpoint.

Standing authorization is reused from TASK 161 and covers PNCP live read/discovery. No per-page authorization is required inside the same PNCP read-only scope.

Exact query scope:

- CNPJ 45132495000140;
- publication window 2025-11-28 through 2026-09-04;
- modality 9 — Inexigibilidade;
- page size 50.

The live workflow fetches page 1 directly as JSON, reads official pagination metadata, and follows only declared pages up to a fail-closed cap. It validates entity and modality identity before normalized records can enter the result.

Primary targets:

- `AQUISICAO DE PASSE ESCOLAR`, estimated R$ 3,816,720;
- process `I00084`, `CURSO DE CAPACITACAO`, estimated R$ 12,400.

Raw PNCP response bodies are never persisted to Git, Drive, or workflow artifacts. Only normalized selected fields, hashes/byte counts, pagination metadata, target hits and semantic screens are uploaded temporarily.

A transport, JSON, schema, entity, modality, page-count, or pagination failure stops without creating NO_MATCH.
