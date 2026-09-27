# TASK 219AB — TDA Contracts JSON extraction provenance

## Purpose

Strengthen TASK 219AA with a machine-readable official export of `LAI - Contratos - Detalhe` obtained by the operator from the Limeira TDA portal.

## Acquisition-route correction

The JSON did **not** come from the black cloud icon. It was obtained from the **three-bars extraction menu** of the Contracts detail area and then the JSON option inside the extraction panel.

This correction matters because the earlier manual exploration temporarily conflated two controls. The canonical record must preserve the actual provenance rather than infer the acquisition path from screenshots.

## Artifact policy

The uploaded ZIP and inner JSON remain outside Git. The repository stores only:

- SHA-256 and byte counts;
- observed text encoding;
- export metadata and filters;
- row-shape semantics;
- bounded structured fields needed for the proof.

No cookie, anti-forgery value, hidden control value, page source or session token is persisted.

## Bounded proof

The export reports `Status=OK`, `Usuario=Convidado`, `Ano Contrato=2026` and `Nro Contrato=45`. `Valores` contains two rows: one totalization row and one actual data row. The totalization row is not a second contract.

The actual data row proves, in machine-readable TDA output:

- Nro SIAM `0000000045` under the exact contract filter 45/2026;
- Med Doctor Acessorios Ltda, CNPJ 37.457.979/0001-31;
- 13/04/2026 to 12/04/2027;
- R$ 210,000.00 contracted;
- R$ 174,999.99 committed;
- R$ 35,000.00 processed;
- R$ 35,000.00 paid;
- object `LOCACAO DE SISTEMA DE ENDOSCOPIA`;
- `Pregao Eletronico (E00010/2026)`;
- administrative-process display `902281`.

The typed municipal procurement identifier `E00010/2026` is the strong machine-readable bridge already used by TASK 219AA to the official Empenhado export. Supplier, amount and object remain consistency checks, not primary identity edges.

## Scientific boundaries

This task does not claim that:

- the totalization row is another contract;
- `902281` by itself proves the formatted legal process `902.281/2025`;
- contract value equals committed/processed/paid value;
- R$ 35,000 paid means contract completion;
- one contract is an exhaustive procurement inventory.

No live portal request is performed by this task.
