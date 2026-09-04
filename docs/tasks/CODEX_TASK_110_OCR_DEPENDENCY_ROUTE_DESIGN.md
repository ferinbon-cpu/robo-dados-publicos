# TASK 110 — T0 OCR dependency route design for PPA 2018–2021

## Context

TASK 109 proved that the GitHub-hosted runner has Chrome/Chromium/ChromeDriver but no usable local OCR chain, and that Chrome accessibility does not recover text from a genuinely image-only PDF.

The only remaining historical primary-planning gap is PPA 2018–2021.

## Canonical route

The minimal proposed chain is:

1. **Poppler `pdftoppm`** renders one source PDF page to a 300-DPI grayscale PNG.
2. **Tesseract CLI** reads that PNG with the Portuguese language model `por`.
3. Tesseract emits **TSV** so recognized words and confidence metadata are preserved.
4. The robot reconstructs normalized text deterministically from TSV and searches only for the already-declared historical planning signal.
5. Provenance preserves source PDF SHA-256, one-based source page, rendered PNG SHA-256 and OCR TSV SHA-256.

Pinned Ubuntu 24.04 / amd64 package candidates:

- `poppler-utils=24.02.0-1ubuntu9.9`;
- `tesseract-ocr=5.3.4-1build5`;
- `tesseract-ocr-por=1:4.1.0-2`.

No Python OCR wrapper is necessary. The initial route intentionally excludes pytesseract, OCRmyPDF, PyMuPDF, OpenCV, Ghostscript and ImageMagick.

## Why TSV

TSV keeps word-level confidence and bounding metadata while still allowing deterministic normalized-text reconstruction. One OCR pass therefore supplies both searchable content and evidence-quality metadata.

## Mandatory synthetic gate before any real PPA OCR

A later TASK 111 may install only the three exact packages above and must prove, on synthetic image-only material:

- installed versions are exact;
- Portuguese language `por` is available;
- the synthetic PDF has no text layer under pypdf;
- PDF page 1 maps to rendered page 1;
- Tesseract recovers an ASCII marker;
- a Portuguese phrase is recoverable after the repository's normalization rule;
- TSV confidence exists;
- rendered-page and TSV hashes are recorded.

TASK 110 itself does **not** authorize that installation.

## Future real-source boundary

Only after a positive TASK 111 synthetic proof may a new task authorize OCR of the already-resolved official PPA URL.

That future source read must remain exact-URL only, GET-only, same-host bounded, no discovery search, no retry, maximum 250 PDF pages, and no semantic promotion beyond primary planning evidence.

Financial identity, transaction execution, implementation and causal effect remain outside this route.
