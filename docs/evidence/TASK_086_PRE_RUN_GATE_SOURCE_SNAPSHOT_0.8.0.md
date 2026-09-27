# TASK 086 — pre-run gate source snapshot

Documentation-only snapshot of the exact sources that existed before the single authorized live run. This file is not under `.github/workflows/` and cannot trigger GitHub Actions.

## Task contract

- commit: `6ce5e4b9cc8f7c20d18f383a67ae82d2993e84ec`
- path: `docs/tasks/CODEX_TASK_086_BOUNDED_NEXT_CONTRACT_QUERY.md`

```markdown
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
```

## Single-use workflow

- execution head: `53f214ab64bdd1d475811586ea062362ae6d2ae3`
- original path: `.github/workflows/task-086-contract-resolver-live-once.yml`
- permissions: `contents: read`
- trigger: push only on `task-086-next-contract-bounded-query`
- host allowlist: `serv42.limeira.sp.gov.br`
- HTTP budget: 3
- actions pinned by SHA
- workflow removed after run `33788639843`

```yaml
name: TASK 086 bounded next contract query live once
run-name: "TASK 086 one bounded municipal contract query by @${{ github.actor }}"

on:
  push:
    branches:
      - task-086-next-contract-bounded-query

permissions:
  contents: read

concurrency:
  group: task-086-contract-resolver-live-once
  cancel-in-progress: false

jobs:
  bounded-readonly-query:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Checkout exact branch head
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd
        with:
          persist-credentials: false
      - name: Python 3.12
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97
        with:
          python-version: '3.12'
          check-latest: false
      - name: Execute exactly one bounded read-only stateful query
        shell: bash
        run: |
          # Full executed source is preserved at commit 53f214ab64bdd1d475811586ea062362ae6d2ae3.
          # The runtime enforced ALLOWED_HOST=serv42.limeira.sp.gov.br and MAX_REQUESTS=3,
          # then executed LimeiraContractsResolver for only RECTASK_6600049d5284824e9a0a44a6.
          # Any fourth request or different host raised a STOP before transport.
          python -c 'raise SystemExit("documentation snapshot: see pinned commit for exact embedded runner")'
      - name: Upload sanitized bounded evidence
        if: always()
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
```

The YAML block above is intentionally non-executable documentation and abbreviates only the embedded Python body; the exact workflow blob remains immutable in Git history at execution head `53f214ab64bdd1d475811586ea062362ae6d2ae3`.
