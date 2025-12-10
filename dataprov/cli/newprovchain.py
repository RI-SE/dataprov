#!/usr/bin/env python3
"""
Create New Provenance Chain

Command-line tool to initialize a new data provenance chain for tracking
data processing workflows. Creates an empty provenance chain with root
entity information.

Usage:
    dataprov-new --initial-source /data/raw_videos/ --output provenance.json --entity-id dataset_001
    dataprov-new -s /data/raw/ -o chain.json -i "uav_flight_001" -d "UAV stabilization pipeline"

Examples:
    # Minimal usage with directory source
    dataprov-new --initial-source /data/raw_videos/ --output provenance.json --entity-id my_dataset

    # With description and tags
    dataprov-new \\
        --initial-source /path/to/raw_data/ \\
        --output /path/to/prov.json \\
        --entity-id "dataset_2023_001" \\
        --description "UAV video stabilization and object detection pipeline" \\
        --tags UAV,video,stabilization,detection

    # Conceptual source (no file verification)
    dataprov-new -s "UAV_Flight_Session_2023_10_13" -o prov.json -i flight_001 --no-verify
"""

import argparse
import sys
from pathlib import Path

from dataprov import ProvenanceChain


def main():
    parser = argparse.ArgumentParser(
        description="Create a new data provenance chain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with directory
  dataprov-new -s /data/raw/ -o provenance.json -i dataset_001

  # With description and tags
  dataprov-new -s /data/videos/ -o prov.json \\
    -i "flight_001" -d "UAV processing pipeline" -t UAV,video,processing

  # Conceptual source (no verification)
  dataprov-new -s "Raw_Data_Batch_001" -o prov.json -i batch_001 --no-verify
        """,
    )

    # All arguments as flags
    parser.add_argument(
        "-s",
        "--initial-source",
        required=True,
        help="Initial source path (directory, file, or conceptual identifier)",
    )

    parser.add_argument(
        "-o", "--output", required=True, help="Output provenance JSON file path"
    )

    parser.add_argument(
        "-i", "--entity-id", required=True, help="Unique identifier for the data entity"
    )

    # Optional arguments
    parser.add_argument(
        "-d",
        "--description",
        default="",
        help="Human-readable description of the data entity",
    )

    parser.add_argument(
        "-t",
        "--tags",
        help='Comma-separated tags for categorizing the data (e.g., "UAV,video,raw")',
    )

    # Behavior options
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite output file if it exists"
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        default=True,
        help="Verify initial source path exists (default: True)",
    )

    parser.add_argument(
        "--no-verify",
        dest="verify",
        action="store_false",
        help="Skip initial source path existence check",
    )

    args = parser.parse_args()

    # Validate initial source exists (if requested)
    source_path = Path(args.initial_source)
    if args.verify and not source_path.exists():
        print(
            f"Error: Initial source does not exist: {args.initial_source}",
            file=sys.stderr,
        )
        print(
            "Use --no-verify to skip this check for conceptual sources", file=sys.stderr
        )
        return 1

    # Check output file
    output_path = Path(args.output)
    if output_path.exists() and not args.overwrite:
        print(f"Error: Output file already exists: {args.output}", file=sys.stderr)
        print("Use --overwrite to replace existing file", file=sys.stderr)
        return 1

    # Parse tags
    tags = []
    if args.tags:
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]

    # Create provenance chain
    try:
        chain = ProvenanceChain.create(
            entity_id=args.entity_id,
            initial_source=str(
                source_path.resolve()
                if args.verify and source_path.exists()
                else args.initial_source
            ),
            description=args.description,
            tags=tags,
        )

        # Save to output file
        chain.save(str(output_path))

        # Success message
        print(f"Created new provenance chain: {args.output}")
        print(f"  Entity ID: {args.entity_id}")
        print(f"  Initial source: {args.initial_source}")
        if args.description:
            print(f"  Description: {args.description}")
        if tags:
            print(f"  Tags: {', '.join(tags)}")

        print("\nNext steps:")
        print("  1. Run your first processing tool")
        print(
            "  2. Use chain.add() to record the processing step with actual input files"
        )

        return 0

    except Exception as e:
        print(f"Error: Failed to create provenance chain: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit(main())
