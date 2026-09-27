# TASK 137 — exact-URL web discovery transport for PNCP candidate

This gate allocates **authorization unit 2 of 10** from the owner's post-TASK-133 grant.

After merge, the operation is limited to one exact-URL web-open invocation against the PNCP procurement-publication URL pinned by TASK 133.

No search query, follow-up click, second open, retry or raw payload persistence is allowed.

Because this retrieval layer abstracts lower-level HTTP, DNS and redirect behavior, its epistemic role is deliberately weaker than the native PNCP transport:

- it may yield a positive administrative-identifier candidate;
- it may not prove exhaustive absence;
- it may not emit a PNCP `NO_MATCH` conclusion;
- a candidate remains at most `CORROBORATED`;
- municipal-primary verification remains mandatory;
- no financial or transaction identity may be promoted.

No detail, items, history, budget-source or linked-contract endpoint is authorized.
