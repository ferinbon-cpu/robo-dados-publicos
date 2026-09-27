# TASK 081 — pre-run gate source snapshot

This is a **non-executable historical audit snapshot**. It preserves, inside the final PR diff, the exact source content that existed before the single bounded live run. It does not authorize or enable any future execution.

## 1. Task contract before execution

- commit: `4502c552593b4e01d7c1c272e6bd1304fe034be1`
- committed at: `2026-09-03T13:23:05Z`
- original path: `docs/tasks/CODEX_TASK_081_BOUNDED_STATEFUL_CONTRACT_RESOLVER.md`
- original blob SHA: `c7868f94e2c730a687484895b2beff298960d63b`

```markdown
# TASK 081 — bounded stateful municipal contract resolver

Fresh owner authorization is the user's 2026-09-03 instruction `Prossiga com o robo entao`, interpreted only for this bounded step.

## Exact scope

Execute the already-implemented `LimeiraContractsResolver.resolve(...)` against exactly one persisted TASK 076 reconciliation task: `RECTASK_39a82b72abdffa19e0dba705` (`target_source=LIMEIRA_CONTRATOS`). This is the same deterministic selection used by TASK 077.

Search keys are fixed to year `2025`, contract number `09/2025.`, CNPJ corroborating signal `12226306000140`, process hint `29.185/2025.` and the fixed object hint already persisted in TASK 077. The resolver may submit only the contract/year search. CNPJ, process and object are corroborating evidence only and must not broaden the query.

## Remote budget

Maximum three HTTP requests total: one GET to the official municipal contracts landing/search surface; at most one stateful form submission using the discovered same-origin public search form; and at most one same-origin ScriptCase autosubmit relay follow-up if and only if the existing resolver proves it unambiguously. Any fourth request is fail-closed and forbidden.

## Hard boundaries

No Google Drive read/write, no StateRegistry or queue mutation, no serving write, no publication, no source move/delete, no schedule/recurrence/retry loop, no automatic contract identity assertion and no financial identity assertion. Result may be at most `MATCH_CANDIDATE` with evidence. `NO_MATCH` is allowed only after an interpretable result table. Schema/origin/form ambiguity must STOP.

The temporary live workflow used to obtain the evidence is branch-local and must be removed before the final PR is proposed for merge.
```

## 2. One-shot branch-local workflow before execution

- commit: `c1ffc0ca8572308936b643672e03feccd9a3c978`
- committed at: `2026-09-03T13:23:45Z`
- original path: `.github/workflows/task-081-contract-resolver-live-once.yml`
- original blob SHA: `cacd796e9eef3481ee472fa1aa8d1df272fcaa68`
- run created at: `2026-09-03T13:23:48Z`
- run id: `33760913444`
- run head SHA: `c1ffc0ca8572308936b643672e03feccd9a3c978`

```yaml
name: TASK 081 bounded contract resolver live once
run-name: "TASK 081 one bounded municipal contract query by @${{ github.actor }}"

on:
  push:
    branches:
      - task-081-bounded-stateful-contract-resolver

permissions:
  contents: read

concurrency:
  group: task-081-contract-resolver-live-once
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
          set -euo pipefail
          mkdir -p runtime
          python - <<'PY'
          import json
          from pathlib import Path
          from urllib.parse import urlparse

          from robo_dados_publicos.reconciliation.resolvers import LimeiraContractsResolver

          ALLOWED_HOST = "serv42.limeira.sp.gov.br"
          MAX_REQUESTS = 3

          task = {
              "task_id": "RECTASK_39a82b72abdffa19e0dba705",
              "target_source": "LIMEIRA_CONTRATOS",
              "task_type": "FIND_CONTRACT_RECORD",
              "status": "READY_SEARCH",
              "match_keys": {
                  "year": 2025,
                  "contract_number": "09/2025.",
                  "cnpj": "12226306000140",
              },
              "search_hints": {
                  "process_number": "29.185/2025.",
                  "object_text": "contratação de empresa para instalação e desinstalação de ar condicionado",
              },
          }

          class BoundedResolver(LimeiraContractsResolver):
              def __init__(self):
                  super().__init__()
                  self.request_log = []

              def _request(self, url, *, method="GET", params=None):
                  if len(self.request_log) >= MAX_REQUESTS:
                      raise RuntimeError("STOP_TASK081_HTTP_BUDGET_EXCEEDED")
                  host = (urlparse(url).hostname or "").lower()
                  if host != ALLOWED_HOST:
                      raise RuntimeError("STOP_TASK081_ORIGIN_OUTSIDE_ALLOWLIST")
                  self.request_log.append({
                      "ordinal": len(self.request_log) + 1,
                      "method": method.upper(),
                      "host": host,
                      "path": urlparse(url).path,
                      "submitted_field_names": sorted((params or {}).keys()),
                  })
                  return super()._request(url, method=method, params=params)

          resolver = BoundedResolver()
          out = {
              "task": "TASK_081_BOUNDED_STATEFUL_CONTRACT_RESOLVER",
              "base_main_sha": "1edd1e23571201513e9bd94c1bc65c3789825031",
              "selected_task_id": task["task_id"],
              "max_http_requests": MAX_REQUESTS,
              "hard_boundaries": {
                  "drive_reads": 0,
                  "drive_writes": 0,
                  "state_registry_writes": 0,
                  "queue_writes": 0,
                  "serving_writes": 0,
                  "publications": 0,
                  "contract_identity_assertions": 0,
                  "financial_identity_assertions": 0,
              },
          }
          try:
              result = resolver.resolve(task)
              payload = result.to_dict()
              if payload["status"] not in {
                  "MATCH_CANDIDATE",
                  "NO_MATCH",
                  "STOP_CONTRACT_FORM_UNPROVEN",
                  "STOP_MISSING_CONTRACT_OR_SUPPLIER_KEY",
                  "STOP_CONTRACT_RELAY_ORIGIN_UNPROVEN",
                  "STOP_CONTRACT_RESULT_SCHEMA_UNPROVEN",
              }:
                  raise RuntimeError("STOP_TASK081_UNEXPECTED_RESOLVER_STATUS")
              out["resolver_result"] = payload
              out["result"] = "PASS_TASK081_BOUNDED_REMOTE_EXECUTION_RECORDED"
          except Exception as exc:
              out["resolver_result"] = {
                  "status": "STOP_TASK081_REMOTE_EXECUTION",
                  "error_type": type(exc).__name__,
                  "error": str(exc)[:500],
                  "candidates": [],
              }
              out["result"] = "STOP_TASK081_REMOTE_EXECUTION_RECORDED"
          out["request_count"] = len(resolver.request_log)
          out["requests"] = resolver.request_log
          if out["request_count"] > MAX_REQUESTS:
              raise SystemExit("STOP_TASK081_HTTP_BUDGET_EXCEEDED")
          Path("runtime/task081_result.json").write_text(
              json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
              encoding="utf-8",
          )
          print(json.dumps({
              "result": out["result"],
              "resolver_status": out["resolver_result"]["status"],
              "candidate_count": len(out["resolver_result"].get("candidates") or []),
              "request_count": out["request_count"],
          }, ensure_ascii=False, sort_keys=True))
          PY

      - name: Upload sanitized bounded evidence
        if: always()
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: task-081-bounded-contract-resolver-evidence
          path: runtime/task081_result.json
          if-no-files-found: error
          retention-days: 1
```

The executable workflow is intentionally absent from the final branch head. The snapshot above is documentation only and cannot trigger GitHub Actions.
