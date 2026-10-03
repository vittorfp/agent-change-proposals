# Agent Change Proposals

[![tests](https://github.com/vittorfp/agent-change-proposals/actions/workflows/test.yml/badge.svg)](https://github.com/vittorfp/agent-change-proposals/actions/workflows/test.yml)
[![release](https://img.shields.io/github/v/release/vittorfp/agent-change-proposals)](https://github.com/vittorfp/agent-change-proposals/releases)
[![license](https://img.shields.io/github/license/vittorfp/agent-change-proposals)](LICENSE)

Evidence-backed improvement proposals for AI agents.

Existing observability and eval tools show what happened. This project helps
describe what should change, why, and how to validate it.

## What This Is

Agent Change Proposals is a small, local toolkit for turning observed agent
runs and outcome signals into structured, reviewable improvement proposals.

It is not an observability platform, agent runtime, prompt optimizer, or a new
telemetry standard. It is intended to sit after tools such as OpenTelemetry,
OpenInference, Phoenix, Langfuse, LangSmith, or custom eval pipelines.

## V0 Flow

```text
observed run + outcome signal + improvement surface
  -> change_proposal.yaml
```

The first vertical slice focuses on a narrow, concrete case:

- a RAG-style agent answers a question that appears to require retrieval;
- the run has a failed outcome signal;
- the trace shows no retrieval span;
- the toolkit proposes a routing or retrieval-policy change;
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
  --output /tmp/change_proposal.json

acp replay compare \
  examples/rag-missed-retrieval/replay_baseline.json \
  examples/rag-missed-retrieval/replay_candidate.json \
  --output /tmp/replay_report.json
```

Then inspect `/tmp/change_proposal.json` and `/tmp/replay_report.json`.

For the full walkthrough, read [docs/first-proposal.md](docs/first-proposal.md).
For positioning, read [docs/not-an-observability-platform.md](docs/not-an-observability-platform.md).
For feedback, join [the public discussion](https://github.com/vittorfp/agent-change-proposals/discussions/6).

## Core Artifacts

- `outcome_event.json`: an append-only signal about a run result.
- `improvement_surface.yaml`: the safe knobs this project is allowed to propose
  changing.
- `change_proposal.yaml`: a reviewable proposal with evidence, hypothesis,
  suggested change, validation plan, risk, and rollback.
- `replay_bundle.yaml`: controlled baseline/candidate cases for comparison.

The public schema files live in [schemas/](schemas/).

## Examples

- [RAG missed retrieval](examples/rag-missed-retrieval)
- [Tool misuse](examples/tool-misuse)
- [Missing escalation](examples/missing-escalation)
- [OpenInference/Phoenix-style import](examples/openinference-phoenix)
- [Langfuse export import](examples/langfuse-export)

Each example includes a checked-in `change_proposal.example.json` so reviewers
can inspect the output without running the CLI.

## Workflow

```text
observed runs + outcome signals + improvement surface
  -> change proposal
  -> controlled replay report
```

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
