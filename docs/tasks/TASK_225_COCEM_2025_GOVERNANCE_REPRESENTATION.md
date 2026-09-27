# TASK 225 — XIII COCEM 2025 governance and representation map

## Purpose

Materialize the primary institutional rules and Annex II representation table from `XIII COCEM 2025- REGIMENTO FINALIZADO.pdf`, linked to MD_01.3 `DOC-105`.

The source has 11 pages. Articles 1–15 occupy pages 1–6; Annex II, with the school-by-school number of teachers to be elected, is on pages 9–10.

## Event and agenda

The Regimento convenes the XIII Conferência Conjunta de Educação Municipal for 24–25 October 2025 at Teatro Nair Bello. Pre-conferences run from 11 September through 3 October 2025.

The theme is `Carreira do Magistério e o Processo de Indução de Resultados Educacionais` and the two axes are:

1. Carreira do Magistério;
2. Financiamento e Indução de Resultados na Educação.

## Governance rules

The conference includes municipal public authorities, CME, CACS-FUNDEB, CAE, Fórum Municipal de Educação, APEOESP, CPP and SINDSEL, plus the other categories defined by the Regimento.

For municipal teachers, Article 5, II states that representatives are elected by peers in the school units and the Annex II table follows the criterion of one teacher representative for each ten classes from Berçário I through 5th grade and EJA.

Article 11, III sets simple majority as the approval rule for proposals and referrals in plenary.

Article 12 distinguishes final recorded decisions from mere proposals: the final minutes consider proposals/referrals together with decisions approved by plenary.

Article 14 only identifies the generic budget source for organization/realization expenses — appropriations assigned to the Municipal Education Secretariat. It does **not** provide an expenditure amount.

## Annex II

The complete Annex II table is materialized as source-preserving institutional school names, planned teacher-delegate slots, and source page.

QA reconstructs:

- 69 school-unit rows;
- 111 planned teacher-delegate slots;
- 7 CEIEF rows;
- 25 CI rows;
- 4 EMEI rows;
- 33 EMEIEF rows.

CEIEF Rafael Affonso Leite has 3 planned teacher-delegate slots in the source table.

The source note says linked-unit class counts were considered together with those of the linking unit. This task does not reverse-engineer or infer the underlying class counts from delegate slots.

## Privacy boundary

Annex I contains a blank field for CPF as part of the pre-conference form. TASK 225 does not materialize any CPF value or personal delegate identity. Only institutional school names and planned counts from Annex II are stored.

## Semantic boundaries

- planned delegate slot != actual attendance;
- Regimento != final conference minutes;
- proposal presented != proposal approved;
- simple majority != unanimity;
- Article 14 budget source != expenditure amount;
- 2025 rules != rules of another COCEM edition.

## Source identity

Title and document content match the MD_01.3 DOC-105 manifest entry. Byte-level identity is not claimed because no source binary hash is proven in this task.

## Non-effects

No new public-source request, Drive write, serving mutation, publication, schedule or recurrence. Canonical contextual coverage remains 38/38; the task adds governance/participation depth.
