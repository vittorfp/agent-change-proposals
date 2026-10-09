# Feedback Sprint: 2026-10-04

Goal: collect concrete workflow feedback on whether `change_proposal` is a
useful artifact for teams operating AI agents.

This sprint separates direct feedback from ambient signals. Direct feedback is
someone reacting to ACP itself. Ambient signals are public workflow pains that
help decide where to ask and what questions to ask.

## Current State

- Latest release: <https://github.com/vittorfp/agent-change-proposals/releases/tag/v0.5.0>
- Public discussion: <https://github.com/vittorfp/agent-change-proposals/discussions/6>
- Feedback issue: <https://github.com/vittorfp/agent-change-proposals/issues/5>
- Schema follow-up issue: <https://github.com/vittorfp/agent-change-proposals/issues/3>
- Best review example:
  [`examples/declared-intent/change_proposal.example.json`](../examples/declared-intent/change_proposal.example.json)

Direct feedback collected so far: 1.

## Outreach Posted

| Date | Channel | URL | Status |
| --- | --- | --- | --- |
| 2026-10-04 | Langfuse GitHub Discussions / Share your Work | <https://github.com/orgs/langfuse/discussions/18200> | Waiting for replies |
| 2026-10-04 | Phoenix GitHub Discussions / Show and tell | <https://github.com/Arize-ai/phoenix/discussions/16767> | Waiting for replies |
| 2026-10-06 | Reddit r/AI_Agents / Discussion | <https://www.reddit.com/r/AI_Agents/comments/1wz9ei5/how_do_you_review_proposed_agent_behavior_changes/> | Waiting for replies |
| 2026-10-06 | Reddit r/AutoGPT | <https://www.reddit.com/r/AutoGPT/comments/1wz9iig/how_do_you_review_behavior_changes_for_autonomous/> | Waiting for replies |
| 2026-10-06 | Reddit r/AIQuality / Question | <https://www.reddit.com/r/AIQuality/comments/1wz9jg7/what_evidence_makes_an_ai_agent_behavior_change/> | Waiting for replies |
| 2026-10-07 | DeepEval GitHub Discussions / Show and tell | <https://github.com/confident-ai/deepeval/discussions/3427> | Waiting for replies |
| 2026-10-07 | Helicone GitHub Discussions / Show and tell | <https://github.com/Helicone/helicone/discussions/5833> | Waiting for replies |
| 2026-10-07 | OpenLLMetry GitHub Discussions / Show and tell | <https://github.com/traceloop/openllmetry/discussions/4579> | Waiting for replies |
| 2026-10-07 | LangChain Forum / Observability & Evals | <https://forum.langchain.com/c/help/langsmith/8> | Submitted; pending moderator approval |
| 2026-10-09 | ACP GitHub Discussions / Polls | <https://github.com/vittorfp/agent-change-proposals/discussions/9> | Waiting for design feedback |

Not posted yet:

- Discord and Slack, because posting there requires an authenticated user
  session and should be done transparently, without anti-detect tooling.

## Ambient Signals

| Source | What It Suggests | ACP Implication |
| --- | --- | --- |
| [LangChain forum: online evals on multi-agent traces](https://forum.langchain.com/t/custom-code-online-evals-on-multi-agent-system-traces-not-seeing-sub-agent-tool-calls-or-any-ids-or-details-about-child-runs/2026) | Some teams cannot easily inspect sub-agent tool calls or child-run details when evaluating multi-agent systems. | Keep investing in trace coverage, import diagnostics, and proposal coverage so ACP can say when evidence is incomplete. |
| [LangChain forum: evals across multiple LangSmith projects](https://forum.langchain.com/t/how-are-teams-handling-evals-when-agent-pipelines-span-multiple-langsmith-projects/3300) | Agent pipelines often span multiple projects or teams, making root cause analysis and release confidence harder. | Position `change_proposal` as a portable review artifact that can sit above fragmented observability systems. |
| [Reddit r/LangChain: testing AI agents before deploying](https://www.reddit.com/r/LangChain/comments/1wsduk3/how_are_you_testing_ai_agents_before_deploying/) | Practitioners care about tool/API use, data access, auth boundaries, escalation behavior, and intermediate steps, not just final answers. | Keep proposals evidence-backed and explicit about validation, risk, rollback, and allowed improvement surfaces. |
| [Langfuse community](https://langfuse.com/community) | Langfuse maintains active community channels for observability and eval workflows. | Good outreach target for workflow feedback, especially integration fit and artifact boundaries. |
| [Phoenix docs](https://arize.com/docs/phoenix/) | Phoenix/OpenInference users already work with tracing, evaluations, experiments, and OpenTelemetry/OpenInference concepts. | Good outreach target for whether ACP should stay downstream of traces or expose deeper OpenInference semantics. |

## Outreach Targets

| Channel | Why It Fits | Ask |
| --- | --- | --- |
| GitHub Discussion #6 | Public, durable, low-friction home for project-level reactions. | Does evidence-backed `change_proposal` deserve to exist? |
| GitHub Issue #5 | Best place to capture structured workflow feedback. | Where would this artifact fit or fail in PR/CI/eval review? |
| LangChain Forum, Observability and Evals | Recent posts show adjacent pain around multi-agent evals and trace visibility. | Would a portable proposal artifact help after an eval identifies a behavior gap? |
| Langfuse Discord/GitHub/community hour | Strong fit for eval and observability practitioners. | Is ACP a useful downstream artifact or unnecessary schema around existing workflows? |
| Phoenix/OpenInference Slack/GitHub | Strong fit for trace import and OpenInference semantics. | Which trace fields need to survive import for proposals to be trustworthy? |
| Direct reviewers | Highest signal if they operate real agents or eval pipelines. | Review one example proposal and say what would block adoption. |

## Draft: Community Post

```text
I am looking for practical feedback on a small open-source artifact for AI
agent improvement workflows: an evidence-backed `change_proposal`.

It is not a tracing standard, observability backend, agent runtime, or prompt
optimizer. The idea is to sit after tools like OpenTelemetry/OpenInference,
Phoenix, Langfuse, LangSmith, Braintrust, or custom eval pipelines and produce
a reviewable proposal:

- what behavior was observed;
- what outcome signal made it important;
- what change is suggested;
- what evidence supports it;
- how to validate it;
- how to roll it back.

Repo: https://github.com/vittorfp/agent-change-proposals
Latest release: https://github.com/vittorfp/agent-change-proposals/releases/tag/v0.5.0
Example proposal: https://github.com/vittorfp/agent-change-proposals/blob/main/examples/declared-intent/change_proposal.example.json
Discussion: https://github.com/vittorfp/agent-change-proposals/discussions/6

The feedback I need is workflow-level:

1. Would this fit PR review, CI, eval review, incident follow-up, or none of
   those?
2. Which fields are missing, confusing, or too speculative?
3. What evidence would make the proposal trustworthy enough to review?
4. Which existing tool or process already solves this for you?
```

## Draft: Reply To Relevant Threads

```text
This pain is close to something I am exploring: after an eval or trace review
shows an agent behavior problem, how should the proposed behavior change be
recorded and reviewed?

I am testing a small open-source artifact called `change_proposal`, downstream
of tracing/eval tools. It tries to capture observed behavior, outcome signal,
evidence, suggested change, validation criteria, risk, and rollback in one
reviewable file.

Example:
https://github.com/vittorfp/agent-change-proposals/blob/main/examples/declared-intent/change_proposal.example.json

Does that shape map to how you would review agent changes, or would it add
ceremony without solving the hard part?
```

## Draft: Direct Message

```text
I am collecting early workflow feedback on an open-source format for
evidence-backed AI agent change proposals.

The short version: traces/evals show what happened; ACP tries to create a
reviewable proposal for what should change, why, and how to validate/rollback
it.

Would you be open to skimming this example and telling me whether it would fit
your agent eval/review workflow?

https://github.com/vittorfp/agent-change-proposals/blob/main/examples/declared-intent/change_proposal.example.json

The most useful answer would be blunt: useful, redundant, too vague, missing
fields, or solving the wrong problem.
```

## Capture Rules

- Record reactions to ACP itself in [feedback-log.md](feedback-log.md) as
  feedback items.
- Record public adjacent pains as ambient signals, not as feedback items.
- Link public comments to issue #5.
- Use issue #3 only when feedback points to a concrete schema change.
- Do not copy private traces, prompts, customer data, or proprietary exports
  into the repo.
