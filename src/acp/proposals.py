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


def build_proposal(
    trace_export: dict[str, Any],
    outcomes: list[dict[str, Any]],
    surface: dict[str, Any],
    agent_manifest: dict[str, Any] | None = None,
    domain_context: dict[str, Any] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    proposal, _coverage = build_proposal_with_coverage(
        trace_export,
        outcomes,
        surface,
        agent_manifest=agent_manifest,
        domain_context=domain_context,
        created_at=created_at,
    )
    return proposal


def render_proposal_pr_checklist(proposal: dict[str, Any]) -> str:
    target = proposal.get("proposed_change", {}).get("target", {})
    validation = proposal.get("validation", {})
    criteria = _normalized_acceptance_criteria(validation.get("acceptance_criteria", []))
    checks_by_criterion = _checks_by_criterion(criteria, validation.get("checks", []))

    lines = [
        f"# {proposal.get('title', 'Agent change proposal')}",
        "",
        f"- Proposal: `{proposal.get('proposal_id', 'unknown')}`",
        f"- Status: `{proposal.get('status', 'unknown')}`",
        f"- Target: `{target.get('target_id', 'unknown')}` ({target.get('type', 'unknown')})",
    ]
    if proposal.get("created_at"):
        lines.append(f"- Created: `{proposal['created_at']}`")
    outcome = validation.get("outcome")
    if outcome:
        lines.append(f"- Validation outcome: `{outcome}`")

    _add_section(lines, "Problem", proposal.get("problem", {}).get("summary"))
    _add_section(lines, "Hypothesis", proposal.get("hypothesis", {}).get("summary"))
    _add_section(lines, "Proposed Change", proposal.get("proposed_change", {}).get("summary"))

    if criteria:
        lines.extend(["", "## Acceptance Criteria"])
        for criterion in criteria:
            criterion_id = criterion["id"]
            description = criterion["description"]
            lines.append(f"- [ ] `{criterion_id}` {description}")
            for check in checks_by_criterion.get(criterion_id, []):
                lines.append(f"  - `{_render_check(check)}`")

    unmatched_checks = checks_by_criterion.get("", [])
    if unmatched_checks:
        lines.extend(["", "## Additional Validation Checks"])
        for check in unmatched_checks:
            lines.append(f"- [ ] `{_render_check(check)}`")

    verdict_diff = validation.get("verdict_diff")
    if isinstance(verdict_diff, dict):
        lines.extend(
            [
                "",
                "## Verdict Diff",
                f"- Pass to fail: `{verdict_diff.get('pass_to_fail', 'unknown')}`",
                f"- Fail to pass: `{verdict_diff.get('fail_to_pass', 'unknown')}`",
                f"- Unchanged pass: `{verdict_diff.get('unchanged_pass', 'unknown')}`",
                f"- Unchanged fail: `{verdict_diff.get('unchanged_fail', 'unknown')}`",
            ]
        )

    evidence = proposal.get("evidence", [])
    if evidence:
        lines.extend(["", "## Evidence"])
        for item in evidence:
            lines.append(f"- {_render_evidence(item)}")

    risk = proposal.get("risk", {})
    if risk:
        lines.extend(["", "## Risk"])
        if risk.get("level"):
            lines.append(f"- Level: `{risk['level']}`")
        if risk.get("notes"):
            lines.append(f"- Notes: {risk['notes']}")

    rollback = proposal.get("rollback", {})
    if rollback:
        lines.extend(["", "## Rollback"])
        if rollback.get("plan"):
            lines.append(f"- Plan: {rollback['plan']}")
        if rollback.get("trigger_ref"):
            lines.append(f"- Trigger: `{rollback['trigger_ref']}`")

    return "\n".join(lines).rstrip() + "\n"


def build_proposal_with_coverage(
    trace_export: dict[str, Any],
    outcomes: list[dict[str, Any]],
    surface: dict[str, Any],
    agent_manifest: dict[str, Any] | None = None,
    domain_context: dict[str, Any] | None = None,
    created_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    created_at = created_at or datetime.now(timezone.utc).isoformat()
    failures = {event["run_id"]: event for event in outcomes if event.get("label") == "failure"}
    runs_by_id = {run.get("run_id"): run for run in trace_export.get("runs", []) if run.get("run_id")}
    tool_misuse = [
        run for run in trace_export.get("runs", [])
        if run.get("run_id") in failures and _looks_like_tool_misuse(run, failures[run["run_id"]])
    ]
    detector_matches: dict[str, list[dict[str, Any]]] = {"tool_misuse": tool_misuse}
    if tool_misuse:
        proposal = _tool_misuse_proposal(tool_misuse[0], failures[tool_misuse[0]["run_id"]], surface, created_at)
        _apply_declared_context(proposal, agent_manifest, domain_context)
        return proposal, _coverage_report(trace_export, outcomes, runs_by_id, proposal, detector_matches)

    missing_escalation = [
        run for run in trace_export.get("runs", [])
        if run.get("run_id") in failures and _looks_like_missing_escalation(run, failures[run["run_id"]])
    ]
    detector_matches["missing_escalation"] = missing_escalation
    if missing_escalation:
        proposal = _missing_escalation_proposal(
            missing_escalation[0], failures[missing_escalation[0]["run_id"]], surface, created_at
        )
        _apply_declared_context(proposal, agent_manifest, domain_context)
        return proposal, _coverage_report(trace_export, outcomes, runs_by_id, proposal, detector_matches)

    missed_retrieval = [
        run for run in trace_export.get("runs", [])
        if run.get("run_id") in failures and _looks_like_missed_retrieval(run)
    ]
    detector_matches["missed_retrieval"] = missed_retrieval
    if missed_retrieval:
        proposal = _missed_retrieval_proposal(
            missed_retrieval[0], failures[missed_retrieval[0]["run_id"]], surface, created_at
        )
        _apply_declared_context(proposal, agent_manifest, domain_context)
        return proposal, _coverage_report(trace_export, outcomes, runs_by_id, proposal, detector_matches)

    proposal = _no_pattern_proposal(trace_export, outcomes, surface, created_at)
    _apply_declared_context(proposal, agent_manifest, domain_context)
    return proposal, _coverage_report(trace_export, outcomes, runs_by_id, proposal, detector_matches)


def _add_section(lines: list[str], heading: str, text: str | None) -> None:
    if text:
        lines.extend(["", f"## {heading}", text])


def _normalized_acceptance_criteria(items: list[Any]) -> list[dict[str, str]]:
    criteria = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            criterion_id = str(item.get("id") or f"criterion-{index}")
            description = str(item.get("description") or "")
        else:
            criterion_id = f"criterion-{index}"
            description = str(item)
        criteria.append({"id": criterion_id, "description": description})
    return criteria


def _checks_by_criterion(criteria: list[dict[str, str]], checks: list[Any]) -> dict[str, list[dict[str, Any]]]:
    criterion_ids = {criterion["id"] for criterion in criteria}
    grouped = {criterion_id: [] for criterion_id in criterion_ids}
    grouped[""] = []
    for check in checks:
        if not isinstance(check, dict):
            continue
        refs = [ref for ref in check.get("criterion_refs", []) if ref in criterion_ids]
        if not refs:
            grouped[""].append(check)
            continue
        for ref in refs:
            grouped[ref].append(check)
    return grouped


def _render_check(check: dict[str, Any]) -> str:
    role = check.get("role", "check")
    suite = check.get("suite", "suite")
    metric = check.get("metric", "metric")
    op = check.get("op", "?")
    value = check.get("value", "unknown")
    parts = [f"{role}: {suite} {metric} {op} {_markdown_value(value)}"]
    if check.get("min_cases") is not None:
        parts.append(f"min_cases={check['min_cases']}")
    if check.get("trace_set_ref"):
        parts.append(f"trace_set={check['trace_set_ref']}")
    if check.get("evidence_refs"):
        parts.append("evidence=" + ", ".join(str(ref) for ref in check["evidence_refs"]))
    return "; ".join(parts)


def _render_evidence(item: dict[str, Any]) -> str:
    evidence_type = item.get("type", "evidence")
    evidence_ref = item.get("evidence_ref")
    immutable_ref = item.get("immutable_ref")
    run_id = item.get("run_id")

    parts = [f"`{evidence_type}`"]
    if evidence_ref:
        parts.append(f"`{evidence_ref}`")
    if run_id:
        parts.append(f"run `{run_id}`")
    if immutable_ref:
        parts.append(f"immutable `{immutable_ref}`")

    observed = item.get("observed")
    if observed:
        parts.append(str(observed))
    return " - ".join(parts)


def _markdown_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    return str(value)


def _coverage_report(
    trace_export: dict[str, Any],
    outcomes: list[dict[str, Any]],
    runs_by_id: dict[str, dict[str, Any]],
    proposal: dict[str, Any],
    detector_matches: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    failed_run_ids = [event["run_id"] for event in outcomes if event.get("label") == "failure"]
    matched_failed_run_ids = sorted(run_id for run_id in failed_run_ids if run_id in runs_by_id)
    detector_match_run_ids = {
        name: sorted(run["run_id"] for run in matches if run.get("run_id"))
        for name, matches in detector_matches.items()
    }
    selected_run_id = proposal.get("problem", {}).get("run_id")
    matched_by_any_detector = set().union(*[set(run_ids) for run_ids in detector_match_run_ids.values()])

    return {
        "schema_version": "0.1",
        "summary": {
            "runs": len(trace_export.get("runs", [])),
            "outcomes": len(outcomes),
            "failed_outcomes": len(failed_run_ids),
            "failed_outcomes_with_trace": len(matched_failed_run_ids),
            "detector_matches": sum(len(run_ids) for run_ids in detector_match_run_ids.values()),
        },
        "failed_run_ids": failed_run_ids,
        "failed_run_ids_missing_trace": sorted(run_id for run_id in failed_run_ids if run_id not in runs_by_id),
        "failed_run_ids_without_detector_match": sorted(set(matched_failed_run_ids) - matched_by_any_detector),
        "detector_matches": detector_match_run_ids,
        "selected_proposal": {
            "proposal_id": proposal.get("proposal_id"),
            "title": proposal.get("title"),
            "run_id": selected_run_id,
            "target_id": proposal.get("proposed_change", {}).get("target", {}).get("target_id"),
        },
    }


def _apply_declared_context(
    proposal: dict[str, Any],
    agent_manifest: dict[str, Any] | None,
    domain_context: dict[str, Any] | None,
) -> None:
    if agent_manifest:
        _apply_agent_manifest(proposal, agent_manifest)
    if domain_context:
        _apply_domain_context(proposal, domain_context)


def _apply_agent_manifest(proposal: dict[str, Any], agent_manifest: dict[str, Any]) -> None:
    target = proposal.get("proposed_change", {}).get("target", {})
    target_component = target.get("component")
    if not target_component:
        return

    component = next(
        (
            item
            for item in agent_manifest.get("components", [])
            if item.get("component_id") == target_component
        ),
        None,
    )
    if not component:
        return

    target["declared_component"] = {
        "component_id": component.get("component_id"),
        "type": component.get("type"),
        "description": component.get("description"),
    }
    proposal.setdefault("evidence", []).append(
        {
            "type": "agent_manifest",
            "component_id": component.get("component_id"),
            "component_type": component.get("type"),
            "declared_role": component.get("description"),
        }
    )


def _apply_domain_context(proposal: dict[str, Any], domain_context: dict[str, Any]) -> None:
    dimensions = _proposal_outcome_dimensions(proposal)
    if not dimensions:
        return

    success_dimensions = {
        item.get("dimension_id"): item
        for item in domain_context.get("success_dimensions", [])
        if item.get("dimension_id")
    }
    matched_dimensions = [
        success_dimensions[dimension_id]
        for dimension_id in dimensions
        if dimension_id in success_dimensions
    ]
    matched_policies = [
        policy
        for policy in domain_context.get("policies", [])
        if set(policy.get("applies_to_dimensions", [])) & set(dimensions)
    ]
    if not matched_dimensions and not matched_policies:
        return

    proposal.setdefault("evidence", []).append(
        {
            "type": "domain_context",
            "matched_success_dimensions": [
                {
                    "dimension_id": item.get("dimension_id"),
                    "name": item.get("name"),
                    "failure_definition": item.get("failure_definition"),
                }
                for item in matched_dimensions
            ],
            "matched_policies": [
                {
                    "policy_id": item.get("policy_id"),
                    "name": item.get("name"),
                    "description": item.get("description"),
                }
                for item in matched_policies
            ],
        }
    )

    criteria = proposal.setdefault("validation", {}).setdefault("acceptance_criteria", [])
    for item in matched_dimensions:
        name = item.get("name") or item.get("dimension_id")
        criteria.append(f"Candidate satisfies declared success dimension: {name}.")


def _proposal_outcome_dimensions(proposal: dict[str, Any]) -> list[str]:
    dimensions: list[str] = []
    for evidence in proposal.get("evidence", []):
        if evidence.get("type") != "outcome_event":
            continue
        for dimension in evidence.get("dimensions", []):
            if dimension not in dimensions:
                dimensions.append(dimension)
    return dimensions


def _missed_retrieval_proposal(
    run: dict[str, Any], outcome: dict[str, Any], surface: dict[str, Any], created_at: str
) -> dict[str, Any]:
    target = _select_target(surface, {"routing_rule", "retrieval_policy"})
    proposal_id = _stable_id(run["run_id"], target.get("target_id", "unknown"))

    return {
        "schema_version": "0.1",
        "proposal_id": proposal_id,
        "title": "Require retrieval for context-dependent questions",
        "status": "proposed",
        "created_at": created_at,
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
            "summary": (
                "The routing or retrieval policy is not requiring retrieval when the user asks for policy, "
                "historical, or source-grounded information."
            ),
            "confidence": "medium",
            "limits": "This is a hypothesis from trace structure and outcome labels, not a causal proof.",
        },
        "proposed_change": {
            "target": target,
            "summary": (
                "Update the target so context-dependent questions trigger retrieval before final response generation."
            ),
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


def _tool_misuse_proposal(
    run: dict[str, Any], outcome: dict[str, Any], surface: dict[str, Any], created_at: str
) -> dict[str, Any]:
    target = _select_target(surface, {"tool_policy", "routing_rule"})
    tool_span = next((span for span in run.get("spans", []) if _is_tool_span(span)), {})
    proposal_id = _stable_id(run["run_id"], target.get("target_id", "unknown"))

    return {
        "schema_version": "0.1",
        "proposal_id": proposal_id,
        "title": "Review tool-selection policy for failed tool use",
        "status": "proposed",
        "created_at": created_at,
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
            "summary": (
                "The tool-selection policy may be routing this class of request to the wrong tool or with "
                "insufficient preconditions."
            ),
            "confidence": "medium",
            "limits": (
                "This proposal relies on tool span metadata and outcome labels; it should be validated with "
                "targeted replay cases."
            ),
        },
        "proposed_change": {
            "target": target,
            "summary": "Tighten tool-selection criteria or add a precondition check before invoking the affected tool.",
            "suggested_patch": {
                "add_precondition": (
                    "Only call the tool when required input fields are present and match the task intent."
                ),
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


def _missing_escalation_proposal(
    run: dict[str, Any], outcome: dict[str, Any], surface: dict[str, Any], created_at: str
) -> dict[str, Any]:
    target = _select_target(surface, {"guardrail_threshold", "routing_rule"})
    proposal_id = _stable_id(run["run_id"], target.get("target_id", "unknown"))

    return {
        "schema_version": "0.1",
        "proposal_id": proposal_id,
        "title": "Add escalation for high-risk uncertain responses",
        "status": "proposed",
        "created_at": created_at,
        "agent_ref": surface.get("agent_ref", {}),
        "problem": {
            "summary": (
                "A failed run appears to require escalation or guardrail handling, but no escalation span was observed."
            ),
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
                "observed": (
                    "Outcome dimensions indicate escalation or guardrail failure, but no escalation/handoff/"
                    "guardrail span was found."
                ),
                "span_count": len(run.get("spans", [])),
            },
        ],
        "hypothesis": {
            "summary": (
                "The escalation threshold or guardrail policy may be too permissive for high-risk uncertain answers."
            ),
            "confidence": "medium",
            "limits": "This identifies a reviewable safety hypothesis, not proof that escalation is always correct.",
        },
        "proposed_change": {
            "target": target,
            "summary": (
                "Escalate when uncertainty is high and the answer concerns protected, high-risk, or "
                "policy-sensitive decisions."
            ),
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
    digest = hashlib.sha256(f"{run_id}:{target_id}".encode()).hexdigest()[:12]
    return f"acp_{digest}"


def _no_pattern_proposal(
    trace_export: dict[str, Any], outcomes: list[dict[str, Any]], surface: dict[str, Any], created_at: str
) -> dict[str, Any]:
    digest = hashlib.sha256(str(trace_export).encode("utf-8")).hexdigest()[:12]
    return {
        "schema_version": "0.1",
        "proposal_id": f"acp_{digest}",
        "title": "No specific improvement pattern detected",
        "status": "proposed",
        "created_at": created_at,
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
