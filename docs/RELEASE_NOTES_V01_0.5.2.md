# SOFTWARE V01 0.5.2 CANDIDATE — M4E.2 Jornal Oficial/Limeira

## Status
CANDIDATE. Active production release remains 0.4.0 until live validation.

## Added
- `journal.official` deterministic parser/discovery layer;
- support for modern index entries and legacy archive-labelled PDFs;
- Portuguese date parsing and canonical edition/source identifiers;
- overlap dedupe by edition, preferring an actually declared PDF route;
- disabled source-inventory generation for discovered editions;
- robots-aware HTML discovery client;
- `journal-discover` CLI command;
- Jornal Oficial runbook and evidence notes;
- Jornal Oficial added to the Limeira Tier-A discovery registry.

## Safety/quality rules
- no PDF URL guessing;
- no synthetic eCrie filenames;
- no CAPTCHA bypass;
- no production download until route/content-type is validated live;
- legacy/modern migration overlap is preserved and deduped rather than assumed away;
- Bronze remains immutable; personal-data minimization belongs to derived layers.

## Next gate
Run one live `journal-discover` from Cloud Shell/GitHub, validate at least one current PDF route/content-type, then enable bounded incremental collection.
