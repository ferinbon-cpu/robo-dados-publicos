# External Review Adjudication Protocol

Status: **governance protocol**  
Project: `robo-dados-publicos`  
Applies from: `0.8.0` candidate onward

## Purpose

This protocol defines how findings from an external reviewer, model, agent, auditor, or human reviewer are evaluated before they become project requirements.

The goal is to preserve the value of adversarial review without allowing a reviewer to silently redefine authorization, provenance, execution scope, or promotion rules after the fact.

## Roles and authority

The project separates four roles:

1. **Owner** — grants or withholds execution authorization and is the authority for owner intent.
2. **Architect/adjudicator** — maps the owner's authorization to the repository's existing contracts, evaluates reviewer findings, and determines whether a finding is a blocker, hardening opportunity, or rejected requirement.
3. **Executor** — implements the bounded change or run exactly within the materialized contract.
4. **External reviewer** — performs adversarial review and may identify defects, missing evidence, unsafe assumptions, or useful hardening opportunities.

An external reviewer is intentionally independent, but is **not** an independent source of owner authorization and does not automatically have veto power over a change.

## Authority hierarchy

When sources disagree, use the following order:

1. explicit current owner authorization;
2. repository governance and already-materialized task/run contract;
3. executable gates, tests, and pinned evidence;
4. architectural conventions established by merged history;
5. external reviewer recommendation.

A lower-ranked source may reveal that a higher-ranked source has been implemented incorrectly, but it may not rewrite the higher-ranked source retroactively.

## Review finding classes

Every material reviewer finding should be adjudicated into one of these classes.

| Class | Meaning | Required treatment |
|---|---|---|
| `BLOCKER_REQUIREMENT_VIOLATION` | Existing requirement, authorization boundary, invariant, or gate is violated | Stop; fix before merge or execution |
| `BLOCKER_EVIDENCE_GAP` | A claim cannot be supported by the available evidence | Stop the claim; obtain evidence or narrow the claim |
| `HARDENING_RISK` | Real technical risk is not yet an explicit requirement | Prefer implementing a proportional fail-closed guard/test; not automatically retroactive |
| `ARCHITECTURAL_IMPROVEMENT` | Useful maintainability, reuse, observability, or auditability improvement | Adopt when proportional and separately reviewable |
| `NEW_GOVERNANCE_PROPOSAL` | Reviewer proposes a new authorization, provenance, approval, signature, issue, or process rule | Evaluate prospectively; never treat as a retroactive blocker solely because the reviewer proposed it |
| `ALREADY_COVERED` | Existing code, gate, test, or evidence already addresses the concern | Record/reply with the covering control; no new requirement |
| `REJECTED_UNSUPPORTED_REQUIREMENT` | Proposed requirement conflicts with or is unsupported by current governance | Reject explicitly; do not fabricate evidence to satisfy it |

## Non-retroactivity rule

A reviewer must not create a new historical fact.

Therefore the project must not:

- create a post-hoc issue and describe it as prior authorization;
- add a signature after execution and claim it existed before execution;
- reinterpret a broad or unrelated owner instruction as authorization for an already-completed effect;
- backfill an approval timestamp, reviewer identity, or evidence chain that did not exist;
- promote a reviewer preference into a pre-existing mandatory requirement without a prospective governance change.

If a new governance rule is valuable, it may be adopted **for future gates** with an explicit effective point.

## Evidence-first adjudication

Reviewer findings about executed behavior should be tested against the strongest available evidence, preferably:

- exact commit/head SHA;
- task or execution contract committed before the effect;
- workflow source at execution time;
- immutable or pinned evidence payloads;
- reproducible hashes;
- independent offline verifiers;
- CI results and regression tests;
- explicit counters for prohibited effects.

When evidence disproves a reviewer concern, classify it as `ALREADY_COVERED` or `REJECTED_UNSUPPORTED_REQUIREMENT` rather than adding redundant process.

When evidence is insufficient, the correct response is to reduce the claim or fail closed, not to invent missing evidence.

## Authorization adjudication

External review may test whether an execution exceeded its authorized scope, but external review cannot itself authorize or de-authorize an already-defined owner instruction.

For one-shot bounded operations, the preferred chain is:

`owner authorization -> pre-run materialized contract -> bounded execution -> pinned evidence -> authorization consumed`

A reviewer may block the chain if it demonstrates that one of these links is missing, inconsistent, or violated.

A reviewer may recommend a stronger future chain, such as an additional approval artifact, but that recommendation becomes binding only after the project adopts it prospectively.

## Security and fail-closed rule

Security-relevant reviewer findings receive conservative treatment.

If the reviewer identifies a plausible path to:

- exceed a network request budget;
- contact a non-allowlisted origin;
- perform an unauthorized write;
- retry automatically when retry is not authorized;
- publish, promote, or assert an identity without sufficient evidence;
- bypass a pinned head or expected SHA;

then the preferred resolution is an executable fail-closed guard plus a regression test, not merely explanatory prose.

## Reviewer independence

Reviewers should be encouraged to disagree with the implementation. A healthy result may include rejected findings.

The project must avoid both failure modes:

- **rubber-stamp review** — accepting the implementation without serious challenge;
- **reviewer capture** — accepting every reviewer demand even when it invents requirements or conflicts with established governance.

The target is evidence-based adjudication.

## Required adjudication record for disputed findings

When a reviewer maintains a material blocker after implementation changes, record at least:

- the reviewer finding;
- the applicable existing requirement or absence of one;
- the relevant evidence/control;
- the classification from this protocol;
- the decision: `ACCEPT`, `HARDEN`, `DEFER_PROSPECTIVELY`, or `REJECT`;
- whether the decision changes any future gate.

The record may live in the PR description, review thread, task evidence, or a dedicated governance artifact as appropriate.

## Example: new signature requirement after a bounded run

If a reviewer argues after execution that the owner should have signed an issue before the run:

- if the repository already required that signature before execution and it is absent, classify as `BLOCKER_REQUIREMENT_VIOLATION`;
- if no such requirement existed and the actual owner authorization plus pre-run contract are preserved, classify the demand as `NEW_GOVERNANCE_PROPOSAL`;
- do not manufacture a retroactive signature;
- evaluate whether to require such a signature for future gates.

## Merge rule

This protocol does not weaken existing CI, branch, expected-head, authorization, or evidence requirements.

A reviewer finding marked `BLOCKER_*` remains blocking until resolved or formally reclassified with evidence. A reviewer finding does not become a blocker merely because it is strongly worded or repeated.

## Design principle

**Use adversarial review to discover defects and convert real risks into executable invariants; never convert reviewer preference into fictional provenance.**
