# RFC 0001: Change Proposal Artifact

Status: Draft  
Schema version: `0.1`  
Discussion: https://github.com/vittorfp/agent-change-proposals/discussions/6

## Summary

The `change_proposal` artifact describes a proposed AI agent behavior change
with evidence, uncertainty, validation criteria, risk, and rollback notes.

It is meant to be reviewed by humans. It is not a command to automatically
patch or deploy an agent.

## Motivation

Observability and eval tools can show that an agent behaved poorly or produced
an expensive, unsafe, slow, or incorrect result. The next step is often less
structured: someone reads traces, forms a hypothesis, edits prompts/configs, and
tries to remember why the change was justified.

ACP proposes a portable artifact for that step:

```text
observed behavior + outcome signal + allowed change target
  -> reviewable improvement proposal
```

## Current Shape

The current public schema lives at:

```text
schemas/change_proposal.schema.json
```

The current examples live under:

```text
examples/*/change_proposal.example.json
```

Required top-level fields:

- `schema_version`
- `proposal_id`
- `title`
- `status`
- `problem`
- `evidence`
- `hypothesis`
- `proposed_change`
- `validation`
- `risk`
- `rollback`

## Field Intent

### `problem`

Describes the observed gap. It should point to the relevant run, outcome label,
and short problem summary.

Open question: should `run_id` be required by schema, or should ACP support
aggregate proposals spanning many runs?

### `evidence`

Contains evidence items such as outcome events, trace patterns, eval results, or
replay references.

Open question: should evidence items have stricter typed variants, or stay loose
until more real workflows are observed?

### `hypothesis`

States the suspected explanation and explicitly describes limits. This is a
hypothesis, not causal proof.

Open question: should confidence be a controlled enum, numeric score, or
free-form field tied to each evidence item?

### `proposed_change`

Describes the target and suggested change. The target should come from an
`improvement_surface`, not from arbitrary model output.

Open question: should suggested patches become structured per target type
(`prompt`, `tool_policy`, `retrieval_policy`, `guardrail_threshold`), or remain
flexible in V0?

### `validation`

Describes how to test the proposal before acceptance. V0 uses simple method and
acceptance criteria fields.

Open question: should acceptance criteria become structured objects with metric,
operator, threshold, and scope?

### `risk`

Describes expected risk of the change. This should help a reviewer decide
whether a proposal is safe to test.

Open question: should risk require a controlled level and explicit affected
dimensions such as quality, safety, latency, cost, or compliance?

### `rollback`

Describes how to undo or reject the change.

Open question: should rollback be a textual plan, a reference to a config diff,
or a structured operation?

## Non-Goals

This artifact should not:

- encode full agent architecture;
- replace tracing semantic conventions;
- prove causality from telemetry alone;
- authorize automatic deployment;
- require a hosted backend;
- require a specific agent framework.

## Feedback Needed

The most useful feedback is concrete:

- Would this artifact fit PR review, CI, eval review, or incident review?
- Which required fields are unnecessary?
- Which missing fields would block adoption?
- Which fields are too vague to trust?
- What should be stricter now, and what should stay flexible until more real
  examples exist?

