from __future__ import annotations

import json
from pathlib import Path

CHANGE_PROPOSAL_SCHEMA = {
    "type": "object",
    "required": [
        "schema_version",
        "proposal_id",
        "title",
        "status",
        "problem",
        "evidence",
        "hypothesis",
        "proposed_change",
        "validation",
        "risk",
        "rollback",
    ],
    "properties": {
        "schema_version": {"type": "string"},
        "proposal_id": {"type": "string"},
        "title": {"type": "string"},
        "status": {"enum": ["proposed", "accepted", "rejected", "tested"]},
        "problem": {"type": "object"},
        "evidence": {"type": "array", "items": {"type": "object"}},
        "hypothesis": {"type": "object"},
        "proposed_change": {"type": "object"},
        "validation": {"type": "object"},
        "risk": {"type": "object"},
        "rollback": {"type": "object"},
    },
}

IMPROVEMENT_SURFACE_SCHEMA = {
    "type": "object",
    "required": ["schema_version", "agent_ref", "allowed_targets"],
    "properties": {
        "schema_version": {"type": "string"},
        "agent_ref": {"type": "object"},
        "allowed_targets": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["target_id", "type", "component"],
                "properties": {
                    "target_id": {"type": "string"},
                    "type": {
                        "enum": [
                            "prompt",
                            "config",
                            "routing_rule",
                            "tool_policy",
                            "retrieval_policy",
                            "guardrail_threshold",
                        ]
                    },
                    "component": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
    },
}

OUTCOME_EVENTS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["run_id", "timestamp", "source", "label", "confidence"],
        "properties": {
            "run_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "source": {"type": "string"},
            "label": {"enum": ["success", "failure", "mixed", "unknown"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "dimensions": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "string"},
        },
    },
}

TRACE_EXPORT_SCHEMA = {
    "type": "object",
    "required": ["runs"],
    "properties": {
        "runs": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["run_id", "input", "spans"],
                "properties": {
                    "run_id": {"type": "string"},
                    "input": {"type": "object"},
                    "spans": {"type": "array", "items": {"type": "object"}},
                    "final_response": {"type": "string"},
                },
            },
        }
    },
}

REPLAY_BUNDLE_SCHEMA = {
    "type": "object",
    "required": ["suite_id", "cases"],
    "properties": {
        "suite_id": {"type": "string"},
        "cases": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["case_id", "passed"],
                "properties": {
                    "case_id": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "metrics": {"type": "object"},
                    "notes": {"type": "string"},
                },
            },
        },
    },
}

SCHEMAS = {
    "change_proposal": CHANGE_PROPOSAL_SCHEMA,
    "improvement_surface": IMPROVEMENT_SURFACE_SCHEMA,
    "outcome_events": OUTCOME_EVENTS_SCHEMA,
    "replay_bundle": REPLAY_BUNDLE_SCHEMA,
    "trace_export": TRACE_EXPORT_SCHEMA,
}


def load_public_schemas() -> dict[str, dict]:
    schema_dir = Path(__file__).resolve().parents[2] / "schemas"
    schema_files = {
        "change_proposal": "change_proposal.schema.json",
        "improvement_surface": "improvement_surface.schema.json",
        "outcome_events": "outcome_events.schema.json",
        "replay_bundle": "replay_bundle.schema.json",
        "trace_export": "trace_export.schema.json",
    }
    loaded = {}
    for name, filename in schema_files.items():
        path = schema_dir / filename
        if not path.exists():
            return SCHEMAS
        loaded[name] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


SCHEMAS = load_public_schemas()
