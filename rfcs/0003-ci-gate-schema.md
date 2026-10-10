# RFC 0003: CI-Ready Validation Fields

Status: Draft
Schema version target: `0.6`
Discussion: https://github.com/vittorfp/agent-change-proposals/discussions/9
Related issue: https://github.com/vittorfp/agent-change-proposals/issues/3

## Summary

ACP should make `change_proposal` usable in CI without turning the artifact into
an opaque machine contract. The proposed v0.6 direction is:

- put immutable references on evidence items;
- put CI gate policy under `validation.gate`;
- keep top-level proposal fields human-readable and stable.

This RFC is a design proposal, not an implemented schema change.

## Motivation

The first direct external feedback said the artifact is useful for eval review
and incident follow-up, but should not be trusted as a CI gate until validation
is machine-readable. The requested fields were:

- immutable evidence refs;
- baseline and candidate artifact IDs;
- evaluator and dataset versions;
- metric threshold;
- sample count;
- rollback trigger.

Those fields matter, but making all of them top-level required fields would
overfit one workflow and make non-CI proposals noisy. CI gating should be
structured when present, but optional until the project sees repeated adoption
signals.

## Proposed Shape

### Evidence References

Evidence items should carry stable identifiers that CI and reviewers can cite.

```json
{
  "type": "evaluation_result",
  "evidence_ref": "evidence:eval:retrieval-required:v1",
  "immutable_ref": "sha256:3ef3b4c7...",
  "artifact_id": "eval-result-2026-10-09T101500Z",
  "description": "Controlled replay result for retrieval-required cases."
}
```

`evidence_ref` is a proposal-local identifier. `immutable_ref` is the stable
content reference, digest, or artifact URI. `artifact_id` is the tool/platform
identifier when one exists.

### Validation Gate

CI policy should live under `validation.gate` because it is validation-specific
and can be omitted for human-only review.

```json
{
  "validation": {
    "method": "controlled_replay",
    "acceptance_criteria": [
      "Candidate improves groundedness without increasing escalation failures."
    ],
    "gate": {
      "mode": "blocking",
      "baseline_artifact_id": "replay-baseline-2026-10-09",
      "candidate_artifact_id": "replay-candidate-2026-10-09",
      "dataset": {
        "id": "refund-policy-replay-set",
        "version": "2026-10-09",
        "sample_count": 48,
        "scope": "policy-sensitive support questions"
      },
      "evaluator": {
        "id": "groundedness-and-policy-check",
        "version": "0.3.1"
      },
      "metrics": [
        {
          "name": "groundedness_pass_rate",
          "operator": ">=",
          "threshold": 0.92,
          "baseline_value": 0.71,
          "candidate_value": 0.94,
          "sample_count": 48,
          "required": true
        }
      ],
      "required_evidence_refs": [
        "evidence:eval:retrieval-required:v1"
      ],
      "rollback_trigger": {
        "metric": "retrieval_latency_p95_ms",
        "operator": ">",
        "threshold": 1800,
        "window": "24h"
      }
    }
  }
}
```

## Why Not A Top-Level `gate` Object?

A top-level `gate` object would make CI feel like a peer to the proposal itself.
That is tempting, but it creates a second decision surface next to
`validation`, `risk`, and `rollback`.

Keeping gate fields under `validation` makes the relationship clearer:

```text
validation describes how to test the change
validation.gate describes when that test is strong enough to block or pass CI
```

## Why Not Only Typed Evidence?

Typed evidence is still useful, but it should not own gate policy. Evidence
answers "what artifact supports this proposal?" The validation gate answers
"what rule decides whether this proposal can proceed?"

Separating them lets one evidence item support multiple gate rules and lets
reviewers inspect supporting artifacts without reading CI policy first.

## Alternative: `validation.checks`

A second direct feedback item proposed `validation.checks` instead of one
`validation.gate` object:

```json
{
  "validation": {
    "method": "controlled_replay",
    "acceptance_criteria": [
      "Candidate run includes at least one retrieval span for this case."
    ],
    "checks": [
      {
        "criterion": 0,
        "suite": "rag_missed_retrieval",
        "metric": "retrieval_called",
        "op": "==",
        "value": true,
        "min_cases": 1
      }
    ]
  }
}
```

This shape has two advantages over the current `validation.gate` draft:

- each machine check can point at the human-readable criterion it verifies;
- criteria without checks remain explicitly human-reviewed instead of being
  hidden inside one aggregate gate.

This may be a better fit if proposals commonly have several acceptance
criteria, only some of which are CI-checkable. Before implementing v0.6, compare
`validation.gate.metrics[*]` with `validation.checks[*]` and decide whether
`gate` should become a wrapper around checks or disappear entirely.

If ACP adopts `validation.checks`, it should decide whether each check points to
one criterion or many. A strict 1:1 shape is simple, but a single machine check
can support several criteria. For example, a row-count-preservation check might
support both "no dropped cases" and "candidate/baseline comparison stayed
well-formed." A possible shape is:

```json
{
  "criteria": [0, 2],
  "suite": "replay_integrity",
  "metric": "row_count_delta",
  "op": "==",
  "value": 0
}
```

That flexibility makes duplicate checks less likely, but makes failure
reporting slightly less direct than a single `criterion` field.

A follow-up suggested that stable criterion IDs are better than array indexes
once criteria become structured. Index references are easy to prototype, but
they become brittle when criteria are reordered. Stable refs also create a
clear CI failure mode: a misspelled or deleted criterion reference can be
rejected outright instead of silently orphaning a check. A later schema could
look like:

```json
{
  "validation": {
    "acceptance_criteria": [
      {
        "id": "retrieval-required",
        "description": "Candidate run includes at least one retrieval span for this case."
      },
      {
        "id": "no-regression",
        "description": "Candidate/baseline comparison stays well-formed with no dropped cases."
      }
    ],
    "checks": [
      {
        "criterion_refs": ["retrieval-required", "no-regression"],
        "suite": "replay_integrity",
        "metric": "row_count_delta",
        "op": "==",
        "value": 0
      }
    ]
  }
}
```

The same feedback also raised approval integrity: `status: accepted` is not
enough if the proposal can be edited after review. A future schema should
consider approval metadata tied to a canonical proposal digest, so edits after
approval invalidate the prior acceptance.

### Reddit Feedback: Counterfactuals, Frozen Sets, And Verdict Diffs

Reddit feedback from agent and eval practitioners added more pressure toward a
checks-based shape. The clearest repeated theme was that a proposal should not
only show that the failing trace improved. It should also show cases where the
fix must not apply.

That suggests `validation.checks` may need to support check roles or case roles,
for example:

```json
{
  "validation": {
    "method": "controlled_replay",
    "acceptance_criteria": [
      "Candidate retrieves policy context for refund-policy questions.",
      "Candidate does not retrieve policy context for simple greeting turns.",
      "Candidate introduces no pass-to-fail verdict flips on tagged guardrail cases."
    ],
    "checks": [
      {
        "criteria": [0],
        "role": "positive",
        "suite": "refund_policy_required",
        "metric": "retrieval_called",
        "op": "==",
        "value": true,
        "trace_set_ref": "sha256:positive-traces..."
      },
      {
        "criteria": [1],
        "role": "negative",
        "suite": "retrieval_not_required",
        "metric": "retrieval_called",
        "op": "==",
        "value": false,
        "trace_set_ref": "sha256:negative-traces..."
      },
      {
        "criteria": [2],
        "role": "verdict_diff",
        "suite": "guardrail_regression_set",
        "metric": "pass_to_fail_flips",
        "op": "==",
        "value": 0,
        "trace_set_ref": "sha256:guardrail-traces..."
      }
    ]
  }
}
```

Other feedback argued that reviewers should read verdict flips, not only
aggregate scores. A future schema could represent a compact old/new comparison:

```json
{
  "verdict_diff": {
    "baseline_artifact_id": "replay-baseline-2026-10-09",
    "candidate_artifact_id": "replay-candidate-2026-10-09",
    "pass_to_fail": 0,
    "fail_to_pass": 7,
    "unchanged_pass": 39,
    "unchanged_fail": 2,
    "unknown": 0
  }
}
```

This feedback also introduced two concepts not covered by the original
`validation.gate` shape:

- `unknown` or `insufficient_evidence` should be a valid outcome when the
  baseline is too thin to support a decision;
- LLM-judge checks may need calibration metadata, such as the size of the human
  verdict set and agreement rate, before reviewers trust the judge.

These are not implementation decisions yet, but they make `validation.checks`
look more extensible than a single gate object.

## Backward Compatibility

For v0.6, these fields should be additive:

- existing v0.1 proposals remain valid;
- `validation.gate` is optional;
- stricter validation applies only when `validation.gate` is present;
- examples should show the expected shape before the schema requires it.

The next implementation step is to exercise `validation.checks` in examples and
CLI validation before deciding whether `validation.gate` should remain as a
wrapper. The first implementation pass should keep these fields optional, reject
dangling `criterion_refs`, and preserve compatibility with string-only
`acceptance_criteria`.

## Open Questions

- Should `mode` allow `advisory`, `blocking`, and `manual_review_required`?
- Should metric operators be limited to `>`, `>=`, `<`, `<=`, `==`, and `!=`?
- Should `immutable_ref` require a URI/digest format or remain a non-empty
  string?
- Should rollback triggers live in both `validation.gate` and `rollback`, or
  should `rollback` reference the gate trigger?
- Should CI decide on all metrics or only metrics marked `required: true`?
- Should checks reference acceptance criteria by stable criterion ID, and
  should dangling check refs fail validation?
- Should one check be allowed to reference multiple acceptance criteria?
- Should accepted proposals include approval metadata with a canonical proposal
  digest?
- Should validation checks have roles such as `positive`, `negative`,
  `counterfactual`, `canary`, or `verdict_diff`?
- Should the schema require at least one negative/counterfactual case for
  behavior changes that could over-apply?
- Should CI approval be based on verdict flips over a frozen trace set instead
  of aggregate score thresholds?
- Should LLM-judge checks include human-verdict calibration metadata?
- Should validation outcomes include `unknown` or `insufficient_evidence`?
