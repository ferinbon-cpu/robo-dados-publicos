# TASK 034 — LOA JOM text-layer readiness

## Objective
Pin the read-only structural review of the custodied Jornal Oficial edition 7127 and define the smallest safe extraction boundary for Lei 7.223/2025 before any parser/OCR/Silver work.

## Source reviewed
- Drive file: `SOURCE_JOM_7127_2025-11-29_LOA_7223_2025.pdf`
- Drive id: `1bRpmMxacX16P1tJBvam-55OOPTYuQnIA`
- bytes: `66119594`
- SHA-256: `37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4`
- edition: `7127`
- total pages: `631`

## Proven LOA boundary
The law starts on Jornal page 15 with `LEI N.º 7.223 DE 28 DE NOVEMBRO DE 2025`.

Visual and text review proves that page 481 still belongs to the LOA annexes. Page 482 starts another act, `PORTARIA Nº 2.084, DE 13 DE NOVEMBRO DE 2025`.

Therefore the LOA block is **pages 15–481 inclusive (467 Jornal pages)**. The previous arithmetic candidate ending at page 480 is superseded by direct visual evidence.

## Text-layer result
The PDF has extracted text on every page, but the LOA block is not uniformly machine-readable.

Within pages 15–481:
- 454 pages contain native/extracted content text suitable for deterministic parser work;
- 6 pages are visually blank inside the law block: `375, 386, 413, 415, 421, 426`;
- exactly 7 pages contain visible LOA content but only header/footer in the text layer: `475, 476, 477, 478, 479, 480, 481`.

Those seven pages are the only targeted extraction/OCR review set currently proven. A full-document OCR of the 466-page standalone LOA or the 467-page Jornal law block is **not required** by this evidence.

## Visual review of the seven targeted pages
The pages remain substantive LOA material:
- 475–479: `ESPECIFICACAO DA LEGISLACAO DA DESPESA` for remaining entities/units;
- 480: `MENSAGEM - ANEXO I` / demonstrativo das transferências financeiras;
- 481: demonstrativo da compatibilidade da programação do orçamento com as metas de resultados fiscais.

No numeric values from these image-only pages are promoted in TASK 034.

## Governance
TASK 034 is read-only analysis of an already-custodied source. It performs no source GET, no Drive write, no OCR, no parser, no Bronze/Silver/Gold, no serving and no publication.

F01 remains `NOT_SILVER`.

## Next boundary
Implement a deterministic, page-aware LOA parser over the native text pages, skipping visually blank pages and returning `REVIEW_REQUIRED` for pages 475–481. Handle those seven pages separately with a targeted extraction path. Do not start full-document OCR and do not promote Silver until the page-aware parser plus targeted-page closure pass QA.
