from __future__ import annotations

from typing import Any


def compare_replay_results(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    baseline_cases = {case["case_id"]: case for case in baseline.get("cases", [])}
    candidate_cases = {case["case_id"]: case for case in candidate.get("cases", [])}
    shared_case_ids = sorted(set(baseline_cases) & set(candidate_cases))

    case_reports = [
        _compare_case(case_id, baseline_cases[case_id], candidate_cases[case_id])
        for case_id in shared_case_ids
    ]

    improved = sum(1 for report in case_reports if report["status"] == "improved")
    regressed = sum(1 for report in case_reports if report["status"] == "regressed")
    unchanged = sum(1 for report in case_reports if report["status"] == "unchanged")

    return {
        "schema_version": "0.1",
        "suite_id": candidate.get("suite_id") or baseline.get("suite_id"),
        "summary": {
            "shared_cases": len(shared_case_ids),
            "improved": improved,
            "regressed": regressed,
            "unchanged": unchanged,
            "verdict": _verdict(improved, regressed),
        },
        "cases": case_reports,
    }


def _compare_case(case_id: str, baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    baseline_passed = bool(baseline.get("passed"))
    candidate_passed = bool(candidate.get("passed"))
    if candidate_passed and not baseline_passed:
        status = "improved"
    elif baseline_passed and not candidate_passed:
        status = "regressed"
    else:
        status = "unchanged"

    return {
        "case_id": case_id,
        "status": status,
        "baseline": {
            "passed": baseline_passed,
            "metrics": baseline.get("metrics", {}),
        },
        "candidate": {
            "passed": candidate_passed,
            "metrics": candidate.get("metrics", {}),
        },
    }


def _verdict(improved: int, regressed: int) -> str:
    if regressed:
        return "reject"
    if improved:
        return "accept"
    return "neutral"
