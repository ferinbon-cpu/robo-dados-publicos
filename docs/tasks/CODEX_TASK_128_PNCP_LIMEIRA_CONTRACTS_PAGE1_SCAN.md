# TASK 128 — PNCP Limeira contracts/empenhos page-1 scan

TASK 128 opens a new transport route after the bounded TCESP and Jornal Oficial PDF transports stopped without bytes.

The query is limited to Limeira CNPJ 45.132.495/0001-40, publication dates 28/11/2025 through 04/09/2026, page 1, at most 500 rows, one GET and zero retry.

The scan qualifies only rows whose object or complementary information contains an explicit Educação Integral marker. Generic oficina/oficineiro/extracurricular wording never qualifies alone.

Within the current TASK 095 epistemic roles, PNCP is treated as SECONDARY_AGGREGATOR even though it is an official federal registry surface. A match may corroborate a contract/empenho candidate but still requires municipal-primary verification before EITI financial or transaction identity can be promoted.

If the API reports more than one page, TASK 128 stops after page 1 and requires a fresh paging gate. Raw JSON is not committed.
