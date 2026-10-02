from __future__ import annotations

import json
from pathlib import Path

import pytest
from acp.cli import main
from acp.importers import openinference_to_trace_export
from acp.proposals import build_proposal
from jsonschema import validate

from acp.schemas import CHANGE_PROPOSAL_SCHEMA


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
        ]
    )

    assert result == 0
    proposal = json.loads(output.read_text(encoding="utf-8"))
    validate(instance=proposal, schema=CHANGE_PROPOSAL_SCHEMA)
    assert proposal["status"] == "proposed"
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
