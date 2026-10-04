from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import validate

from acp.importers import langfuse_observations_to_trace_export, openinference_to_trace_export
from acp.io import load_data
from acp.proposals import build_proposal
from acp.replay import compare_replay_results
from acp.schemas import SCHEMAS

FIXED_EXAMPLE_CREATED_AT = "2026-10-02T00:00:00+00:00"


def verify_examples(examples_root: str | Path) -> list[dict[str, Any]]:
    root = Path(examples_root)
    if not root.exists():
        raise FileNotFoundError(f"examples root not found: {root}")

    reports = []
    for example_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        reports.append(_verify_example(example_dir))
    return reports


def _verify_example(example_dir: Path) -> dict[str, Any]:
    trace_export = _load_trace_export(example_dir)
    outcomes = load_data(example_dir / "outcomes.json")
    surface = load_data(example_dir / "improvement_surface.json")
    checked_in_proposal = load_data(example_dir / "change_proposal.example.json")
    agent_manifest = _load_optional(example_dir / "agent_manifest.json")
    domain_context = _load_optional(example_dir / "domain_context.json")

    validate(instance=trace_export, schema=SCHEMAS["trace_export"])
    validate(instance=outcomes, schema=SCHEMAS["outcome_events"])
    validate(instance=surface, schema=SCHEMAS["improvement_surface"])
    if agent_manifest is not None:
        validate(instance=agent_manifest, schema=SCHEMAS["agent_manifest"])
    if domain_context is not None:
        validate(instance=domain_context, schema=SCHEMAS["domain_context"])
    validate(instance=checked_in_proposal, schema=SCHEMAS["change_proposal"])

    generated_proposal = build_proposal(
        trace_export,
        outcomes,
        surface,
        agent_manifest=agent_manifest,
        domain_context=domain_context,
        created_at=FIXED_EXAMPLE_CREATED_AT,
    )
    validate(instance=generated_proposal, schema=SCHEMAS["change_proposal"])
    if generated_proposal != checked_in_proposal:
        raise ValueError(f"checked-in proposal is stale for example: {example_dir.name}")

    report: dict[str, Any] = {
        "example": example_dir.name,
        "proposal_id": generated_proposal["proposal_id"],
        "title": generated_proposal["title"],
        "proposal": "valid",
    }

    baseline_path = example_dir / "replay_baseline.json"
    candidate_path = example_dir / "replay_candidate.json"
    if baseline_path.exists() or candidate_path.exists():
        if not baseline_path.exists() or not candidate_path.exists():
            raise ValueError(f"incomplete replay bundle pair for example: {example_dir.name}")
        baseline = load_data(baseline_path)
        candidate = load_data(candidate_path)
        validate(instance=baseline, schema=SCHEMAS["replay_bundle"])
        validate(instance=candidate, schema=SCHEMAS["replay_bundle"])
        replay_report = compare_replay_results(baseline, candidate)
        report["replay_verdict"] = replay_report["summary"]["verdict"]

    return report


def _load_trace_export(example_dir: Path) -> dict[str, Any]:
    trace_path = example_dir / "traces.json"
    if trace_path.exists():
        return load_data(trace_path)

    openinference_path = example_dir / "traces.openinference.json"
    if openinference_path.exists():
        return openinference_to_trace_export(load_data(openinference_path))

    langfuse_path = example_dir / "observations.langfuse.json"
    if langfuse_path.exists():
        return langfuse_observations_to_trace_export(load_data(langfuse_path))

    raise FileNotFoundError(f"no supported trace fixture found for example: {example_dir.name}")


def _load_optional(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_data(path)
