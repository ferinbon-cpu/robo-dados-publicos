# TASK 221 — refresh existing-custody digest after File Library re-audit

## Purpose

Correct the stale TASK 179 custody map using assets that are already owned by the user and now directly discoverable in the File Library. This is not a new public-source collection task and does not change the canonical contextual question coverage, which is already 38/38 after TASK 220.

Base main: `5e7bab5dae2bf7c8b64e087acb8165f67c95af62`.

Issue: #753.

## Main correction 1 — MD_01.3 is no longer a missing handoff

The readable File Library contains:

`md_01_3_indice_corpus_documental_transcrito_limeira.md`

Its own manifest declares:

- 228 source files found;
- 194 unique documents transcribed/mirrored;
- 34 duplicates ignored;
- 191 `ok`;
- 3 `sem_texto`;
- exact document-id span `DOC-001..DOC-194`.

Family counts sum to 194:

- payroll/payslips: 70;
- FUNDEB / 25% education portal reports: 50;
- staff-count files: 22;
- RREO/LRF: 18;
- monthly revenue/expense: 10;
- balances/accountability: 9;
- RGF/LRF: 6;
- PPA/LDO/LOA/budget legislation: 5;
- public hearing/fiscal targets: 1;
- Education trial balance: 1;
- positions/pay: 1;
- COCEM/institutional: 1.

Observed `sem_texto` entries include DOC-065, DOC-100 and DOC-102. Existing later tasks already recovered/validated important F01 material through stronger official representations, so TASK 221 does not reopen those files merely because MD_01.3 marks an old transcription as `sem_texto`.

### Privacy boundary

The corpus includes 70 payroll/payslip files and 22 staff-count files. TASK 221 does **not** replicate row-level payroll or personnel content into GitHub. Only inventory metadata and document-family counts are canonized here. Any future personnel use must define purpose, minimization and an aggregate/query-safe schema first.

### Numeric boundary

MD_01.3 is a documentary/migration corpus. Its transcriptions may locate a document, table or candidate line, but they do not automatically outrank official structured TCE/SIOPE/SICONFI/FUNDEB/TDA/PNCP evidence and do not become numeric truth by being present in the corpus.

## Main correction 2 — normative brain is v3.0, not v0.1

The File Library contains:

`Cerebro_Normativo_Gestao_Escolar_Limeira_v3_0_ESPELHO_SME_LEGAL.md`

The v3.0 explicitly turns v2.1 into an auditable SME Legal coverage mirror. It carries four coverage states:

- `INTEGRADO_CORPUS`;
- `PARCIAL`;
- `PENDENTE_CORPUS_INTEGRAL`;
- `LACUNA_CONFIRMADA`.

The document itself warns that v3.0 is not a claim that all SME Legal content has been transcribed and requires gaps to be declared rather than invented. The confirmed example is RH Instrução de Serviço nº 4, Vale-Alimentação.

The registry therefore assigns v3.0 the role:

`DERIVED_RAG_GUIDE_AUDITABLE_SME_LEGAL_COVERAGE_MAP`

This is intentionally below exact official normative documents in authority. Even `INTEGRADO_CORPUS` proves only that a corresponding full text/OCR is incorporated into the derived corpus; it does not, by itself, prove current legal validity or the absence of later amendments/revocations.

## V08 correction — source closure is not runtime completion

The V08 workbook now records as closed in its own analytical layer:

- Censo 2025 / panel 2018–2025;
- TNR school-year 2011–2025;
- ATU school-year 2007–2025;
- HAD school-year 2010–2025.

However TASK 182 already established a transfer boundary: File Library search/readback is not equivalent to a complete binary or full-row stream. The robot has materialized bounded seeds/aggregates, but it has not materialized every row of the 552-row Censo panel or the complete annual ATU/HAD/TNR rowsets.

Therefore the registry says `PARTIALLY_MATERIALIZED` and forbids reconstructing complete rowsets from partial search snippets.

## F01/F02 folder-location correction

Old Drive folder placement under `10_INBOX/PENDENTES` is not processing truth. F01 and the two F02 batches already have later manifests/tasks proving processing and/or Silver promotion. TASK 221 records them in an explicit do-not-reingest list so future inventory logic does not treat a stale folder name as an ingestion state.

## V2 registry

TASK 221 adds `config/existing_custody_corpus_registry.v2.json` rather than mutating v1. The v1 remains historical evidence of what was known at TASK 179.

The v2 separates:

- custody/discovery;
- source-workbook or source-corpus completion claims;
- robot materialization status;
- authority/precedence;
- privacy and numeric boundaries;
- next bounded digest queue.

## Next bounded digest

Priority 1 is now `MD_01_3_DOCUMENT_INDEX_METADATA`.

The next task should materialize a sanitized 194-document index with document id, family, source filename, type, extraction status and a non-sensitive locator. It must not ingest payroll/personnel row payloads and must not promote transcribed numeric content into fiscal truth.

Priority 2 is the v3 SME Legal coverage matrix as a document-index/RAG routing aid. Substantive normative claims should only be promoted when the exact official primary source is independently available and current-vigency semantics are handled.

Priority 3 is a true complete-row transfer path for the closed V08 datasets. Search snippets remain forbidden as a mechanism for pretending a complete binary import.

## Guards

- synthesis != legal proof;
- OCR != numeric truth;
- corpus transcription != canonical structured numeric source by default;
- source workbook closed != robot runtime fully materialized;
- missing != zero;
- old PENDENTES folder != unprocessed;
- no row-level payroll/personnel replication in TASK 221;
- no contextual-coverage inflation: remains 38/38.

## Remote effects

- new public-source network: 0;
- Drive write: 0;
- serving mutation: 0;
- publication: 0;
- schedule: 0;
- recurrence: 0.
