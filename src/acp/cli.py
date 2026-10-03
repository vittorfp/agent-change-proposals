from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jsonschema import ValidationError, validate

from acp.checks import check_bundle
from acp.examples import verify_examples
from acp.importers import (
    langfuse_observations_to_trace_export_with_diagnostics,
    openinference_to_trace_export_with_diagnostics,
)
from acp.io import dump_data, load_data
from acp.proposals import build_proposal_with_coverage
from acp.replay import compare_replay_results
from acp.schemas import SCHEMAS, schema_names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="acp")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("schema", choices=sorted(SCHEMAS))
    validate_parser.add_argument("path")

    bundle_parser = subparsers.add_parser("bundle")
    bundle_subparsers = bundle_parser.add_subparsers(dest="bundle_command", required=True)
    check_parser = bundle_subparsers.add_parser("check")
    check_parser.add_argument("--trace", required=True)
    check_parser.add_argument("--outcomes", required=True)
    check_parser.add_argument("--surface", required=True)
    check_parser.add_argument("--baseline")
    check_parser.add_argument("--candidate")
    check_parser.add_argument("--proposal")
    check_parser.add_argument("--import-diagnostics")
    check_parser.add_argument("--proposal-coverage")
    check_parser.add_argument("--output")

    proposal_parser = subparsers.add_parser("proposal")
    proposal_subparsers = proposal_parser.add_subparsers(dest="proposal_command", required=True)
    from_trace_parser = proposal_subparsers.add_parser("from-trace")
    from_trace_parser.add_argument("trace")
    from_trace_parser.add_argument("--outcomes", required=True)
    from_trace_parser.add_argument("--surface", required=True)
    from_trace_parser.add_argument("--output", required=True)
    from_trace_parser.add_argument("--coverage-output")
    from_trace_parser.add_argument("--created-at")

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
    openinference_parser.add_argument("--diagnostics-output")
    langfuse_parser = import_subparsers.add_parser("langfuse")
    langfuse_parser.add_argument("input")
    langfuse_parser.add_argument("--output", required=True)
    langfuse_parser.add_argument("--diagnostics-output")

    examples_parser = subparsers.add_parser("examples")
    examples_subparsers = examples_parser.add_subparsers(dest="examples_command", required=True)
    verify_parser = examples_subparsers.add_parser("verify")
    verify_parser.add_argument("path", nargs="?", default="examples")

    schema_parser = subparsers.add_parser("schema")
    schema_subparsers = schema_parser.add_subparsers(dest="schema_command", required=True)
    schema_subparsers.add_parser("list")
    export_parser = schema_subparsers.add_parser("export")
    export_parser.add_argument("schema", choices=schema_names())
    export_parser.add_argument("--output")

    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            return _validate(args.schema, args.path)
        if args.command == "bundle" and args.bundle_command == "check":
            return _bundle_check(
                args.trace,
                args.outcomes,
                args.surface,
                baseline_path=args.baseline,
                candidate_path=args.candidate,
                proposal_path=args.proposal,
                import_diagnostics_path=args.import_diagnostics,
                proposal_coverage_path=args.proposal_coverage,
                output_path=args.output,
            )
        if args.command == "proposal" and args.proposal_command == "from-trace":
            return _proposal_from_trace(
                args.trace,
                args.outcomes,
                args.surface,
                args.output,
                coverage_output_path=args.coverage_output,
                created_at=args.created_at,
            )
        if args.command == "replay" and args.replay_command == "compare":
            return _replay_compare(args.baseline, args.candidate, args.output)
        if args.command == "import" and args.import_command == "openinference":
            return _import_openinference(args.input, args.output, args.diagnostics_output)
        if args.command == "import" and args.import_command == "langfuse":
            return _import_langfuse(args.input, args.output, args.diagnostics_output)
        if args.command == "examples" and args.examples_command == "verify":
            return _examples_verify(args.path)
        if args.command == "schema" and args.schema_command == "list":
            return _schema_list()
        if args.command == "schema" and args.schema_command == "export":
            return _schema_export(args.schema, args.output)
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


def _bundle_check(
    trace_path: str,
    outcomes_path: str,
    surface_path: str,
    baseline_path: str | None = None,
    candidate_path: str | None = None,
    proposal_path: str | None = None,
    import_diagnostics_path: str | None = None,
    proposal_coverage_path: str | None = None,
    output_path: str | None = None,
) -> int:
    trace_export = load_data(trace_path)
    outcomes = load_data(outcomes_path)
    surface = load_data(surface_path)
    baseline = load_data(baseline_path) if baseline_path else None
    candidate = load_data(candidate_path) if candidate_path else None
    proposal = load_data(proposal_path) if proposal_path else None
    import_diagnostics = load_data(import_diagnostics_path) if import_diagnostics_path else None
    proposal_coverage = load_data(proposal_coverage_path) if proposal_coverage_path else None

    validate(instance=trace_export, schema=SCHEMAS["trace_export"])
    validate(instance=outcomes, schema=SCHEMAS["outcome_events"])
    validate(instance=surface, schema=SCHEMAS["improvement_surface"])
    if baseline is not None:
        validate(instance=baseline, schema=SCHEMAS["replay_bundle"])
    if candidate is not None:
        validate(instance=candidate, schema=SCHEMAS["replay_bundle"])
    if proposal is not None:
        validate(instance=proposal, schema=SCHEMAS["change_proposal"])

    report = check_bundle(
        trace_export,
        outcomes,
        surface,
        baseline=baseline,
        candidate=candidate,
        proposal=proposal,
        import_diagnostics=import_diagnostics,
        proposal_coverage=proposal_coverage,
    )
    dump_data(Path(output_path or "-"), report)
    return 1 if report["errors"] else 0


def _proposal_from_trace(
    trace_path: str,
    outcomes_path: str,
    surface_path: str,
    output_path: str,
    coverage_output_path: str | None = None,
    created_at: str | None = None,
) -> int:
    trace_export = load_data(trace_path)
    outcomes = load_data(outcomes_path)
    surface = load_data(surface_path)

    validate(instance=trace_export, schema=SCHEMAS["trace_export"])
    validate(instance=outcomes, schema=SCHEMAS["outcome_events"])
    validate(instance=surface, schema=SCHEMAS["improvement_surface"])

    proposal, coverage = build_proposal_with_coverage(trace_export, outcomes, surface, created_at=created_at)
    validate(instance=proposal, schema=SCHEMAS["change_proposal"])
    dump_data(Path(output_path), proposal)
    if coverage_output_path:
        dump_data(Path(coverage_output_path), coverage)
        print(f"wrote: {coverage_output_path}")
    print(f"wrote: {output_path}")
    return 0


def _replay_compare(baseline_path: str, candidate_path: str, output_path: str) -> int:
    baseline = load_data(baseline_path)
    candidate = load_data(candidate_path)
    validate(instance=baseline, schema=SCHEMAS["replay_bundle"])
    validate(instance=candidate, schema=SCHEMAS["replay_bundle"])
    report = compare_replay_results(baseline, candidate)
    dump_data(Path(output_path), report)
    print(f"wrote: {output_path}")
    return 0


def _import_openinference(input_path: str, output_path: str, diagnostics_output_path: str | None = None) -> int:
    payload = load_data(input_path)
    trace_export, diagnostics = openinference_to_trace_export_with_diagnostics(payload)
    validate(instance=trace_export, schema=SCHEMAS["trace_export"])
    dump_data(Path(output_path), trace_export)
    if diagnostics_output_path:
        dump_data(Path(diagnostics_output_path), diagnostics)
        print(f"wrote: {diagnostics_output_path}")
    print(f"wrote: {output_path}")
    return 0


def _import_langfuse(input_path: str, output_path: str, diagnostics_output_path: str | None = None) -> int:
    payload = load_data(input_path)
    trace_export, diagnostics = langfuse_observations_to_trace_export_with_diagnostics(payload)
    validate(instance=trace_export, schema=SCHEMAS["trace_export"])
    dump_data(Path(output_path), trace_export)
    if diagnostics_output_path:
        dump_data(Path(diagnostics_output_path), diagnostics)
        print(f"wrote: {diagnostics_output_path}")
    print(f"wrote: {output_path}")
    return 0


def _examples_verify(path: str) -> int:
    reports = verify_examples(path)
    for report in reports:
        replay_suffix = f", replay={report['replay_verdict']}" if "replay_verdict" in report else ""
        print(f"valid: {report['example']} ({report['title']}{replay_suffix})")
    return 0


def _schema_list() -> int:
    for name in schema_names():
        print(name)
    return 0


def _schema_export(schema_name: str, output_path: str | None) -> int:
    schema = SCHEMAS[schema_name]
    if output_path:
        dump_data(Path(output_path), schema)
        print(f"wrote: {output_path}")
    else:
        dump_data(Path("-"), schema)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
