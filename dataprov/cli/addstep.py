#!/usr/bin/env python3
"""
Add Processing Step to Provenance Chain

Command-line tool to record a processing step in an existing provenance chain.
Wraps the ProvenanceChain.add() method for use in shell pipelines and scripts.

Usage:
    dataprov-add -p provenance.json \\
        --started-at "2024-10-15T11:00:00Z" --ended-at "2024-10-15T11:05:30Z" \\
        --tool-name my_tool --tool-version 1.0 --operation processing \\
        -i input.csv --input-formats CSV \\
        --outputs output.csv --output-formats CSV

Examples:
    # Minimal usage
    dataprov-add -p provenance.json \\
        --started-at "2024-10-15T11:00:00Z" --ended-at "2024-10-15T11:05:30Z" \\
        --tool-name drone_stabilizer --tool-version 2.0 --operation stabilization \\
        -i raw.mp4 --input-formats MP4 \\
        --outputs stabilized.mp4 --output-formats MP4

    # Multiple inputs and outputs with provenance references
    dataprov-add -p provenance.json \\
        --started-at "2024-10-15T12:00:00Z" --ended-at "2024-10-15T12:10:00Z" \\
        --tool-name video_combiner --tool-version 1.5 --operation concatenation \\
        -i video1.mp4 video2.mp4 --input-formats MP4 MP4 \\
        --outputs combined.mp4 --output-formats MP4 \\
        --input-provenance-files video1_prov.json none

    # With agent capture, DRL, and execution log
    dataprov-add -p provenance.json \\
        --started-at "2024-10-15T10:00:00Z" \\
        --tool-name processor --tool-version 1.0 --operation processing \\
        -i input.txt --input-formats TXT \\
        --outputs output.txt --output-formats TXT \\
        --drl 3 --capture-agent --output-log "Processing completed successfully"

    # Capture runtime environment
    dataprov-add -p provenance.json \\
        --started-at "2024-10-15T10:00:00Z" \\
        --tool-name processor --tool-version 1.0 --operation processing \\
        -i input.txt --input-formats TXT \\
        --outputs output.txt --output-formats TXT \\
        --capture-environment

    # Output to new file instead of in-place modification
    dataprov-add -p provenance.json \\
        --started-at "2024-10-15T11:00:00Z" \\
        --tool-name my_tool --tool-version 1.0 --operation processing \\
        -i input.csv --input-formats CSV \\
        --outputs output.csv --output-formats CSV \\
        -o provenance_updated.json
"""

import argparse
import sys
from pathlib import Path

from dataprov import ProvenanceChain


def main():
    parser = argparse.ArgumentParser(
        description="Add a processing step to an existing provenance chain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic step
  dataprov-add -p provenance.json \\
    --started-at "2024-10-15T11:00:00Z" --ended-at "2024-10-15T11:05:30Z" \\
    --tool-name my_tool --tool-version 1.0 --operation processing \\
    -i input.csv --input-formats CSV \\
    --outputs output.csv --output-formats CSV

  # Multiple inputs/outputs
  dataprov-add -p provenance.json \\
    --started-at "2024-10-15T12:00:00Z" --ended-at "2024-10-15T12:10:00Z" \\
    --tool-name combiner --tool-version 1.0 --operation merge \\
    -i a.csv b.csv --input-formats CSV CSV \\
    --outputs merged.csv --output-formats CSV

  # With provenance references (use "none" for missing entries)
  dataprov-add -p provenance.json \\
    --started-at "2024-10-15T12:00:00Z" --ended-at "2024-10-15T12:10:00Z" \\
    --tool-name combiner --tool-version 1.0 --operation merge \\
    -i a.csv b.csv --input-formats CSV CSV \\
    --outputs merged.csv --output-formats CSV \\
    --input-provenance-files a_prov.json none
        """,
    )

    # Required arguments
    parser.add_argument(
        "-p",
        "--provenance-file",
        required=True,
        help="Path to existing provenance JSON file",
    )

    parser.add_argument(
        "--started-at",
        required=True,
        help="ISO 8601 timestamp when processing started (e.g. 2024-10-15T11:00:00Z)",
    )

    parser.add_argument(
        "--tool-name",
        required=True,
        help="Name of the tool that performed this step",
    )

    parser.add_argument(
        "--tool-version",
        required=True,
        help="Version of the tool",
    )

    parser.add_argument(
        "--operation",
        required=True,
        help="Semantic description of the operation (e.g. stabilization, merge, calibration)",
    )

    parser.add_argument(
        "-i",
        "--inputs",
        required=True,
        nargs="+",
        metavar="FILE",
        help="One or more input file paths",
    )

    parser.add_argument(
        "--input-formats",
        required=True,
        nargs="+",
        metavar="FORMAT",
        help="File formats for each input (e.g. MP4 CSV TXT) — must match number of inputs",
    )

    parser.add_argument(
        "--outputs",
        required=True,
        nargs="+",
        metavar="FILE",
        help="One or more output file paths",
    )

    parser.add_argument(
        "--output-formats",
        required=True,
        nargs="+",
        metavar="FORMAT",
        help="File formats for each output — must match number of outputs",
    )

    # Optional step metadata
    parser.add_argument(
        "--ended-at",
        default=None,
        help="ISO 8601 timestamp when processing ended (omit for ongoing/incomplete steps)",
    )

    parser.add_argument(
        "--source",
        default="",
        help="Tool source or organization",
    )

    parser.add_argument(
        "--arguments",
        default="",
        help="Command-line arguments string used for this step",
    )

    parser.add_argument(
        "--output-log",
        default="",
        help="Free-text output log from tool execution",
    )

    parser.add_argument(
        "--warnings",
        default="",
        help="Warning messages or issues encountered",
    )

    parser.add_argument(
        "--input-provenance-files",
        nargs="+",
        metavar="FILE",
        default=None,
        help=(
            "Provenance JSON files for each input (must match number of inputs). "
            'Use "none" for inputs that have no provenance file.'
        ),
    )

    parser.add_argument(
        "--drl",
        type=int,
        default=None,
        metavar="N",
        help="Data Readiness Level after this step (0–9)",
    )

    # Agent tracking
    parser.add_argument(
        "--capture-agent",
        action="store_true",
        default=False,
        help="Capture agent/user information automatically",
    )

    parser.add_argument(
        "--user",
        default=None,
        help="Override username for agent capture (only with --capture-agent)",
    )

    parser.add_argument(
        "--hostname",
        default=None,
        help="Override hostname for agent capture (only with --capture-agent)",
    )

    # Environment tracking
    parser.add_argument(
        "--capture-environment",
        action="store_true",
        default=False,
        help="Capture execution environment information (Python version, platform, etc.)",
    )

    parser.add_argument(
        "--runtime",
        default=None,
        help="Override runtime name for environment capture (default: auto-detect)",
    )

    parser.add_argument(
        "--runtime-version",
        default=None,
        help="Override runtime version for environment capture (default: auto-detect)",
    )

    # Output options
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write updated chain to a new file instead of modifying in place",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output file if it exists (only with -o)",
    )

    args = parser.parse_args()

    # Validate provenance file exists
    prov_path = Path(args.provenance_file)
    if not prov_path.exists():
        print(
            f"Error: Provenance file not found: {args.provenance_file}", file=sys.stderr
        )
        return 1

    # Validate format list lengths
    if len(args.inputs) != len(args.input_formats):
        print(
            f"Error: Number of --input-formats ({len(args.input_formats)}) must match"
            f" number of --inputs ({len(args.inputs)})",
            file=sys.stderr,
        )
        return 1

    if len(args.outputs) != len(args.output_formats):
        print(
            f"Error: Number of --output-formats ({len(args.output_formats)}) must match"
            f" number of --outputs ({len(args.outputs)})",
            file=sys.stderr,
        )
        return 1

    # Validate input provenance files list length
    if args.input_provenance_files is not None and len(
        args.input_provenance_files
    ) != len(args.inputs):
        print(
            f"Error: Number of --input-provenance-files ({len(args.input_provenance_files)})"
            f" must match number of --inputs ({len(args.inputs)})",
            file=sys.stderr,
        )
        return 1

    # Validate agent-only flags
    if not args.capture_agent and (args.user or args.hostname):
        print(
            "Error: --user and --hostname can only be used with --capture-agent",
            file=sys.stderr,
        )
        return 1

    # Validate environment-only flags
    if not args.capture_environment and (args.runtime or args.runtime_version):
        print(
            "Error: --runtime and --runtime-version can only be used with --capture-environment",
            file=sys.stderr,
        )
        return 1

    # Validate output file
    output_path = Path(args.output) if args.output else prov_path
    if args.output and output_path.exists() and not args.overwrite:
        print(f"Error: Output file already exists: {args.output}", file=sys.stderr)
        print("Use --overwrite to replace existing file", file=sys.stderr)
        return 1

    # Convert "none" sentinels to Python None in provenance files list
    input_provenance_files = None
    if args.input_provenance_files is not None:
        input_provenance_files = [
            None if entry.lower() == "none" else entry
            for entry in args.input_provenance_files
        ]

    # Load provenance chain
    try:
        chain = ProvenanceChain.load(args.provenance_file)
    except Exception as e:
        print(f"Error: Failed to load provenance chain: {e}", file=sys.stderr)
        return 1

    # Add the processing step
    try:
        success = chain.add(
            started_at=args.started_at,
            ended_at=args.ended_at,
            tool_name=args.tool_name,
            tool_version=args.tool_version,
            operation=args.operation,
            inputs=args.inputs,
            input_formats=args.input_formats,
            outputs=args.outputs,
            output_formats=args.output_formats,
            source=args.source,
            arguments=args.arguments,
            output_log=args.output_log,
            warnings=args.warnings,
            input_provenance_files=input_provenance_files,
            drl=args.drl,
            capture_agent=args.capture_agent,
            user=args.user,
            hostname=args.hostname,
            capture_environment=args.capture_environment,
            runtime=args.runtime,
            runtime_version=args.runtime_version,
        )

        if not success:
            print(
                "Error: Failed to add processing step (see error messages above)",
                file=sys.stderr,
            )
            return 1

    except Exception as e:
        print(f"Error: Failed to add processing step: {e}", file=sys.stderr)
        return 1

    # Save the updated chain
    try:
        chain.save(str(output_path))
    except Exception as e:
        print(f"Error: Failed to save provenance chain: {e}", file=sys.stderr)
        return 1

    # Success message
    input_list = (
        ", ".join(args.inputs)
        if len(args.inputs) <= 3
        else f"{args.inputs[0]}, ... ({len(args.inputs)} files)"
    )
    output_list = (
        ", ".join(args.outputs)
        if len(args.outputs) <= 3
        else f"{args.outputs[0]}, ... ({len(args.outputs)} files)"
    )

    print(f"Added processing step to {output_path}:", file=sys.stderr)
    print(f"  Tool: {args.tool_name} v{args.tool_version}", file=sys.stderr)
    print(f"  Operation: {args.operation}", file=sys.stderr)
    print(f"  Inputs:  {input_list}", file=sys.stderr)
    print(f"  Outputs: {output_list}", file=sys.stderr)
    if args.drl is not None:
        print(f"  DRL: {args.drl}", file=sys.stderr)

    print("\nProvenance chain updated successfully.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    exit(main())
