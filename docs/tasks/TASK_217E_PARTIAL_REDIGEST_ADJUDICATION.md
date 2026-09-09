# TASK 217E — partial redigest adjudication and school-context guard

The authorized TASK 217D run completed fail-closed. It targeted 87 official Jornal editions and produced a sanitized artifact, but 12 editions remained uncovered. The final workflow failure is therefore expected and correct: INFRA_Q2 asks **which schools** received works, reforms or equipment, so incomplete coverage cannot support an exhaustive answer.

The run still produced useful positive evidence. Seven infrastructure events matched an exact school alias under the original TASK 217A rule. Deterministic contextual adjudication shows that six were homonyms rather than school events:

- Major José Levy Sobrinho referred to the Limeirão stadium;
- Dr. José Carvalho Ferreira referred to a street address.

One event is genuine school infrastructure: Jornal edition 7208, page 42, published 25 March 2026, contract 42/2026, process 22.687/2024, for maintenance of the water reservoir at **CEIEF Prof. Arlindo de Salvo**, with published value R$ 71,000.00.

The identity bridge is therefore hardened: an exact alias now requires a nearby school/unit anchor such as CEIEF, EMEIEF, EMEI, EMEF, escola or unidade escolar. A bare person/place alias cannot create school identity. This is stricter deterministic disambiguation, not fuzzy matching.

The TASK 217D artifact preserved only the exception class for the 12 failures, not each specific stop code. No individual cause is inferred. Recovery must target the exact 12 uncovered edition identities under a new bounded authorization.

INFRA_Q2 remains 33/38 until that recovery closes the content scope.
