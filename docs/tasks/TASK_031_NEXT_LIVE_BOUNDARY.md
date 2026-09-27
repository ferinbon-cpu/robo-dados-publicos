# TASK 031 — next live boundary

No live acquisition is authorized by TASK 031.

The next implementation must be a bounded source-acquisition gate for exactly Jornal Oficial editions 7024, 7119 and 7127. It may be designed to:

- perform at most three source GETs, one exact pinned URL per edition;
- require `Content-Type: application/pdf` and a valid `%PDF-` signature;
- verify the expected edition identity and total page count before any Drive mutation;
- compute byte count and SHA-256 for each complete edition;
- preflight all three target filenames before the first write;
- create exactly three files under `10_INBOX/PENDENTES/F01_PPA_LDO_LOA_2026` using create-only semantics;
- read back all three created files and verify bytes/hash/page count;
- stop before Bronze/Silver/Gold/parser execution.

No retry, pagination expansion, alternate URL guessing, overwrite, replace, delete, cleanup, OCR, extraction, publication, schedule or recurrence should be authorized in the first acquisition proof.

After that implementation is reviewed and merged, a fresh owner authorization pinned to the exact implementation SHA is required before the first live source GET or Drive write.
