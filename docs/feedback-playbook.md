# Feedback Playbook

The next milestone is not more detectors. It is learning whether
`change_proposal` is a useful artifact for people who operate AI agents.

## Who To Ask

Prioritize people who already have traces, evals, incidents, or behavior-change
review workflows.

- Engineers using Phoenix, OpenInference, Langfuse, LangSmith, Braintrust, or
  custom eval pipelines.
- Platform teams running multiple internal agents.
- Developers who review prompt, tool, retrieval, or guardrail changes in PRs.
- People responsible for auditability, safety, or production reliability of
  agent behavior.

Avoid broad "AI product idea" feedback at this stage. The useful feedback is
workflow feedback from people close to agent operations.

## What To Send

Use this short version for direct messages:

```text
I am testing an open-source idea: evidence-backed improvement proposals for AI
agents.

Existing observability/eval tools show what happened. This tries to describe
what should change, why, and how to validate it.

The artifact I want feedback on is this example proposal:
https://github.com/vittorfp/agent-change-proposals/blob/main/examples/rag-missed-retrieval/change_proposal.example.json

Would something like this be useful in your agent review/eval workflow, or is
it solving the wrong problem?
```

Use this version for community posts:

```text
I am exploring a small open-source artifact for AI agent improvement workflows:
an evidence-backed `change_proposal`.

It is not a tracing standard or observability backend. The idea is to sit after
tools like OpenTelemetry/OpenInference/Phoenix/Langfuse/LangSmith and produce a
reviewable proposal: what behavior was observed, what outcome signal made it
important, what change is suggested, what evidence supports it, and how to
validate/rollback it.

Repo: https://github.com/vittorfp/agent-change-proposals
Discussion: https://github.com/vittorfp/agent-change-proposals/discussions/6

I would love practical feedback: would this artifact fit your PR/CI/eval
workflow? What fields are missing or too speculative?
```

## Questions To Ask

Ask concrete workflow questions, not broad opinion questions.

1. After you find a problematic agent run, how does it become a behavior change?
2. Where do you record the evidence and rationale for that change?
3. Would a `change_proposal` artifact fit PR review, CI, eval review, or none
   of those?
4. Which fields in the current proposal are useful?
5. Which fields are missing, confusing, or too speculative?
6. What would make the proposal trustworthy enough to review?
7. Which existing tool already solves this for you?
8. What should ACP integrate with first?

## How To Classify Feedback

Record feedback in [feedback-log.md](feedback-log.md) using these categories:

- **artifact-fit:** whether `change_proposal` belongs in their workflow.
- **schema-gap:** missing/confusing fields.
- **trust-gap:** evidence, confidence, risk, validation, or rollback concerns.
- **integration-gap:** import/export/tooling needed before adoption.
- **not-needed:** existing tool or process already covers the need.

## Decision Rules

Do not change the core schema after a single comment unless it exposes a clear
bug or ambiguity.

Consider changing the schema when at least two independent reviewers point to
the same gap, or when one reviewer provides a concrete workflow that the current
schema cannot represent.

Prefer adding examples or docs before adding schema fields.

