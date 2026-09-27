# CODEX TASK 047 — F01 PPA scoped Silver v2 create-only persistence

## Purpose

TASK 047 records the authorized persistence of the TASK 046 PPA scoped Silver v2 candidate into `02_SILVER` using create-only semantics followed by raw readback verification.

## Authorization

Owner message: `PROSSIGA E ATUALIZE O DRIVE`.

The write was bounded to one new Silver object. The existing PPA Silver v1 remains untouched.

## Persisted object

- file: `F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001__1326c17b53b1__silver_v2.json`
- bytes: `3726`
- SHA-256: `1326c17b53b12064a04cc84123b0414ea77a3e80a8f62fe7cea0dc13eafdd280`
- Drive file id: `168w7l2k7IQilO6tgpFndnneDdWID8eB4`
- target folder: `02_SILVER` (`1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo`)

The raw readback was byte-identical and reproduced the same SHA-256 and byte count.

## Governance

F01 remains `SILVER_SCOPED_PARTIAL_VALIDATED`. The v2 is still a scoped Program 2001/selected-actions representation, not a complete PPA parse. EITI financial identity remains `EVIDENCIA_INSUFICIENTE`.

No overwrite, replacement, delete, OCR, Bronze, Gold, serving or publication occurred.

Canonical result:

`PASS_TASK047_PPA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK_VERIFIED`
