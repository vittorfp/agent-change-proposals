# Roadmap

Agent Change Proposals is currently validating one question:

> Is a structured, evidence-backed proposal a useful artifact for reviewing AI
> agent behavior changes?

## Current Status

The project has a working local CLI, public schemas, checked-in examples, and
file-based import paths for OpenInference/Phoenix-style spans and Langfuse
observation exports. It also has semantic bundle checks, import diagnostics,
and proposal coverage reports so early users can see where evidence is missing.

The next important milestone is feedback from people who run agent evals,
observability pipelines, or internal agent platforms.

## Near-Term Priorities

1. **Collect feedback on the proposal artifact**
   - Discussion: https://github.com/vittorfp/agent-change-proposals/discussions/6
   - Issue: https://github.com/vittorfp/agent-change-proposals/issues/5
   - Playbook: [docs/feedback-playbook.md](docs/feedback-playbook.md)
   - Log: [docs/feedback-log.md](docs/feedback-log.md)

2. **Refine the `change_proposal` schema**
   - Improve field names, required evidence, confidence, risk, and validation
     structure based on feedback.
   - Issue: https://github.com/vittorfp/agent-change-proposals/issues/3
   - Draft RFC: [rfcs/0001-change-proposal.md](rfcs/0001-change-proposal.md)

3. **Improve ecosystem import fidelity**
   - Keep imports file-based for now.
   - Prefer small, documented fixtures over live API dependencies.
   - Use diagnostics to make skipped records and coverage gaps visible.
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
