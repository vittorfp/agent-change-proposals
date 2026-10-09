# Feedback Log

Use this file to summarize feedback from issues, discussions, calls, or direct
messages. Link back to public sources when possible.

## Summary

- Feedback items collected: 2
- Strongest positive signal: useful for eval review and incident follow-up.
- Strongest adoption blocker: CI-gate semantics and approval integrity are not
  structured enough yet.
- Schema changes justified by repeated feedback: machine-readable validation
  should live under `validation`; evidence should stay separate from gate rules.

## Outreach

| Date | Channel | URL | Status |
| --- | --- | --- | --- |
| 2026-10-04 | Langfuse GitHub Discussions | <https://github.com/orgs/langfuse/discussions/18200> | Waiting for replies |
| 2026-10-04 | Phoenix GitHub Discussions | <https://github.com/Arize-ai/phoenix/discussions/16767> | Waiting for replies |
| 2026-10-06 | Reddit r/AI_Agents | <https://www.reddit.com/r/AI_Agents/comments/1wz9ei5/how_do_you_review_proposed_agent_behavior_changes/> | Waiting for replies |
| 2026-10-06 | Reddit r/AutoGPT | <https://www.reddit.com/r/AutoGPT/comments/1wz9iig/how_do_you_review_behavior_changes_for_autonomous/> | Waiting for replies |
| 2026-10-06 | Reddit r/AIQuality | <https://www.reddit.com/r/AIQuality/comments/1wz9jg7/what_evidence_makes_an_ai_agent_behavior_change/> | Waiting for replies |
| 2026-10-07 | DeepEval GitHub Discussions | <https://github.com/confident-ai/deepeval/discussions/3427> | Waiting for replies |
| 2026-10-07 | Helicone GitHub Discussions | <https://github.com/Helicone/helicone/discussions/5833> | Waiting for replies |
| 2026-10-07 | OpenLLMetry GitHub Discussions | <https://github.com/traceloop/openllmetry/discussions/4579> | Waiting for replies |
| 2026-10-07 | LangChain Forum / Observability & Evals | <https://forum.langchain.com/c/help/langsmith/8> | Submitted; pending moderator approval |
| 2026-10-09 | ACP GitHub Discussions / Polls | <https://github.com/vittorfp/agent-change-proposals/discussions/9> | Waiting for design feedback |

## Ambient Signals

Ambient signals are public workflow pains that look relevant to ACP but are not
direct feedback on the project.

| Date | Source | Category | Signal | Action |
| --- | --- | --- | --- | --- |
| 2026-10-04 | [LangChain forum: online evals on multi-agent traces](https://forum.langchain.com/t/custom-code-online-evals-on-multi-agent-system-traces-not-seeing-sub-agent-tool-calls-or-any-ids-or-details-about-child-runs/2026) | integration-gap | Multi-agent eval workflows can lose visibility into sub-agent tool calls and child-run details. | Ask whether proposal coverage and import diagnostics would make incomplete evidence visible enough for review. |
| 2026-10-04 | [LangChain forum: evals across multiple LangSmith projects](https://forum.langchain.com/t/how-are-teams-handling-evals-when-agent-pipelines-span-multiple-langsmith-projects/3300) | artifact-fit | Multi-agent pipelines can span projects and teams, fragmenting debugging and release confidence. | Test whether a portable `change_proposal` helps coordinate review across system boundaries. |
| 2026-10-04 | [Reddit r/LangChain: testing AI agents before deploying](https://www.reddit.com/r/LangChain/comments/1wsduk3/how_are_you_testing_ai_agents_before_deploying/) | trust-gap | Agent testing discussions emphasize tool/API use, data access, auth boundaries, escalation, and intermediate behavior. | Keep examples focused on evidence, allowed surfaces, validation criteria, risk, and rollback instead of only final answers. |
| 2026-10-04 | [Langfuse community](https://langfuse.com/community) | integration-gap | Langfuse has active observability/eval community channels. | Use as a feedback target for whether ACP belongs downstream of existing observability workflows. |
| 2026-10-04 | [Phoenix docs](https://arize.com/docs/phoenix/) | integration-gap | Phoenix/OpenInference workflows already center traces, evals, experiments, and OpenTelemetry/OpenInference concepts. | Ask what OpenInference fields are required for trustworthy proposal generation. |

## Feedback Items

| Date | Source | Reviewer Context | Category | Signal | Action |
| --- | --- | --- | --- | --- | --- |
| 2026-10-06 | [GitHub discussion #6](https://github.com/vittorfp/agent-change-proposals/discussions/6#discussioncomment-18783719) | Public reviewer of v0.5 proposal format | schema-gap, trust-gap | Useful for eval review and incident follow-up, but not ready as a CI gate because nested proposal sections can be underspecified while still validating. Reviewer asked for machine-readable validation, immutable evidence refs, baseline/candidate artifact IDs, evaluator and dataset versions, metric threshold, sample count, rollback trigger, and plain JSON stabilization before more integrations. | Tighten V0 schema around existing nested sections first; track CI-readiness fields in issue #3 before adding new required fields. |
| 2026-10-08 | [GitHub discussion #6](https://github.com/vittorfp/agent-change-proposals/discussions/6#discussioncomment-18815168) and [follow-up](https://github.com/vittorfp/agent-change-proposals/discussions/6#discussioncomment-18837203) | Public reviewer of v0.6 CI-gate direction | schema-gap, trust-gap | Keep gate fields under `validation`, but model them as a list of checks tied to acceptance criteria instead of flat fields or one evaluation object. This would let CI report which criterion failed while keeping prose criteria readable. Reviewer also warned that `status: accepted` is insufficient unless approval is tied to a canonical proposal digest, so edits after approval become stale. Follow-up asks whether one check can reference multiple criteria, since some checks may support several criteria at once. | Add `validation.checks` as a serious RFC 0003 alternative before schema enforcement; track approval digest/version semantics and multi-criterion check references as schema follow-ups. |

## Open Questions

- Does `change_proposal` fit PR review, CI, eval review, or a different workflow?
- Is confidence better represented at proposal level, hypothesis level, or
  evidence level?
- Are risk and rollback specific enough to support human approval?
- Should validation criteria become structured objects instead of strings?
- Should CI checks reference prose acceptance criteria by index, stable ID, or
  embedded criterion object?
- Can one CI check satisfy multiple acceptance criteria?
- Should accepted proposals require approval metadata tied to a canonical
  proposal digest?
- Which importer should become more faithful first: OpenInference/Phoenix or
  Langfuse?
