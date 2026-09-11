# TASK 224 — September 2025 Education trial balance

## Purpose

Materialize a bounded exact-source accounting view from `Balancete_Mes_Setembro_2025_Educacao.pdf`, linked to MD_01.3 `DOC-066` and logical identifier `BALANCETE-EDUC-2025-09`.

The source is a Prefeitura Municipal de Limeira / CN-SIFPM / CONAM report titled `BALANCETE SINTETICO DA DESPESA LIQUIDADA POR ELEMENTO`, covering órgão inicial 15.00.00 Secretaria de Educação through órgão final 15.06.00 Fundo Manut. Desenvol. Educação Básica, month 09/2025.

## What is materialized

The config stores currency in integer BRL cents and records source page for each group.

Directly printed total general values:

- liquidated in September: R$ 38,701,916.33;
- liquidated YTD: R$ 316,726,439.62;
- committed YTD: R$ 350,956,929.20;
- to liquidate: R$ 34,230,489.58;
- appropriation: R$ 519,885,923.78;
- balance: R$ 168,928,994.58.

The same six-stage structure is stored for:

- personnel and social charges;
- other current expenses;
- total current expenses;
- investments;
- debt amortization;
- total capital expenses.

Ten selected directly printed economic elements are also stored, including temporary hiring, fixed personnel compensation, intra-budget employer obligations, material consumption, third-party legal-entity services, ICT services, food allowance, transport allowance, construction/installations and permanent equipment.

This is intentionally **not** a claim of a complete row-level ledger parse.

## Diagnostic accounting checks

Tests verify, without creating new source values:

- liquidated YTD + to liquidate = committed YTD;
- committed YTD + balance = appropriation;
- current expenses + capital expenses = general budget expense across all six columns.

These checks close exactly on the source cents for all stored aggregate groups and selected elements.

## Semantic boundaries

This is a partial position at September 2025, not annual closing.

`appropriation` and `balance` do not mean free cash or freely available resource. A balance can be linked to future obligations, earmarks, contracts, sources or later-period execution.

The document distinguishes committed and liquidated stages; it does not provide a paid-stage total in the materialized schema. The robot must not silently infer paid values from it.

The Education-wide total is not EITI-specific and cannot be attributed to integral-time education without an explicit accounting bridge.

The source can support questions about this trial balance and its element structure, but it does not replace RREO/SIOPE/TCE semantics when a question specifically asks for those official reporting concepts.

## Source precedence

The exact source is authoritative for what is printed in this balancete. MD_01.2 and prior technical notes remain derived aids and cannot override a directly verified balancete value.

Byte-level identity between the File Library copy and the historical MD_01.3 source is not claimed because no source binary hash is available in this task; title and document-content identity are observed.

## Non-effects

No new public-source request, Drive write, serving mutation, publication, schedule or recurrence. Canonical contextual coverage remains 38/38; this task adds accounting depth.
