# TASK 071 — first live Jornal batch to Bronze

## Authorization
Owner granted 7 additional bounded task tokens after TASK 070. This task consumes token 1/7 and uses the active revocable authorization `AUTH_10_INBOX_JORNAL_OFICIAL_V1`.

## Exact scope
Only three TASK 060 records made ELIGIBLE by TASK 069/070:
- edition 7127 — source `1bRpmMxacX16P1tJBvam-55OOPTYuQnIA`;
- edition 7119 — source `1ez1B_mJ428IxTIUht1AHM9-I5SCotKXj`;
- edition 7024 — source `1U_E1I1Lbrq5WvedrDPygFuEfQj-ouOex`.

Source batch folder: `1CdL4T1CVIPqNph3f5xHbiU8KgxgPpkl5` under canonical `10_INBOX`.
Bronze target: canonical `01_BRONZE`, id `18yR-e6I1VCiy7XqG7Zhr0vUIJF0qA_MG`.

## Execution
Each source PDF was downloaded as raw bytes. SHA-256 was computed without semantic parsing. Canonical Bronze-name searches found no existing editions 7127, 7119 or 7024. Because title/size are not duplicate proof, no duplicate claim was made from metadata alone.

Three create-only Drive uploads were made using the existing Jornal Bronze naming convention:
- `limeira_jornal_oficial_edicao_7127.pdf` → `1PXnqz8iMmU1O1Rm2Qu4PgpfCU0qhu_QS`;
- `limeira_jornal_oficial_edicao_7119.pdf` → `1uOeraxmRTKHFNmolG7RN7esUPLod0aqB`;
- `limeira_jornal_oficial_edicao_7024.pdf` → `1JTpCPj4_rL08RubO5wOVvBHjuwqKWfQ8`.

Every new Bronze object was downloaded again. Readback byte count and SHA-256 are identical to the source:
- 7127: `37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4`, 66,119,594 bytes;
- 7119: `cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a`, 16,867,824 bytes;
- 7024: `44d92a6ac948bbf43dcb3302733faac1a4ed5e592702f66c07f0c6ede4ecb73c`, 17,615,179 bytes.

## Boundaries
No OCR, semantic parsing, Silver, Gold, RAG, serving, publication, source move/delete or Bronze overwrite occurred.

## Result
`PASS_TASK071_LIVE_JOURNAL_BRONZE_3_CREATED_3_READBACK_VERIFIED`

## Next gate
TASK 072 may test native-text processability of these exact three immutable Bronze objects with the existing Jornal parser. It must not persist Silver/Gold merely because Bronze creation passed.
