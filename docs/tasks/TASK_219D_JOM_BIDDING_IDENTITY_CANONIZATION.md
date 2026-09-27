# TASK 219D — JOM bidding identity canonization

Issue: #691

TASK 219D creates a second exact administrative bridge from the complete 99-edition 2026 JOM corpus.

## Identity

The exact identity key is:

`PNCP modality id + numeric bidding number + bidding year`

Only already-proven modality mappings are admitted:

- Pregão Eletrônico → 6
- Dispensa → 8
- Inexigibilidade → 9

The JOM bidding number must be complete in `number/year` form. Generic Pregão, Concorrência, Chamamento Público and other unresolved labels are excluded rather than guessed.

Supplier CNPJ, publication date, amount, object text and semantic similarity are not identity fields.

## Canonical result

Across the legacy 12-edition corpus and the 87 additional editions:

- 274 anchor occurrences;
- 143 unique exact bidding identities;
- 126 Pregão Eletrônico identities;
- 13 Dispensa identities;
- 4 Inexigibilidade identities.

The new 87-edition corpus contributes 130 unique identities, 122 of which are new relative to the legacy corpus.

Forty-nine exact bidding identities have at least one JOM event typed as EDITAL. These collapse to only 35 unique `modality + JOM publication date` search seeds.

The date is explicitly **search scope only**. A future PNCP record is accepted only if its modality, numeric `numeroCompra` and `anoCompra` exactly equal the JOM bidding identity.

## Why this matters

The bulk PNCP contracts endpoint produced two fail-closed transport stops in TASK 219C/219C2 before any payload bytes were received. TASK 219D does not reinterpret those failures as PNCP absence. It changes the next discovery strategy from broad contract enumeration to small daily procurement-publication lookups against exact JOM EDITAL seeds.

No PNCP request is executed here. No TCE network, Drive write, serving, publication or question promotion occurs. Coverage remains 34/38.
