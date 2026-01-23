#!/usr/bin/env python3
"""
CLI tool to visualize provenance chains as GraphViz DOT format.

Usage:
    dataprov-visualize provenance.json -o provenance.dot
    dataprov-visualize provenance.json | dot -Tpng -o provenance.png
"""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point for the dataprov-visualize CLI tool."""
    parser = argparse.ArgumentParser(
        description="Generate GraphViz DOT visualization of provenance chain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate DOT file
  dataprov-visualize provenance.json -o provenance.dot

  # Generate PNG directly (requires graphviz installed)
  dataprov-visualize provenance.json | dot -Tpng -o provenance.png

  # Generate SVG
  dataprov-visualize provenance.json | dot -Tsvg -o provenance.svg
        """,
    )

    parser.add_argument("input", help="Path to provenance JSON file")

    parser.add_argument(
        "-o",
        "--output",
        help="Output file for DOT graph (default: stdout)",
        default=None,
    )

    parser.add_argument(
        "--flatten-bundles",
        action="store_true",
        help="Hide nested bundles (only show main chain)",
    )

    parser.add_argument(
        "--normalize-paths",
        action="store_true",
        help="Match entities by filename when full paths don't match "
        "(helps with path prefix mismatches between processing steps)",
    )

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1

    # Load provenance chain
    try:
        from dataprov import ProvenanceChain

        chain = ProvenanceChain.load(args.input)
    except Exception as e:
        print(f"Error loading provenance chain: {e}", file=sys.stderr)
        return 1

    # Generate DOT graph
    try:
        dot_graph = chain.to_dot(
            include_bundles=not args.flatten_bundles,
            normalize_paths=args.normalize_paths,
        )
    except Exception as e:
        print(f"Error generating DOT graph: {e}", file=sys.stderr)
        return 1

    # Output to file or stdout
    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(dot_graph)
            print(f"DOT graph written to {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        print(dot_graph)

    return 0


if __name__ == "__main__":
    sys.exit(main())
