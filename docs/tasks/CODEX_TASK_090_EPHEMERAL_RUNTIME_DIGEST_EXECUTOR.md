# TASK 090 — generic ephemeral runtime digest executor

## Authorization

The owner's current instruction `prossiga` authorizes this engineering task only.

This task is **T0/offline**: it does not authorize a new Drive read, source-network request, Bronze/Silver/Gold/RAG persistence, StateRegistry/queue mutation, serving, publication, retry, recurrence or schedule.

## Why this task exists

TASK 073 already proved the desired operating pattern with three immutable Jornal Oficial PDFs:

- 817 Silver page rows;
- 52 Gold events;
- 1,519 RAG chunks;
- 12 local candidate files in the historical TASK 073 accounting;
- no derived Drive write during that processing step.

TASK 074 deliberately persisted selected derived candidates only in a later, separate gate.

TASK 090 turns the **local-only processing pattern** from TASK 073 into a reusable executor instead of leaving it embedded in one Jornal-specific operational sequence.

## Scope

Add a fail-closed executor that accepts source bytes that have **already been staged inside a fresh ephemeral workspace**.

Initial adapter surface:

- family: `JORNAL_OFICIAL`;
- processor contract: `JORNAL_OFICIAL_LIMEIRA_PDF_V01`;
- MIME: `application/pdf`;
- required maturity: `EXECUTION_READY_BOUNDED`;
- maximum 3 files;
- maximum 70,000,000 bytes per file;
- maximum 110,000,000 input bytes per batch.

The bounds intentionally cover the already-proven TASK 073 three-file batch without broadening execution to arbitrary families.

## Runtime behavior

For every accepted Jornal input, the executor calls the existing `JournalPdfProcessor` with:

- `stage_bronze=false`;
- `plan_reconciliation=false`;
- OCR disabled by contract;
- no network capability;
- no remote persistence capability;
- the exact processor source is pinned to Git blob `7dc539955c99caa6f2a0f1824e8492290ad75344`;
- the pinned processor source is audited before execution for forbidden network/process import roots.

The CLI also requires its manifest file to be a regular file inside the supplied ephemeral workspace; a symlinked workspace root is rejected.

Allowed candidate files are exactly:

- `edition_manifest.json`;
- `pages_silver.jsonl`;
- `events_gold.jsonl`;
- `chunks_rag.jsonl`.

Candidate files exist only below the caller-supplied ephemeral workspace. The executor computes SHA-256 for the staged input and every candidate output and emits a deterministic candidate-set digest.

## Fail-closed boundaries

The executor must STOP on:

- unknown or non-adapted family;
- maturity below the adapter requirement;
- unsupported MIME;
- path traversal;
- symlinked/non-regular source input;
- duplicate source key or duplicate input path;
- more than 3 inputs;
- per-file or aggregate byte limit breach;
- non-fresh candidate root;
- OCR-required / non-PASS processor status;
- unexpected output file;
- any manifest or contract that enables a remote effect.

Partial candidates are deleted when processing stops.

## Important semantic boundary

`AUTO_INGEST` routing eligibility is not execution maturity.

TASK 090 does **not** promote RREO, FUNDEB, MDE, PPA, LDO, LOA, Censo Escolar, IDEB or any other family to generic digest execution. Adding an adapter or increasing a bound requires a separate reviewed task with its own fixture/contract/provenance evidence.

## Files

- `config/ephemeral_runtime_digest.v1.json`
- `robo_dados_publicos/manual_ingest/ephemeral_runtime_digest.py`
- `scripts/run_ephemeral_runtime_digest.py`
- `tests/test_task_090_ephemeral_runtime_digest.py`

## Acceptance

Required repository validation remains the canonical set from `AGENTS.md`, including full unit regression and selftest.

No PASS is claimed by this document before CI observes it.

## Next bounded gate

After TASK 090 passes review, a separate TASK 091 may stage bytes from an explicitly authorized source into a fresh runner temp directory and invoke this executor.

That future staging step is remote-read scope and is **not authorized by TASK 090**. Persistence of candidates remains a separate gate after digest validation.


## TASK 171 compatibility note

The Jornal processor evolved in TASK 171 to emit semantic facets by default. This legacy ephemeral digest contract explicitly calls `emit_semantic_facets=false`, so its historical four-file candidate output set remains unchanged. The processor blob pin is updated to the reviewed TASK 171 processor source; no output-set broadening or remote effect is introduced here.


## TASK 173 compatibility note

TASK 173 adds an accounting-query sidecar to normal Jornal processing, but the legacy ephemeral digest still calls the processor with `emit_semantic_facets=false`. Therefore neither `event_semantics_gold.jsonl` nor `accounting_query_tasks.jsonl` enters the historical four-file TASK 090 candidate set. The processor blob pin is updated explicitly; no remote effect or output-set broadening is authorized.
