from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

from acp.cli import main
from acp.examples import verify_examples
from acp.importers import langfuse_observations_to_trace_export, openinference_to_trace_export
from acp.proposals import build_proposal
from acp.schemas import CHANGE_PROPOSAL_SCHEMA, SCHEMAS

EXAMPLES = [
    ("rag-missed-retrieval", "Require retrieval for context-dependent questions"),
    ("tool-misuse", "Review tool-selection policy for failed tool use"),
    ("missing-escalation", "Add escalation for high-risk uncertain responses"),
]


def test_proposal_from_trace(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "proposal.json"

    result = main(
        [
            "proposal",
            "from-trace",
            str(root / "examples/rag-missed-retrieval/traces.json"),
            "--outcomes",
            str(root / "examples/rag-missed-retrieval/outcomes.json"),
            "--surface",
            str(root / "examples/rag-missed-retrieval/improvement_surface.json"),
            "--output",
            str(output),
            "--created-at",
            "2026-10-02T00:00:00+00:00",
        ]
    )

    assert result == 0
    proposal = json.loads(output.read_text(encoding="utf-8"))
    validate(instance=proposal, schema=CHANGE_PROPOSAL_SCHEMA)
    assert proposal["status"] == "proposed"
    assert proposal["created_at"] == "2026-10-02T00:00:00+00:00"
    assert proposal["proposed_change"]["target"]["target_id"] == "retrieval_policy.main"
    assert "retrieval" in proposal["title"].lower()


def test_validate_example_surface() -> None:
    root = Path(__file__).resolve().parents[1]
    result = main(
        [
            "validate",
            "improvement_surface",
            str(root / "examples/rag-missed-retrieval/improvement_surface.json"),
        ]
    )
    assert result == 0


def test_replay_compare(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "replay_report.json"

    result = main(
        [
            "replay",
            "compare",
            str(root / "examples/rag-missed-retrieval/replay_baseline.json"),
            str(root / "examples/rag-missed-retrieval/replay_candidate.json"),
            "--output",
            str(output),
        ]
    )

    assert result == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"]["verdict"] == "accept"
    assert report["summary"]["improved"] == 1


def test_validate_example_replay_bundle() -> None:
    root = Path(__file__).resolve().parents[1]
    result = main(
        [
            "validate",
            "replay_bundle",
            str(root / "examples/rag-missed-retrieval/replay_baseline.json"),
        ]
    )
    assert result == 0


def test_examples_verify_command() -> None:
    assert main(["examples", "verify"]) == 0


def test_verify_examples_reports_all_examples() -> None:
    reports = verify_examples(Path(__file__).resolve().parents[1] / "examples")

    assert {report["example"] for report in reports} == {
        "declared-intent",
        "langfuse-export",
        "missing-escalation",
        "openinference-phoenix",
        "rag-missed-retrieval",
        "tool-misuse",
    }


def test_schema_list_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["schema", "list"]) == 0
    output = capsys.readouterr().out
    assert "agent_manifest" in output
    assert "change_proposal" in output
    assert "domain_context" in output
    assert "trace_export" in output


def test_schema_export_command(tmp_path: Path) -> None:
    output = tmp_path / "schema.json"

    assert main(["schema", "export", "change_proposal", "--output", str(output)]) == 0

    schema = json.loads(output.read_text(encoding="utf-8"))
    assert schema["title"] == "Agent Change Proposal"


def test_change_proposal_schema_rejects_underspecified_nested_sections() -> None:
    sparse_proposal = {
        "schema_version": "0.1",
        "proposal_id": "acp_sparse",
        "title": "Sparse proposal",
        "status": "proposed",
        "problem": {},
        "evidence": [{}],
        "hypothesis": {},
        "proposed_change": {},
        "validation": {},
        "risk": {},
        "rollback": {},
    }

    with pytest.raises(ValidationError):
        validate(instance=sparse_proposal, schema=CHANGE_PROPOSAL_SCHEMA)


def test_validate_rejects_dangling_validation_check_refs(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    proposal = {
        "schema_version": "0.6-draft",
        "proposal_id": "acp_dangling_ref",
        "title": "Reject dangling validation refs",
        "status": "proposed",
        "problem": {"summary": "A check points at a missing criterion."},
        "evidence": [{"type": "trace_pattern", "observed": "Example evidence."}],
        "hypothesis": {"summary": "The check is orphaned.", "confidence": "high"},
        "proposed_change": {
            "target": {
                "target_id": "retrieval_policy.main",
                "type": "retrieval_policy",
                "component": "main_retriever",
            },
            "summary": "No-op for validation test.",
        },
        "validation": {
            "method": "controlled_replay",
            "acceptance_criteria": [
                {"id": "existing-criterion", "description": "Existing criterion."}
            ],
            "checks": [
                {
                    "criterion_refs": ["missing-criterion"],
                    "metric": "retrieval_called",
                    "op": "==",
                    "value": True,
                }
            ],
        },
        "risk": {"level": "low", "notes": "Validation-only fixture."},
        "rollback": {"plan": "No-op."},
    }
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    result = main(["validate", "change_proposal", str(proposal_path)])

    assert result == 1
    assert "unknown criterion_refs: missing-criterion" in capsys.readouterr().err


def test_validate_accepts_structured_validation_checks(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    proposal_path = root / "rfcs" / "examples" / "pr-ready.change_proposal.example.json"

    assert main(["validate", "change_proposal", str(proposal_path)]) == 0


def test_declared_intent_contracts_are_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    example = root / "examples/declared-intent"

    agent_manifest = json.loads((example / "agent_manifest.json").read_text(encoding="utf-8"))
    domain_context = json.loads((example / "domain_context.json").read_text(encoding="utf-8"))

    validate(instance=agent_manifest, schema=SCHEMAS["agent_manifest"])
    validate(instance=domain_context, schema=SCHEMAS["domain_context"])


def test_bundle_check_accepts_example(capsys: pytest.CaptureFixture[str]) -> None:
    root = Path(__file__).resolve().parents[1]

    result = main(
        [
            "bundle",
            "check",
            "--trace",
            str(root / "examples/rag-missed-retrieval/traces.json"),
            "--outcomes",
            str(root / "examples/rag-missed-retrieval/outcomes.json"),
            "--surface",
            str(root / "examples/rag-missed-retrieval/improvement_surface.json"),
            "--baseline",
            str(root / "examples/rag-missed-retrieval/replay_baseline.json"),
            "--candidate",
            str(root / "examples/rag-missed-retrieval/replay_candidate.json"),
        ]
    )

    assert result == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "passed"
    assert report["summary"]["errors"] == 0


def test_bundle_check_reports_missing_outcome_trace(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    outcomes_path = tmp_path / "outcomes.json"
    outcomes_path.write_text(
        json.dumps(
            [
                {
                    "run_id": "missing_run",
                    "timestamp": "2026-10-01T17:00:00Z",
                    "source": "human_review",
                    "label": "failure",
                    "confidence": 0.9,
                }
            ]
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "bundle",
            "check",
            "--trace",
            str(root / "examples/rag-missed-retrieval/traces.json"),
            "--outcomes",
            str(outcomes_path),
            "--surface",
            str(root / "examples/rag-missed-retrieval/improvement_surface.json"),
        ]
    )

    assert result == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "failed"
    assert {error["code"] for error in report["errors"]} == {"outcome.missing_trace"}


def test_bundle_check_reports_replay_case_mismatch(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(
        json.dumps(
            {
                "suite_id": "rag-regression-v0",
                "cases": [{"case_id": "different_case", "passed": True}],
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "bundle",
            "check",
            "--trace",
            str(root / "examples/rag-missed-retrieval/traces.json"),
            "--outcomes",
            str(root / "examples/rag-missed-retrieval/outcomes.json"),
            "--surface",
            str(root / "examples/rag-missed-retrieval/improvement_surface.json"),
            "--baseline",
            str(root / "examples/rag-missed-retrieval/replay_baseline.json"),
            "--candidate",
            str(candidate_path),
        ]
    )

    assert result == 1
    report = json.loads(capsys.readouterr().out)
    assert "replay.no_shared_cases" in {error["code"] for error in report["errors"]}
    assert "replay.candidate_missing_cases" in {error["code"] for error in report["errors"]}


def test_proposal_from_trace_can_write_coverage_report(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    proposal_output = tmp_path / "proposal.json"
    coverage_output = tmp_path / "coverage.json"

    result = main(
        [
            "proposal",
            "from-trace",
            str(root / "examples/rag-missed-retrieval/traces.json"),
            "--outcomes",
            str(root / "examples/rag-missed-retrieval/outcomes.json"),
            "--surface",
            str(root / "examples/rag-missed-retrieval/improvement_surface.json"),
            "--output",
            str(proposal_output),
            "--coverage-output",
            str(coverage_output),
        ]
    )

    assert result == 0
    coverage = json.loads(coverage_output.read_text(encoding="utf-8"))
    assert coverage["summary"]["failed_outcomes"] == 1
    assert coverage["summary"]["failed_outcomes_with_trace"] == 1
    assert coverage["detector_matches"]["missed_retrieval"] == ["run_rag_001"]
    assert coverage["selected_proposal"]["target_id"] == "retrieval_policy.main"


def test_proposal_from_trace_uses_declared_intent(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    example = root / "examples/declared-intent"
    proposal_output = tmp_path / "proposal.json"

    result = main(
        [
            "proposal",
            "from-trace",
            str(example / "traces.json"),
            "--outcomes",
            str(example / "outcomes.json"),
            "--surface",
            str(example / "improvement_surface.json"),
            "--agent-manifest",
            str(example / "agent_manifest.json"),
            "--domain-context",
            str(example / "domain_context.json"),
            "--output",
            str(proposal_output),
            "--created-at",
            "2026-10-02T00:00:00+00:00",
        ]
    )

    assert result == 0
    proposal = json.loads(proposal_output.read_text(encoding="utf-8"))
    evidence_types = {item["type"] for item in proposal["evidence"]}
    assert {"agent_manifest", "domain_context"}.issubset(evidence_types)
    assert proposal["proposed_change"]["target"]["declared_component"]["component_id"] == "main_retriever"
    assert "Candidate satisfies declared success dimension: Groundedness." in proposal["validation"][
        "acceptance_criteria"
    ]


def test_bundle_check_can_include_proposal_coverage_file(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    root = Path(__file__).resolve().parents[1]
    proposal_output = tmp_path / "proposal.json"
    coverage_output = tmp_path / "coverage.json"

    assert main(
        [
            "proposal",
            "from-trace",
            str(root / "examples/rag-missed-retrieval/traces.json"),
            "--outcomes",
            str(root / "examples/rag-missed-retrieval/outcomes.json"),
            "--surface",
            str(root / "examples/rag-missed-retrieval/improvement_surface.json"),
            "--output",
            str(proposal_output),
            "--coverage-output",
            str(coverage_output),
        ]
    ) == 0
    capsys.readouterr()

    assert main(
        [
            "bundle",
            "check",
            "--trace",
            str(root / "examples/rag-missed-retrieval/traces.json"),
            "--outcomes",
            str(root / "examples/rag-missed-retrieval/outcomes.json"),
            "--surface",
            str(root / "examples/rag-missed-retrieval/improvement_surface.json"),
            "--proposal",
            str(proposal_output),
            "--proposal-coverage",
            str(coverage_output),
        ]
    ) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["proposal_coverage"]["selected_proposal"]["proposal_id"]
    assert report["summary"]["warnings"] == 0


def test_bundle_check_warns_from_import_diagnostics(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    diagnostics_path = tmp_path / "diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "source": "openinference",
                "summary": {
                    "input_records": 2,
                    "output_runs": 1,
                    "output_spans": 1,
                    "skipped_records": 1,
                    "warnings": 0,
                },
                "skipped_records": [{"reason": "missing_run_id", "count": 1}],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "bundle",
            "check",
            "--trace",
            str(root / "examples/rag-missed-retrieval/traces.json"),
            "--outcomes",
            str(root / "examples/rag-missed-retrieval/outcomes.json"),
            "--surface",
            str(root / "examples/rag-missed-retrieval/improvement_surface.json"),
            "--import-diagnostics",
            str(diagnostics_path),
        ]
    )

    assert result == 0
    report = json.loads(capsys.readouterr().out)
    assert "import.skipped_records" in {warning["code"] for warning in report["warnings"]}


@pytest.mark.parametrize(("example_name", "expected_title"), EXAMPLES)
def test_examples_generate_expected_proposals(tmp_path: Path, example_name: str, expected_title: str) -> None:
    root = Path(__file__).resolve().parents[1]
    example = root / "examples" / example_name
    output = tmp_path / f"{example_name}.proposal.json"

    result = main(
        [
            "proposal",
            "from-trace",
            str(example / "traces.json"),
            "--outcomes",
            str(example / "outcomes.json"),
            "--surface",
            str(example / "improvement_surface.json"),
            "--output",
            str(output),
        ]
    )

    assert result == 0
    proposal = json.loads(output.read_text(encoding="utf-8"))
    validate(instance=proposal, schema=CHANGE_PROPOSAL_SCHEMA)
    assert proposal["title"] == expected_title
    assert proposal["status"] == "proposed"


@pytest.mark.parametrize(
    ("example_name", "expected_title"),
    EXAMPLES
    + [
        ("declared-intent", "Require retrieval for context-dependent questions"),
        ("openinference-phoenix", "Require retrieval for context-dependent questions"),
        ("langfuse-export", "Review tool-selection policy for failed tool use"),
    ],
)
def test_checked_in_example_proposals_are_valid(example_name: str, expected_title: str) -> None:
    root = Path(__file__).resolve().parents[1]
    proposal_path = root / "examples" / example_name / "change_proposal.example.json"
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))

    validate(instance=proposal, schema=CHANGE_PROPOSAL_SCHEMA)
    assert proposal["title"] == expected_title
    assert proposal["created_at"] == "2026-10-02T00:00:00+00:00"


@pytest.mark.parametrize(("example_name", "_expected_title"), EXAMPLES)
def test_examples_replay_compare_accepts_improvement(tmp_path: Path, example_name: str, _expected_title: str) -> None:
    root = Path(__file__).resolve().parents[1]
    example = root / "examples" / example_name
    output = tmp_path / f"{example_name}.replay.json"

    result = main(
        [
            "replay",
            "compare",
            str(example / "replay_baseline.json"),
            str(example / "replay_candidate.json"),
            "--output",
            str(output),
        ]
    )

    assert result == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"]["verdict"] == "accept"
    assert report["summary"]["regressed"] == 0


def test_retrieval_span_prevents_missed_retrieval_proposal() -> None:
    trace_export = {
        "runs": [
            {
                "run_id": "run_with_retrieval",
                "input": {"text": "According to the refund policy, what should we do?"},
                "spans": [
                    {
                        "span_id": "span_retriever",
                        "kind": "retriever",
                        "attributes": {},
                    }
                ],
            }
        ]
    }
    outcomes = [
        {
            "run_id": "run_with_retrieval",
            "timestamp": "2026-10-01T17:00:00Z",
            "source": "human_review",
            "label": "failure",
            "confidence": 0.9,
        }
    ]
    surface = {
        "schema_version": "0.1",
        "agent_ref": {"name": "test-agent"},
        "allowed_targets": [
            {
                "target_id": "retrieval_policy.main",
                "type": "retrieval_policy",
                "component": "main_retriever",
            }
        ],
    }

    proposal = build_proposal(trace_export, outcomes, surface)

    assert proposal["title"] == "No specific improvement pattern detected"
    assert proposal["proposed_change"]["summary"] == "No change proposed."


def test_openinference_import_generates_trace_export(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    example = root / "examples/openinference-phoenix"
    output = tmp_path / "trace_export.json"

    result = main(
        [
            "import",
            "openinference",
            str(example / "traces.openinference.json"),
            "--output",
            str(output),
        ]
    )

    assert result == 0
    trace_export = json.loads(output.read_text(encoding="utf-8"))
    assert trace_export["runs"][0]["run_id"] == "oi_trace_rag_001"
    assert trace_export["runs"][0]["input"]["text"].startswith("According to")
    assert trace_export["runs"][0]["spans"][0]["kind"] == "agent"


def test_openinference_import_can_write_diagnostics(tmp_path: Path) -> None:
    payload = {
        "spans": [
            {
                "traceId": "trace-1",
                "spanId": "span-1",
                "name": "agent",
                "attributes": {"input.value": "hello"},
            },
            {
                "spanId": "span-missing-trace",
                "name": "orphan",
                "attributes": {},
            },
        ]
    }
    input_path = tmp_path / "openinference.json"
    output_path = tmp_path / "trace_export.json"
    diagnostics_path = tmp_path / "diagnostics.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    result = main(
        [
            "import",
            "openinference",
            str(input_path),
            "--output",
            str(output_path),
            "--diagnostics-output",
            str(diagnostics_path),
        ]
    )

    assert result == 0
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    assert diagnostics["summary"]["input_records"] == 2
    assert diagnostics["summary"]["output_runs"] == 1
    assert diagnostics["summary"]["skipped_records"] == 1
    assert diagnostics["skipped_records"] == [{"reason": "missing_run_id", "count": 1}]


def test_openinference_import_feeds_proposal_generation(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    example = root / "examples/openinference-phoenix"
    trace_export = tmp_path / "trace_export.json"
    proposal_output = tmp_path / "proposal.json"

    assert main(
        [
            "import",
            "openinference",
            str(example / "traces.openinference.json"),
            "--output",
            str(trace_export),
        ]
    ) == 0

    assert main(
        [
            "proposal",
            "from-trace",
            str(trace_export),
            "--outcomes",
            str(example / "outcomes.json"),
            "--surface",
            str(example / "improvement_surface.json"),
            "--output",
            str(proposal_output),
        ]
    ) == 0

    proposal = json.loads(proposal_output.read_text(encoding="utf-8"))
    assert proposal["title"] == "Require retrieval for context-dependent questions"
    assert proposal["problem"]["run_id"] == "oi_trace_rag_001"


def test_openinference_otlp_attribute_shape_is_supported() -> None:
    payload = {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": "trace_otlp_001",
                                "spanId": "span_agent_001",
                                "name": "agent",
                                "attributes": [
                                    {"key": "openinference.span.kind", "value": {"stringValue": "AGENT"}},
                                    {"key": "input.value", "value": {"stringValue": "According to policy?"}},
                                ],
                            }
                        ]
                    }
                ]
            }
        ]
    }

    trace_export = openinference_to_trace_export(payload)

    assert trace_export["runs"][0]["run_id"] == "trace_otlp_001"
    assert trace_export["runs"][0]["spans"][0]["kind"] == "agent"


def test_langfuse_import_generates_trace_export(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    example = root / "examples/langfuse-export"
    output = tmp_path / "trace_export.json"

    result = main(
        [
            "import",
            "langfuse",
            str(example / "observations.langfuse.json"),
            "--output",
            str(output),
        ]
    )

    assert result == 0
    trace_export = json.loads(output.read_text(encoding="utf-8"))
    assert trace_export["runs"][0]["run_id"] == "lf_trace_tool_001"
    assert trace_export["runs"][0]["spans"][1]["kind"] == "tool"


def test_langfuse_import_can_write_diagnostics(tmp_path: Path) -> None:
    payload = {
        "data": [
            {
                "id": "obs-1",
                "traceId": "trace-1",
                "name": "llm-call",
                "type": "generation",
            },
            {
                "id": "obs-missing-trace",
                "name": "tool-call",
                "type": "span",
            },
        ]
    }
    input_path = tmp_path / "langfuse.json"
    output_path = tmp_path / "trace_export.json"
    diagnostics_path = tmp_path / "diagnostics.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    result = main(
        [
            "import",
            "langfuse",
            str(input_path),
            "--output",
            str(output_path),
            "--diagnostics-output",
            str(diagnostics_path),
        ]
    )

    assert result == 0
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    assert diagnostics["summary"]["input_records"] == 2
    assert diagnostics["summary"]["output_runs"] == 1
    assert diagnostics["summary"]["skipped_records"] == 1
    assert diagnostics["skipped_records"] == [{"reason": "missing_trace_id", "count": 1}]


def test_langfuse_import_feeds_proposal_generation(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    example = root / "examples/langfuse-export"
    trace_export = tmp_path / "trace_export.json"
    proposal_output = tmp_path / "proposal.json"

    assert main(
        [
            "import",
            "langfuse",
            str(example / "observations.langfuse.json"),
            "--output",
            str(trace_export),
        ]
    ) == 0

    assert main(
        [
            "proposal",
            "from-trace",
            str(trace_export),
            "--outcomes",
            str(example / "outcomes.json"),
            "--surface",
            str(example / "improvement_surface.json"),
            "--output",
            str(proposal_output),
        ]
    ) == 0

    proposal = json.loads(proposal_output.read_text(encoding="utf-8"))
    assert proposal["title"] == "Review tool-selection policy for failed tool use"
    assert proposal["problem"]["run_id"] == "lf_trace_tool_001"


def test_langfuse_observations_shape_is_supported() -> None:
    payload = {
        "data": [
            {
                "id": "obs-1",
                "traceId": "trace-1",
                "name": "llm-call",
                "type": "generation",
                "input": "hello",
                "output": "hi",
            }
        ],
        "meta": {"cursor": None},
    }

    trace_export = langfuse_observations_to_trace_export(payload)

    assert trace_export["runs"][0]["run_id"] == "trace-1"
    assert trace_export["runs"][0]["spans"][0]["kind"] == "llm"
