# TASK 201A — privacy-safe workforce live probe

## Goal

Discover the exact primary-source shape needed to close TEACH_Q2 without exploiting the historical ANY metric gate.

## Fixed primary sources

- INEP 2025 Sinopse Estatística: municipality/dependency aggregate search for docentes.
- SME Limeira current homepage: operational evidence for effective and CLT process-selection categories.
- SME Limeira current "Professores Contratados em Classe": privacy-safe aggregate of current contracted-teacher assignments and unique registrations.

## Privacy boundary

The SME contracted page publicly exposes person-level fields. TASK 201A may read those values only ephemerally in runner memory to deduplicate. No name, CPF, registration value, pseudonym or person-level hash may be persisted, logged, committed, uploaded to Drive, served or published.

Only aggregate counts, category labels, dates, structural QA and source hashes may leave the temporary process.

## Semantics

- assignment rows are not unique people;
- school-level docente sums are not a unique network headcount;
- 2025 INEP annual data are not silently merged into a 2026 SME current snapshot;
- CLT/contracted is not assumed to exhaust all non-effective relationships;
- this probe does not materialize STAFF_COUNT or EMPLOYMENT_BOND.

A later TASK 201B may materialize only fields whose exact semantics are proven by this sanitized discovery.

## Remote effects

The live step performs bounded GETs to the fixed official sources only. It has no Drive write, serving, publication, schedule or recurrence.
