# TASK 217C — canonical discovery result

The authorization-gated discovery carrier ran successfully against the official Limeira Jornal Oficial index.

## Proven scope

Run `34292251773`, pinned to implementation `993f8a07516bae641461221959552e6e2950a8d1`, completed all nine monthly partitions from 1 January through 8 September 2026.

The official index declared 99 documents:

- Jan: 12
- Feb: 12
- Mar: 12
- Apr: 12
- May: 12
- Jun: 12
- Jul: 10
- Aug: 12
- Sep through day 8: 5

The run used nine index pages, an estimated 18 GETs including robots checks, and downloaded zero PDFs.

The sanitized result hash is `7c31c9791793c889a8c76e27bcf0d6b6b26f23a3b6bec07fbd95d8c1fba29510`. The workflow artifact ZIP hash is `2f4534f4da59f6af59b0ca78e8a7a424c88f5761a2871b6fde309354a4f3a393`.

## Deduplication against the current JOM corpus

The current materialized JOM event fixture already covers 12 editions, 7304 through 7315, yielding 303 validated events. Those 12 are present in the discovery scope and do not need redigestion.

Therefore the bounded new-document scope is 87 editions.

This is still not content evidence. INFRA_Q2 remains blocked at 33/38 until those 87 editions are read under a separate authorization, events are extracted, and exact TASK 217A school identity is found.
