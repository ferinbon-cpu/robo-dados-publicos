# TASK 109 — offline visual/OCR capability gate for the remaining PPA 2018–2021 gap

## State entering the task

TASK 108 is merged on main `a6f6f11eb4bfd7ff9a4b07b2742f9b586a91ac90`.

Historical planning state:

- 2022–2025: primary planning signal PROVEN from TASK 107.
- 2026–2029: primary planning signal PROVEN.
- 2018–2021: the only remaining historical primary-planning gap.

TASK 107 already resolved the official 2018–2021 PDF, but pypdf returned empty text. No inference was made from that failure.

## Phase A only

This PR initially performs only a local capability inventory of the GitHub-hosted runner.

It checks whether local commands/modules already exist for:

- OCR;
- PDF/image rendering;
- browser rendering;
- image manipulation.

No package is installed by this phase. No official PPA source is read. No OCR is run on the real document.

## Decision rule

A later commit may build a synthetic image-only PDF proof only after the inventory demonstrates a plausible local chain.

If no safe local chain exists, record STOP and design a separately reviewed dependency route. Do not silently install broad OCR stacks.

## Hard boundaries

No source network, Drive, Bronze/Silver/Gold, StateRegistry, queue, serving, publication, financial identity, transaction identity, implementation proof or causal effect.


## Phase A observed result

CI run `33917496591`, job `101168021407`, on head
`6723aee2ba5391ecff94e0fdbfaa5c779cd2bd51` executed the inventory under the
canonical unittest suite.

Observed local capabilities:

- `google-chrome`: present;
- `chromium`: present;
- `chromedriver`: present;
- Python `PIL`: present;
- `tesseract`: absent;
- `pdftoppm`: absent;
- `pdfimages`: absent;
- `mutool`: absent;
- Ghostscript: absent;
- ImageMagick: absent;
- Python `fitz`, `cv2`, `pytesseract`, `pdf2image`: absent.

### Decision

`STOP_NO_LOCAL_OCR_CHAIN`.

Chrome/PIL availability alone is not accepted as proof that an image-only PDF can
be OCRed deterministically. Because the inventory did not reveal a plausible OCR
chain, TASK 109 does **not** proceed to the synthetic image-only PDF proof and does
not read or OCR the real PPA 2018–2021.

A dependency route must be designed separately. No package installation is
authorized by this task.

## Next boundary

TASK 110 may compare narrowly bounded dependency strategies for a reproducible
Portuguese-capable PDF-image OCR path. It must remain T0/design-only until a
separate reviewed gate authorizes any dependency installation or real-source OCR.
