# TASK 201A2 — SME-only workforce discovery

TASK 201A live run 34164368084 stopped fail-closed after the fixed INEP Sinopse URL returned URLError on all three authorized attempts. No mirror or extra retry is introduced here.

TASK 201A2 therefore:
- does not retry INEP;
- reads only fixed official SME pages;
- aggregates the current contracted-teacher page with private identifiers used ephemerally for deduplication and discarded;
- confirms current operational bond labels EFETIVO and CLT_PROCESSO_SELETIVO;
- discovers only same-host, query-stripped internal SME paths related to attribution, effective teachers, docentes, classes, turmas or HR.

The goal is to find the authoritative SME surface for effective-teacher counts without blind endpoint guessing.

No STAFF_COUNT or EMPLOYMENT_BOND is materialized in this discovery step. No Drive write, serving, publication, schedule or recurrence occurs.
