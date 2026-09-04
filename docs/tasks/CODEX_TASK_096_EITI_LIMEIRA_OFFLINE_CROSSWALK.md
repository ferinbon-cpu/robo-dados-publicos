# TASK 096 — EITI-Limeira offline research crosswalk

## Scope

T0/offline only, using evidence already versioned in this repository.

No Drive read, web/public-source request, source acquisition, OCR, write, serving or publication is performed.

## Objective

Exercise the new TASK 093–095 research architecture on the first real policy case: EITI-Limeira.

The crosswalk migrates selected validated legacy relations and F01 evidence into:

- generic entities;
- typed relations;
- research claims;
- evidence records;
- source-role semantics;
- negative-search observations;
- an institutionalization matrix.

It is not a complete EITI corpus and is not a dissertation conclusion.

## Legacy migration

The repository already contained a validated `edges_v08.csv` graph.

TASK 096 preserves key legacy semantics:

- Decreto 118/2024 → EITI-Limeira: confidence A;
- Lei 7.366/2026 → EITI-Limeira: confidence A;
- EITI-Limeira ↔ Programa 2001 thematic planning correspondence: confidence B;
- EITI-Limeira ↔ indicator correspondence: confidence B;
- legacy QA explicitly expected no `financial_identity` edge between EITI-Limeira and Program 2001.

These become PROVEN or CORROBORATED in the generic ontology according to the existing A/B mapping.

## First institutionalization matrix

The current repository evidence supports:

- **Normative: PROVEN**
  - Decreto 118/2024;
  - Lei 7.366/2026 official ementa evidence.

- **Planning: CORROBORATED**
  - Program 2001 has explicit education-integral planning signals and indicator;
  - the policy-to-whole-program correspondence is thematic/planning, not financial identity.

- **Budgetary policy identity: UNKNOWN**
  - selected PPA/LOA actions are generic and marked `eiti_specific=false`;
  - amount/key correspondence does not prove policy attribution.

- **Financial reporting: PROVEN, scoped**
  - the first-bimester 2026 SIOPE/FUNDEB report has a dedicated `FOMENTO ETI (4%)` reporting bucket;
  - required amount R$ 1,315,673.39;
  - applied amount reported R$ 0.00.

- **Transaction execution identity: UNKNOWN**
  - the report does not expose a stable program/action/ficha/cost-center/transaction bridge sufficient to prove an individual EITI empenho→liquidação→pagamento chain.

- **Organizational: CANDIDATE**
  - SME responsibility for Program 2001 is proven;
  - policy-specific organizational responsibility is not separately proven by the evidence used here.

- **Material delivery: UNKNOWN**

- **Outcome/effect: UNKNOWN**
  - PPA targets are planning targets, not observed outcomes;
  - no causal claim is authorized.

- **Normative/planning persistence: CORROBORATED**
  - 2021 CME signal → 2024 decree → PPA 2026–2029 → 2026 law;
  - this is a continuity signal only.

- **Budgetary persistence: UNKNOWN**
  - no multi-year policy-specific budget identity is proven.

## Important discovered inconsistency

The legacy graph records PPA Program 2001 evidence on page 18, while the later scoped JOM evidence identifies the relevant program/indicator on JOM page 15.

TASK 096 does **not** silently reconcile the numbering.

Both locators are preserved and `page_numbering_reconciled=false`.

A future corpus-normalization task may resolve whether this is document-local versus JOM-global pagination or another numbering convention, but current evidence does not justify choosing one.

## Negative evidence

Two scoped negative observations are preserved:

1. no explicit EITI/ETI/Educação Integral/Tempo Integral label among the 27 Program 2001 action rows checked in TASK 049;
2. no stable transaction-level EITI accounting key in the single SIOPE-MAVS report read in TASK 056.

Both may prove the search result within their scopes.

Neither proves that EITI spending does not exist.

## Financial guardrail

TASK 096 explicitly forbids promotion of:

- total Program 2001 → EITI;
- action 2690 → EITI;
- action 2720 → EITI;
- PPA/LOA amount alignment → financial identity;
- FOMENTO ETI reporting bucket → individual transaction identity;
- zero FUNDEB FOMENTO ETI in one period → zero total municipal EITI spending.

## CI and dependency integration

TASK 096 does not vendor copies of pre-existing repository dependencies into its diff.

The following are already present on protected main and are intentionally reused:

- `robo_dados_publicos/research/ontology.py` — merged by TASK 093;
- `robo_dados_publicos/research/evidence_semantics.py` — merged by TASK 095;
- `tests/fixtures/edges_v08.csv`;
- `tests/fixtures/graph_qa_v08.csv`.

The new test module is automatically executed by the existing canonical `CI_OFFLINE` repository-wide unittest discovery. TASK 096 adds no new workflow because it adds no new trigger, credential, autonomous executor or remote capability.

The existing CI also runs the repository preflight, automation-policy gate, engineer-policy gate, unit suite and historical regression before a PR can merge. Public readiness remains a separate protected status check.

## Research significance

This is the first concrete demonstration of the structural redesign:

`document → evidence → relation/claim → institutionalization dimension`

instead of:

`document → extracted number → conclusion`.

## Next decision

TASK 096 intentionally stops before any new source read.

The next useful phase is no longer automatically "read the next file". We can now choose between:

1. resolve the PPA pagination/provenance crosswalk offline if repository evidence is sufficient;
2. expand the policy crosswalk backward to PPA 2018–2021 / PPA 2022–2025 from already-held corpus;
3. pursue the transaction-level EITI accounting bridge;
4. generalize this crosswalk machinery to another policy such as VAAR.

Any option requiring a new source read remains separately gated.
