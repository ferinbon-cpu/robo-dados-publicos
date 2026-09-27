# TASK 229 — RGF 2026 Q1 primary-source authority

## Goal

Promote the six official 2026 first-quadrimester RGF annexes from derived-reference support to a primary auditable layer. This is an authority/provenance upgrade, not new contextual coverage.

## Sources

- DOC-042 — Annex 1 — personnel expenditure, May/2025–Apr/2026.
- DOC-049 — Annex 2 — consolidated net debt, first quadrimester/2026.
- DOC-051 — Annex 3 — guarantees and counter-guarantees.
- DOC-054 — Annex 4 — credit operations.
- DOC-057 — Annex 5 — cash availability and Restos a Pagar.
- DOC-058 — Annex 6 — simplified RGF summary.

All six were directly rechecked against the primary PDFs. Identity is title/content plus MD_01.3B mapping; byte hashes are not claimed.

## Primary facts and semantics

Annex 1 distinguishes gross personnel expenditure (R$ 871,749,522.77) from LRF DTP (R$ 668,594,529.13; 37.75% of adjusted RCL). Adjusted personnel RCL is R$ 1,770,885,388.89. Formal alert, prudential and maximum limits are 48.60%, 51.30% and 54.00%.

Annex 2 reports consolidated debt of R$ 352,841,178.81, deductions of R$ 341,468,070.50 and net consolidated debt of R$ 11,373,108.31. Adjusted RCL for debt limits is R$ 1,780,680,788.07; DCL is 0.63% and the formal limit is 120%.

Annex 3 reports guarantees granted of R$ 0.00, with a 22% formal limit. Annex 4 reports R$ 0.00 of credit operations in the period/year-to-date, with a 16% general limit and 7% ARO limit. Zero credit operations is not equivalent to zero debt.

Annex 5 is explicitly printed as `Relatorio fora do Periodo de Publicacao - Somente para Acompanhamento`. Its status is preserved. Selected rows include Education-linked gross cash of R$ 46,643,520.24 and liquid cash of R$ 44,132,623.74; FUNDEB transfers show R$ 26,811,796.00 gross and liquid cash. These values are linked cash positions, not authorization for new spending.

Direct page review corrected the Annex 5 column model before PR creation: the Education R$ 1,899,953.37 is prior-exercise committed/unliquidated Restos a Pagar, not `other financial obligations`. Tests reconstruct the selected rows using the source columns.

Annex 6 is reconciled to the detailed annexes, not used as an untraceable summary: DTP matches Annex 1, DCL matches Annex 2, guarantees match Annex 3, and credit operations match Annex 4.

## Authority rule

For facts present in `config/rgf_2026_q1_primary.v1.json`, the primary RGF layer takes precedence over MD_01.2 derived synthesis. MD_01.2 remains methodology/context and is not counted as a second observation.

## Guards

- primary authority upgrade != new fact;
- gross personnel expenditure != LRF DTP;
- formal LRF limit/headroom != free cash or spending authorization;
- cash availability != budget authorization;
- linked Education/FUNDEB cash != unrestricted money;
- Annex 5 accompaniment status != final published period;
- zero credit operations != zero debt;
- no double counting with MD_01.2;
- contextual coverage remains 38/38.

## Remote effects

None: no new web acquisition, Drive write, serving/publication change, schedule or recurrence.
