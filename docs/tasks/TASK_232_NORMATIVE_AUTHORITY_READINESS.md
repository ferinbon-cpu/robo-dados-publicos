# TASK 232 — SME Legal integrated corpus: authority readiness

Issue: #780

## Purpose

Convert the 11 `INTEGRADO_CORPUS` menu items from TASK 222 into a fail-closed authority-readiness layer. This task does **not** revalidate current law on the internet. It classifies what is already in custody so the robot does not confuse text presence with current legal authority.

The central rule is:

> `INTEGRADO_CORPUS` proves that full text/OCR is incorporated in the derived corpus. It does not prove current vigency, complete amendment consolidation or standalone normative authority.

## Result

The 11 menu items resolve to only eight logical source packages. Three menu items are backed by primary normative texts in custody:

- LC 41/1991 — Estatuto dos Funcionários Públicos Municipais;
- LC 461/2009 — Estatuto do Magistério Público Municipal;
- Lei Municipal 6.089/2018 — Sistema Municipal de Ensino.

Even these three remain `NOT_REVALIDATED_CURRENTLY` in this task.

The other eight menu items resolve to operational guidance, training material, administrative instructions or onboarding templates. They are useful context, but not standalone legal authority.

## Menu/source deduplication

Three apparent menu duplications/containments are explicit:

- `SMELEGAL-028 Conselho de Escola` is integrated through `SMELEGAL-014 Gestão Legal I`, specifically Eixo 5;
- `SMELEGAL-045 Projeto Político Pedagógico` and `SMELEGAL-061 Projeto Político Pedagógico (PPP)` use the same PPP Part 1 + Part 2 package;
- `SMELEGAL-056 Vice-diretor` and `SMELEGAL-065 Instrução de Serviço nº 1: Vice-Diretor` belong to the same Vice-Diretor package.

Therefore menu count must never be treated as distinct-source count.

## Source roles

TASK 232 uses a bounded role vocabulary:

- `PRIMARY_NORMATIVE_TEXT` — source text of a law/statute incorporated in custody;
- `ADMINISTRATIVE_INSTRUCTION` — local administrative package whose current act chain is not revalidated here;
- `OPERATIONAL_GUIDANCE` — management guidance/checklist material;
- `TRAINING_MATERIAL` — supervision/training documents that may cite normative sources;
- `ONBOARDING_RECORD_TEMPLATE` — acknowledgement/orientation forms for staff.

Only the three `PRIMARY_NORMATIVE_TEXT` items are marked `SOURCE_TEXT_USABLE_WITH_VIGENCY_GUARD`. Every other role is `CONTEXT_ONLY_NOT_STANDALONE_LEGAL_AUTHORITY`.

## Extraction evidence

Existing-custody evidence establishes:

- LC 41/1991: 25 pages, PDF text extraction OK, with multiple later-law references;
- LC 461/2009: 32 pages, PDF text extraction OK, with later inclusions/amendments visible in the integrated text;
- Lei 6.089/2018: 26-page source scan incorporated by OCR; OCR is not treated as the official publication;
- Conselho de Ciclo: `formacao-conselho-de-ciclo.PDF`, 61 pages, PDF text extraction OK, Equipe de Supervisão SME, June 2022;
- PPP: two-document training package; known Part 2 member has 24 pages and PDF text extraction OK.

Unknown page totals for multi-file packages are kept `null`; they are not guessed.

## Hard guards

The config and tests enforce:

- `INTEGRADO_CORPUS_NE_CURRENT_VIGENCY_PROOF`;
- `TRAINING_MATERIAL_NE_NORMATIVE_ACT`;
- `OPERATIONAL_GUIDANCE_NE_LAW`;
- `ADMINISTRATIVE_TEMPLATE_NE_GENERAL_NORM`;
- `OCR_NE_OFFICIAL_PUBLICATION`;
- `MENU_ITEM_NE_DISTINCT_SOURCE_PACKAGE`;
- `DUPLICATE_MENU_ENTRY_NE_NEW_AUTHORITY`;
- `EMBEDDED_AMENDMENT_REFERENCES_NE_COMPLETE_CURRENT_CONSOLIDATION`;
- `SOURCE_TEXT_PRESENT_NE_NO_LATER_AMENDMENT`;
- `NO_GENERIC_OTHER_NETWORK_RULE_INVENTION`;
- `NO_CONTEXTUAL_COVERAGE_CHANGE`.

## What this task does not do

It does not:

- access external official legislation sites;
- assert that any incorporated law/instruction remains currently vigente;
- reconstruct missing amendment chains;
- promote training slides or forms into normative acts;
- change contextual coverage from 38/38;
- write to Drive or publish/serve data.

## Next bounded step

A separate official-source task should verify current identity/vigency/amendment chains for exactly four high-value packages first:

1. LC 41/1991;
2. LC 461/2009;
3. Lei Municipal 6.089/2018;
4. Vice-Diretor package.

That future task may use official municipal legislation/SME sources. Its results must override this derived readiness layer when exact official evidence is available.
