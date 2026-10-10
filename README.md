# Agent Change Proposals

[![tests](https://github.com/vittorfp/agent-change-proposals/actions/workflows/test.yml/badge.svg)](https://github.com/vittorfp/agent-change-proposals/actions/workflows/test.yml)
[![release](https://img.shields.io/github/v/release/vittorfp/agent-change-proposals)](https://github.com/vittorfp/agent-change-proposals/releases)
[![license](https://img.shields.io/github/license/vittorfp/agent-change-proposals)](LICENSE)

Evidence-backed improvement proposals for AI agents.

Existing observability and eval tools show what happened. This project helps
draft a reviewable hypothesis about what should change, why, and how to
validate it.

## What This Is

Agent Change Proposals is a small, local toolkit for turning observed agent
runs and outcome signals into structured, reviewable improvement proposals.

It is not an observability platform, agent runtime, prompt optimizer, or a new
telemetry standard. It is intended to sit after tools such as OpenTelemetry,
OpenInference, Phoenix, Langfuse, LangSmith, or custom eval pipelines.

## Current Status

ACP has a working local CLI, public schemas, checked-in examples, and
file-based import paths for OpenInference/Phoenix-style spans and Langfuse
observation exports. The current v0.6 direction is PR-ready validation checks:
proposals can keep human-readable acceptance criteria while adding optional
machine-checkable `validation.checks`.

See [ROADMAP.md](ROADMAP.md) for current priorities.

## Where This Fits

ACP is meant for the moment after an agent run, eval, or incident review shows
that behavior should probably change, but before someone edits prompts, tool
rules, retrieval policy, or guardrails.

```text
failed run or eval signal
  -> traces + outcome events + improvement surface
  -> ACP drafts a candidate change proposal
  -> reviewer attaches it to a PR, eval review, or incident follow-up
  -> replay/eval decides whether to accept, revise, or reject the change
```

The `improvement_surface` is the trust boundary. The owning team declares which
targets ACP may discuss, for example:

```json
{
  "target_id": "retrieval_policy.main",
  "type": "retrieval_policy",
  "component": "main_retriever"
}
```

ACP can only propose changes to declared targets. V0 schemas are intentionally
permissive while the project learns from real workflows; examples and the RFC
show the intended review shape.

## PR-Ready Validation Checks

Feedback from early reviewers pushed ACP toward a PR-adjacent artifact rather
than a separate approval system. A proposal can now carry stable acceptance
criterion IDs and optional checks that point back to those criteria:

```json
{
  "validation": {
    "method": "controlled_replay",
    "acceptance_criteria": [
      {
        "id": "retrieval-required",
        "description": "Candidate retrieves policy context before answering refund-policy eligibility questions."
      },
      {
        "id": "counterfactual-no-overapply",
        "description": "Candidate does not force retrieval on simple non-policy turns."
      }
    ],
    "checks": [
      {
        "criterion_refs": ["retrieval-required"],
        "role": "positive",
        "suite": "refund_policy_required",
        "metric": "retrieval_called",
        "op": "==",
        "value": true
      },
      {
        "criterion_refs": ["counterfactual-no-overapply"],
        "role": "negative",
        "suite": "retrieval_not_required",
        "metric": "retrieval_called",
        "op": "==",
        "value": false
      }
    ]
  }
}
```

Supported check roles include `positive`, `negative`, `counterfactual`,
`verdict_diff`, and `canary`. The CLI rejects dangling `criterion_refs`, so a
misspelled criterion ID fails validation instead of becoming an orphaned check:

```bash
acp validate change_proposal rfcs/examples/pr-ready.change_proposal.example.json
```

See the full
[PR-ready example](rfcs/examples/pr-ready.change_proposal.example.json) for
trace refs, counterfactual cases, verdict diffs, canary guardrails, and rollback
notes.

## V0 Flow

```text
observed run + outcome signal + improvement surface
  -> change_proposal.yaml
```

The first vertical slice focuses on a narrow, concrete case:

- a RAG-style agent answers a question that appears to require retrieval;
- the run has a failed outcome signal;
- the trace shows no retrieval span;
- the toolkit drafts a routing or retrieval-policy change for review;
- the proposal includes evidence, risk, validation criteria, and rollback notes.

## Quickstart

The CLI command is `acp`, short for Agent Change Proposals.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

acp proposal from-trace \
  examples/rag-missed-retrieval/traces.json \
  --outcomes examples/rag-missed-retrieval/outcomes.json \
  --surface examples/rag-missed-retrieval/improvement_surface.json \
  --output /tmp/change_proposal.json \
  --coverage-output /tmp/proposal_coverage.json

acp replay compare \
  examples/rag-missed-retrieval/replay_baseline.json \
  examples/rag-missed-retrieval/replay_candidate.json \
  --output /tmp/replay_report.json

acp bundle check \
  --trace examples/rag-missed-retrieval/traces.json \
  --outcomes examples/rag-missed-retrieval/outcomes.json \
  --surface examples/rag-missed-retrieval/improvement_surface.json \
  --baseline examples/rag-missed-retrieval/replay_baseline.json \
  --candidate examples/rag-missed-retrieval/replay_candidate.json

acp examples verify

acp schema list
acp schema export change_proposal --output /tmp/change_proposal.schema.json
```

Then inspect `/tmp/change_proposal.json` and `/tmp/replay_report.json`.
`--coverage-output` explains how many failed outcomes had trace coverage, which
detectors matched, and which proposal was selected.
`acp bundle check` validates whether the trace, outcomes, surface, and optional
replay bundles are semantically ready for review, not just schema-valid.
`acp examples verify` validates every checked-in example and ensures generated
proposals match the committed `change_proposal.example.json` files.
`acp schema export` makes schemas available even when ACP is installed outside
of a source checkout.

Optional declared-intent contracts can enrich proposals without widening what
ACP may change:

```bash
acp proposal from-trace \
  examples/declared-intent/traces.json \
  --outcomes examples/declared-intent/outcomes.json \
  --surface examples/declared-intent/improvement_surface.json \
  --agent-manifest examples/declared-intent/agent_manifest.json \
  --domain-context examples/declared-intent/domain_context.json \
  --output /tmp/declared_change_proposal.json
```

For the full walkthrough, read [docs/first-proposal.md](docs/first-proposal.md).
For positioning, read [docs/not-an-observability-platform.md](docs/not-an-observability-platform.md).
For release history, read [CHANGELOG.md](CHANGELOG.md).
For feedback, join [the public discussion](https://github.com/vittorfp/agent-change-proposals/discussions/6),
open a workflow/schema issue using the GitHub issue templates, or read
[docs/feedback-playbook.md](docs/feedback-playbook.md).

## Core Artifacts

- `agent_manifest.json`: optional declared facts about the agent and its
  observable components.
- `domain_context.json`: optional declared domain intent, success dimensions,
  and policies.
- `outcome_event.json`: an append-only signal about a run result.
- `improvement_surface.yaml`: the safe knobs this project is allowed to propose
  changing.
- `change_proposal.yaml`: a reviewable proposal with evidence, hypothesis,
  suggested change, validation plan, risk, and rollback.
- `replay_bundle.yaml`: controlled baseline/candidate cases for comparison.

The public schema files live in [schemas/](schemas/).
The draft schema rationale lives in [RFC 0001](rfcs/0001-change-proposal.md).
The optional manifest/context boundary is described in [RFC 0002](rfcs/0002-agent-manifest-domain-context.md).
The proposed CI-gate validation shape is described in
[RFC 0003](rfcs/0003-ci-gate-schema.md).

## Examples

- [RAG missed retrieval](examples/rag-missed-retrieval)
- [Declared intent](examples/declared-intent)
- [Tool misuse](examples/tool-misuse)
- [Missing escalation](examples/missing-escalation)
- [OpenInference/Phoenix-style import](examples/openinference-phoenix)
- [Langfuse export import](examples/langfuse-export)
- [PR-ready validation-check draft](rfcs/examples/pr-ready.change_proposal.example.json)

Each example includes a checked-in `change_proposal.example.json` so reviewers
can inspect the output without running the CLI.

Import commands can also write diagnostics:

```bash
acp import openinference examples/openinference-phoenix/traces.openinference.json \
  --output /tmp/trace_export.json \
  --diagnostics-output /tmp/import_diagnostics.json
```

Diagnostics report input record counts, output run/span counts, and skipped
records such as spans or observations that lack a run/trace ID.

## Workflow

```text
observed runs + outcome signals + improvement surface
  -> change proposal
  -> controlled replay report
```

## Feedback Wanted

The most useful feedback right now is concrete workflow feedback:

- after you find a problematic agent run, how does it become a behavior change?
- where a `change_proposal` would fit after a failed agent run;
- which fields are missing, unclear, or too speculative;
- what would make the proposal trustworthy enough to review;
- which import path or realistic example would unblock trying ACP.

Use the issue templates for structured feedback, or add a broader comment to
[the public discussion](https://github.com/vittorfp/agent-change-proposals/discussions/6).

## Non-Goals

- Do not replace OpenTelemetry or OpenInference.
- Do not collect traces directly in V0.
- Do not auto-deploy or auto-patch production agents.
- Do not model every possible agent architecture.
- Do not promise deterministic replay of production runs.

## Long-Term Vision

The broader vision is a portable improvement layer for AI agents: systems can
observe real runs, attach outcome signals, generate evidence-backed proposals,
test those proposals against replay/eval bundles, and require human approval
before promoting behavior changes.

V0 starts with the smallest useful artifact: a structured improvement proposal.
