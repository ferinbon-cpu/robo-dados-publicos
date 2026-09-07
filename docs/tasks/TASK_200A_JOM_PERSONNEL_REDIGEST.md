# TASK 200A — Jornal Oficial personnel redigest

## Goal

Recover personnel events for the municipal education network from primary Jornal Oficial PDF text already under custody, without OCR and without rewriting event identities.

## Diagnostic

The current 303-row JOM_EVENT_INDEX contains 226 rows with blank object_text. Among PORTARIA/DECRETO/LEI/RESOLUCAO, 148 of 157 rows are blank.

TASK 200A performs a bounded subject-aware redigest of ten unambiguous PORTARIA rows. Each selected page was extracted from the native PDF text layer, and each local PDF SHA-256 exactly matches the source SHA already pinned in the current event snapshot.

## Selected subject

Only acts whose principal subject is EDUCATION_PERSONNEL are promoted.

The operative clauses cover:
- effective appointment of Monitor linked to public competition;
- rectification of effective appointments for Monitor and Secretário de Escola;
- requested exonerations;
- one ex officio exoneration;
- revocation of an effective Monitor appointment.

The native extracted text is preserved as-is, including text-layer imperfections. No silent spelling correction is introduced.

## Semantic hardening

PERSONNEL_EVENTS now requires both:
- policy domain EDUCATION;
- evidence layer PERSONNEL.

This prevents an appointment in another municipal department from answering education-network personnel questions.

SCHOOL_NORMS is also hardened. A generic PORTARIA of personnel can no longer satisfy school-functioning norms merely because its act type is normative or its role contains the word Escola. The JOM norms signal requires a normative event type plus a non-workforce education topic.

## Expected answerability

32 answerable / 6 partial / 0 explicit gaps
→ 34 answerable / 4 partial / 0 explicit gaps.

Only PERS_Q1 and PERS_Q2 may change in TASK 200A.

NORMS_Q1 and NORMS_Q2 remain partial and continue in the parent TASK 200. EQUITY_Q1 and TEACH_Q2 also remain partial.

## Guards

No OCR. No event-id rewrite. No fabricated object text. No keyword-only promotion. Publication remains distinct from implementation.
