# TASK 162 — PNCP modality 9 stable-ID recovery guard

## Purpose

Keep the Inexigibilidade discovery moving without converting chronology into identity.

## Current leads

### Process I00084

Observed indexed/direct descriptive fields:

- process: `I00084`;
- object: `CURSO DE CAPACITACAO`;
- publication date: `2026-08-19`;
- estimated value: `R$ 12,400.00`;
- modality: Inexigibilidade.

The neighboring publication sequence evidence makes `sequencialCompra=593` a strong chronological candidate, because sequence 592 is independently associated with another object in the same date window and sequence 594 appears as a Dispensa record in owner-relayed official JSON. This remains an inference only.

**Invariant:** an adjacent sequence gap does not prove `numeroControlePNCP`.

No `45132495000140-1-000593/2026` identity is created until the source or an exact cross-source record matches at minimum CNPJ, process, object and publication date.

### School-pass lead

`AQUISICAO DE PASSE ESCOLAR`, estimated R$ 3,816,720.00, remains `EDUCATION_RELEVANT` only. Its stable PNCP purchase ID has not been recovered. No EITI, contract, supplier, financial or transaction identity is created from the object/value alone.

## Latest live attempt

A direct technical GET attempt to the authorized official PNCP publication endpoint on 2026-09-05 failed during DNS resolution before source reach.

Required semantics:

`DNS_RESOLUTION_FAILURE_PRE_SOURCE -> SOURCE_TRANSPORT_UNAVAILABLE`

It must never become PNCP `NO_MATCH`.

## Promotion boundary

Chronology, sequence gaps and search-index snippets are discovery aids only. Stable-ID promotion requires direct source evidence or exact cross-source identity. Downstream contract, supplier, financial, transaction or EITI promotion is forbidden until that stable identity is established.
