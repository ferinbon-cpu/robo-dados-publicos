# SIOPE — evidence map for historical regimes (v1)

## Purpose

This note pins the evidence that must be consulted before extending the Limeira/SP SIOPE pipeline beyond the currently proven 2016–2024 range. It is an engineering input for `CODEX_TASK_001_SIOPE_REGIME_DISCOVERY.md`; it does **not** authorize live collection, Drive access, Bronze/Silver/Gold creation, publication or future batch execution.

## Evidence hierarchy

Use the following order when reconciling a regime:

1. `OFFICIAL_PRIMARY` — FNDE/SIOPE manuals, data dictionary, analytical-data pages, official downloads/metadata.
2. `INTERNAL_PROVEN` — evidence already pinned by `ferinbon-cpu/robo-dados-publicos` live runs and regression tests.
3. `INDEPENDENT_IMPLEMENTATION` — external code that consumes the same public SIOPE surfaces and corroborates route/period conventions.
4. `CANDIDATE_ONLY` — behavior observed only in external code or historical material that is not enough to promote a runtime contract.

External corroboration never replaces an official or internally proven gate.

## Sources to reconcile

### A. FNDE / official material

1. **SIOPE data dictionary (2019)**
   - URL: `https://www.fnde.gov.br/phocadownload/sistemas/siope/Manuais/DICIONARIO%20DE%20DADOS%20SIOPE%202019.pdf`
   - Engineering fact to verify/pin from the document: for the historical annual regime, 2008–2016 use period 1 as the annual declaration; from 2017 onward the system is bimonthly and period 6 represents the annual consolidation.
   - Also inspect field definitions for revenue, expenditure, education expenditure, supplementary information, consolidated data and indicators relevant to the current Gold calculations.

2. **FNDE — Arquivos / Dados Analíticos**
   - URL: `https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/arquivos-dados-analiticos`
   - Engineering fact to verify/pin: official analytical-data group for **2008–2016**, including consolidated revenue, expenditure and education-expenditure data plus indicators and supplementary information.
   - This raises confidence that 2008–2015 are not an undocumented legacy zone, but it does **not** prove compatibility with the current `Dados_Gerais_Siope` 52-field contract.

3. **FNDE — SIOPE manuals**
   - URL: `https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/manuais-do-siope`
   - Engineering purpose: compare annual municipal manuals for 2005, 2006, 2007 and later years to identify terminology, reporting-period, field and semantic changes before any live contract is proposed for 2005–2007.

4. **FNDE — historical SIOPE downloads/installers**
   - Base URL: `https://www.fnde.gov.br/siope/download.do`
   - Engineering purpose: inspect per-year installers/release notes and historical corrections. These may indicate year-specific semantic or schema changes that must be reflected in the regime map instead of forced into one continuous contract.

### B. Independent implementation already registered in MD_00.2

Repository: `tuffyli/RA_work` (Insper / Cátedra Ruth Cardoso research code).

Relevant file:
`Insper-Catedra-Ruth-Cardoso/Fundef-Fundeb/Scripts/New/00_siope_extract.R`

Pinned observations from the public file:

```r
f_periodo <- function(ano) ifelse(ano <= 2016, 1, 6)

for (ano in 2000:2024) {
    ...
}
```

The script consumes the official FNDE Olinda service and uses `P1` through 2016 and `P6` afterward. It also attempts years 2000–2024. Treat this as:

- strong independent corroboration for the 2016/2017 period boundary;
- a useful discovery hint for years before 2008;
- **not** proof that 2000–2007 are valid under our current resource/schema/metric contract.

The project Drive reference `MD_00_2_REFERENCIAIS_TECNICOS_PRIOR_ART_E_FONTES_OFICIAIS_V01.md` already classifies this implementation as a high-adherence technical reference and records the same historical-period rule.

## Current regime confidence map before TASK 001

| Range | Period / status | Evidence status | What remains to prove |
|---|---|---|---|
| 2017–2024 | P6 annual consolidation | `INTERNAL_PROVEN` | nothing for the already persisted range |
| 2016 | P1 annual | `INTERNAL_PROVEN` | nothing for 2016 already persisted |
| 2008–2015 | P1 annual | `OFFICIAL_PRIMARY_DOCUMENTED` + independent corroboration | actual Olinda resource availability, exact schema, required fields, Gold comparability, year-specific drift |
| 2005–2007 | likely legacy annual reporting, exact contract not yet promoted | `OFFICIAL_PRIMARY_LEGACY_DOCUMENTED` | manuals/installers, resource availability, period contract, schema and semantic comparability |
| 2000–2004 | external implementation attempts these years | `CANDIDATE_ONLY` | official corroboration plus live read-only contract discovery before any promotion |
| 2025 | must not be assumed equal to 2024 | `UNPROVEN_RECENT` | available periods, closure status, schema, fields for 8 metrics, annual-series eligibility |
| 2026 | current exercise; must remain provisional/current-year | `UNPROVEN_CURRENT_YEAR` | available periods, current schema and explicit current-year semantics; do not merge into closed annual series |

## Required Codex reconciliation questions

For each candidate range/year, the agent must answer without live data access in TASK 001:

- Which official source documents the reporting regime?
- What period number is official/candidate for annual interpretation?
- Is the evidence about `Dados_Gerais_Siope`, another SIOPE family, or only the old desktop system?
- Which current 52 fields are known, unknown or potentially renamed?
- Which of the 8 current Gold metrics are mathematically calculable if the needed fields exist?
- Which metrics may be semantically non-comparable despite similar field names?
- Are there release-note corrections or regime breaks that require a distinct adapter?
- What evidence would be sufficient to promote `CANDIDATE` to `PROVEN` in a later gate?

## Fail-closed interpretation

Do not infer that a year is safe because an external script loops over it. Do not infer that an official manual implies the current Olinda resource exposes the same schema. Do not infer that matching names imply semantic equivalence. Unknowns remain `UNKNOWN`/`CANDIDATE` until a later bounded read-only gate proves them.
