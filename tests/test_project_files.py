from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import validate

from acp.schemas import SCHEMAS, validate_instance

REQUIRED_ISSUE_TEMPLATES = {
    "feedback.md": {"label": "feedback"},
    "workflow-feedback.md": {"label": "feedback"},
    "schema-gap.md": {"label": "schema"},
    "integration-example.md": {"label": "feedback"},
}

REQUIRED_TRUST_FILES = [
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
]


def _front_matter(path: Path) -> dict[str, str]:
    content = path.read_text(encoding="utf-8")
    marker = "---\n"
    assert content.startswith(marker), f"{path} must start with front matter"
    _, raw_front_matter, body = content.split(marker, 2)
    data = yaml.safe_load(raw_front_matter)
    assert isinstance(data, dict), f"{path} front matter must parse as a mapping"
    assert body.strip(), f"{path} must include a body"
    return data


def test_issue_templates_are_present_and_actionable() -> None:
    root = Path(__file__).resolve().parents[1]
    templates_dir = root / ".github" / "ISSUE_TEMPLATE"

    for filename, expectation in REQUIRED_ISSUE_TEMPLATES.items():
        path = templates_dir / filename
        assert path.exists(), f"missing issue template: {filename}"

        data = _front_matter(path)
        assert data["name"]
        assert data["about"]
        assert data["title"].endswith(": ")
        assert expectation["label"] in data["labels"]


def test_trust_files_exist_and_discourage_sensitive_public_data() -> None:
    root = Path(__file__).resolve().parents[1]

    for filename in REQUIRED_TRUST_FILES:
        path = root / filename
        assert path.exists(), f"missing trust file: {filename}"
        assert path.read_text(encoding="utf-8").strip()

    security = (root / "SECURITY.md").read_text(encoding="utf-8").lower()
    assert "sensitive" in security
    assert "traces" in security
    assert "prompts" in security


def test_ci_gate_rfc_example_matches_current_change_proposal_schema() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "rfcs" / "examples" / "ci-gate.change_proposal.example.json"

    proposal = json.loads(path.read_text(encoding="utf-8"))

    validate(instance=proposal, schema=SCHEMAS["change_proposal"])
    assert proposal["validation"]["gate"]["mode"] == "blocking"
    assert proposal["validation"]["gate"]["required_evidence_refs"]


def test_pr_ready_rfc_example_matches_current_change_proposal_schema() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "rfcs" / "examples" / "pr-ready.change_proposal.example.json"

    proposal = json.loads(path.read_text(encoding="utf-8"))

    validate_instance("change_proposal", proposal)
    criteria = proposal["validation"]["acceptance_criteria"]
    checks = proposal["validation"]["checks"]
    assert {criterion["id"] for criterion in criteria} == {
        "retrieval-required",
        "counterfactual-no-overapply",
        "no-guardrail-regression",
        "canary-latency-cost",
    }
    assert {check["role"] for check in checks} == {
        "positive",
        "negative",
        "verdict_diff",
        "canary",
    }
