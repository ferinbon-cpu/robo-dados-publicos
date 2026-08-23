# Jornal Oficial de Limeira — M4E.2 runbook

## Role
Municipal event/act backbone for the Limeira public-data observatory. It complements the TDA financial core: the Jornal Oficial records acts/events; financial sources test whether and how those acts become execution.

## Public surface proven in research
- modern official index: `https://www.limeira.sp.gov.br/jornaloficial`;
- query contract visibly exposed by the public index: `?ano=YYYY&mes=M` and `?dataDiario=D/M/YYYY`;
- index fields: date range, edition and term search;
- explicit link to an older archive around the 01/02/2023 migration boundary;
- recent editions are published as PDFs, with many PDFs hosted under eCrie;
- historical Limeira PDFs also exist under the municipal `/jornal/NNNN.pdf` route;
- public access is described as free and without registration in the Jornal Oficial itself.

## Boundary rule
Do not assume a clean cutover date. The legacy page can overlap the modern archive around February 2023. Merge by edition number and later by SHA-256. Never discard an overlapping item merely because it came from the other archive.

## Acquisition rule
1. Read the official index HTML.
2. Extract only document routes declared by that HTML.
3. Never synthesize/guess eCrie filenames or `/jornal/<edition>.pdf` paths.
4. Validate the document response as `application/pdf` before enabling production collection.
5. Store original PDFs in Bronze by immutable hash-qualified name.
6. Build text/metadata derivatives later in Silver/RAG; do not mutate Bronze.

## Privacy/minimization
The official PDF is preserved in Bronze as public evidence. Derived Silver/Gold/RAG layers must not replicate personal identifiers unless analytically necessary and justified. Business identifiers such as supplier CNPJ remain available when required for procurement/financial joins.

## Intended event schema (future Silver)
`edition`, `publication_date`, `page`, `organ`, `secretariat`, `act_type`, `act_number`, `process_number`, `contract_number`, `procurement_number`, `supplier`, `cnpj`, `object`, `value`, `effective_from`, `effective_to`, `source_pdf`, `source_hash`.

## Current gate
0.5.2 implements deterministic index discovery/parsing and disabled inventory emission. A live Cloud Shell/GitHub discovery must prove the current HTML/document route and content type before production downloads are enabled.

## Pagination completeness guard
The modern page can report more items than are visible on the first result page. The collector therefore reads the portal's own `Total de itens encontrados`, follows only pagination links explicitly emitted by the same index path, filters out the separate "recent editions" block by target month, and returns `PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED` rather than silently claiming completeness when the reported total is not reached.
