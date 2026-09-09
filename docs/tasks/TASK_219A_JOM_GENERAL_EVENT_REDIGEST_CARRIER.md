# TASK 219A — bounded general-event redigest of the 87 additional JOM editions

TASK 219A expands the 2026 Jornal Oficial corpus from the existing 12-edition / 303-event general index to the 87 additional editions already proven by TASK 217C/217/218.

This task does **not** join procurement records and cannot promote any question. Its purpose is to materialize the missing general event layer required before another strong JOM↔PNCP↔TCE identity attempt is scientifically justified.

## Network boundary

The carrier reconstructs the exact TASK 217C discovery and requires the canonical result hash to match. It then excludes editions 7304–7315 and downloads exactly the remaining 87 documents.

Maximum remote work:

- 18 index GETs;
- 87 PDF GET attempts;
- 105 remote GETs total;
- no retry;
- 250 MiB per document;
- 4 GiB aggregate.

The 4 GiB cap is evidence-based. The overlap-inclusive sum of document bytes accounted by TASK 217D, 217F and 217G is 1,865,479,856 bytes. Because overlap is intentionally not removed, that number is a conservative prior upper bound.

## Derived output

For each successfully processed edition, JournalPdfProcessor runs in temporary storage with:

- Bronze persistence disabled;
- reconciliation planning disabled;
- processor semantic/accounting emission disabled; semantic classification is derived after event parsing.

Only these derived products may leave temporary storage:

- redacted events_gold rows;
- compact semantic classification rows;
- deterministic strong administrative anchors.

No PDF, page text, RAG chunk, accounting query task or raw source payload may be persisted in the workflow artifact.

## Strong identity semantics

Strong anchors reuse TASK 216 rules. Only complete administrative identifiers from allowed procurement-shaped events can anchor:

- complete process number; or
- complete contract number.

CNPJ alone, amount, date, object text and semantic similarity are explicitly forbidden as identity inputs.

A strong JOM anchor is **not** an end-to-end procurement identity chain. PNCP/TCE joining, if justified by the new corpus, is a later separately governed task.

The runtime is inert on main and requires a fresh authorization pinned to the final merged implementation SHA.
