# TASK 217D — bounded school-infrastructure JOM redigest carrier

TASK 217D prepares the content-reading step after the canonical TASK 217C discovery.

The carrier first reconstructs the official nine-month discovery and requires the exact canonical discovery hash before downloading any Jornal PDF. It then excludes the 12 already-materialized editions 7304–7315 and targets exactly 87 new editions.

The 87 documents are grouped into eight monthly partitions: January through July and September through 8 September. August is excluded because all 12 discovered August editions are already represented by the current 303-event JOM fixture.

PDFs are temporary only. The mature JournalPdfProcessor performs pypdf extraction, privacy redaction and Gold event parsing with Bronze persistence disabled. Raw PDF bytes and page text are never uploaded as workflow artifacts.

The sanitized result contains only:
- per-document processing summaries;
- bounded redacted page candidates where infrastructure and a school/generic-school reference co-occur;
- exact-school structured infrastructure events;
- generic unassigned structured infrastructure events.

Page screening is discovery support, not identity. Positive school identity still requires the exact TASK 217A event bridge.

A document that requires OCR or otherwise fails is recorded as a failure; processing may continue for the other documents, but the final runtime is partial and the workflow fails only after uploading the sanitized partial artifact. Partial scope never permits absence inference.

This PR does not authorize the live run. The workflow is inert on main and requires a separate owner authorization pinned to the exact merged implementation SHA.
