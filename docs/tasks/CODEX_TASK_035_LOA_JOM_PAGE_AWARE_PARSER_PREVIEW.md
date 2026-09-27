# TASK 035 — LOA JOM page-aware parser preview

## Decision
The JOM 7127 text layer is OCR-derived and is useful for navigation and structural candidate discovery, but it is not trustworthy enough for automatic critical numeric promotion.

Direct page rendering exposed a material example: on JOM page 173 the OCR text reports the Alimentação Escolar unit/program total as R$ 29.000.000,00, while the source page image shows R$ 28.000.000,00. On page 174 the OCR layer corrupts `12.306.2001.2720` as `12. 30 6 . 2001. 2 ~20` and again reports R$ 29.000.000,00 where the rendered source shows R$ 28.000.000,00.

Therefore the parser is deliberately two-stage:
1. OCR-derived text may identify pages, exact digit codes when present, and numeric candidates.
2. Critical numeric values and corrupted codes require visual or independent validation before any downstream promotion.

No silent character repair and no LLM numeric reconstruction are permitted.

## Directly verified bridge rows
- JOM page 171 / internal LOA page 124: `12.362.2001.2690 TRANSPORTE ESCOLAR`, R$ 6.152.000,00. Text and visual source agree.
- JOM page 174 / internal LOA page 127: `12.306.2001.2720 ALIMENTACAO ESCOLAR`, R$ 28.000.000,00. This is source-verified visually; the OCR text is materially wrong.

Both are broad Program 2001 actions and remain `eiti_specific=false`. Their presence does not prove EITI financial identity.

## Page policy
- pages 375, 386, 413, 415, 421, 426: `SKIP_BLANK`;
- pages 475–481: `REVIEW_REQUIRED_TARGETED_EXTRACTION`;
- other pages 15–481: candidate parsing only.

## Governance
TASK 035 adds offline parser logic, fixtures, tests and pinned evidence. It performs no source GET, no Drive write, no OCR execution and no Bronze/Silver/Gold/serving/publication. F01 remains `NOT_SILVER`.

## Next boundary
After CI/merge, the next step is a bounded parser run over the already-custodied LOA to build a page-indexed candidate manifest. The manifest must keep numeric confidence explicit and cannot become Silver until the required page/source validations close.
