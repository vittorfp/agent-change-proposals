# Feedback Request

I am exploring an open format for evidence-backed improvement proposals for AI
agents.

Existing observability and eval tools are good at showing what happened. This
project tries to describe what should change, why, and how to validate it.

## The Question

Would this artifact be useful in your agent, eval, or observability workflow?

Public discussion:

https://github.com/vittorfp/agent-change-proposals/discussions/6

## What To Review

- [README](../README.md): project positioning and quickstart.
- [First proposal walkthrough](first-proposal.md): the smallest end-to-end
  workflow.
- [Not an observability platform](not-an-observability-platform.md): project
  boundaries and ecosystem fit.
- [Change proposal schema](../schemas/change_proposal.schema.json): the core
  artifact.
- [Examples](../examples): missed retrieval, tool misuse, and missing
  escalation.

## Feedback I Am Looking For

- Does the `change_proposal` artifact belong in your review or CI workflow?
- Which fields are missing, confusing, or too speculative?
- What would make a proposal trustworthy enough to review?
- Which existing tool should this integrate with first?
- What part feels like unnecessary schema or ceremony?

## Short Post

I am exploring an open format for evidence-backed improvement proposals for AI
agents.

Existing observability and eval tools show what happened. This project tries to
describe what should change, why, and how to validate it, without becoming a
new tracing standard or agent runtime.

The first version is intentionally small: observed run + outcome signal +
allowed improvement surface -> reviewable `change_proposal`.

Repo: https://github.com/vittorfp/agent-change-proposals

I would love feedback from people running agent evals, observability pipelines,
or internal agent platforms: would this artifact help you review behavior
changes, or is it solving the wrong problem?
