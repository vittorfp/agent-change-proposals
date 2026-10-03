# Roadmap

Agent Change Proposals is currently validating one question:

> Is a structured, evidence-backed proposal a useful artifact for reviewing AI
> agent behavior changes?

## Current Status

The project has a working local CLI, public schemas, checked-in examples, and
file-based import paths for OpenInference/Phoenix-style spans and Langfuse
observation exports.

The next important milestone is feedback from people who run agent evals,
observability pipelines, or internal agent platforms.

## Near-Term Priorities

1. **Collect feedback on the proposal artifact**
   - Discussion: https://github.com/vittorfp/agent-change-proposals/discussions/6
   - Issue: https://github.com/vittorfp/agent-change-proposals/issues/5

2. **Refine the `change_proposal` schema**
   - Improve field names, required evidence, confidence, risk, and validation
     structure based on feedback.
   - Issue: https://github.com/vittorfp/agent-change-proposals/issues/3

3. **Improve ecosystem import fidelity**
   - Keep imports file-based for now.
   - Prefer small, documented fixtures over live API dependencies.
   - Add fields only when they improve proposal quality.

4. **Make replay more reviewable**
   - Keep controlled replay honest about its limits.
   - Improve reports so they are easy to use in PR/CI review.

## Later, If The Artifact Proves Useful

- GitHub Action that comments a proposal and replay report on a PR.
- More realistic export fixtures from production-grade observability tools.
- Stronger schema versioning and migration notes.
- Optional package publishing.
- More conservative detectors for common agent improvement patterns.

## Non-Goals For Now

- Hosted dashboard.
- Agent runtime.
- Production telemetry collector.
- Automatic code patching.
- Automatic deployment of behavior changes.
- Universal agent manifests.

