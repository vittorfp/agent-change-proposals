from __future__ import annotations

from pathlib import Path

import yaml

REQUIRED_ISSUE_TEMPLATES = {
    "feedback.md": {"label": "feedback"},
    "workflow-feedback.md": {"label": "feedback"},
    "schema-gap.md": {"label": "schema"},
    "integration-example.md": {"label": "feedback"},
}


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
