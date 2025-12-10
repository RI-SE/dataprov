#!/usr/bin/env python3
"""
Add Attribution to Provenance Chain

Command-line tool to add attribution relationships (wasAttributedTo) to an
existing provenance chain. Use this for manually created files, external
data sources, or to establish data ownership/responsibility.

Usage:
    dataprov-add-attribution -p provenance.json -i file.csv --current-user --role curator
    dataprov-add-attribution -p prov.json -i data.csv --agent-name "Dr. Smith" --role PI

Examples:
    # Attribute single file to current user
    dataprov-add-attribution -p provenance.json -i reference/data.csv \\
        --current-user --role curator

    # Attribute to external organization
    dataprov-add-attribution -p provenance.json -i census.csv \\
        --agent-name "US Census Bureau" --agent-type organization

    # Multiple files to same agent
    dataprov-add-attribution -p provenance.json \\
        -i file1.csv file2.csv file3.csv \\
        --agent-name "dr.smith@hospital.org" --role "principal_investigator"

    # With explicit format and creation time
    dataprov-add-attribution -p provenance.json -i legacy_data.dat \\
        --agent-name "Legacy System" --agent-type organization \\
        --formats BINARY --created-at "2020-01-15T00:00:00Z"

    # Output to new file instead of in-place modification
    dataprov-add-attribution -p provenance.json -i data.csv \\
        --agent-name "curator" -o provenance_updated.json
"""

import argparse
import sys
from pathlib import Path

from dataprov import ProvenanceChain


def main():
    parser = argparse.ArgumentParser(
        description="Add attribution relationships to existing provenance chain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file - attribute to current user
  dataprov-add-attribution -p provenance.json -i reference/data.csv \\
    --current-user --role curator

  # Single file - attribute to organization
  dataprov-add-attribution -p provenance.json -i census.csv \\
    --agent-name "US Census Bureau" --agent-type organization

  # Multiple files to same agent
  dataprov-add-attribution -p provenance.json \\
    -i file1.csv file2.csv file3.csv \\
    --agent-name "dr.smith@hospital.org" --role "principal_investigator"

  # Works with shell wildcards
  dataprov-add-attribution -p provenance.json -i reference/*.csv \\
    --agent-name "curator_team" --role "data_curator"
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
        "-i",
        "--input",
        required=True,
        nargs="+",
        metavar="FILE",
        help="One or more file paths to attribute",
    )

    # Agent specification (mutually exclusive)
    agent_group = parser.add_mutually_exclusive_group(required=True)
    agent_group.add_argument(
        "--current-user",
        action="store_true",
        help="Attribute to current user (auto-detect username and hostname)",
    )

    agent_group.add_argument(
        "--agent-name", help="Name of external agent (person or organization)"
    )

    # Optional arguments
    parser.add_argument(
        "-t",
        "--agent-type",
        choices=["person", "organization"],
        default="person",
        help="Type of agent (default: person)",
    )

    parser.add_argument(
        "-r",
        "--role",
        help='Role of the agent (e.g., "curator", "author", "principal_investigator")',
    )

    parser.add_argument(
        "-f",
        "--formats",
        help="Comma-separated file formats (default: auto-detect from extensions)",
    )

    parser.add_argument(
        "--created-at",
        help="ISO 8601 timestamp when files were created (default: auto-detect from mtime)",
    )

    parser.add_argument("--user", help="Override username (only with --current-user)")

    parser.add_argument(
        "--hostname", help="Override hostname (only with --current-user)"
    )

    # Output options
    parser.add_argument(
        "-o", "--output", help="Output to new file instead of in-place modification"
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

    # Validate user/hostname only with --current-user
    if not args.current_user and (args.user or args.hostname):
        print(
            "Error: --user and --hostname can only be used with --current-user",
            file=sys.stderr,
        )
        return 1

    # Validate output file
    output_path = args.output if args.output else args.provenance_file
    if args.output:
        output_path = Path(args.output)
        if output_path.exists() and not args.overwrite:
            print(f"Error: Output file already exists: {args.output}", file=sys.stderr)
            print("Use --overwrite to replace existing file", file=sys.stderr)
            return 1

    # Parse formats if provided
    file_formats = None
    if args.formats:
        file_formats = [fmt.strip() for fmt in args.formats.split(",")]
        if len(file_formats) != len(args.input):
            print(
                f"Error: Number of formats ({len(file_formats)}) must match number of files ({len(args.input)})",
                file=sys.stderr,
            )
            return 1

    # Load provenance chain
    try:
        chain = ProvenanceChain.load(args.provenance_file)
    except Exception as e:
        print(f"Error: Failed to load provenance chain: {e}", file=sys.stderr)
        return 1

    # Prepare agent_type for API (convert to W3C PROV format)
    agent_type_api = (
        f"prov:{args.agent_type.capitalize()}" if args.agent_name else "prov:Person"
    )

    # Add attribution
    try:
        success = chain.add_attribution(
            files=args.input,
            file_formats=file_formats,
            agent_name=args.agent_name,
            agent_type=agent_type_api,
            capture_current_user=args.current_user,
            user=args.user,
            hostname=args.hostname,
            created_at=args.created_at,
            role=args.role,
        )

        if not success:
            print(
                "Error: Failed to add attribution (see error messages above)",
                file=sys.stderr,
            )
            return 1

    except Exception as e:
        print(f"Error: Failed to add attribution: {e}", file=sys.stderr)
        return 1

    # Save the updated chain
    try:
        chain.save(str(output_path))
    except Exception as e:
        print(f"Error: Failed to save provenance chain: {e}", file=sys.stderr)
        return 1

    # Success message
    file_list = (
        ", ".join(args.input)
        if len(args.input) <= 3
        else f"{args.input[0]}, ... ({len(args.input)} files)"
    )

    print(f"Added attribution to {output_path}:", file=sys.stderr)
    print(f"  Files: {file_list}", file=sys.stderr)

    if args.current_user:
        # Get the actual agent that was created
        agent_ids = list(chain.data["agent"].keys())
        if agent_ids:
            last_agent = chain.data["agent"][agent_ids[-1]]
            user_info = last_agent.get("dataprov:user", "current_user")
            hostname_info = last_agent.get("dataprov:hostname", "localhost")
            print(f"  Agent: {user_info}@{hostname_info} (Person)", file=sys.stderr)
    else:
        agent_type_display = args.agent_type.capitalize()
        print(f"  Agent: {args.agent_name} ({agent_type_display})", file=sys.stderr)

    if args.role:
        print(f"  Role: {args.role}", file=sys.stderr)

    print("\nProvenance chain updated successfully.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    exit(main())
