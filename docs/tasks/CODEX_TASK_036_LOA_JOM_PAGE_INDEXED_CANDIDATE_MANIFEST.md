# TASK 036 — LOA JOM page-indexed candidate manifest

## Objective
Run the deterministic candidate index over the exact-byte JOM 7127 source and pin a reproducible page-level manifest boundary without treating OCR-derived numbers as source truth.

## Input and execution boundary
The run used `SOURCE_JOM_7127_2025-11-29_LOA_7223_2025.pdf`, 66,119,594 bytes, SHA-256 `37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4`, matching the already-custodied source. The runtime input was a conversation-materialized exact-byte copy, so this task performed no new public-source GET and no Drive read/write.

Text extraction used PyMuPDF 1.26.7 over the existing OCR-derived text layer. No new OCR was executed.

## Page manifest result
The LOA boundary remains pages 15–481 inclusive: 467 pages.

- 454 pages are eligible for text-layer candidate parsing.
- 6 visually blank pages remain `SKIP_BLANK`: 375, 386, 413, 415, 421 and 426.
- 7 substantive pages remain `REVIEW_REQUIRED_TARGETED_EXTRACTION`: 475–481.
- 453 pages finish as `PARSED_CANDIDATES_ONLY`.
- Exactly one page, 174, remains `REVIEW_REQUIRED_CODE_CORRUPTION` under the stricter corruption detector.

The run observed 18 pages carrying digit-exact education action codes, with 49 exact code occurrences. It also detected 6,060 OCR-text monetary candidates across 347 pages, but their values are deliberately not committed into the manifest and are not promotable.

The page-row digest is `92c1b5ee1ddab8b2269219fd8f82897ab490d7f9513cbc01358386d111ee56af`; the ordered page/text hash-chain digest is `9d3df16b1132d3ecb99405ce67fd07dac3b027b06a7735748adc243f1c3c0b10`.

## Heuristic hardening
The TASK 035 preview detector had a broad fail-closed fallback that also flagged page 392 because unrelated OCR noise (`~`) appeared on a Program 2001 page. TASK 036 tightens this rule: corrupted action-code review now requires the noisy final token to be locally anchored to an exact `12.xxx.xxxx.` stem.

This preserves the real page 174 corruption (`12.306.2001.2720` rendered visually but corrupted in the OCR layer) while removing the page 392 false positive.

## Exact action-code index
A compact source-bound index is committed separately in `TASK_036_LOA_JOM_ACTION_CODE_INDEX_0.8.0.json`. It contains only digit-exact action codes found by the text layer, not inferred repairs.

Directly source-validated bridge rows from TASK 035 remain:
- page 171: `12.362.2001.2690 TRANSPORTE ESCOLAR`, R$ 6,152,000.00;
- page 174: `12.306.2001.2720 ALIMENTACAO ESCOLAR`, R$ 28,000,000.00, visually verified because OCR is materially wrong.

Both remain broad Program 2001 actions and `eiti_specific=false`; neither proves EITI financial identity.

## Governance
No Bronze, Silver, Gold, serving or publication promotion occurs. F01 remains `NOT_SILVER`, and EITI financial identity remains `EVIDENCIA_INSUFICIENTE`.

## Next boundary
Close pages 475–481 through targeted visual extraction or deterministic targeted OCR, and selectively validate any critical numeric candidates required for the F01 structured model. Silver remains blocked until those closures and QA pass.
