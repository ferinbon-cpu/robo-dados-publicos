# Jornal Oficial de Limeira — research notes — 2026-08-21

## Evidence-led findings
- The public page exposes recent editions and a searchable archive.
- Public query URLs indexed by search engines show `ano` + `mes` and `dataDiario` parameters.
- Search-by-term requires a complete date interval when invoked through the public page.
- The current archive explicitly links to an older archive around the February 2023 platform transition.
- The older archive exposes edition-labelled PDFs; a verified indexed example is edition 6411 at `/jornal/6411.pdf`.
- A recent indexed PDF (edition 6952, 27/03/2025) states that the digital Jornal Oficial was created by Municipal Law 5909/2017, circulates Tuesday through Saturday, and that access is free without registration.
- Recent Limeira PDFs are frequently hosted under eCrie's DiarioOficial upload area, but filenames are treated as opaque provider identifiers and MUST NOT be guessed.

## Engineering consequence
The Jornal Oficial can likely become the first fully automated municipal connector because its public index is server-readable and the documents are PDF-oriented, unlike the more opaque scripted TDA surface. The connector must still be live-validated before production activation.
