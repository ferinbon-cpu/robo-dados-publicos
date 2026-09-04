# TASK 102 — generic offline research query-spec contract

## Scope

T0/offline, deterministic and stdout-only.

No workflow, network client, Drive client, OCR, LLM, persistence, serving, publication, retry, recurrence or schedule is introduced.

## Objective

Remove the EITI-Limeira hard-coding from the researcher-facing CLI without introducing arbitrary prompts or source acquisition.

The generic command is:

    python scripts/render_research_answer_offline.py

Its default spec is:

    config/research_queries/eiti_limeira_policy_status.v1.json

## Contract

The generic path has three reviewed layers.

1. config/research_dataset_registry.v1.json
   - registers research datasets and subject identity;
   - pins exact source bytes by SHA-256;
   - binds source paths to versioned files under config/;
   - declares allowed deterministic query types.

2. config/research_queries/*.json
   - declares a query over one registered dataset;
   - cannot declare source paths, source URLs, prompts or free-form questions;
   - declares only query identity/type, subject and deterministic display flags.

3. scripts/render_research_answer_offline.py
   - accepts only a query-spec filename, never an arbitrary path;
   - verifies registered source bytes before parsing;
   - executes TASK 099 and TASK 100 unchanged;
   - writes only Markdown to stdout.

## Generalization boundary

A future research object can be introduced by a reviewed registry entry plus versioned query spec and compatible ontology/crosswalk data. The generic Python CLI does not need object-specific code.

This does not mean arbitrary data can be queried. Registry and query-spec changes remain repository changes subject to PR review and CI.

## Fail-closed conditions

The command stops on path traversal or subdirectory injection, unknown spec, unknown dataset, dataset/subject mismatch, invalid query type, source path outside config/, malformed registry/spec, SHA-256 drift, or invalid research packets.

## Preserved epistemic limits

TASK 102 cannot promote claim status, create financial identity, create causal effect, turn scoped NO_MATCH into nonexistence, rewrite claim text through a language model, acquire missing PPA evidence or prove transaction execution.

Those remain separate evidence-producing tasks.

## Next empirical boundary

After TASK 102, the next useful task is a separately gated acquisition design for the complete primary evidence of PPA 2018–2021 and PPA 2022–2025. That gate should seek only the primary-document identity, stable source identity/hash, typed locator and direct text/visual evidence already declared as missing by TASK 098.
