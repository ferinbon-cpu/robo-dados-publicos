# TASK 161 — PNCP manual publication sweep evidence guards

## Purpose

Convert the owner-relayed official PNCP publication sweep into sanitized, auditable repository evidence and add fail-closed semantics learned from the sweep. Raw JSON is deliberately not persisted.

## Fresh authorization

TASK 160 closed the prior 10-unit batch at zero. After that closure, the owner issued a fresh explicit instruction:

`Autorizado pn p irrestrito`

For this task the phrase is interpreted narrowly as unmetered **PNCP live read/discovery** authorization until revoked or superseded. It does not authorize PNCP mutations, Drive writes, or unrelated live sources.

## Exact observed official API scope

Endpoint:

`/api/consulta/v1/contratacoes/publicacao`

Filters:

- CNPJ: `45132495000140`
- municipality identity: MUNICIPIO DE LIMEIRA / Limeira-SP
- publication date axis: `dataPublicacaoPncp`
- `dataInicial=20251128`
- `dataFinal=20260904`
- `tamanhoPagina=50`

Owner-relayed official JSON produced complete pagination for:

- modality 6 — Pregão Eletrônico: 181/181, 4/4 pages;
- modality 8 — Dispensa: 434/434, 9/9 pages;
- modality 12 — Credenciamento: 5/5, 1/1 page.

No explicit EITI wording was observed in those three complete exact scopes. This is **not** a global PNCP negative conclusion.

Modality 9 — Inexigibilidade remains non-exhaustive. Indexed/documentary discovery surfaced an education-relevant school-pass lead, but the stable PNCP purchase identifier has not yet been recovered, so it cannot be promoted beyond discovery status.

## New fail-closed guards

1. **Entity identity guard** — platform/domain similarity is insufficient. CNPJ/municipality/UF must match. A search result presented as “PCA 2026 - Educação” was opened and proved to be Itupeva, not Limeira; it is rejected as `ENTITY_IDENTITY_MISMATCH`.
2. **Pagination guard** — an exhaustive conclusion requires every page plus total page/record metadata in the exact query scope.
3. **Indexed discovery guard** — search snippets can generate leads, never exhaustive negatives.
4. **Transport guard** — URL-safety, DNS, cache, proxy, HTTP or tool failures are `SOURCE_TRANSPORT_UNAVAILABLE`, never source `NO_MATCH`.
5. **Evidence ladder** — `EDUCATION_RELEVANT != EITI_PROVEN`.
6. **Stable ID guard** — correlated promotion requires stable administrative identifiers.
7. **Anomaly preservation** — malformed or suspicious source values remain raw and receive anomaly flags; silent repair is forbidden.

## Evidence ladder

`GENERAL → EDUCATION_RELEVANT → EITI_CANDIDATE → EITI_CORROBORATED → EITI_PROVEN`

School transport, school meals, school management systems, literary-contest student prizes and school passes can prove educational relevance. They do not prove EITI without explicit extended-day/full-time linkage.

## Boundary

This task records sanitized evidence and guards only. It creates no EITI financial identity, transaction identity, supplier identity or global PNCP no-match.

Next research action: recover the stable PNCP ID for the 2026 school-pass Inexigibilidade, finish modality 9 exhaustively when transport is available, then continue modalities 15, 4, 7, 5 and 14.
