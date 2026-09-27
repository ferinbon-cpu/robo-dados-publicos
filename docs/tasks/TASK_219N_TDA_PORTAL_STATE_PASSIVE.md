# TASK 219N — passive vSDT_TDAPORTAL state capture

Issue: #717  
Parent: #691

## Result

TASK 219N read the already-loaded public GeneXus portal state through the exact read-only getter previously proved by TASK 219M:

`gx.fn.getControlValue("vSDT_TDAPORTAL")`

The session performed one normal public navigation and no interaction.

## Boundary

Exactly one browser session and one initial navigation.

Zero:
- clicks;
- typing;
- form submissions;
- manual XHR/fetch;
- direct endpoint calls;
- LayerInfo replay;
- PortalAction trigger;
- Empenho lookup;
- retries.

Raw portal state, HAR, cookies and tokens were not persisted.

## GeneXus state successfully materialized

The browser exposed:

`gx.fn.getControlValue` → available

and:

`vSDT_TDAPORTAL` → decoded object

The loaded public state contains:

- 1 layer;
- 8 areas.

The layer is:

`LAI - Acesso Rápido(WhatsApp)`

## Complete loaded area map

1. **Exercício**
   - AreaId ends in `DSA5`
   - AreaOrigin ends in `VIS1342`

2. **Receita**
   - AreaId ends in `DSA3`
   - AreaOrigin ends in `VIS1341`

3. **Despesa**
   - AreaId: `0e1483cd46954696a3e9b01c5be19e23DSA6`
   - AreaDivId: same as AreaId
   - AreaOrigin: `2_92_guestuser_207_6_DSL0_VIS1343`
   - AreaType: `content`
   - AreaFormat: `HTML Template`
   - AreaAgg: `HTMLTemplate`
   - AreaOriginalType / AreaShowingType: `17_1_0`

4. **WhatsApp**
   - AreaId ends in `DSA8`
   - AreaOrigin ends in `VIS1346`

5. **Resumo**
   - AreaId ends in `DSA1`
   - AreaOrigin ends in `VIS1345`

6. **Estatística de Acessos**
   - AreaId ends in `DSA7`
   - AreaOrigin ends in `VIS1344`
   - Column2D / SingleSerie

7. **Acesso Rápido**
   - AreaId ends in `DSA2`
   - AreaOrigin ends in `VIS1340`
   - show-filter button enabled

8. technical filter area
   - AreaId `DASH_WITHOUT_FILTER_AREA`
   - AreaType `filter`

## Despesa identity is now proven

Under the predeclared fail-closed rule, an area could be promoted only if its already-loaded public state explicitly named an accounting domain.

Exactly one area satisfies that rule:

**AreaName = Despesa**

Therefore the canonical identity is:

**TDA DESPESA AREA = PROVEN**

Exact target:

`AreaId = 0e1483cd46954696a3e9b01c5be19e23DSA6`

`AreaOrigin = 2_92_guestuser_207_6_DSL0_VIS1343`

This conclusion does not depend on ordinal, payload size, similarity or generic table shape.

## What remains unproven

TASK 219N did not open or trigger the Despesa area.

It does not yet prove:
- the official action/request contract for opening or refreshing that exact area;
- a direct query contract;
- any lookup of Empenho 3286-2026;
- Contract 45/2026 ↔ Empenho 3286-2026 identity;
- payment attribution.

Coverage remains **34/38**.

## Provenance

Run: `34415945900`  
Execution head: `e3de7b683e74f8b4e122075dde3fb09ccf1a8cc7`  
Artifact: `10129069763`

Artifact ZIP SHA-256:

`0f649aa154560f5a1560ccd7d30c5100ff156a30baf51c052525c2c64b502b1a`

Artifact member SHA-256:

`8af43bbcb6efb0cfaf9d00b719e5265210d80da94701497144f527478612a207`

Executed workflow blob equals preserved historical source:

`c9b510662ca3d23d15c49dba61a2dd5f658a0f39`

Live workflow removed after execution:

`52e65904cc8b23f4a720992ca5c782cfc79f7432`

## Next safe leap

Use the exact Despesa target plus the already-mined client source to identify the official portal action generated for this area.

A separately authorized run may perform one exact official interaction while passively capturing the action name/parameter and resulting network contract.

Do not query Empenho 3286-2026 until that action/request contract is proved.
