# TASK 031 — Use the Jornal Oficial originals as the primary F01 source

## Why this task exists
TASK 030 correctly proved where the PPA, LDO and LOA were published, but its next step still assumed that a full equivalence audit against the standalone Prefeitura PDFs should precede extraction. The owner clarified the simpler and preferable architecture: the full Jornal Oficial edition itself is an original official publication source and should be used directly.

## Decision
For F01, the unmodified full Jornal Oficial edition PDF is the **primary source for extraction**. The standalone Prefeitura PDF is retained as an **official complementary copy** for validation, recovery and provenance.

Full-content or byte equivalence between the Jornal edition and the standalone copy is **not a prerequisite** for beginning extraction from the Jornal. If the two official representations diverge materially, the pipeline stops for review; it must never silently combine or correct them.

## Exact source editions
- LDO 2026 — Lei 7.141/2025 — Jornal Oficial edition 7024, 08/07/2025 — `https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_07072025191855.pdf` — 79 pages; law begins at journal page 5.
- PPA 2026–2029 — Lei 7.213/2025 — edition 7119, 15/11/2025 — `https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_14112025171148.pdf` — 107 pages; law begins at page 5.
- LOA 2026 — Lei 7.223/2025 — edition 7127, 29/11/2025 — `https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_28112025211140.pdf` — 631 pages; law begins at page 15.

Public indexing demonstrates that the three editions expose searchable textual representation, including the LDO law text and LOA tables. Search-engine text is discovery evidence only and is explicitly forbidden as the extraction source.

## Custody before parsing
The next live step must acquire exactly those three full edition PDFs and place them create-only under `10_INBOX/PENDENTES/F01_PPA_LDO_LOA_2026`, with deterministic filename, page count, byte count, SHA-256 and readback. Only after that custody proof may the parser use the Jornal originals.

## Extraction strategy
1. Read the full, unmodified Jornal edition.
2. Identify the target law by law number, law date and title/ementa.
3. Treat known page starts and section boundaries as navigation hints, not identity proof.
4. Prefer the Jornal text layer.
5. Use OCR only for individual Jornal pages that lack sufficient text.
6. Use the standalone Prefeitura copy for validation or recovery, never as a silent substitute.

## Safety boundary
This TASK is T0/offline only. It authorizes no source GET, no Drive create/write, no Bronze/Silver/Gold, no serving and no publication.

The next task must implement a bounded acquisition gate for exactly editions 7024, 7119 and 7127. After implementation review and merge, the first live GET/Drive create-only execution requires a fresh owner authorization pinned to that exact implementation SHA.
