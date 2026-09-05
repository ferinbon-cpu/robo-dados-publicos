# TASK 133 — design one-shot PNCP procurement publication live gate

TASK 132 selected the PNCP procurement/publication surface and was merged at `ca09484b3967e6e7820d949dc8859129d5586b24`.

TASK 133 is **design only**. It pins the next live probe but does not authorize or execute it.

## Fixed future probe

- endpoint: `/api/consulta/v1/contratacoes/publicacao`
- CNPJ: `45132495000140`
- modality: **Credenciamento (12)**
- dates: 2025-11-28 through 2026-09-04
- page: 1
- page size: 500
- maximum: 1 GET
- redirects: 0
- retries: 0
- raw response persistence: forbidden

A qualifying candidate must contain a strong Educação Integral policy marker in `objetoCompra` or `informacaoComplementar`. Credenciamento/oficineiro/oficinas context alone does not qualify.

Any recovered `numeroControlePNCP`, `anoCompra`, `sequencialCompra`, `numeroCompra` or `processo` remains a **candidate administrative identifier** from a secondary aggregator. Municipal-primary verification is mandatory before promotion.

## Authorization boundary

The design contract requires `authorized_now=false`. A future execution requires a new owner authorization issued **after TASK 133 is merged**, bound to the then-current gate/head and consumed by one run only.

No detail/items/history/budget-source/linked-contract request is authorized by TASK 133. No financial identity or transaction identity can be promoted here.
