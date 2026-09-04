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

### Interim decision after inventory

`STOP_NO_LOCAL_OCR_CHAIN`.

The inventory established that no OCR engine/render chain was already available.
Chrome/Chromium/ChromeDriver remained the only plausible dependency-free local
surface worth testing. That narrower question was therefore isolated in one
synthetic-only sub-gate below; the real PPA remained outside the task.

No OCR stack installation was authorized. The only dependency used by the later
synthetic proof was the already-pinned project dependency `pypdf==6.10.0`, solely
to prove that the generated fixture had no extractable text layer.

## Synthetic image-only Chrome proof

Because Chrome/Chromium/ChromeDriver were present, one additional local-only sub-gate tested whether Chrome accessibility could recover text without installing an OCR stack.

Run `33917837446`, job `101169024384`, execution head
`5d886bc0d2b528a53d21a67020bd3dbeffe072b4`.

The workflow installed only the already-pinned project dependency `pypdf==6.10.0` to verify that the generated PDF truly had no extractable text layer. It did not install Tesseract, Poppler, Ghostscript, ImageMagick, PyMuPDF, OpenCV or any OCR package.

Observed synthetic proof:

- raster PNG: 18,356 bytes;
- image-only PDF: 18,287 bytes;
- PDF pages: 1;
- pypdf text: empty;
- Chrome accessibility strings: 0;
- marker in accessibility tree: false;
- marker in page source: false;
- marker in body innerText: false;
- source reads: 0;
- real-source OCR: false.

### Final TASK 109 decision

`STOP_NO_LOCAL_OCR_CHAIN_CHROME_IMAGE_ONLY_NEGATIVE`.

Chrome renders the image-only PDF but does not expose a usable text/OCR channel in this runner configuration. Therefore the remaining PPA 2018–2021 gap cannot be closed with the currently available local toolchain.

The real official PPA was not reread and was not OCRed in TASK 109.

## Next boundary

TASK 110 may compare narrowly bounded dependency strategies for a reproducible Portuguese-capable PDF-image OCR path. It must remain T0/design-only until a separately reviewed gate authorizes any new OCR dependency installation or real-source OCR.
