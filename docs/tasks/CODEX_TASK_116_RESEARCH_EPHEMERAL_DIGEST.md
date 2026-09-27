# TASK 116 — generic research ephemeral digest

## Purpose

TASK 116 converts a family-adapter-normalized packet into an ontology-aware research candidate packet while preserving the ephemeral/no-persistence boundary established by TASK 090–092.

Architecture:

`source bytes -> family adapter -> normalized research segments -> TASK116 research digest -> candidate packet -> separate adjudication/persistence gate`

TASK 116 intentionally does not read Drive or public sources and does not add family adapters.

## Ontology coverage

The EITI profile pins the TASK 055A ontology and validates all five families:

- A: 8 canonical policy identifiers;
- B: 6 local planning/normative aliases;
- C: 15 operational offer/journey signals;
- D: 13 financing/induction signals;
- E: 21 accounting/planning linkage keys.

Total: 63 terms.

TASK 113 remains the qualification source for A/B/C strength and companion-context rules. D and E are observable signals but cannot create a policy signal on their own.

## Generic normalized input

Every adapter must eventually emit `RESEARCH_EPHEMERAL_DIGEST_INPUT_V1` with:

- typed document identity;
- source role;
- registered source family;
- SHA-256;
- adapter contract;
- bounded text segments;
- non-empty provenance locator per segment;
- optional structured accounting keys;
- optional amount + execution-stage observations;
- all remote-effect authorizations false.

This is a data contract, not an adapter implementation.

## Financial bridge semantics

TASK 116 emits a financial-identity bridge only as `CANDIDATE`, and only within one segment where all of the following coexist:

1. a qualified A/B/C policy signal;
2. at least one explicit or adapter-proven stable accounting key;
3. a BRL amount;
4. a declared execution stage.

D/E lexical terms, amount equality, or generic accounting keys alone never establish EITI attribution.

The separate financial identity resolver remains responsible for cross-document/multidimensional adjudication.

## Source-role semantics

TASK 095 remains authoritative about what a source role can prove. TASK 116 reports that maximum but caps its own output at `CANDIDATE`. Therefore a primary accounting source does not turn a TASK 116 candidate into a proven policy link automatically.

## Effects

T0/offline only:
- network 0;
- Drive 0;
- Bronze/Silver/Gold/RAG persistence 0;
- StateRegistry/queue/serving/publication 0;
- overwrite/delete/move 0;
- retry/recurrence/schedule 0;
- LLM 0;
- causal inference 0.

## Follow-up

After CI/merge, the next tasks should implement adapters independently, beginning with already-versioned evidence:

1. PPA normalized adapter;
2. LOA normalized adapter;
3. BUDGET_EXECUTION normalized adapter;
4. SIOPE/FUNDEB normalized adapter.

Only after those fixtures can reproduce known repository facts should the financial-identity resolver consume their candidate packets.
