# TASK 103 — bounded primary PPA evidence acquisition design

## Scope

T0/offline contract design for a later, separate T1 read-only acquisition.

No live source network, Drive access, persistence, publication, retry, recurrence or schedule is introduced by this task.

## Research gap

TASK 098 preserves two historical planning signals but correctly leaves their primary evidence incomplete:

- 2018–2021: `escolas com programas em tempo integral`;
- 2022–2025: `ÍNDICE DE ALUNOS EM EDUCACAO INTEGRAL`.

The Drive custody check performed before this task found only the PPA 2026–2029 in the existing PPA_LDO_LOA folder. Therefore the historical gaps cannot be closed by silently treating the TASK 055A aliases as primary documents.

## Primary identities

- PPA 2018–2021: Lei Municipal 5.947/2017.
- PPA 2022–2025: Lei Municipal 6.659/2021.

The official Prefeitura budget index lists both identities. The Câmara record for Projeto de Lei 240/2017 independently identifies the proposal that established the 2018–2021 PPA and relates it to Lei Ordinária 5947.

## Known acquisition state

### 2022–2025

A direct Prefeitura PDF candidate is known and pinned in the contract:

`https://www.limeira.sp.gov.br/sitenovo/downloads/9d8dd63f39cc3b51ef032a4c96210a07.pdf`

External inspection observed the expected Educação Integral indicator in that document. TASK 103 does not treat that external observation as repository evidence: the future T1 runner must download the bytes itself, hash them, establish document identity and create its own typed locator.

### 2018–2021

The official law and legislative project identities are known, but the exact primary PDF bytes are not yet pinned. The contract therefore preserves `primary_pdf_candidate_url=null` and requires bounded resolution from official hosts. No invented URL is allowed.

## Evidence required before promotion

Each period must independently satisfy all four TASK 098 requirements:

1. PRIMARY_PPA_DOCUMENT_IDENTITY
2. STABLE_SOURCE_HASH_OR_EQUIVALENT_IDENTITY
3. TYPED_LOCATOR_FOR_THE_RELEVANT_PLANNING_SIGNAL
4. DIRECT_TEXT_OR_VISUAL_EVIDENCE

Partial satisfaction remains a gap.

## Future T1 bounds

The future acquisition runner is limited to:

- HTTPS official hosts only;
- GET only;
- maximum 6 HTTP requests total;
- maximum 3 requests per period;
- no pagination;
- no retry;
- redirects only while the destination remains allowlisted;
- SHA-256 of exact source bytes before parsing;
- typed locator coordinate system;
- bounded statuses including PRIMARY_MATCH, CANDIDATE_MATCH, NO_MATCH and explicit STOP states.

NO_MATCH means only no match inside this bounded execution.

## Semantic boundary

Historical planning evidence cannot by itself:

- create EITI financial identity;
- establish accounting identity from indicator similarity;
- prove implementation;
- prove causal outcomes;
- automatically upgrade continuity across the three PPAs to PROVEN.

## Next step

After CI and review of this T0 design, implement the single-use T1 read-only runner under this exact contract and owner authorization, then pin its observed evidence in a separate post-run task.
