# TASK 080 — DeepSeek automatic PR review

## Objective

Promote the proven DeepSeek bootstrap into an automatic reviewer that runs after the repository's normal PR CI completes and posts one bounded review to the PR conversation.

## Trigger and trust boundary

- trigger: `workflow_run` after `CI offline 0.8.0 candidate M7` completes for a pull request;
- the privileged reviewer workflow is loaded from the default branch;
- only same-repository PR heads are eligible;
- fork or foreign heads are blocked;
- exact PR head SHA must match the completed upstream CI head;
- the workflow checks out only the trusted default branch;
- pull-request code is never checked out or executed by the DeepSeek worker;
- no `pull_request_target`, direct secret-bearing `pull_request` workflow, schedule or recurrence.

## Authorized effects

- read PR metadata and diff;
- read existing PR comments for same-head deduplication;
- make one DeepSeek API request per new eligible PR head;
- post one conversation comment containing the validated review;
- write Actions job-summary telemetry.

## Still blocked

- code or branch writes;
- direct `main` writes;
- merge or self-merge;
- Drive read/write;
- live source collection;
- serving or publication;
- overwrite/replace/delete;
- financial-identity promotion;
- MDE/FUNDEB compliance conclusions;
- schedule/recurrence.

## Cost control

The reviewer uses `deepseek-v4-flash` by default. A marker bound to the exact head SHA avoids a second DeepSeek request when the same CI/head is rerun and an automatic review comment already exists.

## Validation

Only four focused tests are added for this promotion: policy boundaries, trusted workflow shape, same-repository/exact-head enforcement, and head-bound comment rendering. The repository's existing CI remains authoritative; no extra manual DeepSeek test is required before merge.
