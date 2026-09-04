# TASK 097 — PPA provenance and pagination crosswalk

## Scope

T0/offline only, using evidence already versioned on protected main.

No Drive read, web/public-source request, source acquisition, OCR, remote write, serving or publication is performed.

## Problem inherited from TASK 096

The EITI-Limeira crosswalk preserved two locators for the PPA 2026–2029 Program 2001 evidence:

- legacy graph: page 18;
- later primary Jornal evidence: JOM PDF page 15.

TASK 096 correctly refused to reconcile them silently.

## Offline finding

The current repository does **not** contain enough provenance to prove that page 18 and page 15 are equivalent coordinates.

The legacy `edges_v08.csv` records `evidence_doc=ppa_7213_2025` and `page=18`, but does not identify:

- the concrete source file/hash used for that locator;
- whether 18 means physical PDF page, printed/internal page, standalone-copy page or another coordinate system;
- a deterministic page-offset artifact linking that coordinate to the primary Jornal PDF.

By contrast, TASK 041 identifies the primary source as the full Jornal Oficial edition 7119 PDF, SHA-256 `cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a`, with Program 2001 indicator on JOM PDF page 15 and a page-15 text SHA-256 `b6d44ee39efeed3b1acc3dccabbf56c73fb6914ef8ce15003d144c44a59e5eb4`.

Therefore the correct result is:

`UNRESOLVED_LEGACY_COORDINATE_SYSTEM`

not `18=15`, not `18≠15`, and not an inferred offset of -3.

## Structural improvement

TASK 097 introduces typed locator coordinate systems:

- `JOURNAL_EDITION_PDF_PAGE`
- `STANDALONE_PDF_PAGE`
- `DOCUMENT_INTERNAL_PRINTED_PAGE`
- `REPORT_LINE`
- `LEGACY_UNTYPED_PAGE`

Page equivalence may be asserted only when:

1. both locators use the same coordinate system and the same stable source identity; or
2. two typed coordinate systems are connected by an explicit, evidence-backed offset/mapping artifact.

Arithmetic difference alone never proves equivalence.

## Citation policy for the EITI case

For **new** research citations to the validated Program 2001/indicator material, the primary locator is:

`Jornal Oficial edition 7119 PDF — page 15`

The legacy page-18 locator remains preserved as historical evidence and is not rewritten.

This preference does not claim the two page numbers are equivalent; it selects the later, source-hashed primary locator for future citation.

## Files

- `config/research_locator_provenance.v1.json`
- `robo_dados_publicos/research/provenance_locator.py`
- `tests/test_task_097_ppa_provenance_pagination_crosswalk.py`
- `docs/evidence/TASK_097_PPA_PROVENANCE_PAGINATION_CROSSWALK_0.8.0.json`

## Effects

All remote-effect classes are zero. No workflow, credential or autonomous execution surface is introduced.

## Next step

After CI/review, the next coherent offline task is to expand the EITI-Limeira planning crosswalk backward into PPA 2018–2021 and PPA 2022–2025 **only where already-versioned repository evidence is sufficient**. Missing source evidence must remain `UNKNOWN` rather than triggering an automatic live read.
