# TASK 042 — F01 PPA/LDO scoped Silver persistence review

## Purpose

Pin and review the two create-only Silver writes authorized after TASK 041 for the JOM-native scoped PPA and LDO candidates. This task is a post-write, fail-closed review; it does not perform additional source collection or downstream promotion.

## Authorized and observed boundary

- base implementation/main: `319b4ac04c191f17f19f46ea47ce7da24b4ed50e`
- owner command: `Prossiga`
- target: `02_SILVER`
- preflight inventory: exactly one bounded listing, zero target collisions
- creates: exactly two create-only JSON objects
- readbacks: exactly two complete raw-file readbacks
- overwrite/replace/delete/cleanup/retry: zero
- source GET/OCR/Bronze/Gold/serving/publication: zero

## Persisted candidates

### PPA 2026–2029

`F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001__0cba09dade1c__silver_v1.json`

- contract: `F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001_SILVER_V1`
- scope: `SCOPED_PROGRAM_2001_AND_SELECTED_ACTIONS_NOT_COMPLETE_PPA_PARSE`
- bytes: 2812
- SHA-256: `0cba09dade1c09224e549e817a859c63edb12a6fb0a5223c5ddb8aa5fe6dc730`
- MD5: `0b35160ccaece5c6b7eb29786576a7b7`
- readback: byte-identical

### LDO 2026

`F01_LDO_JOM_2026_SCOPED_STRUCTURAL_MARKERS__4719631a3dd4__silver_v1.json`

- contract: `F01_LDO_JOM_2026_SCOPED_STRUCTURAL_MARKERS_SILVER_V1`
- scope: `SCOPED_LEGAL_IDENTITY_AND_STRUCTURAL_MARKERS_NOT_COMPLETE_LDO_PARSE`
- bytes: 1544
- SHA-256: `4719631a3dd476efe8c760f2b9ce07eba15d678c85b56e95345af70237f02182`
- MD5: `1dc39a4ac76aaabdb64e776eb30ac51b`
- readback: byte-identical

## Governance

TASK 041 remains the authority for candidate content and readiness. The PPA candidate is not a complete PPA parse and retains the ambiguous Ensino Médio/Superior row as unpromoted review material. The LDO candidate is limited to legal identity, the corrected JOM boundary 5–38 and structural markers; it is not a complete LDO parse.

F01 remains `SILVER_SCOPED_PARTIAL_VALIDATED`, now with scoped Silver objects for LOA, PPA and LDO. No Gold, serving, publication, fiscal-compliance conclusion or EITI financial-identity claim is authorized. `EVIDENCIA_INSUFICIENTE` remains the correct EITI financial-identity status.
