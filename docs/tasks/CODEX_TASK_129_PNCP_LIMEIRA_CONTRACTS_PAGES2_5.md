# TASK 129 — PNCP Limeira contracts pages 2–5

TASK 128 established a five-page fixed PNCP query snapshot and scanned page 1. TASK 129 is only the separately gated continuation for pages 2, 3, 4 and 5.

It preserves the exact CNPJ, date interval, page size, strong policy markers, weak-term guard and candidate fields from TASK 128.

A complete bounded conclusion is allowed only if all four responses repeat totalRegistros=2023 and totalPaginas=5. Any pagination metadata drift prevents combining the responses with TASK 128 page 1.

Maximum live requests: four GETs, one per page. No retries, redirects, page-1 reread, raw payload persistence or scope widening.

Any candidate remains SECONDARY_AGGREGATOR evidence requiring municipal primary verification. No automatic financial or transaction identity is permitted.
