# CODEX TASK 045 — F01 bounded existing-custody read-only review

## Governance boundary

TASK 045 consumes the owner's fresh authorization `Autorizado e prossiga`, granted on 2026-09-02 at 16:40 -03:00 and pinned to reviewed main `8c9638859fef42527d99181f846f264a545e9af6`.

The authorized tier is exactly `T1_EXISTING_CUSTODY_READONLY`, carrying forward the TASK 044 design. The review is limited to two already-custodied primary Jornal Oficial PDFs and exactly twelve pages:

- PPA JOM 7119: pages 15–16;
- LOA JOM 7127: pages 153–156 and 170–175.

No public-source network request, Drive write, OCR, Bronze, Silver write, Gold, serving or publication is authorized or performed. Local materialization is used only to verify whole-file hashes and render the authorized pages for direct visual inspection.

## Source closure

The PPA source is pinned to Drive file `1ez1B_mJ428IxTIUht1AHM9-I5SCotKXj`, SHA-256 `cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a`, 107 PDF pages.

The LOA source is pinned to Drive file `1bRpmMxacX16P1tJBvam-55OOPTYuQnIA`, SHA-256 `37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4`, 631 PDF pages.

All twelve authorized pages were rendered at 220 DPI without OCR. The render-chain SHA-256 is `eb24c0c0686f25b90d7b9d23fb740e7e09600392122f43dc08557e18a179ce0e`.

## PPA 2690 direct resolution

Direct visual review of primary-JOM page 15 resolves the previously blocked Program 2001 row:

- action 2690 — TRANSPORTE ESCOLAR;
- education level: ENSINO MEDIO E SUPERIOR;
- function/subfunction: 12/362;
- product: ALUNOS TRANSPORTADOS, unit UNIDADES;
- financial unit: R$ milhares medios / 2025;
- 2026: 16.020;
- 2027: 15.520;
- 2028: 15.521;
- 2029: 15.522;
- total: 62.583;
- physical targets: 180, 190, 200, 210.

The prior `PARSER_REVIEW_REQUIRED` condition is therefore resolved at evidence level as `RESOLVED_DIRECT_PRIMARY_JOM_VISUAL_SOURCE`. TASK 045 does not mutate the persisted PPA Silver v1.

## LOA explicit action context

For `12.362.2001.2690 TRANSPORTE ESCOLAR`, pages 170–171 explicitly establish unit `10.04.00 ENSINO MEDIO E SUPERIOR`, Program 2001, appropriation R$ 6.152.000,00 and action-level source totals of R$ 943.000,00 Tesouro plus R$ 5.209.000,00 Transferências e Convênios Estaduais - Vinculados. The selected pages expose group/modalidade information, but not a complete expense-nature code; that field remains `UNKNOWN_NOT_EXPLICIT_ON_SELECTED_PAGES`.

For `12.306.2001.2720 ALIMENTACAO ESCOLAR`, pages 173–174 explicitly establish unit `10.05.00 ALIMENTACAO ESCOLAR`, Program 2001, visual-source appropriation R$ 28.000.000,00 and source totals of R$ 8.680.000,00 Tesouro plus R$ 19.320.000,00 Transferências e Convênios Federais - Vinculados. Complete expense nature remains unknown on the selected pages.

LOA enactment does not establish committed, liquidated or paid stages; no execution stage is inferred.

## Material text/visual divergence

A material divergence is deliberately preserved rather than silently repaired. The extracted text layer on LOA pages 173–174 reports R$ 29.000.000,00 in places, while the directly rendered primary source shows R$ 28.000.000,00. TASK 045 records `REVIEW_STOP_DIRECT_VISUAL_SOURCE_RECORDED`, with no silent repair and no automatic promotion.

## Reconciliation outcome

For action 2690, the PPA 2026 value is R$ 16.020.000,00 after unit conversion, while the enacted LOA appropriation is R$ 6.152.000,00, a LOA-minus-PPA delta of -R$ 9.868.000,00. Program/action/function/subfunction/education-level continuity is now directly resolved, but amount alignment is false and the cause of the difference is not inferred.

For action 2720, PPA 2026 and LOA 2026 both equal R$ 28.000.000,00. This proves program/action and 2026 amount alignment only. It does not prove EITI financial identity, because the action is generic Alimentação Escolar and remains `eiti_specific=false`.

## Fail-closed result

The EITI identity chain remains incomplete. There is still no direct EITI-indicator-to-explicit-budget-action/subaction mapping, no EITI-tagged budget item, no complete expense nature on this bounded page set, and no execution stages. Program 2001 totals remain non-attributable to EITI.

Therefore the canonical result is:

`STOP_TASK045_EITI_FINANCIAL_IDENTITY_CHAIN_STILL_INCOMPLETE_AFTER_BOUNDED_READONLY_REVIEW`

F01 remains `SILVER_SCOPED_PARTIAL_VALIDATED`. No remote layer is promoted by this task, and the consumed authorization does not authorize any later Silver v2 persistence, OCR, Gold, serving or publication.
