# TASK 185 — JSON API 2026 fallback

## Purpose

Use the official TCESP JSON expenses API as a bounded fallback when the current-year ZIP body cannot be transported by the active environment.

Official documented route pattern:

`https://transparencia.tce.sp.gov.br/api/json/despesas/{municipio}/{year}/{month}`

The published documentation still labels the exercise range as 2014–2019. The current TCESP portal nevertheless exposes Limeira 2026 expense events in its web UI. Therefore 2026 API support is treated as UNKNOWN until the January probe succeeds.

## Bounded live contract

- exact municipality: `limeira`
- exact fiscal year: `2026`
- exact months: 1–8
- January is the probe
- maximum source GETs: 8
- retry: 0
- redirects: forbidden
- no endpoint discovery
- January invalid/unsupported => STOP before February
- expected JSON top level: array
- required fields: orgao, mes, evento, nr_empenho, id_fornecedor, nm_fornecedor, dt_emissao_despesa, vl_despesa

The single-use authorization mechanism is an exact issue #581 comment bound to the then-current `main` SHA.

## Capability model

The JSON route can support:
- commitment number
- supplier public identity/name
- event date
- event stage
- event amount

It does not prove:
- function/subfunction
- program/action
- funding source/application
- expense element
- procurement modality
- rests payable
- history text

The semantic answerability engine was made capability-aware so product presence alone cannot overclaim these missing dimensions.

## Custody

The workflow preserves every monthly response body byte-for-byte in the GitHub Actions artifact together with SHA-256 hashes, a manifest, the derived ledger, and the 38-question transition report.

After successful readback, the artifact can be copied create-only to the existing Bronze custody folder `01_BRONZE/CONTABILIDADE_LIMEIRA_2025_2026` without issuing another TCESP request.

## No serving

This task does not authorize serving, publication, recurrence, scheduling, or mutation of stable BI surfaces.
