# TASK 217G — four oversized Jornal editions recovery carrier

TASK 217G targets only editions 7243, 7253, 7270 and 7287, the four documents proven by TASK 217F to exceed the 85 MiB ceiling.

There is no rediscovery and no retry. The live boundary is at most four GETs. Each document may be at most 250 MiB; four documents at that ceiling still remain below the one-GiB aggregate budget.

Processing reuses JournalPdfProcessor plus the hardened school identity and infrastructure semantics from TASK 217E/F2. Raw PDFs remain temporary and only the sanitized result may be uploaded.

The runtime is inert on main. It requires a separate owner authorization pinned to the exact final merged implementation SHA. Even a successful runtime cannot promote INFRA_Q2 by itself; canonization is mandatory.
