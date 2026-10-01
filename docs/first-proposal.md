# First Proposal Walkthrough

This walkthrough shows the smallest useful workflow in the project:

```text
observed run + outcome signal + improvement surface
  -> change proposal
  -> controlled replay comparison
```

## 1. Observed Run

The example run lives at:

```text
examples/rag-missed-retrieval/traces.json
```

The user asks a policy-dependent question:

```text
According to the refund policy, what should we do for a late cancellation?
```

The trace contains an LLM span, but no retrieval span.

## 2. Outcome Signal

The outcome lives at:

```text
examples/rag-missed-retrieval/outcomes.json
```

Human review marks the run as a failure with dimensions:

```text
groundedness, policy_compliance
```

This is important: the proposal is not inferred from telemetry alone. It needs
an outcome signal that says the observed behavior mattered.

## 3. Improvement Surface

The improvement surface lives at:

```text
examples/rag-missed-retrieval/improvement_surface.json
```

It declares the only target this example allows the tool to propose changing:

```text
retrieval_policy.main
```

The project deliberately avoids a universal agent manifest in V0. It only needs
to know which knobs are reviewable.

## 4. Generate A Proposal

```bash
acp proposal from-trace \
  examples/rag-missed-retrieval/traces.json \
  --outcomes examples/rag-missed-retrieval/outcomes.json \
  --surface examples/rag-missed-retrieval/improvement_surface.json \
  --output /tmp/change_proposal.json
```

The generated proposal says:

- what behavior was observed;
- which outcome signal made it important;
- which improvement surface is affected;
- what hypothesis might explain the behavior;
- what change should be reviewed;
- how to validate the change;
- what risk and rollback path exist.

The key sentence is in the hypothesis limits:

```text
This is a hypothesis from trace structure and outcome labels, not a causal proof.
```

## 5. Compare Replay Results

```bash
acp replay compare \
  examples/rag-missed-retrieval/replay_baseline.json \
  examples/rag-missed-retrieval/replay_candidate.json \
  --output /tmp/replay_report.json
```

The replay report is intentionally simple. It does not claim production
determinism. It compares controlled cases and produces a reviewable verdict:

```text
accept, reject, or neutral
```

## What This Proves

- The project can generate a structured improvement proposal from concrete
  artifacts.
- The proposal is reviewable, testable, and scoped to an allowed change target.
- The workflow can be run locally and tested automatically.

## What This Does Not Prove

- It does not prove the hypothesis is causally correct.
- It does not guarantee the candidate will improve production behavior.
- It does not replace observability tools or eval platforms.
- It does not automate deployment.

