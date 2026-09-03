# TASK 082 — actionable DeepSeek automatic review

Owner authorization is the user's 2026-09-03 instruction `Entao corrija`, interpreted only as permission to correct the already-authorized automatic DeepSeek reviewer so that its findings are inspectable and its merge signal is deterministic.

## Problem

The automatic reviewer successfully executed read-only calls but exposed only a top-level model verdict in retrievable logs. Repeated `CHANGES_REQUESTED` values therefore created operational friction because the concrete findings remained trapped in the GitHub Actions job summary and could not be inspected reliably by the orchestrator.

## Exact correction

1. Keep the existing trusted `workflow_run` trigger and same-repository/head checks.
2. Keep checkout pinned to the trusted default branch; never execute PR code.
3. Remove the obsolete `issues: write` permission. The automatic reviewer is strictly read-only with respect to GitHub repository state.
4. Redact secret-like strings recursively from model output before local materialization or logging.
5. Emit the complete sanitized review JSON between stable log markers so the orchestrator can retrieve the actual findings.
6. Add a deterministic `deepseek_gate_decision`:
   - `BLOCK` only when `blocking_findings` is non-empty;
   - `PASS` when the model says PASS and no blocking finding exists;
   - `ADVISORY` for REVIEW or CHANGES_REQUESTED without a concrete blocking finding.
7. Preserve CI and repository policy as independent gates. DeepSeek's raw verdict alone is not a merge gate.
8. Include finding counts, effective verdict and review SHA-256 in the machine-readable summary.

## Hard boundaries

No source collection, no Drive access, no branch/code/issue/PR write by DeepSeek, no merge, no publication, no schedule or new recurrence, no live public-data query and no financial/contract identity promotion. API behavior remains one bounded review request per already-existing automatic review event.
