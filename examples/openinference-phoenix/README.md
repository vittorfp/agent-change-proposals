# OpenInference/Phoenix-Style Import

This example demonstrates the first ecosystem-facing path:

```text
OpenInference-style spans -> ACP trace export -> change proposal
```

The fixture is intentionally small and file-based. It does not call Phoenix or
any hosted API. The goal is to prove that ACP can sit after existing
observability tooling instead of inventing a new tracing format.

OpenInference defines `openinference.span.kind` values such as `LLM`, `TOOL`,
`RETRIEVER`, `AGENT`, `GUARDRAIL`, and `EVALUATOR`. ACP imports only the
minimum fields it needs for V0 proposal generation.

```bash
acp import openinference \
  examples/openinference-phoenix/traces.openinference.json \
  --output /tmp/openinference.trace_export.json

acp proposal from-trace \
  /tmp/openinference.trace_export.json \
  --outcomes examples/openinference-phoenix/outcomes.json \
  --surface examples/openinference-phoenix/improvement_surface.json \
  --output /tmp/openinference.change_proposal.json
```

The expected proposal is the same class as the native fixture: a retrieval
policy proposal grounded in an observed run and a failed outcome signal.
