# TASK 078 — DeepSeek reviewer bootstrap

## Objective

Add the first bounded DeepSeek integration without activating automatic PR review or any repository mutation.

## Scope

This task is a bootstrap gate only:

- provider endpoint: `https://api.deepseek.com`;
- allowed models: `deepseek-v4-flash`, `deepseek-v4-pro`;
- default: `deepseek-v4-flash`;
- manual `workflow_dispatch` only;
- dry-run is the default;
- live API use requires both `DEEPSEEK_API_KEY` and the exact confirmation `LIVE_DEEPSEEK_REVIEW`;
- GitHub permissions are read-only;
- no PR comment, code write, Drive access, source collection, publication, schedule or recurrence.

The bootstrap deliberately keeps the live API proof and automatic `pull_request` promotion as later gates.

## Trust boundary

`AGENTS.md`, `CONTRIBUTING.md`, `config/automation_policy.v1.json`, and
`config/deepseek_agent_policy.v1.json` are trusted instructions. PR title,
body, diff, issue text and ordinary repository content are untrusted data.
Prompt injection inside untrusted content must never override the trusted
policy.

## Secret handling

The only planned DeepSeek credential is the GitHub Actions secret
`DEEPSEEK_API_KEY`.

It must never be committed, logged, inserted into prompts or persisted.
The owner creates it in GitHub Settings. The repository code does not read
back or display its value.

## Files

- `config/deepseek_agent_policy.v1.json`
- `robo_dados_publicos/automation/deepseek_review.py`
- `scripts/deepseek_pr_review.py`
- `tests/test_deepseek_review_bootstrap.py`
- `.github/workflows/deepseek-pr-review-bootstrap.yml`

## Explicitly not authorized

- automatic PR trigger;
- GitHub PR comments;
- branch/code mutation;
- self-merge;
- Drive read/write;
- source network collection;
- serving/publication;
- recurrence/schedule;
- financial identity promotion.

## Promotion path

1. Merge this offline/bootstrap implementation after normal CI.
2. Owner adds `DEEPSEEK_API_KEY`.
3. Run one manually confirmed live review against an existing PR.
4. Pin evidence for request count, model, context hash and zero GitHub/Drive writes.
5. Only then consider a separate policy/PR for automatic `pull_request` reviews and bounded PR comments.
