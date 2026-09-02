# TASK 030 — Budget laws ↔ Jornal Oficial publication map

## Objective
Promote the newly verified publication identities for Limeira's PPA 2026–2029, LDO 2026 and LOA 2026 into a versioned, fail-closed mapping contract without claiming unproven full-content equivalence.

## Verified publication identities

- **PPA — Lei 7.213/2025**, dated 12/11/2025 → Jornal Oficial de Limeira **edition 7119**, dated 15/11/2025. The law starts at journal page 5/107. Administration starts at page 77, so the Gabinete block ends at page 76. The exact PPA annex end remains unverified.
- **LDO — Lei 7.141/2025**, dated 02/07/2025 → Jornal Oficial de Limeira **edition 7024**, dated 08/07/2025. The law starts at page 5/79. Page 42 already contains Portaria 1.669/2025, so the LDO occupies pages 5–41 inclusive, exactly 37 pages, matching the standalone copy's page count. Byte identity is not claimed.
- **LOA — Lei 7.223/2025**, dated 28/11/2025 → Jornal Oficial de Limeira **edition 7127**, dated 29/11/2025. The law starts at page 15/631. The standalone canonical copy has 466 pages, yielding candidate journal end page 480 by arithmetic only. Administration starts at page 485. Full page-by-page equivalence remains pending.

## Architectural decision
The Jornal Oficial is the **primary legal-publication source**. Standalone Prefeitura PDFs remain canonical official copies/representations. The journal may serve as an official textual extraction and validation bridge when its text layer is available, but it does not replace the canonical PDF without equivalence proof.

## Fail-closed rules
- Same law number does not prove full annex equivalence.
- Matching page count does not prove byte/content equivalence.
- Section boundaries do not prove exact document end.
- LOA page 480 is a candidate end, not a verified end.
- Divergence triggers REVIEW/STOP; no silent correction.
- No Silver, Gold, serving or publication promotion is authorized by this task.

## Next step
Build a deterministic sample-based equivalence audit, prioritizing LOA because the journal offers searchable textual content that may avoid a full 466-page OCR run.
