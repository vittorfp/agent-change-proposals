from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


RETRIEVAL_KEYWORDS = {
    "according",
    "context",
    "decision",
    "document",
    "evidence",
    "history",
    "policy",
    "refund",
    "source",
}

RETRIEVAL_SPAN_KINDS = {"retriever", "retrieval", "rag"}
TOOL_SPAN_KINDS = {"tool", "tool_call"}
ESCALATION_SPAN_KINDS = {"escalation", "handoff", "human_handoff", "guardrail"}


def build_proposal(trace_export: dict[str, Any], outcomes: list[dict[str, Any]], surface: dict[str, Any]) -> dict[str, Any]:
    failures = {event["run_id"]: event for event in outcomes if event.get("label") == "failure"}
    tool_misuse = [
        run for run in trace_export.get("runs", [])
        if run.get("run_id") in failures and _looks_like_tool_misuse(run, failures[run["run_id"]])
    ]
    if tool_misuse:
        return _tool_misuse_proposal(tool_misuse[0], failures[tool_misuse[0]["run_id"]], surface)

    missing_escalation = [
        run for run in trace_export.get("runs", [])
        if run.get("run_id") in failures and _looks_like_missing_escalation(run, failures[run["run_id"]])
    ]
    if missing_escalation:
        return _missing_escalation_proposal(missing_escalation[0], failures[missing_escalation[0]["run_id"]], surface)

    missed_retrieval = [
        run for run in trace_export.get("runs", [])
        if run.get("run_id") in failures and _looks_like_missed_retrieval(run)
    ]
    if missed_retrieval:
        return _missed_retrieval_proposal(missed_retrieval[0], failures[missed_retrieval[0]["run_id"]], surface)

    return _no_pattern_proposal(trace_export, outcomes, surface)


def _missed_retrieval_proposal(run: dict[str, Any], outcome: dict[str, Any], surface: dict[str, Any]) -> dict[str, Any]:
    target = _select_target(surface, {"routing_rule", "retrieval_policy"})
    proposal_id = _stable_id(run["run_id"], target.get("target_id", "unknown"))

    return {
        "schema_version": "0.1",
        "proposal_id": proposal_id,
        "title": "Require retrieval for context-dependent questions",
        "status": "proposed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent_ref": surface.get("agent_ref", {}),
        "problem": {
            "summary": "A failed run appears to require external context, but no retrieval step was observed.",
            "run_id": run["run_id"],
            "outcome_label": outcome.get("label"),
            "outcome_source": outcome.get("source"),
        },
        "evidence": [
            {
                "type": "outcome_event",
                "run_id": run["run_id"],
                "label": outcome.get("label"),
                "confidence": outcome.get("confidence"),
                "dimensions": outcome.get("dimensions", []),
            },
            {
                "type": "trace_pattern",
                "run_id": run["run_id"],
                "observed": "No retrieval span found for a context-dependent input.",
                "span_count": len(run.get("spans", [])),
            },
        ],
        "hypothesis": {
            "summary": "The routing or retrieval policy is not requiring retrieval when the user asks for policy, historical, or source-grounded information.",
            "confidence": "medium",
            "limits": "This is a hypothesis from trace structure and outcome labels, not a causal proof.",
        },
        "proposed_change": {
            "target": target,
            "summary": "Update the target so context-dependent questions trigger retrieval before final response generation.",
            "suggested_patch": {
                "require_retrieval_when_input_mentions": sorted(RETRIEVAL_KEYWORDS),
            },
        },
        "validation": {
            "method": "controlled_replay",
            "acceptance_criteria": [
                "Candidate run includes at least one retrieval span for this case.",
                "Groundedness or correctness outcome improves without increasing blocked or escalated runs.",
            ],
        },
        "risk": {
            "level": "low",
            "notes": "May increase latency and retrieval cost for borderline context-dependent questions.",
        },
        "rollback": {
            "plan": "Revert the routing or retrieval-policy change if replay or online evaluation regresses.",
        },
    }


def _tool_misuse_proposal(run: dict[str, Any], outcome: dict[str, Any], surface: dict[str, Any]) -> dict[str, Any]:
    target = _select_target(surface, {"tool_policy", "routing_rule"})
    tool_span = next((span for span in run.get("spans", []) if _is_tool_span(span)), {})
    proposal_id = _stable_id(run["run_id"], target.get("target_id", "unknown"))

    return {
        "schema_version": "0.1",
        "proposal_id": proposal_id,
        "title": "Review tool-selection policy for failed tool use",
        "status": "proposed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent_ref": surface.get("agent_ref", {}),
        "problem": {
            "summary": "A failed run includes a tool-use signal that appears inconsistent with the expected task.",
            "run_id": run["run_id"],
            "outcome_label": outcome.get("label"),
            "outcome_source": outcome.get("source"),
        },
        "evidence": [
            {
                "type": "outcome_event",
                "run_id": run["run_id"],
                "label": outcome.get("label"),
                "confidence": outcome.get("confidence"),
                "dimensions": outcome.get("dimensions", []),
            },
            {
                "type": "trace_pattern",
                "run_id": run["run_id"],
                "observed": "A tool span was marked as mismatched, errored, or associated with a tool-use failure.",
                "span": _span_summary(tool_span),
            },
        ],
        "hypothesis": {
            "summary": "The tool-selection policy may be routing this class of request to the wrong tool or with insufficient preconditions.",
            "confidence": "medium",
            "limits": "This proposal relies on tool span metadata and outcome labels; it should be validated with targeted replay cases.",
        },
        "proposed_change": {
            "target": target,
            "summary": "Tighten tool-selection criteria or add a precondition check before invoking the affected tool.",
            "suggested_patch": {
                "add_precondition": "Only call the tool when required input fields are present and match the task intent.",
            },
        },
        "validation": {
            "method": "controlled_replay",
            "acceptance_criteria": [
                "Candidate avoids the mismatched tool call for this case.",
                "Candidate still uses the tool on positive control cases where it is required.",
            ],
        },
        "risk": {
            "level": "medium",
            "notes": "A stricter tool policy can reduce useful tool use if the preconditions are too narrow.",
        },
        "rollback": {
            "plan": "Revert the tool-policy change if positive control cases regress.",
        },
    }


def _missing_escalation_proposal(run: dict[str, Any], outcome: dict[str, Any], surface: dict[str, Any]) -> dict[str, Any]:
    target = _select_target(surface, {"guardrail_threshold", "routing_rule"})
    proposal_id = _stable_id(run["run_id"], target.get("target_id", "unknown"))

    return {
        "schema_version": "0.1",
        "proposal_id": proposal_id,
        "title": "Add escalation for high-risk uncertain responses",
        "status": "proposed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent_ref": surface.get("agent_ref", {}),
        "problem": {
            "summary": "A failed run appears to require escalation or guardrail handling, but no escalation span was observed.",
            "run_id": run["run_id"],
            "outcome_label": outcome.get("label"),
            "outcome_source": outcome.get("source"),
        },
        "evidence": [
            {
                "type": "outcome_event",
                "run_id": run["run_id"],
                "label": outcome.get("label"),
                "confidence": outcome.get("confidence"),
                "dimensions": outcome.get("dimensions", []),
            },
            {
                "type": "trace_pattern",
                "run_id": run["run_id"],
                "observed": "Outcome dimensions indicate escalation or guardrail failure, but no escalation/handoff/guardrail span was found.",
                "span_count": len(run.get("spans", [])),
            },
        ],
        "hypothesis": {
            "summary": "The escalation threshold or guardrail policy may be too permissive for high-risk uncertain answers.",
            "confidence": "medium",
            "limits": "This identifies a reviewable safety hypothesis, not proof that escalation is always correct.",
        },
        "proposed_change": {
            "target": target,
            "summary": "Escalate when uncertainty is high and the answer concerns protected, high-risk, or policy-sensitive decisions.",
            "suggested_patch": {
                "escalate_when": [
                    "risk_class is high",
                    "confidence is low",
                    "policy-sensitive decision is requested",
                ],
            },
        },
        "validation": {
            "method": "controlled_replay",
            "acceptance_criteria": [
                "Candidate escalates this case.",
                "Candidate does not over-escalate low-risk control cases.",
            ],
        },
        "risk": {
            "level": "medium",
            "notes": "Lower escalation thresholds can increase human-review load.",
        },
        "rollback": {
            "plan": "Revert the escalation-threshold change if over-escalation exceeds the agreed limit.",
        },
    }


def _looks_like_missed_retrieval(run: dict[str, Any]) -> bool:
    input_text = str(run.get("input", {}).get("text", "")).lower()
    mentions_context = any(keyword in input_text for keyword in RETRIEVAL_KEYWORDS)
    has_retrieval = any(_is_retrieval_span(span) for span in run.get("spans", []))
    return mentions_context and not has_retrieval


def _is_retrieval_span(span: dict[str, Any]) -> bool:
    kind = str(span.get("kind") or span.get("name") or "").lower()
    attributes = span.get("attributes", {})
    span_kind = str(attributes.get("openinference.span.kind") or attributes.get("gen_ai.operation.name") or "").lower()
    return kind in RETRIEVAL_SPAN_KINDS or span_kind in RETRIEVAL_SPAN_KINDS


def _looks_like_tool_misuse(run: dict[str, Any], outcome: dict[str, Any]) -> bool:
    dimensions = set(outcome.get("dimensions", []))
    if not dimensions.intersection({"tool_use", "tool_selection", "tool_error"}):
        return False
    return any(_is_tool_span(span) and _tool_span_has_failure_signal(span) for span in run.get("spans", []))


def _is_tool_span(span: dict[str, Any]) -> bool:
    kind = str(span.get("kind") or span.get("name") or "").lower()
    attributes = span.get("attributes", {})
    span_kind = str(attributes.get("openinference.span.kind") or attributes.get("gen_ai.operation.name") or "").lower()
    return kind in TOOL_SPAN_KINDS or span_kind in TOOL_SPAN_KINDS


def _tool_span_has_failure_signal(span: dict[str, Any]) -> bool:
    attributes = span.get("attributes", {})
    return bool(
        attributes.get("tool.mismatch")
        or attributes.get("tool.error")
        or attributes.get("error")
        or span.get("status") == "error"
    )


def _looks_like_missing_escalation(run: dict[str, Any], outcome: dict[str, Any]) -> bool:
    dimensions = set(outcome.get("dimensions", []))
    needs_escalation = bool(dimensions.intersection({"escalation", "guardrail", "safety", "human_review"}))
    has_escalation = any(_is_escalation_span(span) for span in run.get("spans", []))
    return needs_escalation and not has_escalation


def _is_escalation_span(span: dict[str, Any]) -> bool:
    kind = str(span.get("kind") or span.get("name") or "").lower()
    attributes = span.get("attributes", {})
    span_kind = str(attributes.get("openinference.span.kind") or attributes.get("gen_ai.operation.name") or "").lower()
    return kind in ESCALATION_SPAN_KINDS or span_kind in ESCALATION_SPAN_KINDS


def _span_summary(span: dict[str, Any]) -> dict[str, Any]:
    return {
        "span_id": span.get("span_id"),
        "name": span.get("name"),
        "kind": span.get("kind"),
        "status": span.get("status"),
        "attributes": span.get("attributes", {}),
    }


def _select_target(surface: dict[str, Any], preferred_types: set[str] | None = None) -> dict[str, Any]:
    targets = surface.get("allowed_targets", [])
    preferred_types = preferred_types or set()
    for target in targets:
        if target.get("type") in preferred_types:
            return target
    for target in targets:
        if target.get("type") in {"routing_rule", "retrieval_policy"}:
            return target
    return targets[0] if targets else {"target_id": "unspecified", "type": "config", "component": "unknown"}


def _stable_id(run_id: str, target_id: str) -> str:
    digest = hashlib.sha256(f"{run_id}:{target_id}".encode("utf-8")).hexdigest()[:12]
    return f"acp_{digest}"


def _no_pattern_proposal(trace_export: dict[str, Any], outcomes: list[dict[str, Any]], surface: dict[str, Any]) -> dict[str, Any]:
    digest = hashlib.sha256(str(trace_export).encode("utf-8")).hexdigest()[:12]
    return {
        "schema_version": "0.1",
        "proposal_id": f"acp_{digest}",
        "title": "No specific improvement pattern detected",
        "status": "proposed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent_ref": surface.get("agent_ref", {}),
        "problem": {
            "summary": "The input data did not match a supported V0 detector.",
            "failed_outcome_count": sum(1 for event in outcomes if event.get("label") == "failure"),
        },
        "evidence": [],
        "hypothesis": {
            "summary": "More specific detectors or outcome labels are needed.",
            "confidence": "low",
        },
        "proposed_change": {
            "target": {"target_id": "none", "type": "config", "component": "none"},
            "summary": "No change proposed.",
        },
        "validation": {
            "method": "manual_review",
            "acceptance_criteria": ["Add a supported detector or richer outcome labels."],
        },
        "risk": {"level": "none", "notes": "No behavior change proposed."},
        "rollback": {"plan": "No rollback needed."},
    }
