# TASK 060 — Drive 10_INBOX metadata-only pilot

## Objective
Run the Drive Ingestion Controller v2 against the canonical `10_INBOX` tree using **metadata only**.

This task proves folder discovery and routing behavior on real existing custody without opening source content or writing to Drive/Bronze/Silver/Gold.

## Authorized scope
Owner message: `Prossiga`.

Interpreted narrowly as authorization for the already-described TASK 060 metadata-only pilot. The canonical folder was selected from the persistent product roadmap, where `10_INBOX` is the official manual batch entry point.

Root:
- `10_INBOX` — `16lvKYsbW96JLoLbRGuTUohjyzndrR9r8`

Discovered descendants:
- `PENDENTES` — `1ofFcveMY7kzYsYujo5hfSM-iv6pzzcMY`
- `DUPLICATAS` — `1WnbSqyjKvdRRVhFoMaCEapAKvC5Xk2dy`
- `PENDENTES/F01_PPA_LDO_LOA_2026` — `1CdL4T1CVIPqNph3f5xHbiU8KgxgPpkl5`

## Boundary
Drive searches used explicit metadata-only item types and `best_effort_fetch=false`.

Forbidden in this task:
- source-content fetch/read;
- OCR;
- public-source network collection;
- Drive write;
- Bronze/Silver/Gold write or promotion;
- serving/publication changes.

GitHub evidence/test commits are allowed because they do not mutate source custody.

## Observed inventory
No documents were directly present in `10_INBOX`, `PENDENTES`, or `DUPLICATAS`.

Nine documents were discovered in `PENDENTES/F01_PPA_LDO_LOA_2026`:
1. `SOURCE_JOM_7127_2025-11-29_LOA_7223_2025.pdf`
2. `SOURCE_JOM_7119_2025-11-15_PPA_7213_2025.pdf`
3. `SOURCE_JOM_7024_2025-07-08_LDO_7141_2025.pdf`
4. `MANIFEST_F01_PPA_LDO_LOA_2026_V03`
5. `SOURCE_LOA_2026_LEI_7223_2025_LIMEIRA.pdf`
6. `SOURCE_LDO_2026_LEI_7141_2025_LIMEIRA.pdf`
7. `MANIFEST_F01_PPA_LDO_LOA_2026_V02`
8. `SOURCE_PPA_2026_2029_LEI_7213_2025_LIMEIRA.pdf`
9. `MANIFEST_F01_PPA_LDO_LOA_2026_V01`

## Routing result
Using `config/drive_ingestion_controller.v2.json`:

- `AUTO_INGEST = 0`
- `REVIEW = 9`
- `QUARANTINE = 0`

This is an expected result, not a failed pilot.

The three `SOURCE_JOM_*` documents match both `JORNAL_OFICIAL` and one planning family, therefore fail closed to `REVIEW` with `MULTIPLE_FAMILY_MATCHES`.

The three manifests contain PPA/LDO/LOA simultaneously and also route to `REVIEW` with `MULTIPLE_FAMILY_MATCHES`.

The standalone PPA, LDO and LOA source files match one family each, but those families are explicitly `REVIEW`-first in controller v2 until the appropriate source-specific schema/adapter is selected.

## Interpretation
TASK 060 proves the real Drive hierarchy can be traversed and classified without reading file content. It also confirms why the maturity-aware v2 catalog was necessary: a naive `AUTO_INGEST` policy would incorrectly treat mixed Jornal/planning artifacts as a single unambiguous family.

EITI played no role in determining the ingestion scope or routing. It remains an analytic use case, not the global controller filter.

## Next gate
`TASK_061_DRIVE_INGESTION_EXECUTION_POLICY_DESIGN` should define durable folder/family authorization rules for progressing from routing into bounded content/hash ingestion. Its purpose is to avoid returning to permanent file-by-file authorization while preserving fail-closed behavior for unknown families, mixed-family artifacts and schema drift.

TASK 060 itself authorizes no content read for TASK 061.

## Result
`PASS_TASK060_10_INBOX_METADATA_ONLY_PILOT_9_REVIEW_0_AUTO_0_QUARANTINE_NO_CONTENT_READ`
