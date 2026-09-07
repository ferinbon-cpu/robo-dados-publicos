# TASK 195 — SIOPE official Receita/Despesas handoff audit

## Goal

Use direct official FNDE/SIOPE Olinda JSON returned for Limeira 2025/P6 to strengthen the operational alias bridge without weakening fail-closed rules.

This task is intentionally **partial**. It records what is now proved and preserves the remaining blocker for `VL_DESP_DOTA_ATUA_EDU`.

## Provenance

The owner opened exact FNDE/SIOPE Olinda URLs in a normal browser and pasted the official JSON response into the project conversation.

Classification:

`USER_MEDIATED_DIRECT_OFFICIAL_URL_RESPONSE_PASTED`

The pasted response is authoritative evidence of the observed fields and values, but it is **not** treated as a byte-identical raw endpoint capture. No raw endpoint SHA-256 is invented.

Sanitized derived evidence JSONs were persisted in Drive under `01_BRONZE/SIOPE` and are pinned by Drive ID, byte size and SHA-256 of those derived files.

## Receita_Siope findings

Exact Limeira identity was observed:

- `TIPO=Municipal`
- `NUM_ANO=2025`
- `NUM_PERI=6`
- `SIG_UF=SP`
- `COD_MUNI=352690`
- `NOM_MUNI=Limeira`

Official labels observed directly:

- `PA = Previsão Atualizada`
- `RR = Receitas Realizadas`
- `DF = Deduções FUNDEB`
- `IO = IntraOrçamentaria`
- `OD = Outras Deduções`

Two existing aliases reconcile exactly:

- Receitas Correntes PA `2,198,860,107.12`
- Receitas de Capital PA `43,133,736.15`
- total `2,241,993,843.27`
- existing `VAL_RECE_PREV_ATUA = 2,241,993,843.27`
- variance `0.00`

and:

- Receitas Correntes RR `2,087,296,383.01`
- Receitas de Capital RR `39,799,480.18`
- total `2,127,095,863.19`
- existing `VAL_RECE_REAL = 2,127,095,863.19`
- variance `0.00`

Therefore both are now backed by exact operational label/value reconciliation.

## Despesas_Siope findings

Official labels observed directly:

- `DE = Desp. Empenhadas`
- `DL = Desp. Liquidadas`
- `DP = Desp. Pagas`

The FUNDEB/VAAR row gives:

- receita realizada VAAR: `885,554.43`
- despesa empenhada VAAR: `885,554.43`
- despesa liquidada VAAR: `885,554.43`
- despesa paga VAAR: `885,554.43`

This is exact equality observed across the two official resources. It is operational evidence, not a license to infer broader causality or accounting identities.

## Education-transfer research value

The Receita response also exposes source-defined rows for:

- Salário-Educação;
- PNAE;
- PNATE;
- FUNDEB;
- VAAR;
- Fundeb resources for creation of ETI enrollments;
- state transfers for education programs.

Of particular research interest, the 2025/P6 response shows `R$ 1,033,952.81` in realized revenue for Fundeb resources destined to creation of ETI enrollments.

These rows are **not yet promoted into new canonical products** in TASK 195. They are preserved for a dedicated scoped materialization task.

## OData transport lesson

The canonical robot `Dados_Gerais_Siope` client already emits `%20` in the municipal OData filter, so no client patch is needed.

During the manual auxiliary-resource handoff, `+` as encoded whitespace produced OData parser errors. Receita succeeded with `%20`; Despesas succeeded with `%09` token whitespace in the manually clicked URL.

This finding is preserved as handoff/transport evidence, not generalized beyond what was observed.

## What remains UNKNOWN

TASK 195 does **not** close:

- `S1_NUM_POPU`;
- `VL_DESP_DOTA_ATUA_EDU`;
- `S2_FINANCIAL_ALIAS_BRIDGE`;
- annual closure/finality.

The current Despesas subset contains DE/DL/DP rows but no source-defined `DA` row set establishing the education-scope dotação atualizada inclusion rule.

## Next bounded probe

Query `Despesas_Siope` for the exact Limeira 2025/P6 identity with:

`IDN_CLAS = DA`

Then enumerate the returned folders/items and test whether a source-defined education aggregate exactly corresponds to `VL_DESP_DOTA_ATUA_EDU`.

No sum of convenient-looking rows may be promoted unless the source structure itself proves the inclusion rule.

## Guards

- no invented raw endpoint hash;
- derived Drive JSON is not raw endpoint capture;
- missing DA is not zero;
- EDU is not silently equated to MDE;
- exact equality is not causal identity;
- no Gold or closed-series promotion in this partial task.
