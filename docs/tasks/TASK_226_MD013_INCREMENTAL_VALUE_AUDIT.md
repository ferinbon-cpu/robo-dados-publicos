# TASK 226 — rank remaining MD_01.3 documents by incremental value

## Purpose

After TASK 224 (`DOC-066`, Education September/2025 trial balance) and TASK 225 (`DOC-105`, XIII COCEM governance), the safe MD_01.3 slice has 99 documents left. This task prevents the robot from treating every available PDF as a new fact.

No numeric fact is promoted by TASK 226. It is a novelty/overlap audit that decides what should be digested next.

## Exact partition

The 99 remaining documents are partitioned, without overlap, into:

- 7 `NOVEL_SUBSTANTIVE`;
- 24 `CORROBORATION_ONLY`;
- 15 `SUPERSEDED_BY_STRONGER_CANONICAL_SOURCE`;
- 52 `INDEX_ONLY`;
- 1 `BLOCKED_NO_TEXT`.

Tests reconstruct the complete safe universe and fail if any document disappears, appears twice, or if excluded `DOC-067` enters the audit.

## 1. Novel substantive — annual accounting statements

Seven documents add year-end accounting dimensions not already materialized as canonical robot products:

- `DOC-005` — Balanço Orçamentário 2024;
- `DOC-006` — Balanço Orçamentário 2025;
- `DOC-009` — Balanço Financeiro 2024;
- `DOC-010` — Balanço Financeiro 2025;
- `DOC-013` — Demonstração das Variações Patrimoniais 2024;
- `DOC-016` — Balanço Patrimonial 2024;
- `DOC-017` — Balanço Patrimonial 2025.

Direct File Library inspection confirms that `DOC-010` exposes linked Education annual budget revenue and expense, while `DOC-017` adds assets, liabilities, patrimonial balance and financial-source surplus/deficit tables with Education/FUNDEB rows. Repository probes for representative 2025 values returned no exact hit.

The two annual `Prestação de contas` documents (`DOC-103`, `DOC-104`) are not placed in this class because they are TCE submission receipts, not the substantive statements.

## 2. Corroboration / primary-authority upgrade

### RREO — 18 documents

The robot already has direct materializations such as TASK 188 (Restos a Pagar) and TASK 190 (education spending/MDE), and broader derived fiscal context in MD_01.2. Therefore the remaining RREO annexes must be used only when they add granularity or for independent corroboration; the same accounting fact must never be counted twice.

### RGF — 6 documents

RGF facts such as personnel limits, debt, guarantees, credit operations and cash availability already exist in the derived MD_01.2 technical layer. The exact RGF PDFs can still provide an important **authority upgrade** from secondary synthesis to primary document, but that is not mislabeled as a new fact.

## 3. Superseded by stronger canonical sources

The ten January–May revenue/expense PDFs are behind structured and/or already processed layers: TASK 186 TCESP revenue, TASK 187 TCESP rich expenses and F02 local monitoring. The custody registry already forbids reingesting F02 simply because files remain under old folder names.

The five 2026 planning documents overlap F01 and the primary planning chain from TASK 184/TASK 189. In particular, historical `DOC-100` was `sem_texto` in MD_01.3 and later OCR-recovered in MD_01.3B, but operational LOA content is already stronger elsewhere.

## 4. Index only

The 50 opaque FUNDEB/25%-Education portal reports span repeated filenames, timestamped exports and multiple periods. Availability is not enough to prove novelty. They remain index-only until a later task fingerprints logical report identity, period and headers, then deduplicates them before any content promotion.

`DOC-103` and `DOC-104` stay as annual-account submission provenance receipts.

## 5. Blocked no-text

`DOC-065` remains historically `sem_texto` in MD_01.3. MD_01.3B has OCR text, which can support navigation/review but cannot become numeric truth without validation against a primary readable source.

## Priority queue

The next substantive bundle is intentionally compact:

1. `DOC-017` Balanço Patrimonial 2025;
2. `DOC-010` Balanço Financeiro 2025;
3. `DOC-006` Balanço Orçamentário 2025.

Together these create a coherent annual 2025 accounting layer while preserving the distinct semantics of patrimonial position, financial flows and budget execution.

The next comparator bundle is the 2024 equivalents plus `DOC-013`. Only after that should exact RGF documents be promoted as primary-source authority upgrades. RREO and the 50 FUNDEB portal reports remain lower priority unless a specific missing semantic gap is proven.

## Guards

- PDF availability != novelty;
- same fact in another file != a new fact;
- structured official source precedence;
- no double counting;
- corroboration != canonical override;
- receipt != substantive financial statement;
- OCR != numeric truth;
- primary-source upgrade != new fact when semantics already exist;
- 38/38 contextual coverage remains unchanged.

## Remote effects

None. No new public-source network access, Drive write, serving mutation, publication, schedule or recurrence.
