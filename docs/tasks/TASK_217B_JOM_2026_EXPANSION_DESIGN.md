# TASK 217B — bounded 2026 JOM expansion design

TASK 217A proved the exact 69-school identity bridge but found no named municipal school in the current 303-event corpus. TASK 217B prepares the next evidence acquisition without authorizing it.

## Exact future live scope

- source: official Limeira Jornal Oficial index and only links declared by that index;
- period: 1 January 2026 through 8 September 2026;
- nine monthly partitions;
- maximum five index pages per month and 45 total;
- maximum 300 documents;
- maximum 50 MiB per document and 1 GiB aggregate;
- no automatic retry;
- no guessed alternate PDF URLs;
- robots policy must be readable/allow the request;
- incomplete discovery for any month means STOP and forbids absence inference.

The first pass is discovery metadata only. Page-level text screening may reduce later processing work, but it is never an identity source. School identity is created only at event level by the exact TASK 217A alias-to-INEP bridge.

Generic references such as “unidades escolares” remain unassigned even when they are strong infrastructure evidence.

## Authorization boundary

This PR is T0/offline. It performs no source network request and creates no live workflow. The consumed TASK 018 authorization is explicitly rejected. A future live run must carry a separate owner authorization pinned to the exact merged implementation SHA, repository, branch, source, operation and date scope. Live runtime is also forbidden from changing answerability directly; any exact matches require a separate canonization step.
