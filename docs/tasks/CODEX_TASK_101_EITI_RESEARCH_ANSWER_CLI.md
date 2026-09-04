# TASK 101 — EITI-Limeira offline research answer CLI

## Scope

T0/offline and stdout-only.

No workflow is added. No network, Drive, OCR, LLM, remote persistence, serving, publication, retry, recurrence or schedule is introduced.

## Objective

Expose the TASK 099 query layer plus the TASK 100 integrity-checked Markdown renderer through a simple local command for the researcher.

Default command:

    python scripts/render_eiti_research_answer_offline.py

The command prints the deterministic POLICY_STATUS_PACKET for POLICY:EITI_LIMEIRA to stdout.

Before parsing either research config, the CLI verifies the SHA-256 of its exact bytes against hashes pinned from the canonical TASK 100 merge state. Missing, malformed or byte-drifted inputs stop fail-closed.

## Supported views

The CLI exposes only the query types already defined by TASK 099:

- CLAIM_AUDIT
- INSTITUTIONALIZATION_MATRIX
- EVIDENCE_GAPS
- POLICY_STATUS_PACKET

It does not accept arbitrary source paths, URLs, prompts or free-form questions in this first version.

## Evidence controls

The optional --no-evidence flag removes expanded evidence packets from the view while preserving evidence IDs.

The optional --no-unknown-gaps flag suppresses the dedicated matrix-gap list. It does not promote UNKNOWN claims or dimensions and does not rewrite the institutionalization matrix itself.

## Integrity chain

The path is:

SHA-256-pinned versioned EITI evidence → TASK 099 deterministic query packet → TASK 100 query-packet SHA verification → TASK 100 Markdown renderer → TASK 101 stdout

Any packet tampering detected by TASK 100 stops rendering.

## Why stdout only

TASK 101 deliberately does not decide persistence.

A user or later bounded runner may redirect stdout into an ephemeral workspace, but repository/Drive/serving/publication persistence remains a separate future gate.

## First researcher-facing use

The default output visibly includes the current EITI-Limeira evidence state, including:

- normative and planning evidence;
- financial-identity uncertainty;
- transaction-execution uncertainty;
- outcome/effect uncertainty;
- historical acquisition gaps for PPA 2018-2021 and PPA 2022-2025;
- document identities and locators when expanded evidence is enabled.

## Files

- scripts/render_eiti_research_answer_offline.py
- tests/test_task_101_eiti_research_answer_cli.py
- docs/evidence/TASK_101_EITI_RESEARCH_ANSWER_CLI_0.8.0.json

TASK 101 preserves the original TASK 100 evidence snapshot unchanged and adds a separate post-merge GitHub API readback record at `docs/evidence/TASK_100_POST_MERGE_CLOSURE_0.8.0.json`, after the referenced PR, runs and merge already existed.

## Next step

After CI/review, the next useful boundary is not an LLM. TASK 102 should define a generic offline query-spec input contract so the same CLI path can answer additional policies or research objects without hard-coding EITI-Limeira, while still refusing arbitrary source acquisition or remote effects.
