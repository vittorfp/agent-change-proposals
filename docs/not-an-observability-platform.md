# Not An Observability Platform

Agent Change Proposals is meant to complement observability and eval systems,
not replace them.

## What Existing Tools Do Well

Tools and standards such as OpenTelemetry, OpenInference, Phoenix, Langfuse,
LangSmith, and Braintrust help teams collect, inspect, evaluate, and experiment
with agent behavior.

ACP should not duplicate that layer.

## What ACP Focuses On

ACP starts after an observed run and an outcome signal exist.

```text
observability/evals
  -> observed run
  -> outcome signal
  -> ACP change proposal
  -> review / replay / approval
```

The core artifact is a reviewable proposal:

- what behavior was observed;
- what outcome signal made it important;
- what change target is allowed;
- what hypothesis explains the gap;
- what change should be reviewed;
- how to validate it;
- what risk and rollback path exist.

## Boundaries

ACP should not:

- define a new tracing semantic convention;
- collect production telemetry directly in V0;
- become an agent runtime;
- become a hosted dashboard;
- claim causal proof from traces alone;
- auto-deploy agent behavior changes.

ACP should:

- accept exports from existing tools;
- preserve evidence references;
- generate artifacts that work in review and CI workflows;
- stay explicit about uncertainty and validation limits.

## First Integration Direction

The first ecosystem-facing example is OpenInference/Phoenix-style import:

```text
OpenInference-style spans -> ACP trace export -> change proposal
```

OpenInference is built on OpenTelemetry and uses `openinference.span.kind` to
classify spans such as `LLM`, `TOOL`, `RETRIEVER`, `AGENT`, `GUARDRAIL`, and
`EVALUATOR`. See the
[OpenInference semantic conventions](https://github.com/Arize-ai/openinference/blob/main/spec/semantic_conventions.md)
for the authoritative reference.

For V0, ACP imports only the minimum fields needed to generate a proposal:

- trace/run ID;
- span ID;
- parent span ID;
- span name;
- span kind;
- status;
- attributes;
- root input/output values.

ACP also includes a Langfuse export fixture. Langfuse's Observations API returns
observation rows grouped by `traceId`; ACP converts those rows into the same
minimal trace export used by proposal generation.
