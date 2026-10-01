# Contributing

Agent Change Proposals is intentionally narrow.

The project is not trying to become a new tracing standard, observability
backend, hosted eval platform, or autonomous self-improvement loop. It focuses
on one artifact: a structured, reviewable proposal for changing an AI agent's
behavior.

## Design Principles

- **Proposal-first:** the main output should be useful in a human review.
- **Evidence-backed, not magic:** proposals must reference observed runs,
  outcome signals, replay cases, or eval results.
- **Compatible with existing telemetry:** prefer OpenTelemetry GenAI and
  OpenInference-compatible inputs over new tracing semantics.
- **Human approval by default:** the project may suggest changes, but it should
  not auto-deploy them.
- **Small improvement surfaces:** describe only the knobs that are safe to
  change, not the entire agent architecture.
- **Explicit limits:** every proposal should state what it does not prove.

## Good Contributions

- New examples that show a realistic run-to-proposal workflow.
- Schema improvements that make proposals easier to review or validate.
- Conservative detectors with clear evidence and tests.
- Importers for existing trace or eval exports.
- Replay/reporting improvements that make validation clearer.

## Contributions To Avoid For Now

- New agent runtimes or orchestration frameworks.
- Hosted services, dashboards, or long-running daemons.
- Automatic code patching.
- Broad universal agent manifests.
- Claims of causal proof from telemetry alone.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q
```

