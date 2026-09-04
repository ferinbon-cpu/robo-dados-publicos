# TASK 119 — LOA repository-evidence adapter for the research digest

## Scope

T0/offline. Uses only the blob-pinned TASK 048 LOA 2026 candidate review. It does not read the 631-page PDF, Drive or any public source.

## What enters the digest

For the two directly validated generic actions (2690 and 2720), the adapter emits:

- action-total authorization observations;
- expense-group components;
- funding-source components;
- stable org/unit/function/subfunction/program/action keys;
- funding_source or expense_group keys where the source provides them.

Ten segments are emitted in total.

## Financial-stage semantics

Every monetary observation is `AUTHORIZATION`.

LOA enactment is never relabelled as:
- commitment;
- liquidation;
- payment.

## EITI boundary

The source itself records:
- Program 2001 -> explicit EITI action/subaction: NOT_PROVEN;
- action 2690 EITI-specific: false;
- action 2720 EITI-specific: false;
- generic action/program total attribution to EITI: FORBIDDEN.

TASK 119 therefore expects zero financial-identity candidates even though stable budget keys and authorization amounts are present.

This is the intended complement to TASK 117:
- PPA: policy signal + planning key, missing financial stage;
- LOA: budget key + authorization amount, missing policy-specific signal.

Neither side alone closes the identity bridge.

## Divergence guard

Pages 173–174 preserve the known text-layer vs direct-visual divergence for Alimentação Escolar:
- text layer: R$ 29,000,000;
- direct visual validation: R$ 28,000,000.

The adapter uses R$ 28,000,000 and preserves the divergence explicitly. No silent repair is permitted.

## Effects

No network, Drive, OCR, Bronze/Silver/Gold/RAG write, StateRegistry, queue, serving, publication, retry, recurrence or schedule.

## Next

Build the SIOPE/FUNDEB reporting adapter using the active 64-term vocabulary. It should rediscover `FOMENTO ETI` as a policy-finance reporting signal, amounts and reporting-stage observations, while still failing to create a transaction bridge because the stable accounting key is absent.
