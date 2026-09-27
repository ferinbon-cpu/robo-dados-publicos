# TASK 217 — JOM structured school identity bridge

## 217A: current-corpus identity audit

TASK 217A installs a deterministic school-identity layer for Jornal Oficial events without changing the evidentiary threshold of INFRA_Q2.

The identity roster is the current 69-unit municipal roster already verified by TASK 199E. The 12 schools held in TASK 199E are held only for school-to-census-sector geography; their official school/INEP identity is still proven and may be used here.

Accepted identity is limited to an exact, unambiguous normalized alias of an official school name found in `object_text` or `excerpt_redacted`. Prefix removal and removal of honorific suffixes are deterministic alias generation, not fuzzy matching. Edit distance, semantic similarity, address-only inference and generic network language are forbidden as identity.

Infrastructure markers are a separate relevance gate. They may classify an event as a works/equipment candidate but can never create a school identity.

## Current 303-row result

The canonical JOM corpus currently spans 14–29 August 2026 and contains 303 validated events.

The deterministic audit finds:

- 69 current municipal schools;
- 224 unique accepted aliases;
- 0 ambiguous aliases;
- 14 infrastructure-shaped events;
- 0 exact named-school events;
- 0 exact named-school infrastructure events;
- 1 generic school infrastructure event.

The generic event is `JOEV_84b4ca10af2609ca127a`, edition 7311, 25 August 2026, page 3: acquisition of playground equipment for “unidades escolares da rede municipal”. It is relevant evidence at network level but does not identify recipient schools and therefore cannot answer “quais escolas”.

INFRA_Q2 remains blocked and contextual coverage remains 33/38. This is a scoped zero-match result over the current 303-row corpus, not a claim that no school work, reform or equipment event exists elsewhere in 2026.

## 217B boundary

The next step is a bounded 2026 JOM discovery/redigest using the already mature official index/parser and PDF processor. Live execution is not authorized by 217A. The consumed TASK 018 authorization must not be silently reused. Any new live run requires its own exact scope/authorization and must fail closed on incomplete monthly discovery or document-processing failure.
