# TASK 086 — bounded next municipal contract query

Fresh owner authorization is the user's 2026-09-03 instruction `Prossiga`, interpreted only for this bounded step after TASK 085 selected the next deterministic `LIMEIRA_CONTRATOS` task.

## Exact scope

Execute `LimeiraContractsResolver.resolve(...)` against exactly one TASK 076 reconciliation task selected and pinned by TASK 085: `RECTASK_6600049d5284824e9a0a44a6` (`target_source=LIMEIRA_CONTRATOS`).

Fixed match keys are year `2024`, contract number `170/2024`, CNPJ `51656458000134`, contractor `Consil Sistema Prevenção Contra Incêndio Ltda`; the persisted process hint is `900.711/2025`. The public query may submit only the year/contract search supported by the resolver. CNPJ, supplier, process and object remain corroborating evidence and must not broaden the query.

## Remote budget

Maximum three HTTP requests total: one GET to the official municipal contracts search surface; at most one stateful form submission; and at most one same-origin ScriptCase autosubmit relay if and only if the resolver proves it unambiguously. Any fourth request is fail-closed and forbidden. Only host `serv42.limeira.sp.gov.br` is allowed.

## Hard boundaries

No Google Drive read/write, no StateRegistry or queue mutation, no serving write, no publication, no source move/delete, no schedule/recurrence/retry loop, no automatic contract identity assertion and no financial identity assertion. Result may be at most `MATCH_CANDIDATE`; `NO_MATCH` and fail-closed STOP states are valid outcomes.

The live gate is single-use. Any temporary branch-local workflow must be removed immediately after the one authorized run. No future execution is authorized by this task.
