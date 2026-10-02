from __future__ import annotations

from collections import defaultdict
from typing import Any


def openinference_to_trace_export(payload: dict[str, Any]) -> dict[str, Any]:
    spans = _extract_spans(payload)
    runs: dict[str, dict[str, Any]] = {}
    grouped_spans: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for span in spans:
        normalized = _normalize_span(span)
        run_id = normalized.get("trace_id") or normalized.get("run_id")
        if not run_id:
            continue
        grouped_spans[run_id].append(normalized)

    for run_id, run_spans in grouped_spans.items():
        root_span = _select_root_span(run_spans)
        runs[run_id] = {
            "run_id": run_id,
            "input": {"text": _extract_input_text(root_span)},
            "spans": [
                {
                    "span_id": span.get("span_id"),
                    "name": span.get("name"),
                    "kind": span.get("kind"),
                    "status": span.get("status"),
                    "attributes": span.get("attributes", {}),
                }
                for span in run_spans
            ],
            "final_response": _extract_output_text(root_span),
        }

    return {"runs": list(runs.values())}


def _extract_spans(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("spans"), list):
        return payload["spans"]

    spans = []
    for resource_span in payload.get("resourceSpans", []):
        for scope_span in resource_span.get("scopeSpans", []):
            spans.extend(scope_span.get("spans", []))
    return spans


def _normalize_span(span: dict[str, Any]) -> dict[str, Any]:
    attributes = _normalize_attributes(span.get("attributes", {}))
    span_kind = attributes.get("openinference.span.kind") or span.get("kind")
    return {
        "trace_id": span.get("trace_id") or span.get("traceId") or span.get("trace_id_hex"),
        "run_id": span.get("run_id"),
        "span_id": span.get("span_id") or span.get("spanId"),
        "parent_span_id": span.get("parent_span_id") or span.get("parentSpanId"),
        "name": span.get("name"),
        "kind": str(span_kind).lower() if span_kind else None,
        "status": _normalize_status(span.get("status")),
        "attributes": attributes,
    }


def _normalize_attributes(attributes: Any) -> dict[str, Any]:
    if isinstance(attributes, dict):
        return attributes

    normalized = {}
    if not isinstance(attributes, list):
        return normalized

    for item in attributes:
        key = item.get("key")
        if not key:
            continue
        normalized[key] = _attribute_value(item.get("value"))
    return normalized


def _attribute_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    for key in (
        "stringValue",
        "boolValue",
        "intValue",
        "doubleValue",
        "arrayValue",
        "kvlistValue",
        "bytesValue",
    ):
        if key in value:
            return value[key]
    return value


def _normalize_status(status: Any) -> str | None:
    if isinstance(status, str):
        return status.lower()
    if isinstance(status, dict):
        code = status.get("code")
        if isinstance(code, str):
            return code.lower()
    return None


def _select_root_span(spans: list[dict[str, Any]]) -> dict[str, Any]:
    for span in spans:
        if not span.get("parent_span_id"):
            return span
    return spans[0] if spans else {}


def _extract_input_text(span: dict[str, Any]) -> str:
    attributes = span.get("attributes", {})
    value = attributes.get("input.value") or attributes.get("input")
    return str(value or "")


def _extract_output_text(span: dict[str, Any]) -> str:
    attributes = span.get("attributes", {})
    value = attributes.get("output.value") or attributes.get("output")
    return str(value or "")
