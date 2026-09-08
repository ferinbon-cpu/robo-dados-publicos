# TASK 206 — offline observatory answer CLI and representative QA

## Objective

Make the 38 deterministic TASK205 human-answer cards directly executable from the repository without enabling serving or publication.

The CLI is intentionally narrow:

- `--question-id <ID>` — render one canonical question to stdout;
- `--all` — render all 38 questions to stdout, separated by Markdown rules;
- `--list-questions` — list the canonical IDs, domains and question texts.

No arbitrary prompt, path or URL is accepted.

## Deterministic runtime

The first CLI version pins:

- `generated_at = 2026-09-08T02:05:00+00:00`
- `software_version = 0.8.0`

This keeps card and Markdown hashes reproducible for identical repository state.

## Representative QA

QA is executed over the current product bundle and the real renderer output. It does not use rewritten answer fixtures.

Required cases:

- `ACC_Q1` — accounting stages;
- `FIN_Q3` — revenue/FUNDEB/transfers;
- `PLAN_Q1` — planning vs execution;
- `NORMS_Q1` — norm vs implementation;
- `TEACH_Q2` — workforce stock and bond categories;
- `EQUITY_Q1` — equity and territorial missingness.

## Presentation repairs discovered by QA

### TEACH_Q2

The prior renderer showed the indicator value but could hide the descriptive context containing the four bond counts. TASK 206 makes the validated indicator context visible.

The answer can therefore expose:

- 1,280 unique municipal docentes in the 2025 Census scope;
- 681 concursado/efetivo/estável;
- 291 temporário;
- 0 terceirizado;
- 400 CLT;

while retaining the non-additivity caveat and the rule that personnel event flow is not workforce stock.

### EQUITY_Q1

The prior renderer exposed territorial records but not the validated missingness boundary used by the V4 answerability gate.

TASK 206 adds an explicit validated coverage fact:

- 64 of 69 active schools have strong school-to-sector links;
- 5 remain HELD;
- full-network territorial coverage remains false.

No held school is promoted by this task.

## Usage

```bash
python scripts/render_observatory_answer_offline.py --list-questions
python scripts/render_observatory_answer_offline.py --question-id ACC_Q1
python scripts/render_observatory_answer_offline.py --all
```

## Guards

The CLI and QA preserve all TASK205 boundaries:

- formatting allowed, inference forbidden;
- no LLM;
- no numeric invention;
- no causal-effect creation;
- revenue != expenditure;
- restos payable != current-year expenditure;
- planning != execution;
- norm != implementation;
- personnel event flow != workforce stock;
- territorial missingness remains explicit;
- stdout only;
- no Drive/network/serving/publication/schedule/recurrence.
