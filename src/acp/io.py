from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_data(path: str | Path) -> Any:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def dump_data(path: str | Path, data: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.suffix.lower() in {".yaml", ".yml"}:
        destination.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )
        return
    destination.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

