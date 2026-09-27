# TASK 130 — PNCP Limeira pages 3–5

TASK 130 is a fresh, separately gated continuation after TASK 129 consumed page 2 and stopped on a page-3 30-second timeout.

Pages 1 and 2 are already proven within the fixed query snapshot and are not reread. TASK 130 requests only pages 3, 4 and 5.

The query scope is unchanged: CNPJ 45132495000140, 2025-11-28 through 2026-09-04, page size 500, expected 2023 records / 5 pages.

The transport timeout is increased to 60 seconds per page, but redirects and retries remain zero. The task stops after the first failure.

Matching is inherited exactly from TASK 129/TASK 128. Weak terms never qualify alone.

Only if pages 3–5 preserve the 2023/5 snapshot and contain exactly 1023 rows may the result combine with the prior 1000 rows as an exhaustive 2023-row bounded scan.

Any candidate remains SECONDARY_AGGREGATOR evidence requiring municipal primary verification.
