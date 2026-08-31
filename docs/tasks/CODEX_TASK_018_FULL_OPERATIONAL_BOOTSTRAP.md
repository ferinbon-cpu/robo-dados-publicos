# TASK 018 — Full bounded operational bootstrap

## Movement A: implementation only

This change prepares, but does not authorize or execute, the campaign. The semantic is
`DRAIN_ALL_ELIGIBLE_ITEMS_WITHIN_AUTHORIZED_PROVEN_SCOPE`. Eligibility comes from the
checked-in inventory, not from connector availability. The only fresh-collection family
is `LIMEIRA_JORNAL_OFICIAL`, and only declared HTTPS links in proven discovery windows
and the fixed host allowlist qualify. TDA is contract-unproven, SIOPE 2016–2024 is reused,
and SIOPE 2025 remains semantically blocked.

The batch deduplicates by logical key before GET/create, validates PDF bytes and SHA-256,
uses create-only Bronze/derived/quarantine writes, continues after item-local STOPs, and
stops downstream stages after systemic STOPs. Safety-ceiling exhaustion is `PARTIAL`,
with a deterministic remaining-key checkpoint, never a false completion.

## Zero-effect statement

- live source requests: **0**
- Drive reads: **0**
- Drive writes: **0**
- publication writes: **0**
- live reconciliation: **0**
- workflow_dispatch executions: **0**
- owner authorization: **PENDING**
- bootstrap live run: **NOT EXECUTED**

The later authorization-only PR may modify only the owner evidence, pin the exact
implementation merge SHA, and explicitly authorize T1, T2, and T3. It must not promote
the release or SIOPE 2025.
