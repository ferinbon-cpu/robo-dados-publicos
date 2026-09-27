# TASK 132 — select official procurement publication surface

TASK 132 changes the search object from **contracts** to **procurement publications/contratações**.

The PNCP contract surface was exhaustively scanned in TASK 128–130 and yielded no strong policy marker in 2,023 records. The Jornal Oficial PDF route was consumed with zero bytes, and TASK 131 web-index queries did not reveal a stable process/editais identifier.

The selected surface is the PNCP public consultation endpoint for contratações by publication date:

`/api/consulta/v1/contratacoes/publicacao`

The target modality is **Credenciamento (code 12)**. The next probe is restricted to Limeira CNPJ 45132495000140, 2025-11-28 through 2026-09-04, page 1, size 500, one GET only.

No live request is executed in TASK 132.

If a strong EITI policy marker appears, the candidate must expose or lead to a stable procurement identifier such as numeroControlePNCP / anoCompra / sequencialCompra / processo. The candidate remains secondary-registry evidence requiring municipal primary verification.

Once an exact contratação identifier exists, current PNCP detail, item, history, budget-source and linked contract/empenho endpoints can be queried — each under a separate gate.
