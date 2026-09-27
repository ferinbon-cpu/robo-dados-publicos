# TASK 118 — active EITI terminology registry v2

## Why

TASK 055A created the five-family base ontology (A–E) with 63 distinct terms. TASK 056 later discovered a strong composite alias, `FOMENTO ETI`, and explicitly marked it `must_be_added_to_future_matching=true`.

Historical TASK 055A evidence must remain immutable. TASK 118 therefore creates an active terminology registry as an overlay.

## Active vocabulary

- immutable base A–E: 63 terms;
- discovered composite aliases: 1;
- active distinct vocabulary: 64 terms.

Current discovered alias:

`FOMENTO ETI`

Classification:

`STRONG_POLICY_FINANCE_REPORTING_ALIAS`

Semantic roles:
- policy signal;
- financing signal;
- reporting-bucket alias.

## Scope guard

The alias is scoped to `ACCOUNTING_EXECUTION_PRIMARY` sources and `FINANCIAL_REPORTING_ONLY`.

Therefore:
- it can identify that a primary accounting report contains a policy-finance reporting bucket;
- it cannot, by itself, prove generic municipal EITI financial identity;
- it cannot prove transaction identity;
- an amount alongside the alias is still insufficient;
- a stable accounting key remains required before TASK 116 may emit even a transaction-link candidate.

## TASK 116 integration

TASK 116 now:
- preserves the 63-term base;
- loads the versioned terminology overlay;
- searches 64 active terms;
- records composite-alias semantic roles and source-role scope;
- qualifies `FOMENTO ETI` only for accounting-execution-primary sources;
- keeps all outputs candidate-only.

## TASK 117 compatibility

The PPA adapter is repinned to the new TASK 116 contract. PPA semantics must remain unchanged: no financial identity candidate is created.

## Effects

T0/offline only. No network, Drive, OCR, persistence, serving, publication, retry, recurrence or schedule.

## Next

Use this active vocabulary for the LOA and SIOPE/FUNDEB repository-evidence adapters. LOA should expose authorization amounts and generic budget keys without policy attribution; SIOPE should rediscover the dedicated FOMENTO ETI reporting bucket while preserving missing transaction-level linkage.
