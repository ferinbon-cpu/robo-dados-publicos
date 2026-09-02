# TASK 041 — F01 JOM-native PPA/LDO scoped Silver readiness review

## Purpose
Review, without new layer writes, the primary Jornal Oficial editions already under custody for PPA 2026–2029 and LDO 2026 and prepare bounded scoped-Silver candidates.

Base reviewed `main`: `ea706547453830cf2df2ed9b1ea0e7fb3276c2ac`.

## Primary sources
- PPA — JOM 7119, 15/11/2025, Lei 7.213/2025, Drive `1ez1B_mJ428IxTIUht1AHM9-I5SCotKXj`, 107 pages, 16,867,824 bytes, SHA-256 `cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a`.
- LDO — JOM 7024, 08/07/2025, Lei 7.141/2025, Drive `1U_E1I1Lbrq5WvedrDPygFuEfQj-ouOex`, 79 pages, 17,615,179 bytes, SHA-256 `44d92a6ac948bbf43dcb3302733faac1a4ed5e592702f66c07f0c6ede4ecb73c`.

Both relevant law ranges have native text layers; OCR is not needed in TASK 041.

## Corrected law boundaries
- PPA Lei 7.213/2025: JOM pages **5–64**, 60 pages. Page 65 starts Lei 7.214/2025.
- LDO Lei 7.141/2025: JOM pages **5–38**, 34 pages. Page 39 starts Portaria 1.666/2025.

The old LDO mapping `5–41` is explicitly superseded. No pages 39–41 may be represented as part of Lei 7.141/2025.

## PPA scoped candidate
Contract: `F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001_SILVER_V1`.

Included only:
- Program 2001 `EDUCACAO QUE INCLUI E TRANSFORMA VIDAS`;
- responsible unit `10.00.00 SECRETARIA DE EDUCACAO`;
- indicator `INDICE DE ALUNOS EM EDUCACAO INTEGRAL / PERCENTUAL`, targets 52, 53, 55, 57, 59, 59;
- directly reviewed rows:
  - 2690 Transporte Escolar — Educação Infantil — 12/365 — 3694, 3842, 4015, 4256, total 15807;
  - 2690 Transporte Escolar — Ensino Fundamental — 12/361 — 8720, 9069, 9477, 10046, total 37312;
  - 2720 Alimentação Escolar — 12/306 — 28000, 29120, 30430, 32256, total 119806.

All values are in `R$ milhares medios/2025` as printed. None of these rows is EITI-specific. The Ensino Médio/Superior row remains `PARSER_REVIEW_REQUIRED` and is not promoted.

The primary JOM table extraction is not treated as machine-complete merely because all pages have a text layer. Critical table values above are limited to direct source verification.

## LDO scoped candidate
Contract: `F01_LDO_JOM_2026_SCOPED_STRUCTURAL_MARKERS_SILVER_V1`.

Included only:
- legal identity and corrected JOM boundary;
- structural markers with first observed JOM page:
  - `METAS_FISCAIS` — 5;
  - `RISCOS_FISCAIS` — 6;
  - `RESERVA_CONTINGENCIA` — 7;
  - `EDUCACAO` — 8;
  - `PESSOAL` — 9.

No fiscal-compliance, MDE/Fundeb-compliance or EITI financial-identity conclusion is authorized or implied.

## Existing LOA state
TASK 040 remains authoritative for the existing LOA scoped Silver:
`SILVER_SCOPED_PARTIAL_VALIDATED`, candidate SHA-256 `3894ede7c67e60d3e12795dec3964d78baf24ff350355d98f3825dd5f81caf4c`.

## TASK 041 effects
Observed source work is limited to two reads of existing Drive custody files for verification. There are no new Drive writes, source-network requests, OCR, Bronze, Silver, Gold, serving or publication effects in this task.

## Readiness decision
If all fail-closed gates pass:
- PPA: `READY_FOR_SCOPED_SILVER_CREATE_ONLY_SEPARATE_AUTH_REQUIRED`;
- LDO: `READY_FOR_SCOPED_SILVER_CREATE_ONLY_SEPARATE_AUTH_REQUIRED`;
- LOA remains `SILVER_SCOPED_PARTIAL_VALIDATED`.

Persisting either new candidate in `02_SILVER` is outside TASK 041 and requires a separately scoped create-only execution with readback.
