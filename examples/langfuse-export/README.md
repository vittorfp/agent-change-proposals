# Langfuse Export Import

This example demonstrates a file-based path from Langfuse observation rows into
ACP:

```text
Langfuse observations export -> ACP trace export -> change proposal
```

Langfuse's
[Observations API](https://langfuse.com/docs/api-and-data-platform/features/observations-api)
returns observation rows grouped by `traceId`.
ACP imports only the minimum fields needed for V0 proposal generation:

- `traceId`
- observation `id`
- `parentObservationId`
- `name`
- `type`
- `input`
- `output`
- `level`
- `metadata`

```bash
acp import langfuse \
  examples/langfuse-export/observations.langfuse.json \
  --output /tmp/langfuse.trace_export.json

acp proposal from-trace \
  /tmp/langfuse.trace_export.json \
  --outcomes examples/langfuse-export/outcomes.json \
  --surface examples/langfuse-export/improvement_surface.json \
  --output /tmp/langfuse.change_proposal.json
```

This is not a live Langfuse API client. It is a checked-in export fixture that
keeps ACP's boundary clear: consume observations, produce proposals.
