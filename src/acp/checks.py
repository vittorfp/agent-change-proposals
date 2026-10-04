from __future__ import annotations

from typing import Any

from acp.proposals import build_proposal_with_coverage


def check_bundle(
    trace_export: dict[str, Any],
    outcomes: list[dict[str, Any]],
    surface: dict[str, Any],
    baseline: dict[str, Any] | None = None,
    candidate: dict[str, Any] | None = None,
    proposal: dict[str, Any] | None = None,
    agent_manifest: dict[str, Any] | None = None,
    domain_context: dict[str, Any] | None = None,
    import_diagnostics: dict[str, Any] | None = None,
    proposal_coverage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    runs = trace_export.get("runs", [])
    run_ids = {run.get("run_id") for run in runs if run.get("run_id")}
    target_ids = {
        target.get("target_id")
        for target in surface.get("allowed_targets", [])
        if target.get("target_id")
    }

    if not runs:
        _add(errors, "trace.empty", "Trace export has no runs.")

    for event in outcomes:
        run_id = event.get("run_id")
        if run_id and run_id not in run_ids:
            _add(errors, "outcome.missing_trace", f"Outcome references unknown run_id: {run_id}.")

    if not surface.get("allowed_targets"):
        _add(errors, "surface.empty_targets", "Improvement surface has no allowed targets.")

    for run in runs:
        for span in run.get("spans", []):
            if not span.get("kind") and not span.get("name"):
                span_id = span.get("span_id") or "unknown"
                run_id = run.get("run_id") or "unknown"
                _add(warnings, "span.missing_kind_or_name", f"Span {span_id} in run {run_id} has no kind or name.")

    _check_replay(errors, warnings, baseline, candidate)

    if import_diagnostics:
        _check_import_diagnostics(warnings, import_diagnostics)

    generated_proposal, generated_coverage = build_proposal_with_coverage(
        trace_export,
        outcomes,
        surface,
        agent_manifest=agent_manifest,
        domain_context=domain_context,
    )
    if proposal is not None:
        generated_proposal = proposal
    coverage = proposal_coverage or generated_coverage
    _check_proposal_coverage(warnings, coverage)
    _check_proposal(errors, warnings, generated_proposal, target_ids)

    return {
        "schema_version": "0.1",
        "status": "failed" if errors else "passed",
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
            "runs": len(runs),
            "outcomes": len(outcomes),
            "allowed_targets": len(surface.get("allowed_targets", [])),
        },
        "errors": errors,
        "warnings": warnings,
        "proposal_coverage": coverage,
    }


def _check_import_diagnostics(warnings: list[dict[str, str]], diagnostics: dict[str, Any]) -> None:
    skipped_records = diagnostics.get("summary", {}).get("skipped_records", 0)
    if skipped_records:
        _add(
            warnings,
            "import.skipped_records",
            f"Importer skipped {skipped_records} records; inspect import diagnostics for reasons.",
        )


def _check_proposal_coverage(warnings: list[dict[str, str]], coverage: dict[str, Any]) -> None:
    missing_trace = coverage.get("failed_run_ids_missing_trace", [])
    if missing_trace:
        _add(
            warnings,
            "coverage.failed_outcomes_missing_trace",
            "Failed outcomes missing trace coverage: " + ", ".join(missing_trace),
        )

    unmatched = coverage.get("failed_run_ids_without_detector_match", [])
    if unmatched:
        _add(
            warnings,
            "coverage.failed_outcomes_unmatched",
            "Failed traced runs without detector matches: " + ", ".join(unmatched),
        )


def _check_replay(
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
    baseline: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
) -> None:
    if baseline is None and candidate is None:
        return
    if baseline is None or candidate is None:
        _add(errors, "replay.incomplete", "Replay checking requires both baseline and candidate bundles.")
        return

    baseline_suite = baseline.get("suite_id")
    candidate_suite = candidate.get("suite_id")
    if baseline_suite != candidate_suite:
        _add(errors, "replay.suite_mismatch", "Baseline and candidate replay bundles have different suite_id values.")

    baseline_case_ids = {case.get("case_id") for case in baseline.get("cases", []) if case.get("case_id")}
    candidate_case_ids = {case.get("case_id") for case in candidate.get("cases", []) if case.get("case_id")}
    shared_case_ids = baseline_case_ids & candidate_case_ids
    missing_candidate = sorted(baseline_case_ids - candidate_case_ids)
    extra_candidate = sorted(candidate_case_ids - baseline_case_ids)

    if not shared_case_ids:
        _add(errors, "replay.no_shared_cases", "Baseline and candidate replay bundles have no shared cases.")
    if missing_candidate:
        _add(
            errors,
            "replay.candidate_missing_cases",
            "Candidate replay bundle is missing baseline cases: " + ", ".join(missing_candidate),
        )
    if extra_candidate:
        _add(
            warnings,
            "replay.candidate_extra_cases",
            "Candidate replay bundle has cases not present in baseline: " + ", ".join(extra_candidate),
        )


def _check_proposal(
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
    proposal: dict[str, Any],
    target_ids: set[str],
) -> None:
    target_id = proposal.get("proposed_change", {}).get("target", {}).get("target_id")
    proposed_change_summary = proposal.get("proposed_change", {}).get("summary")
    is_no_change = target_id in {None, "none"} or proposed_change_summary == "No change proposed."

    if target_id and not is_no_change and target_id not in target_ids:
        _add(errors, "proposal.target_not_allowed", f"Proposal target is not declared in surface: {target_id}.")

    if proposal.get("status") == "proposed" and not is_no_change and not proposal.get("evidence"):
        _add(errors, "proposal.empty_evidence", "Proposed behavior change has no evidence entries.")

    if proposal.get("title") == "No specific improvement pattern detected":
        _add(
            warnings,
            "proposal.no_supported_pattern",
            "Generated proposal did not match a supported V0 improvement pattern.",
        )


def _add(collection: list[dict[str, str]], code: str, message: str) -> None:
    collection.append({"code": code, "message": message})
