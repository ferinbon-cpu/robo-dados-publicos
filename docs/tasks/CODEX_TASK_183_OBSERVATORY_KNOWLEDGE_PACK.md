# TASK 183 — fuse existing-custody products and compute semantic question answerability

## Purpose

Turn the separate TASK 180–182 materialization blocks into one deterministic local Observatório knowledge pack and replace product-presence coverage with question/metric-level answerability.

## Fused products

The pack fuses currently materialized existing-custody rows:

- TASK 180 school seed: 798 rows;
- TASK 181 network education series: 171 rows;
- TASK 182 Censo aggregate series: 48 rows;
- TASK 181 SIOPE fiscal series: 38 rows.

Expected fused products:

- SCHOOL_INDICATOR_SERIES: 1,017 rows;
- FISCAL_SERIES: 38 rows;
- QUERY_PRODUCT_CATALOG: 2 catalog rows for the two materialized substantive products.

Logical-key collisions fail closed. Exact duplicates may deduplicate; conflicting values on the same logical key stop the build.

## Semantic metric inventory

The fused school product exposes 36 unique indicator ids and the fiscal product 2 unique metric ids, for 38 distinct materialized metrics. Inventory includes periods, scope levels, scope ids, source families and quality statuses.

## Question-level answerability

All 38 questions from the 15-domain ontology are mapped to explicit semantic recipes. The evaluator does not equate product presence with answerability.

Statuses:

- MATERIALIZED_ANSWERABLE;
- MATERIALIZED_PARTIAL;
- ROUTE_READY_PRODUCT_NOT_BUNDLED;
- SOURCE_READY_NOT_MATERIALIZED;
- EXPLICIT_GAP.

A metric can be partial because it exists but lacks enough periods or required scope levels. Missing metrics are reported explicitly. The LLM is not allowed to fill missing numeric evidence.

Expected current question counts, enforced by tests:

- 8 MATERIALIZED_ANSWERABLE;
- 4 MATERIALIZED_PARTIAL;
- 19 ROUTE_READY_PRODUCT_NOT_BUNDLED;
- 2 SOURCE_READY_NOT_MATERIALIZED;
- 5 EXPLICIT_GAP.

Domain-level summary:

- 7 MATERIALIZED_PARTIAL domains;
- 7 ROUTE_READY_PRODUCT_NOT_BUNDLED domains;
- 1 EXPLICIT_GAP domain: TERRITORY_CONTEXT.

No domain is yet declared fully materialized because every domain still has at least one unanswered or nonbundled question.

## Examples

Already materialized as answerable:

- IDEB/SAEB/SARESP historical learning question;
- learning-versus-flow decomposition using proficiency plus approval;
- school-to-network comparison for common indicators such as IDEB;
- teacher training/regularity/effort snapshot;
- infrastructure snapshot for the 40 schools;
- AEE/inclusion trend from current aggregates;
- catalog/source coverage questions.

Materialized but partial:

- full-time trend: only one currently materialized period at school level;
- flow trend including TDI: approval/failure/dropout are historical, TDI is not yet historical in the pack;
- equity/context question: PPI, INSE and Special Education exist, territorial vulnerability does not;
- FUNDEB/own-source/transfers question: SIOPE percentages exist, but full revenue composition does not.

Explicit gaps include:

- total students/classes/schools scale metrics in the current fused pack;
- spending per student;
- nominal-versus-real monetary expenditure trend;
- territory/demographic context.

JOM and ACCOUNTING_LEDGER are treated as route-ready but not bundled until actual snapshots are supplied. PLANNING_DOCUMENT_INDEX is source-ready from custody but not yet materialized into the pack.

## Evidence packets

The pack also generates deterministic sample evidence packet summaries for learning 2025, Rafael Affonso Leite equity/context 2025 and financing 2025. These use the real fused snapshots through the TASK 175/176 query path.

## Remote effects

Network 0; Drive write 0; serving 0; publication 0; schedule 0; recurrence 0.

## Next

Use the answerability matrix to rank the next ingestion by question-value gain rather than by source availability alone. High-value candidates are planning/normative materialization, total enrollment/school-count series, monetary education expenditure and territorial context, followed by ATU/HAD/TNR/Censo full-panel expansion.
