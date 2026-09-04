# TASK 111 — synthetic proof of the pinned OCR route

## Purpose

Prove the exact TASK 110 Poppler → Tesseract Portuguese TSV route before any OCR of the real PPA 2018–2021.

## Dependencies downloaded

Exact Ubuntu 24.04 / amd64 packages:

- `poppler-utils=24.02.0-1ubuntu9.9`;
- `tesseract-ocr=5.3.4-1build5`;
- `tesseract-ocr-por=1:4.1.0-2`.

Testing dependency already pinned by the project:

- `pypdf==6.10.0`.

No OCRmyPDF, PyMuPDF, pytesseract, OpenCV, Ghostscript or ImageMagick were installed.

## Attempt 1

Run `33919509155`, job `101174340312`.

The package installation and exact-version checks passed, but the synthetic fixture failed the image-only assertion because the Chrome print path added PDF header/footer text. This was a fixture defect, not an OCR dependency defect.

No PPA source was read.

## Successful proof

Run `33919583422`, job `101174577341`, head `67f6b6f05ee444990cb0767fc4b0f05a826d1223`.

The corrected fixture disabled PDF headers/footers.

Observed result:

- synthetic PDF pages: 1;
- pypdf extracted text: empty;
- Poppler rendered source page 1 at 300 DPI grayscale;
- Tesseract language: `por`;
- normalized OCR text: `TASK111 MARCADOR OCR 73159 EDUCACAO INTEGRAL LIMEIRA`;
- ASCII marker recovered: yes;
- Portuguese phrase recovered: yes;
- confidence-bearing OCR words: 7;
- minimum confidence: 91.055252;
- maximum confidence: 96.537155;
- synthetic PDF SHA-256: `c3b8a549e64b6a933a4e762a70e26ffd2d2633e3c9f140dbc709954905485272`;
- rendered page SHA-256: `28c86fe1035e100f1a3049375cc14ec78382c4567e7bf0dfdad8b8e97451c7fd`;
- OCR TSV SHA-256: `ce34e5ad0e8e7f53ed0a550e12765b97613b21c8a5a41c907e205f7a15ae25d3`.

## Decision

`PASS_SYNTHETIC_OCR_ROUTE_PROVEN`.

The missing OCR dependencies have been demonstrated to work together deterministically on image-only synthetic material.

## Boundary

TASK 111 does not authorize OCR of the real PPA.

A separate gate is still required for the already-resolved official PPA 2018–2021. Financial identity, transaction execution, implementation and causal effects remain outside the OCR evidence boundary.
