# TASK 217F — bounded recovery of the 12 uncovered JOM editions

TASK 217F is a narrow continuation of the fail-closed TASK 217D result.

It does not rediscover the Jornal Oficial. The 12 target edition/date/URL identities were already canonized by TASK 217E from the official TASK 217C discovery. The carrier therefore performs at most 12 document GETs.

The previous per-document ceiling was 50 MiB and the large 87-document batch also accumulated more than one GiB in its accounting. TASK 217F does not assign a specific cause to any individual failure because TASK 217D did not preserve the stop code. Instead it uses a fresh bounded envelope: up to 85 MiB per target, with 12 × 85 MiB plus the adapter's one-byte guards still below the one-GiB aggregate ceiling.

Each failure now records both exception class and exact stop code in the sanitized result.

The hardened TASK 217E school identity rule is used: exact names require nearby school/unit context. Street and stadium homonyms cannot become schools.

The runtime is inert on main and requires a separate owner authorization pinned to its final merged implementation SHA. It writes no Drive data and cannot promote INFRA_Q2. A complete successful recovery must still be canonized before answerability changes.
