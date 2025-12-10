#!/usr/bin/env python3
"""
CLI tool to generate HTML reports from provenance chains.

Usage:
    dataprov-report provenance.json -o report.html
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path


def generate_html_report(chain) -> str:
    """Generate an HTML report from provenance chain.

    Args:
        chain: ProvenanceChain instance

    Returns:
        str: HTML report content
    """
    # Extract metadata from PROV-JSON format
    metadata = chain.data.get("dataprov:metadata", {})
    version = metadata.get("version", "unknown")
    created = metadata.get("created", "unknown")
    last_modified = metadata.get("lastModified", "unknown")
    entity_id = metadata.get("rootEntityId", "unknown")
    description = metadata.get("description", "")
    initial_source = metadata.get("initialSource", "unknown")
    tags = metadata.get("tags", [])

    steps = chain.get_steps()

    # Build HTML
    html_parts = []

    # HTML header with CSS
    html_parts.append(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Provenance Report: {entity_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .header {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metadata {{
            background-color: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #4CAF50;
            margin-bottom: 20px;
        }}
        .metadata-item {{
            margin: 5px 0;
        }}
        .metadata-label {{
            font-weight: bold;
            color: #555;
        }}
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}
        .tag {{
            background-color: #4CAF50;
            color: white;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.9em;
        }}
        .environment {{
            background-color: #e3f2fd;
            padding: 15px;
            border-left: 4px solid #2196F3;
            margin-bottom: 20px;
        }}
        .step {{
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .step-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .step-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2196F3;
        }}
        .step-meta {{
            color: #666;
            font-size: 0.9em;
        }}
        .drl-badge {{
            background-color: #FF9800;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .agent-info {{
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            font-size: 0.9em;
        }}
        .files {{
            margin: 15px 0;
        }}
        .file-list {{
            margin: 10px 0;
        }}
        .file-item {{
            background-color: #fafafa;
            padding: 8px;
            margin: 5px 0;
            border-left: 3px solid #ccc;
            font-family: monospace;
            font-size: 0.9em;
        }}
        .file-item.input {{
            border-left-color: #4CAF50;
        }}
        .file-item.output {{
            border-left-color: #2196F3;
        }}
        .file-meta {{
            color: #666;
            font-size: 0.85em;
            margin-top: 4px;
        }}
        .arguments, .log {{
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            overflow-x: auto;
        }}
        .section-title {{
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 5px;
            color: #555;
        }}
        .warning {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
        }}
        .timeline {{
            color: #666;
            font-size: 0.9em;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
"""
    )

    # Header section
    html_parts.append(f"""
    <div class="header">
        <h1>Provenance Report</h1>
        <p style="font-size: 1.1em; color: #666;">Entity: <strong>{entity_id}</strong></p>
    </div>
""")

    # Metadata section
    html_parts.append(f"""
    <div class="metadata">
        <h2>Chain Metadata</h2>
        <div class="metadata-item"><span class="metadata-label">Schema Version:</span> {version}</div>
        <div class="metadata-item"><span class="metadata-label">Created:</span> {created}</div>
        <div class="metadata-item"><span class="metadata-label">Last Modified:</span> {last_modified}</div>
        <div class="metadata-item"><span class="metadata-label">Initial Source:</span> {initial_source}</div>
""")

    if description:
        html_parts.append(
            f'        <div class="metadata-item"><span class="metadata-label">Description:</span> {description}</div>\n'
        )

    if tags:
        html_parts.append(
            '        <div class="metadata-item"><span class="metadata-label">Tags:</span></div>\n'
        )
        html_parts.append('        <div class="tags">\n')
        for tag in tags:
            html_parts.append(f'            <span class="tag">{tag}</span>\n')
        html_parts.append("        </div>\n")

    html_parts.append("    </div>\n")

    # Processing steps
    html_parts.append(f"""
    <h2>Processing Chain ({len(steps)} steps)</h2>
""")

    for step in steps:
        step_id = step.get("step_id", "?")
        tool_info = step.get("tool", {})
        tool_name = tool_info.get("name", "unknown")
        tool_version = tool_info.get("version", "unknown")
        tool_vendor = tool_info.get("vendor", "")
        operation = step.get("operation", "unknown")

        # Timing info
        started_at = step.get("started_at", step.get("timestamp", "unknown"))
        ended_at = step.get("ended_at")
        if ended_at is None:
            ended_at = step.get("timestamp", "In progress")

        # DRL
        drl = step.get("drl")

        # Agent
        agent = step.get("agent")

        html_parts.append(f"""
    <div class="step">
        <div class="step-header">
            <div>
                <div class="step-title">Step {step_id}: {tool_name} v{tool_version}</div>
                <div class="step-meta">Operation: {operation}</div>
            </div>
            {"<span class='drl-badge'>DRL: " + str(drl) + "</span>" if drl is not None else ""}
        </div>
""")

        # Timing
        if ended_at == "In progress":
            html_parts.append(f"""
        <div class="timeline">
            <strong>Started:</strong> {started_at}<br>
            <strong>Status:</strong> <em>{ended_at}</em>
        </div>
""")
        else:
            html_parts.append(f"""
        <div class="timeline">
            <strong>Started:</strong> {started_at}<br>
            <strong>Ended:</strong> {ended_at}
        </div>
""")

        # Agent info
        if agent:
            user = agent.get("user", "unknown")
            hostname = agent.get("hostname", "unknown")
            agent_type = agent.get("type", "unknown")
            html_parts.append(f"""
        <div class="agent-info">
            <strong>Executed by:</strong> {user} ({agent_type}) on {hostname}
        </div>
""")

        # Environment info
        environment = step.get("environment")
        if environment:
            html_parts.append("""
        <div class="environment">
            <strong>Environment:</strong><br>
""")
            for key, value in environment.items():
                html_parts.append(
                    f'            <span class="metadata-label">{key.replace("_", " ").title()}:</span> {value}<br>\n'
                )
            html_parts.append("        </div>\n")

        if tool_vendor:
            html_parts.append(
                f'        <div class="metadata-item"><span class="metadata-label">Vendor:</span> {tool_vendor}</div>\n'
            )

        # Inputs
        inputs = step.get("inputs", [])
        if inputs:
            html_parts.append('        <div class="files">\n')
            html_parts.append('            <div class="section-title">Inputs:</div>\n')
            for inp in inputs:
                path = inp.get("path", "unknown")
                fmt = inp.get("format", "unknown")
                size = inp.get("size_bytes", 0)
                checksum = inp.get("checksum", "")

                # Format size
                if size:
                    if size > 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
                    elif size > 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.2f} MB"
                    elif size > 1024:
                        size_str = f"{size / 1024:.2f} KB"
                    else:
                        size_str = f"{size} bytes"
                else:
                    size_str = "unknown size"

                html_parts.append('            <div class="file-item input">\n')
                html_parts.append(f"                <div>{path}</div>\n")
                html_parts.append(
                    f'                <div class="file-meta">Format: {fmt} | Size: {size_str}</div>\n'
                )
                if checksum:
                    html_parts.append(
                        f'                <div class="file-meta">Checksum: {checksum}</div>\n'
                    )
                html_parts.append("            </div>\n")
            html_parts.append("        </div>\n")

        # Outputs
        outputs = step.get("outputs", [])
        if outputs:
            html_parts.append('        <div class="files">\n')
            html_parts.append('            <div class="section-title">Outputs:</div>\n')
            for out in outputs:
                path = out.get("path", "unknown")
                fmt = out.get("format", "unknown")
                size = out.get("size_bytes", 0)
                checksum = out.get("checksum", "")

                # Format size
                if size:
                    if size > 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
                    elif size > 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.2f} MB"
                    elif size > 1024:
                        size_str = f"{size / 1024:.2f} KB"
                    else:
                        size_str = f"{size} bytes"
                else:
                    size_str = "unknown size"

                html_parts.append('            <div class="file-item output">\n')
                html_parts.append(f"                <div>{path}</div>\n")
                html_parts.append(
                    f'                <div class="file-meta">Format: {fmt} | Size: {size_str}</div>\n'
                )
                if checksum:
                    html_parts.append(
                        f'                <div class="file-meta">Checksum: {checksum}</div>\n'
                    )
                html_parts.append("            </div>\n")
            html_parts.append("        </div>\n")

        # Arguments
        arguments = step.get("arguments", "")
        if arguments:
            html_parts.append('        <div class="section-title">Arguments:</div>\n')
            html_parts.append(f'        <div class="arguments">{arguments}</div>\n')

        # Output log
        output_log = step.get("output_log", "")
        if output_log:
            html_parts.append('        <div class="section-title">Output Log:</div>\n')
            html_parts.append(f'        <div class="log">{output_log}</div>\n')

        # Warnings
        warnings = step.get("warnings", "")
        if warnings:
            html_parts.append(
                f'        <div class="warning"><strong>Warnings:</strong> {warnings}</div>\n'
            )

        html_parts.append("    </div>\n")

    # Footer
    html_parts.append(f"""
    <div class="footer">
        Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} by dataprov-report
    </div>
</body>
</html>
""")

    return "".join(html_parts)


def main():
    """Main entry point for the dataprov-report CLI tool."""
    parser = argparse.ArgumentParser(
        description="Generate HTML report from provenance chain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  dataprov-report provenance.json -o report.html
        """,
    )

    parser.add_argument("input", help="Path to provenance JSON file")

    parser.add_argument(
        "-o", "--output", help="Output HTML file (default: stdout)", default=None
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

    # Generate HTML report
    try:
        html_report = generate_html_report(chain)
    except Exception as e:
        print(f"Error generating HTML report: {e}", file=sys.stderr)
        return 1

    # Output to file or stdout
    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(html_report)
            print(f"HTML report written to {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        print(html_report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
