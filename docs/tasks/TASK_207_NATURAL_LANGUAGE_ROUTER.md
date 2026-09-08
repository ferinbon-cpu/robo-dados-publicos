# TASK 207 — offline natural-language router

## Objective

Allow a person to ask the municipal observatory a bounded question in ordinary Portuguese without knowing canonical IDs such as `FIN_Q1` or `TEACH_Q2`.

The route is:

`user text -> deterministic lexical router -> confidence/ambiguity gate -> canonical question ID(s) -> TASK206/TASK205 renderer`

Text selects the question. Text never becomes numeric truth.

## V1 method

V1 is deliberately simple and auditable:

- Unicode NFKD normalization;
- diacritic removal;
- case folding;
- non-alphanumeric normalization;
- exact canonical-question self-routing;
- versioned weighted phrases;
- versioned individual terms;
- versioned negative markers;
- deterministic score, margin and confidence.

No embeddings, network calls or LLM are required.

## Route states

### ROUTED

A single question is selected only when the score and margin gates are met.

A compound query may select at most two canonical questions when:

- an explicit compound marker is present;
- both candidates independently pass the compound minimum score;
- both have a matched weighted phrase.

### AMBIGUOUS

The router does not choose when two candidates have meaningful but insufficiently separated scores.

Example:

`como estão os professores`

This can refer to teacher quality or to workforce/bonds, so V1 returns ambiguity rather than silently choosing `TEACH_Q1` or `TEACH_Q2`.

### LOW_CONFIDENCE_STOP

Text without enough ontology signal receives no canonical question.

Example:

`me conta alguma coisa`

## Representative routes

- `quanto Limeira gastou com educação` -> `FIN_Q1`
- `quanto foi empenhado liquidado e pago` -> `ACC_Q1`
- `quanto se gasta por aluno` -> `FIN_Q2`
- `quanto veio do Fundeb e de transferências` -> `FIN_Q3`
- `tem restos a pagar` -> `ACC_Q3`
- `quantos professores efetivos temporários e CLT` -> `TEACH_Q2`
- `como está a formação e o esforço dos professores` -> `TEACH_Q1`
- `como está o AEE` -> `EQUITY_Q2`
- `desigualdade por raça renda e território` -> `EQUITY_Q1`
- `quais normas mudaram calendário e matrícula` -> `NORMS_Q2`
- `o que saiu no Jornal Oficial` -> `JOM_Q1`
- `quais fontes estão desatualizadas ou bloqueadas` -> `CTRL_Q1`

Compound:

`quanto gastou com educação e quanto veio do Fundeb`
-> `FIN_Q1 + FIN_Q3`

## CLI

```bash
python scripts/ask_observatory_offline.py --ask "quanto Limeira gastou com educação"
python scripts/ask_observatory_offline.py --ask "como estão os professores" --route-only
```

A routed question invokes the existing deterministic renderer. Ambiguous and low-confidence text returns non-zero without rendering an answer.

## Guards

- text route != truth source;
- routing score != evidence;
- ambiguity remains visible;
- low confidence stops;
- routed IDs must be in the current canonical 38;
- no numeric fact is created by the router;
- no causal or administrative identity is created by the router;
- no LLM/embedding/network is required;
- no serving/publication/schedule/recurrence.
