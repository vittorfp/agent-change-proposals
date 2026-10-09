# RFC 0003: CI-Ready Validation Fields

Status: Draft  
Schema version target: `0.6`  
Discussion: https://github.com/vittorfp/agent-change-proposals/discussions/6  
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

## Backward Compatibility

For v0.6, these fields should be additive:

- existing v0.1 proposals remain valid;
- `validation.gate` is optional;
- stricter validation applies only when `validation.gate` is present;
- examples should show the expected shape before the schema requires it.

The next implementation step is to add schema validation for `validation.gate`
without making it globally required.

## Open Questions

- Should `mode` allow `advisory`, `blocking`, and `manual_review_required`?
- Should metric operators be limited to `>`, `>=`, `<`, `<=`, `==`, and `!=`?
- Should `immutable_ref` require a URI/digest format or remain a non-empty
  string?
- Should rollback triggers live in both `validation.gate` and `rollback`, or
  should `rollback` reference the gate trigger?
- Should CI decide on all metrics or only metrics marked `required: true`?
