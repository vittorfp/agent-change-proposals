# RFC 0002: Optional Agent Manifest And Domain Context

## Status

Draft.

## Motivation

The original ACP vision includes five contracts:

- Agent Manifest
- Domain / Intent Context
- Telemetry Contract
- Evaluation / Outcome Contract
- Change Proposal Contract

V0 intentionally started with the smallest useful artifact: observed runs,
outcome signals, an improvement surface, and a change proposal. This RFC adds
two optional contracts without turning ACP into an agent runtime or universal
architecture language.

## Contract Boundaries

### `agent_manifest`

Use this for stable, declared facts about the agent:

- identity and version;
- human-readable purpose;
- observable components such as retrievers, tools, routers, prompts, guardrails,
  memories, or LLM calls;
- high-level dependencies between those components;
- known limits.

Do not use `agent_manifest` to declare what ACP may change. That belongs in
`improvement_surface`.

### `improvement_surface`

Use this for the reviewable knobs ACP is allowed to propose changing:

- target IDs;
- target type;
- owning component;
- target description.

The improvement surface remains the trust boundary. A manifest can explain a
component, but only the improvement surface can make a target eligible for a
proposal.

### `domain_context`

Use this for stable, declared facts about the domain:

- domain identity and version;
- narrative business or operational context;
- success dimensions;
- failure definitions;
- policies that explain why an outcome dimension matters.

Do not use `domain_context` to record what happened in a run. That belongs in
`outcome_events` and trace exports.

### `outcome_events`

Use this for observed run-level result signals:

- run ID;
- timestamp;
- source;
- label;
- confidence;
- dimensions;
- notes.

Outcome events say that a run mattered. Domain context explains what the
dimension means.

## Proposal Enrichment

When `agent_manifest` and `domain_context` are supplied, ACP may add declared
context to a proposal:

- manifest evidence for the affected component;
- domain-context evidence for matched success dimensions and policies;
- validation criteria tied to declared success dimensions.

These fields are evidence for human review. They do not prove causality and do
not authorize ACP to propose changes outside the improvement surface.

## Example

See [examples/declared-intent](../examples/declared-intent). It uses the same
missed-retrieval pattern as the basic RAG example, but adds:

- `agent_manifest.json`, declaring `main_retriever`;
- `domain_context.json`, defining `groundedness`, `policy_compliance`, and a
  refund-policy grounding policy.

The resulting proposal includes extra `agent_manifest` and `domain_context`
evidence and validation criteria tied to those declared success dimensions.
