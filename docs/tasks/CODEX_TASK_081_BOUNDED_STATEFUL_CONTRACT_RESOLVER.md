# TASK 081 — bounded stateful municipal contract resolver

Fresh owner authorization is the user's 2026-09-03 instruction `Prossiga com o robo entao`, interpreted only for this bounded step. The consumed authorization is normalized in `docs/evidence/TASK_081_BOUNDED_STATEFUL_CONTRACT_RESOLVER_OWNER_AUTHORIZATION_0.8.0.json`.

## Exact scope

Execute the already-implemented `LimeiraContractsResolver.resolve(...)` against exactly one persisted TASK 076 reconciliation task: `RECTASK_39a82b72abdffa19e0dba705` (`target_source=LIMEIRA_CONTRATOS`). This is the same deterministic selection used by TASK 077.

Search keys are fixed to year `2025`, contract number `09/2025.`, CNPJ corroborating signal `12226306000140`, process hint `29.185/2025.` and the fixed object hint already persisted in TASK 077. The resolver may submit only the contract/year search. CNPJ, process and object are corroborating evidence only and must not broaden the query.

## Remote budget

Maximum three HTTP requests total: one GET to the official municipal contracts landing/search surface; at most one stateful form submission using the discovered same-origin public search form; and at most one same-origin ScriptCase autosubmit relay follow-up if and only if the existing resolver proves it unambiguously. Any fourth request is fail-closed and forbidden.

## Hard boundaries

No Google Drive read/write, no StateRegistry or queue mutation, no serving write, no publication, no source move/delete, no schedule/recurrence/retry loop, no automatic contract identity assertion and no financial identity assertion. Result may be at most `MATCH_CANDIDATE` with evidence. `NO_MATCH` is allowed only after an interpretable result table. Schema/origin/form ambiguity must STOP.

## Auditable execution chronology

This task contract was committed before the live run at `4502c552593b4e01d7c1c272e6bd1304fe034be1` (2026-09-03T13:23:05Z). The temporary bounded workflow was then committed at `c1ffc0ca8572308936b643672e03feccd9a3c978` (2026-09-03T13:23:45Z), with `contents: read`, exact branch scope, host allowlist and hard maximum of three requests. Run `33760913444` was created at 2026-09-03T13:23:48Z on that exact workflow SHA and completed successfully.

The temporary live workflow was removed from the final PR head after the single run so it cannot execute again. Its historical source remains auditable at the pinned gate commit. The later normalized authorization file explicitly does not claim to have been the pre-run gate. The complete chain is pinned in `docs/evidence/TASK_081_PRE_RUN_GATE_CHAIN_0.8.0.json`.
