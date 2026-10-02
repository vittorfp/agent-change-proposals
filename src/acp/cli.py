from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jsonschema import ValidationError, validate

from acp.io import dump_data, load_data
from acp.importers import openinference_to_trace_export
from acp.proposals import build_proposal
from acp.replay import compare_replay_results
from acp.schemas import SCHEMAS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="acp")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("schema", choices=sorted(SCHEMAS))
    validate_parser.add_argument("path")

    proposal_parser = subparsers.add_parser("proposal")
    proposal_subparsers = proposal_parser.add_subparsers(dest="proposal_command", required=True)
    from_trace_parser = proposal_subparsers.add_parser("from-trace")
    from_trace_parser.add_argument("trace")
    from_trace_parser.add_argument("--outcomes", required=True)
    from_trace_parser.add_argument("--surface", required=True)
    from_trace_parser.add_argument("--output", required=True)

    replay_parser = subparsers.add_parser("replay")
    replay_subparsers = replay_parser.add_subparsers(dest="replay_command", required=True)
    compare_parser = replay_subparsers.add_parser("compare")
    compare_parser.add_argument("baseline")
    compare_parser.add_argument("candidate")
    compare_parser.add_argument("--output", required=True)

    import_parser = subparsers.add_parser("import")
    import_subparsers = import_parser.add_subparsers(dest="import_command", required=True)
    openinference_parser = import_subparsers.add_parser("openinference")
    openinference_parser.add_argument("input")
    openinference_parser.add_argument("--output", required=True)

    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            return _validate(args.schema, args.path)
        if args.command == "proposal" and args.proposal_command == "from-trace":
            return _proposal_from_trace(args.trace, args.outcomes, args.surface, args.output)
        if args.command == "replay" and args.replay_command == "compare":
            return _replay_compare(args.baseline, args.candidate, args.output)
        if args.command == "import" and args.import_command == "openinference":
            return _import_openinference(args.input, args.output)
    except ValidationError as error:
        print(f"validation failed: {error.message}", file=sys.stderr)
        return 1

    parser.error("unsupported command")
    return 2


def _validate(schema_name: str, path: str) -> int:
    data = load_data(path)
    validate(instance=data, schema=SCHEMAS[schema_name])
    print(f"valid: {path}")
    return 0


def _proposal_from_trace(trace_path: str, outcomes_path: str, surface_path: str, output_path: str) -> int:
    trace_export = load_data(trace_path)
    outcomes = load_data(outcomes_path)
    surface = load_data(surface_path)

    validate(instance=trace_export, schema=SCHEMAS["trace_export"])
    validate(instance=outcomes, schema=SCHEMAS["outcome_events"])
    validate(instance=surface, schema=SCHEMAS["improvement_surface"])

    proposal = build_proposal(trace_export, outcomes, surface)
    validate(instance=proposal, schema=SCHEMAS["change_proposal"])
    dump_data(Path(output_path), proposal)
    print(f"wrote: {output_path}")
    return 0


def _replay_compare(baseline_path: str, candidate_path: str, output_path: str) -> int:
    baseline = load_data(baseline_path)
    candidate = load_data(candidate_path)
    report = compare_replay_results(baseline, candidate)
    dump_data(Path(output_path), report)
    print(f"wrote: {output_path}")
    return 0


def _import_openinference(input_path: str, output_path: str) -> int:
    payload = load_data(input_path)
    trace_export = openinference_to_trace_export(payload)
    validate(instance=trace_export, schema=SCHEMAS["trace_export"])
    dump_data(Path(output_path), trace_export)
    print(f"wrote: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
