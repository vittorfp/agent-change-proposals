from __future__ import annotations

import json
from pathlib import Path

from jsonschema import ValidationError, validate

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
        "schema_version": {"type": "string", "minLength": 1},
        "proposal_id": {"type": "string", "minLength": 1},
        "title": {"type": "string", "minLength": 1},
        "status": {"enum": ["proposed", "accepted", "rejected", "tested"]},
        "problem": {
            "type": "object",
            "required": ["summary"],
            "properties": {
                "summary": {"type": "string", "minLength": 1},
                "run_id": {"type": "string", "minLength": 1},
                "outcome_label": {"type": "string", "minLength": 1},
                "outcome_source": {"type": "string", "minLength": 1},
            },
        },
        "evidence": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["type"],
                "properties": {
                    "type": {"type": "string", "minLength": 1},
                    "run_id": {"type": "string", "minLength": 1},
                    "label": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "dimensions": {"type": "array", "items": {"type": "string"}},
                    "observed": {"type": "string", "minLength": 1},
                    "span_count": {"type": "integer", "minimum": 0},
                    "span": {"type": "object"},
                    "component_id": {"type": "string", "minLength": 1},
                    "component_type": {"type": "string", "minLength": 1},
                    "declared_role": {"type": "string", "minLength": 1},
                    "matched_success_dimensions": {"type": "array"},
                    "matched_policies": {"type": "array"},
                },
            },
        },
        "hypothesis": {
            "type": "object",
            "required": ["summary", "confidence"],
            "properties": {
                "summary": {"type": "string", "minLength": 1},
                "confidence": {"type": "string", "minLength": 1},
                "limits": {"type": "string"},
            },
        },
        "proposed_change": {
            "type": "object",
            "required": ["target", "summary"],
            "properties": {
                "target": {
                    "type": "object",
                    "required": ["target_id", "type", "component"],
                    "properties": {
                        "target_id": {"type": "string", "minLength": 1},
                        "type": {"type": "string", "minLength": 1},
                        "component": {"type": "string", "minLength": 1},
                        "description": {"type": "string"},
                    },
                },
                "summary": {"type": "string", "minLength": 1},
                "suggested_patch": {"type": "object"},
            },
        },
        "validation": {
            "type": "object",
            "required": ["method", "acceptance_criteria"],
            "properties": {
                "method": {"type": "string", "minLength": 1},
                "acceptance_criteria": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "oneOf": [
                            {"type": "string", "minLength": 1},
                            {
                                "type": "object",
                                "required": ["id", "description"],
                                "properties": {
                                    "id": {"type": "string", "minLength": 1},
                                    "description": {"type": "string", "minLength": 1},
                                },
                            },
                        ],
                    },
                },
                "checks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["criterion_refs", "metric", "op", "value"],
                        "properties": {
                            "criterion_refs": {
                                "type": "array",
                                "minItems": 1,
                                "items": {"type": "string", "minLength": 1},
                            },
                            "role": {
                                "enum": [
                                    "positive",
                                    "negative",
                                    "counterfactual",
                                    "verdict_diff",
                                    "canary",
                                ]
                            },
                            "suite": {"type": "string", "minLength": 1},
                            "metric": {"type": "string", "minLength": 1},
                            "op": {"enum": [">", ">=", "<", "<=", "==", "!="]},
                            "value": {},
                            "min_cases": {"type": "integer", "minimum": 0},
                            "trace_set_ref": {"type": "string", "minLength": 1},
                            "evidence_refs": {
                                "type": "array",
                                "items": {"type": "string", "minLength": 1},
                            },
                        },
                    },
                },
                "verdict_diff": {
                    "type": "object",
                    "properties": {
                        "baseline_artifact_id": {"type": "string", "minLength": 1},
                        "candidate_artifact_id": {"type": "string", "minLength": 1},
                        "pass_to_fail": {"type": "integer", "minimum": 0},
                        "fail_to_pass": {"type": "integer", "minimum": 0},
                        "unchanged_pass": {"type": "integer", "minimum": 0},
                        "unchanged_fail": {"type": "integer", "minimum": 0},
                        "unknown": {"type": "integer", "minimum": 0},
                    },
                },
                "outcome": {"enum": ["pass", "fail", "unknown", "insufficient_evidence"]},
            },
        },
        "risk": {
            "type": "object",
            "required": ["level", "notes"],
            "properties": {
                "level": {"enum": ["low", "medium", "high"]},
                "notes": {"type": "string", "minLength": 1},
            },
        },
        "rollback": {
            "type": "object",
            "required": ["plan"],
            "properties": {
                "plan": {"type": "string", "minLength": 1},
            },
        },
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

AGENT_MANIFEST_SCHEMA = {
    "type": "object",
    "required": ["schema_version", "agent_ref"],
    "properties": {
        "schema_version": {"type": "string"},
        "agent_ref": {"type": "object"},
        "description": {"type": "string"},
        "components": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["component_id", "type"],
                "properties": {
                    "component_id": {"type": "string"},
                    "type": {
                        "enum": [
                            "llm",
                            "router",
                            "retriever",
                            "tool",
                            "memory",
                            "guardrail",
                            "prompt",
                            "config",
                        ]
                    },
                    "description": {"type": "string"},
                    "depends_on": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "limits": {"type": "array", "items": {"type": "string"}},
    },
}

DOMAIN_CONTEXT_SCHEMA = {
    "type": "object",
    "required": ["schema_version", "domain_ref"],
    "properties": {
        "schema_version": {"type": "string"},
        "domain_ref": {"type": "object"},
        "narrative": {"type": "string"},
        "success_dimensions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["dimension_id", "name"],
                "properties": {
                    "dimension_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "success_definition": {"type": "string"},
                    "failure_definition": {"type": "string"},
                },
            },
        },
        "policies": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["policy_id", "name", "description"],
                "properties": {
                    "policy_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "applies_to_dimensions": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
}

SCHEMAS = {
    "agent_manifest": AGENT_MANIFEST_SCHEMA,
    "change_proposal": CHANGE_PROPOSAL_SCHEMA,
    "domain_context": DOMAIN_CONTEXT_SCHEMA,
    "improvement_surface": IMPROVEMENT_SURFACE_SCHEMA,
    "outcome_events": OUTCOME_EVENTS_SCHEMA,
    "replay_bundle": REPLAY_BUNDLE_SCHEMA,
    "trace_export": TRACE_EXPORT_SCHEMA,
}


def load_public_schemas() -> dict[str, dict]:
    schema_dir = Path(__file__).resolve().parents[2] / "schemas"
    schema_files = {
        "agent_manifest": "agent_manifest.schema.json",
        "change_proposal": "change_proposal.schema.json",
        "domain_context": "domain_context.schema.json",
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


def schema_names() -> list[str]:
    return sorted(SCHEMAS)


def validate_instance(schema_name: str, instance: object) -> None:
    validate(instance=instance, schema=SCHEMAS[schema_name])
    if schema_name == "change_proposal" and isinstance(instance, dict):
        validate_change_proposal_semantics(instance)


def validate_change_proposal_semantics(proposal: dict) -> None:
    validation = proposal.get("validation")
    if not isinstance(validation, dict):
        return

    criteria = validation.get("acceptance_criteria", [])
    criterion_ids = {
        criterion["id"]
        for criterion in criteria
        if isinstance(criterion, dict) and isinstance(criterion.get("id"), str)
    }

    checks = validation.get("checks", [])
    if not checks:
        return

    if not criterion_ids:
        raise ValidationError(
            "validation.checks requires structured acceptance_criteria with stable ids"
        )

    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            continue
        refs = check.get("criterion_refs", [])
        dangling = [ref for ref in refs if ref not in criterion_ids]
        if dangling:
            joined = ", ".join(sorted(dangling))
            raise ValidationError(f"validation.checks[{index}] has unknown criterion_refs: {joined}")
