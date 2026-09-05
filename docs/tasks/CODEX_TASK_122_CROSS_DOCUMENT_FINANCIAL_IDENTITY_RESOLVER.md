# TASK 122 — cross-document EITI financial identity resolver

## Purpose

TASK 122 is the first resolver that consumes the three independently tested evidence adapters:

- TASK 117 — PPA planning/policy evidence;
- TASK 119 — LOA budget authorization evidence;
- TASK 121 — SIOPE/FUNDEB FOMENTO ETI reporting evidence.

It does not acquire new data. Its purpose is to determine whether the current corpus contains an admissible cross-document bridge from EITI policy identity to a budget/execution identity.

## Current anchors

### PPA 2026–2029

The policy/planning anchor contains the Educação Integral indicator and stable planning keys including Program 2001.

### LOA 2026

The authorization anchor contains Program 2001 and generic actions 2690/2720 with budget-unit/function/subfunction/source/group information and authorization amounts.

### SIOPE/FUNDEB 1º bimestre/2026

The accounting-reporting anchor contains the scoped composite policy-finance alias `FOMENTO ETI` and reporting-bucket values, but no program/action/subaction, ficha, cost center or transaction stable key.

## Resolution rule

A cross-document financial bridge requires more than a shared string or number.

Keys are comparable only when:
1. the accounting-key type matches;
2. the value matches;
3. the shared key is independently admissible as policy-specific.

The current PPA↔LOA intersection contains `program=2001`, but TASK 049 and TASK 051 forbid treating Program 2001 or generic actions 2690/2720 as EITI financial identity.

The PPA value `unit=10.00.00` and LOA value `org=10.00.00` are explicitly recorded as a same-value/different-dimension observation, not a match.

SIOPE has no stable accounting key to intersect with PPA or LOA.

## Legacy 2607004 clue

`2607004` remains a hypothesis only. Historical repository logic already distinguishes multiple identities involving that application code and includes revenue contexts. It cannot become a policy or transaction key until primary granular evidence binds it to:

- an explicit EITI/FOMENTO ETI marker;
- a stable accounting object;
- an execution event;
- provenance.

## Current result

`STOP_NO_STABLE_POLICY_TO_ACCOUNTING_EXECUTION_KEY`

No cross-document financial identity candidate is emitted. Financial identity and transaction identity remain UNKNOWN.

## Directed next evidence

The next acquisition should not repeat generic PPA/LOA searches. It should seek, in priority order:

1. explicit EITI cost center/subaction/execution tag;
2. detailed education budget execution/balancete;
3. empenho/liquidação/pagamento detail.

The immediate unlocking record must combine:
- explicit policy marker;
- stable accounting identifier;
- source provenance.

For a transaction chain it must additionally contain:
- execution document/event ID;
- amount;
- date/period;
- execution stage.

## Effects

T0/offline only. No network, Drive, OCR, persistence, StateRegistry, queue, serving, publication, retry, recurrence or schedule.
