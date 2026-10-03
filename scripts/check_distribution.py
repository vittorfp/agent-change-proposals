from __future__ import annotations

import tarfile
from pathlib import Path

REQUIRED_SDIST_PATHS = [
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/workflow-feedback.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "ROADMAP.md",
    "SECURITY.md",
    "docs/feedback-playbook.md",
    "examples/rag-missed-retrieval/change_proposal.example.json",
    "rfcs/0001-change-proposal.md",
    "schemas/change_proposal.schema.json",
]


def main() -> int:
    sdists = sorted(Path("dist").glob("agent_change_proposals-*.tar.gz"))
    if not sdists:
        raise SystemExit("no source distribution found under dist/")

    sdist = sdists[-1]
    with tarfile.open(sdist) as archive:
        names = archive.getnames()

    missing = []
    for required_path in REQUIRED_SDIST_PATHS:
        if not any(name.endswith(required_path) for name in names):
            missing.append(required_path)

    if missing:
        raise SystemExit(f"{sdist} is missing expected files: {', '.join(missing)}")

    print(f"valid distribution: {sdist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
