# CODEX TASK 037 - LOA JOM targeted OCR review

## Base and authorization
- base `main`: `eb8f370e6957de5788bbfbbe97d8cd77c5fb9632`
- owner instruction: `Prossiga`
- authorized scope: exact-byte Drive read of the already-custodied JOM 7127, render only pages 475-481, targeted OCR of only those seven pages, and recording derived evidence.
- not authorized: public source discovery, Drive write, full-document OCR, silent OCR repair, LLM numeric reconstruction, Bronze/Silver/Gold, serving, publication.

## Source
- `SOURCE_JOM_7127_2025-11-29_LOA_7223_2025.pdf`
- Drive file id: `1bRpmMxacX16P1tJBvam-55OOPTYuQnIA`
- bytes: `66,119,594`
- pages: `631`
- SHA-256: `37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4`

The source was downloaded once from the existing Drive custody and reverified byte-for-byte before rendering.

## Deterministic targeted extraction
Only pages `475-481` were rendered:
- renderer: PyMuPDF `1.26.7`
- 300 DPI
- RGB
- alpha disabled
- render config SHA-256: `f34141496ad0fffcd7f47809855709a8f777f8be77fe7929fb35b7dd95e3f68d`

OCR:
- Tesseract `5.5.0`
- language `eng`
- OEM `1`
- PSM `6`
- `preserve_interword_spaces=1`
- OCR config SHA-256: `4b7482b941944c0de111d178cc4ba7f8c02e18033d16c99de2e23aa327ee4252`
- executed twice against the same seven rendered images
- all seven OCR text SHA-256 values were identical across both runs

## Result
The seven pages now have pinned image and OCR-text hashes. Pages 475-479 recover candidate textual content from the end of the LOA annexes. Pages 480-481 contain numeric tables and remain `REVIEW_REQUIRED_NUMERIC_TABLE`.

The OCR itself is not committed as source truth. The hashes are sufficient to reproduce the same OCR output from the exact custodied PDF and pinned render/OCR configuration.

Important boundaries:
- OCR output is derived evidence only.
- No OCR numeric value is source truth.
- No critical numeric automatic promotion.
- No silent character repair.
- No LLM numeric reconstruction.
- Visual or independent validation remains required for numeric use.
- F01 remains `NOT_SILVER`.

Manifest rows SHA-256: `528bfaf3bf305d395eb874f9e0d22181a93e4e9b80a9b6c4512c11346ac5f773`  
Image hash-chain SHA-256: `5d6a9f73b1dd28448292c585fad9eb51afe5ee67a205aa57f432096e714fe0f3`  
OCR text hash-chain SHA-256: `d826be350ed7f6de6cc3e4e090197fdb2785bff49c619c8a000ba86f167201ec`  
OCR text total characters: `16,732`

## Page-level interpretation
- 475-479: `ESPECIFICACAO DA LEGISLACAO DA DESPESA` candidates.
- 480: `DEMONSTRATIVO DAS TRANSFERENCIAS FINANCEIRAS` - numeric table, review required.
- 481: `DEMONSTRATIVO DA COMPATIBILIDADE DA PROGRAMACAO DO ORCAMENTO COM AS METAS DE RESULTADOS FISCAIS` - numeric table, review required.

## Next gate
A later, separately authorized task may visually or independently validate selected structural fields and values from pages 480-481 and reconcile them against LDO/LOA totals. This task itself performs no promotion.
