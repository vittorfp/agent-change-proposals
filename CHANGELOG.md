# Changelog

## v0.6.0 - 2026-10-11

PR-ready validation checks for agent change proposals.

- Added optional structured `validation.acceptance_criteria` entries with
  stable `id` fields.
- Added optional `validation.checks[*]` with `criterion_refs`, check roles,
  metrics, operators, trace-set refs, and evidence refs.
- Added semantic CLI validation that rejects dangling `criterion_refs`.
- Added optional `validation.verdict_diff` and `validation.outcome` fields for
  PR review and insufficient-evidence workflows.
- Added a PR-ready RFC example covering positive, negative/counterfactual,
  verdict-diff, and canary checks.

## v0.5.0 - 2026-10-04

Optional declared-intent contracts.

- Added optional `agent_manifest` and `domain_context` artifacts.
- Used declared components, success dimensions, and policies to enrich proposal
  evidence and validation criteria.
- Kept `improvement_surface` as the trust boundary for allowed changes.

## v0.4.0 - 2026-10-03

Import diagnostics and proposal coverage.

- Added import diagnostics for file-based OpenInference/Phoenix and Langfuse
  fixtures.
- Added proposal coverage reports so reviewers can see missing trace or outcome
  coverage.

## v0.3.0 - 2026-10-03

Semantic bundle readiness checks.

- Added bundle checks across traces, outcomes, surfaces, proposals, and replay
  bundles.
- Added replay comparison reporting for baseline/candidate cases.

## v0.2.2 - 2026-10-03

Packaged public artifacts and schema export.

- Included schemas, examples, docs, and trust files in the source
  distribution.
- Added schema export support for installed environments.

## v0.2.1 - 2026-10-03

Verification and packaging checks.

- Added project-file checks and package-distribution checks.

## v0.2.0 - 2026-10-02

Ecosystem fixtures and reviewable examples.

- Added checked-in examples for common agent behavior-change cases.
- Added file-based ecosystem fixture support.

## v0.1.0 - 2026-10-02

First public seed.

- Added the first local CLI, public schemas, and seed proposal workflow.
