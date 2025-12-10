"""
Data Provenance Tracking Library (PROV-JSON Format)

W3C PROV-compliant provenance tracking for data processing chains.
Implements PROV-JSON serialization with dataprov extensions.

Example usage:
    # Create a new provenance chain
    chain = ProvenanceChain.create(
        entity_id="dataset_001",
        initial_source="/path/to/raw/videos/",
        description="UAV video stabilization pipeline",
        tags=["UAV", "video", "stabilization"]
    )

    # Add a processing step (user provides timestamps)
    success = chain.add(
        started_at="2024-10-15T11:00:00Z",
        ended_at="2024-10-15T11:05:30Z",
        tool_name="drone_stabilizer",
        tool_version="2.0",
        operation="video_stabilization",
        inputs=["/path/to/raw.mp4"],
        input_formats=["MP4"],
        outputs=["/path/to/stabilized.mp4"],
        output_formats=["MP4"],
        # Optional parameters
        arguments="python drone_stabilizer.py --detector sift",
        output_log="Processing completed successfully",
        warnings="Frame 299 could not be read from input",
        drl=3  # Data Readiness Level after this step
    )

    # Add a step with linked input provenance chains
    success = chain.add(
        started_at="2024-10-15T12:00:00Z",
        ended_at="2024-10-15T12:10:00Z",
        tool_name="video_combiner",
        tool_version="1.5",
        operation="video_concatenation",
        inputs=["/data/video1.mp4", "/data/video2.mp4", "/data/video3.mp4"],
        input_formats=["MP4", "MP4", "MP4"],
        outputs=["/data/combined.mp4"],
        output_formats=["MP4"],
        # Link to existing provenance chains (mixed case: some have provenance, others don't)
        input_provenance_files=["/data/video1_prov.json", None, "/data/video3_prov.json"],
        arguments="python combiner.py --mode concat",
        output_log="Successfully combined 3 videos"
    )

    if success:
        chain.save("provenance.json")
"""

import hashlib
import json
import os
import platform
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATAPROV_VERSION = "3.0"
DATAPROV_NS = "https://ri-se.github.io/dataprov/ontology/dataprov.ttl#"
PROV_NS = "http://www.w3.org/ns/prov#"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"


def _capture_environment(
    runtime: str | None = None, runtime_version: str | None = None
) -> dict[str, str]:
    """Capture execution environment information.

    Args:
        runtime: Override runtime name (default: auto-detect Python)
        runtime_version: Override runtime version (default: auto-detect)

    Returns:
        Dict with environment information
    """
    import sys

    # Auto-detect or use overrides
    if runtime is None:
        runtime = platform.python_implementation()
    if runtime_version is None:
        runtime_version = sys.version.split()[0]

    return {
        "runtime": runtime,
        "runtime_version": runtime_version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
    }


def _capture_agent(
    user: str | None = None,
    hostname: str | None = None,
    agent_type: str | None = None,
) -> dict[str, str]:
    """Capture agent/executor information.

    Args:
        user: Override username (default: auto-detect)
        hostname: Override hostname (default: auto-detect)
        agent_type: Override agent type, "human" or "automated" (default: auto-detect)

    Returns:
        Dict with agent information
    """
    # Auto-detect user and agent type
    if agent_type is None:
        if user is None:
            try:
                user = os.getlogin()
                agent_type = "human"
            except (OSError, AttributeError):
                # Fallback for environments where os.getlogin() doesn't work
                user = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
                agent_type = "automated"
        else:
            agent_type = "human"
    elif user is None:
        try:
            user = os.getlogin()
        except (OSError, AttributeError):
            user = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"

    # Auto-detect hostname
    if hostname is None:
        try:
            hostname = socket.gethostname()
        except OSError:
            hostname = "unknown"

    return {"user": user, "hostname": hostname, "type": agent_type}


def _calculate_provenance_checksum(prov_file: str) -> str | None:
    """Calculate SHA256 checksum of a provenance JSON file.

    Args:
        prov_file: Path to the provenance JSON file

    Returns:
        Checksum string in format "sha256:..." or None if file cannot be read
    """
    try:
        prov_path = Path(prov_file)
        if not prov_path.exists():
            return None

        # Calculate SHA256 hash of the JSON file
        sha256_hash = hashlib.sha256()
        with open(prov_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return f"sha256:{sha256_hash.hexdigest()}"

    except (OSError, PermissionError) as e:
        print(
            f"Warning: Cannot read provenance file for checksum {prov_file}: {e}",
            file=sys.stderr,
        )
        return None


def _calculate_file_checksum(file_path: str) -> str | None:
    """Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        Checksum string in format "sha256:..." or None if file cannot be read
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None

        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return f"sha256:{sha256_hash.hexdigest()}"

    except (OSError, PermissionError) as e:
        print(
            f"Warning: Cannot read file for checksum {file_path}: {e}", file=sys.stderr
        )
        return None


def _validate_provenance_file(provenance_file: str) -> bool:
    """Validate that a provenance file exists and is valid JSON.

    Args:
        provenance_file: Path to the provenance file to validate

    Returns:
        bool: True if valid, False otherwise (prints warnings for issues)
    """
    try:
        prov_path = Path(provenance_file)
        if not prov_path.exists():
            print(
                f"Warning: Provenance file not found: {provenance_file}",
                file=sys.stderr,
            )
            return False

        # Try to load and validate the provenance file
        with open(prov_path) as f:
            prov_data = json.load(f)

        # Basic validation - check if it looks like a provenance chain
        if not isinstance(prov_data, dict):
            print(
                f"Warning: Provenance file is not a valid JSON object: {provenance_file}",
                file=sys.stderr,
            )
            return False

        # Check for PROV-JSON format (v3.0)
        if "prefix" in prov_data and "dataprov:metadata" in prov_data:
            # PROV-JSON format
            return True
        else:
            print(
                f"Warning: Provenance file missing expected PROV-JSON structure: {provenance_file}",
                file=sys.stderr,
            )
            return False

    except json.JSONDecodeError as e:
        print(
            f"Warning: Invalid JSON in provenance file {provenance_file}: {e}",
            file=sys.stderr,
        )
        return False
    except (OSError, PermissionError) as e:
        print(
            f"Warning: Cannot read provenance file {provenance_file}: {e}",
            file=sys.stderr,
        )
        return False


def _inline_provenance_files(prov_data: dict, mode: str) -> dict:
    """Recursively inline provenance files into bundles according to mode.

    Args:
        prov_data: The PROV-JSON provenance data
        mode: "reference" (default), "inline", or "both"

    Returns:
        Modified prov_data with bundle section containing inlined provenance
    """
    if mode == "reference":
        # No inlining needed
        return prov_data

    if mode not in ["inline", "both"]:
        print(
            f"Warning: Unknown input_prov mode '{mode}', using 'reference'",
            file=sys.stderr,
        )
        return prov_data

    # Collect provenance bundle references from used relationships
    prov_bundle_refs = []
    for _usage_id, usage in prov_data.get("used", {}).items():
        bundle_ref = usage.get("dataprov:hadProvenance")
        if bundle_ref and not bundle_ref.startswith("bundle:"):
            # This is a file path reference, not a bundle reference
            prov_bundle_refs.append(bundle_ref)

    if not prov_bundle_refs:
        # No provenance files to inline
        return prov_data

    # Initialize bundles section if not exists
    if "bundle" not in prov_data:
        prov_data["bundle"] = {}

    # Track inlined files: {original_path: bundle_id}
    inlined_map = {}
    nested_counter = 0

    def inline_file(prov_path: str, bundle_id: str | None = None) -> str | None:
        """Recursively inline a provenance file and return its bundle_id."""
        nonlocal nested_counter

        # Check if already inlined
        if prov_path in inlined_map:
            return inlined_map[prov_path]

        # Try to load the provenance file
        try:
            prov_file_path = Path(prov_path)
            if not prov_file_path.exists():
                print(
                    f"Warning: Provenance file not found for inlining: {prov_path}",
                    file=sys.stderr,
                )
                return None

            with open(prov_file_path) as f:
                external_prov = json.load(f)

            # Calculate checksum of the original file
            checksum = _calculate_provenance_checksum(prov_path)
            if not checksum:
                print(
                    f"Warning: Could not calculate checksum for {prov_path}",
                    file=sys.stderr,
                )
                return None

            # Generate bundle_id if not provided
            if bundle_id is None:
                bundle_id = f"bundle:nested_{nested_counter}"
                nested_counter += 1
            elif not bundle_id.startswith("bundle:"):
                bundle_id = f"bundle:{bundle_id}"

            inlined_map[prov_path] = bundle_id

            # Convert to PROV-JSON bundle content
            # The external file might be old format or new format
            if "prefix" in external_prov:
                # Already PROV-JSON, extract the content for bundle
                bundle_content = {
                    "entity": external_prov.get("entity", {}),
                    "activity": external_prov.get("activity", {}),
                    "agent": external_prov.get("agent", {}),
                    "used": external_prov.get("used", {}),
                    "wasGeneratedBy": external_prov.get("wasGeneratedBy", {}),
                    "wasDerivedFrom": external_prov.get("wasDerivedFrom", {}),
                    "wasAssociatedWith": external_prov.get("wasAssociatedWith", {}),
                    "wasAttributedTo": external_prov.get("wasAttributedTo", {}),
                }

                # Recursively process nested provenance files in the bundle
                for usage in bundle_content.get("used", {}).values():
                    nested_prov = usage.get("dataprov:hadProvenance")
                    if nested_prov and not nested_prov.startswith("bundle:"):
                        # Make path absolute relative to current prov file's directory
                        if not Path(nested_prov).is_absolute():
                            nested_prov = str(prov_file_path.parent / nested_prov)
                        nested_bundle_id = inline_file(nested_prov)
                        if nested_bundle_id:
                            usage["dataprov:hadProvenance"] = nested_bundle_id

            else:
                # Not PROV-JSON format
                print(
                    f"Warning: Cannot inline non-PROV-JSON file: {prov_path}",
                    file=sys.stderr,
                )
                print("Only PROV-JSON (v3.0+) format is supported", file=sys.stderr)
                return None

            # Add bundle to prov_data
            prov_data["bundle"][bundle_id] = bundle_content

            # Create or update bundle entity with metadata
            if "entity" not in prov_data:
                prov_data["entity"] = {}

            prov_data["entity"][bundle_id] = {
                "prov:type": "prov:Bundle",
                "dataprov:bundleChecksum": checksum,
            }

            if mode == "both":
                # Keep original path reference
                prov_data["entity"][bundle_id]["dataprov:originalPath"] = str(prov_path)
            elif mode == "inline":
                # Store original path only in entity metadata (not as external reference)
                prov_data["entity"][bundle_id]["dataprov:originalPath"] = str(prov_path)

            return bundle_id

        except json.JSONDecodeError as e:
            print(
                f"Warning: Could not parse provenance file {prov_path}: {e}",
                file=sys.stderr,
            )
            return None
        except Exception as e:
            print(
                f"Warning: Error inlining provenance file {prov_path}: {e}",
                file=sys.stderr,
            )
            return None

    # Inline all collected provenance files
    for prov_path in prov_bundle_refs:
        inline_file(prov_path)

    # Update usage relationships to reference bundles
    for usage in prov_data.get("used", {}).values():
        prov_ref = usage.get("dataprov:hadProvenance")
        if prov_ref and prov_ref in inlined_map:
            if mode == "inline":
                usage["dataprov:hadProvenance"] = inlined_map[prov_ref]
            elif mode == "both":
                usage["dataprov:hadProvenanceBundle"] = inlined_map[prov_ref]
                # Keep original path in dataprov:hadProvenance

    return prov_data


class ProvenanceChain:
    """W3C PROV-JSON provenance chain with dataprov extensions."""

    def __init__(self, data: dict):
        """Initialize with PROV-JSON data structure.

        Args:
            data: PROV-JSON formatted dictionary
        """
        self.data = data
        self._step_counter = 0

        # Store namespace registry from prefix section
        self.namespaces = data.get("prefix", {})

        # Count existing steps to initialize counter
        if "activity" in data:
            self._step_counter = len(data["activity"])

    def _validate_prefix(self, property_name: str) -> None:
        """Validate that a property name uses a declared namespace prefix.

        Args:
            property_name: Property name in format "prefix:property"

        Raises:
            ValueError: If the prefix is not declared in the namespace registry
        """
        if ":" not in property_name:
            raise ValueError(
                f"Invalid property name '{property_name}'. "
                f"Property names must use namespace prefix format 'prefix:property'"
            )

        prefix = property_name.split(":", 1)[0]
        if prefix not in self.namespaces:
            raise ValueError(
                f"Undeclared namespace prefix '{prefix}' in property '{property_name}'. "
                f"Declared prefixes: {list(self.namespaces.keys())}"
            )

    def _parse_custom_properties(
        self, custom_properties: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """Parse custom properties with target prefixes and group by target.

        Args:
            custom_properties: Dict with format 'target:namespace:property' as keys
                             Examples: 'entity:myapp:field', 'activity:myapp:status'

        Returns:
            Dict grouped by target: {'entity': {'myapp:field': value}, 'activity': {...}, ...}

        Raises:
            ValueError: If property format is invalid or namespace prefix is undeclared
        """
        VALID_TARGETS = {"entity", "input-entity", "output-entity", "activity", "agent"}
        grouped = {}

        for key, value in custom_properties.items():
            # Parse format: target:namespace:property
            parts = key.split(":", 2)
            if len(parts) != 3:
                raise ValueError(
                    f"Invalid custom property format '{key}'. "
                    f"Expected format: 'target:namespace:property' (e.g., 'entity:myapp:field')"
                )

            target, namespace, property_name = parts

            # Validate target
            if target not in VALID_TARGETS:
                raise ValueError(
                    f"Invalid target '{target}' in property '{key}'. "
                    f"Valid targets: {VALID_TARGETS}"
                )

            # Validate namespace prefix
            if namespace not in self.namespaces:
                raise ValueError(
                    f"Undeclared namespace prefix '{namespace}' in property '{key}'. "
                    f"Declared prefixes: {list(self.namespaces.keys())}"
                )

            # Group by target
            if target not in grouped:
                grouped[target] = {}
            # Store as namespace:property (drop the target prefix)
            grouped[target][f"{namespace}:{property_name}"] = value

        return grouped

    @classmethod
    def create(
        cls,
        entity_id: str,
        initial_source: str,
        description: str = "",
        tags: list[str] | None = None,
        custom_namespaces: dict[str, str] | None = None,
        custom_metadata: dict[str, Any] | None = None,
    ) -> "ProvenanceChain":
        """Create a new provenance chain in PROV-JSON format.

        Args:
            entity_id: Unique identifier for the data entity
            initial_source: Original source file or location of the data
            description: Human-readable description (optional)
            tags: Tags for categorizing or labeling the data (optional)
            custom_namespaces: Custom ontology namespaces as {prefix: URI} dict (optional)
            custom_metadata: Custom top-level metadata with format 'namespace:property' as keys (optional)
                           Example: {'myapp:projectId': 'PROJ-001', 'myapp:funding': 'NSF Grant'}

        Returns:
            ProvenanceChain: New provenance chain instance

        Raises:
            ValueError: If custom namespace prefix conflicts with reserved prefixes or
                       if custom_metadata uses undeclared namespace prefix
        """
        # Validate custom namespaces don't conflict with reserved ones
        reserved_prefixes = {"dataprov", "prov", "xsd"}
        if custom_namespaces:
            for prefix in custom_namespaces:
                if prefix in reserved_prefixes:
                    raise ValueError(
                        f"Custom namespace prefix '{prefix}' conflicts with reserved prefix. "
                        f"Reserved prefixes: {reserved_prefixes}"
                    )

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Build prefix section with default and custom namespaces
        prefixes = {"dataprov": DATAPROV_NS, "prov": PROV_NS, "xsd": XSD_NS}
        if custom_namespaces:
            prefixes.update(custom_namespaces)

        # Validate custom_metadata uses declared namespaces
        if custom_metadata:
            for key in custom_metadata:
                if ":" not in key:
                    raise ValueError(
                        f"Invalid custom metadata key '{key}'. "
                        f"Keys must use namespace prefix format 'namespace:property'"
                    )
                prefix = key.split(":", 1)[0]
                if prefix not in prefixes:
                    raise ValueError(
                        f"Undeclared namespace prefix '{prefix}' in custom metadata key '{key}'. "
                        f"Declared prefixes: {list(prefixes.keys())}"
                    )

        data = {
            "prefix": prefixes,
            "dataprov:metadata": {
                "version": DATAPROV_VERSION,
                "created": now,
                "lastModified": now,
                "rootEntityId": entity_id,
                "description": description,
                "initialSource": initial_source,
                "tags": tags or [],
            },
            "entity": {
                entity_id: {
                    "prov:type": "dataprov:RootEntity",
                    "prov:atLocation": initial_source,
                }
            },
            "activity": {},
            "agent": {},
            "used": {},
            "wasGeneratedBy": {},
            "wasDerivedFrom": {},
            "wasAssociatedWith": {},
            "wasAttributedTo": {},
        }

        # Add custom metadata sections if provided
        if custom_metadata:
            data.update(custom_metadata)

        return cls(data)

    @classmethod
    def load(cls, filepath: str) -> "ProvenanceChain":
        """Load existing provenance chain from file.

        Args:
            filepath: Path to the existing provenance JSON file (PROV-JSON v3.0 format)

        Returns:
            ProvenanceChain: Loaded provenance chain instance
        """
        with open(filepath) as f:
            data = json.load(f)

        # Check format version
        if "prefix" not in data:
            raise ValueError(
                f"File {filepath} is not in PROV-JSON format (v3.0+). "
                f"Only PROV-JSON format is supported."
            )

        return cls(data)

    @classmethod
    def load_or_create(cls, filepath: str, **create_kwargs) -> "ProvenanceChain":
        """Load existing chain or create new one if file doesn't exist.

        Args:
            filepath: Path to the provenance JSON file
            **create_kwargs: Arguments for create() if file doesn't exist

        Returns:
            ProvenanceChain: Loaded or newly created provenance chain
        """
        if Path(filepath).exists():
            return cls.load(filepath)
        return cls.create(**create_kwargs)

    def add(
        self,
        started_at: str,
        ended_at: str | None,
        tool_name: str,
        tool_version: str,
        operation: str,
        inputs: list[str],
        input_formats: list[str],
        outputs: list[str],
        output_formats: list[str],
        # Optional parameters
        source: str = "",
        arguments: str = "",
        output_log: str = "",
        warnings: str = "",
        input_provenance_files: list[str | None] | None = None,
        drl: int | None = None,
        derivation_map: dict[int, list[int]] | None = None,
        # Agent tracking (opt-in with auto-capture)
        capture_agent: bool = False,
        user: str | None = None,
        hostname: str | None = None,
        agent_type: str | None = None,
        # Environment tracking (opt-in with auto-capture)
        capture_environment: bool = False,
        runtime: str | None = None,
        runtime_version: str | None = None,
        # Custom ontology properties
        custom_properties: dict[str, Any] | None = None,
    ) -> bool:
        """Add a processing step to the chain as PROV-JSON entities/activities.

        Args:
            started_at: ISO 8601 timestamp when the processing step started
            ended_at: ISO 8601 timestamp when the processing step ended (optional)
            tool_name: Name of the tool that performed this step
            tool_version: Version of the tool
            operation: Semantic description of the operation performed
            inputs: List of input file paths
            input_formats: List of input file formats (same length as inputs)
            outputs: List of output file paths
            output_formats: List of output file formats (same length as outputs)
            source: Tool source or organization (optional)
            arguments: Command line arguments string (optional)
            output_log: Free-text output log from tool execution (optional)
            warnings: Warning messages or issues encountered (optional)
            input_provenance_files: List of provenance file paths for inputs (optional)
            drl: Data Readiness Level (0-9) after this processing step (optional)
            derivation_map: Optional precise input-output mapping (default: all outputs derive from all inputs)
                           Dict format: {input_index: [output_index, ...]}
                           Example: {0: [0], 1: [1], 2: [0, 1]} means input 0->output 0, input 1->output 1, input 2->both outputs
            capture_agent: If True, capture agent/user information (optional)
            user: Override username for agent capture (default: auto-detect)
            hostname: Override hostname for agent capture (default: auto-detect)
            agent_type: Override agent type, "human" or "automated" (default: auto-detect)
            capture_environment: If True, capture execution environment info (optional)
            runtime: Override runtime name for environment capture (default: auto-detect)
            runtime_version: Override runtime version for environment capture (default: auto-detect)
            custom_properties: Custom ontology properties as dict with format 'target:namespace:property'.
                              Targets: 'entity' (all entities), 'input-entity', 'output-entity', 'activity', 'agent'.
                              Example: {'entity:myapp:field': 'value', 'activity:myapp:mode': 'fast'}
                              Namespace prefix must be declared in custom_namespaces.

        Returns:
            bool: True if successful, False if any validation fails

        Raises:
            ValueError: If custom property format is invalid or namespace prefix is undeclared
        """
        if len(inputs) != len(input_formats):
            print(
                "Error: inputs and input_formats lists must have same length",
                file=sys.stderr,
            )
            return False

        if len(outputs) != len(output_formats):
            print(
                "Error: outputs and output_formats lists must have same length",
                file=sys.stderr,
            )
            return False

        # Validate provenance files lists if provided
        if input_provenance_files is not None and len(input_provenance_files) != len(
            inputs
        ):
            print(
                "Error: input_provenance_files list must have same length as inputs",
                file=sys.stderr,
            )
            return False

        # Validate DRL if provided
        if drl is not None and (drl < 0 or drl > 9):
            print(
                "Error: drl must be an integer between 0 and 9 (inclusive)",
                file=sys.stderr,
            )
            return False

        # Validate derivation_map if provided
        if derivation_map is not None:
            for input_idx, output_indices in derivation_map.items():
                if input_idx < 0 or input_idx >= len(inputs):
                    print(
                        f"Error: derivation_map input index {input_idx} out of range (0-{len(inputs) - 1})",
                        file=sys.stderr,
                    )
                    return False
                for output_idx in output_indices:
                    if output_idx < 0 or output_idx >= len(outputs):
                        print(
                            f"Error: derivation_map output index {output_idx} out of range (0-{len(outputs) - 1})",
                            file=sys.stderr,
                        )
                        return False

        # Parse custom properties by target if provided
        custom_props_by_target = {}
        if custom_properties:
            custom_props_by_target = self._parse_custom_properties(custom_properties)

        # Generate IDs
        self._step_counter += 1
        step_id = self._step_counter
        activity_id = f"activity:step_{step_id}"

        # Generate agent ID - include user if agent capture is enabled for uniqueness
        if capture_agent:
            # Capture agent info first to get user
            executor = _capture_agent(user, hostname, agent_type)
            actual_user = executor["user"]
            actual_hostname = executor["hostname"]
            tool_agent_id = f"agent:tool_{tool_name}_{tool_version}_{actual_user}_{actual_hostname}".replace(
                " ", "_"
            )
        else:
            tool_agent_id = f"agent:tool_{tool_name}_{tool_version}".replace(" ", "_")
            executor = None

        # Create activity
        activity = {"prov:startedAtTime": started_at, "dataprov:operation": operation}

        if ended_at is not None:
            activity["prov:endedAtTime"] = ended_at

        if arguments:
            activity["dataprov:arguments"] = arguments

        if output_log:
            activity["dataprov:outputLog"] = output_log

        if warnings:
            activity["dataprov:warnings"] = warnings

        if drl is not None:
            activity["dataprov:drl"] = drl

        # Add custom properties to activity if provided
        if "activity" in custom_props_by_target:
            activity.update(custom_props_by_target["activity"])

        self.data["activity"][activity_id] = activity

        # Create tool agent if not exists
        if tool_agent_id not in self.data["agent"]:
            agent = {
                "prov:type": "prov:SoftwareAgent",
                "dataprov:toolName": tool_name,
                "dataprov:toolVersion": tool_version,
            }

            if source:
                agent["dataprov:toolSource"] = source

            # Optionally capture environment info on agent
            if capture_environment:
                env = _capture_environment(runtime, runtime_version)
                agent.update(
                    {
                        "dataprov:runtime": env["runtime"],
                        "dataprov:runtimeVersion": env["runtime_version"],
                        "dataprov:platform": env["platform"],
                        "dataprov:machine": env["machine"],
                        "dataprov:processor": env["processor"],
                    }
                )

            # Optionally capture executor agent info
            if capture_agent and executor:
                agent.update(
                    {
                        "dataprov:user": executor["user"],
                        "dataprov:hostname": executor["hostname"],
                        "dataprov:agentType": executor["type"],
                    }
                )

            # Add custom properties to agent if provided
            if "agent" in custom_props_by_target:
                agent.update(custom_props_by_target["agent"])

            self.data["agent"][tool_agent_id] = agent

        # Create association (activity was associated with agent)
        assoc_id = f"_:assoc_{step_id}"
        self.data["wasAssociatedWith"][assoc_id] = {
            "prov:activity": activity_id,
            "prov:agent": tool_agent_id,
        }

        # Process input entities
        for i, (file_path, file_format) in enumerate(
            zip(inputs, input_formats, strict=True)
        ):
            entity_id = f"entity:{file_path}"

            # Create entity if not exists
            if entity_id not in self.data["entity"]:
                entity = {
                    "prov:type": "dataprov:DataFile",
                    "dataprov:format": file_format,
                }

                # Calculate checksum and size
                checksum = _calculate_file_checksum(file_path)
                if checksum:
                    entity["dataprov:checksum"] = checksum

                try:
                    path = Path(file_path)
                    if path.exists():
                        entity["dataprov:sizeBytes"] = path.stat().st_size
                except (OSError, PermissionError):
                    pass

                # Add custom properties to input entity if provided
                # Apply both 'entity' (all entities) and 'input-entity' (input-specific)
                if "entity" in custom_props_by_target:
                    entity.update(custom_props_by_target["entity"])
                if "input-entity" in custom_props_by_target:
                    entity.update(custom_props_by_target["input-entity"])

                self.data["entity"][entity_id] = entity

            # Create usage relationship
            usage_id = f"_:u_{step_id}_{i}"
            usage = {"prov:activity": activity_id, "prov:entity": entity_id}

            # Add provenance file reference if provided
            if input_provenance_files and input_provenance_files[i] is not None:
                prov_file = input_provenance_files[i]
                _validate_provenance_file(prov_file)

                # Create bundle entity for the provenance file
                bundle_id = f"bundle:step{step_id}_input{i}"
                bundle_checksum = _calculate_provenance_checksum(prov_file)

                self.data["entity"][bundle_id] = {
                    "prov:type": "prov:Bundle",
                    "dataprov:externalPath": prov_file,
                }

                if bundle_checksum:
                    self.data["entity"][bundle_id]["dataprov:bundleChecksum"] = (
                        bundle_checksum
                    )

                usage["dataprov:hadProvenance"] = (
                    prov_file  # Store path for later inlining
                )

            self.data["used"][usage_id] = usage

        # Process output entities
        for i, (file_path, file_format) in enumerate(
            zip(outputs, output_formats, strict=True)
        ):
            entity_id = f"entity:{file_path}"

            # Create entity
            entity = {"prov:type": "dataprov:DataFile", "dataprov:format": file_format}

            # Calculate checksum and size
            checksum = _calculate_file_checksum(file_path)
            if checksum:
                entity["dataprov:checksum"] = checksum

            try:
                path = Path(file_path)
                if path.exists():
                    entity["dataprov:sizeBytes"] = path.stat().st_size
            except (OSError, PermissionError):
                pass

            # Add custom properties to output entity if provided
            # Apply both 'entity' (all entities) and 'output-entity' (output-specific)
            if "entity" in custom_props_by_target:
                entity.update(custom_props_by_target["entity"])
            if "output-entity" in custom_props_by_target:
                entity.update(custom_props_by_target["output-entity"])

            self.data["entity"][entity_id] = entity

            # Create generation relationship
            gen_id = f"_:g_{step_id}_{i}"
            self.data["wasGeneratedBy"][gen_id] = {
                "prov:entity": entity_id,
                "prov:activity": activity_id,
            }

            # Create derivation relationships
            if derivation_map is None:
                # Default: all outputs derive from all inputs (backward compatible)
                for j, input_path in enumerate(inputs):
                    deriv_id = f"_:d_{step_id}_{i}_{j}"
                    self.data["wasDerivedFrom"][deriv_id] = {
                        "prov:generatedEntity": entity_id,
                        "prov:usedEntity": f"entity:{input_path}",
                        "prov:activity": activity_id,
                    }
            else:
                # Precise mapping: only create specified derivations
                for input_idx, output_indices in derivation_map.items():
                    if i in output_indices:  # This output is produced by this input
                        input_path = inputs[input_idx]
                        deriv_id = f"_:d_{step_id}_{i}_{input_idx}"
                        self.data["wasDerivedFrom"][deriv_id] = {
                            "prov:generatedEntity": entity_id,
                            "prov:usedEntity": f"entity:{input_path}",
                            "prov:activity": activity_id,
                        }

        # Update last_modified
        self.data["dataprov:metadata"]["lastModified"] = (
            ended_at if ended_at is not None else started_at
        )

        return True

    def add_attribution(
        self,
        files: str | list[str],
        file_formats: str | list[str] | None = None,
        # Agent specification (exactly one required)
        agent_name: str | None = None,
        agent_type: str = "prov:Person",
        capture_current_user: bool = False,
        # Optional overrides for current user capture
        user: str | None = None,
        hostname: str | None = None,
        # Optional metadata
        created_at: str | None = None,
        role: str | None = None,
        # Custom ontology properties
        custom_properties: dict[str, Any] | None = None,
    ) -> bool:
        """Add attribution relationship linking entity/entities to an agent.

        This creates wasAttributedTo relationships without requiring an activity.
        Use this for manually created files, external data sources, or to establish
        ownership/responsibility for entities.

        Args:
            files: Single file path or list of file paths to attribute
            file_formats: File format(s) - auto-detected from extension if not provided
            agent_name: Name of external agent (person or organization)
            agent_type: Type of agent ("prov:Person" or "prov:Organization")
            capture_current_user: If True, attribute to current user instead of agent_name
            user: Override username for current user capture (default: auto-detect)
            hostname: Override hostname for current user capture (default: auto-detect)
            created_at: ISO 8601 timestamp when file was created (default: auto-detect from mtime)
            role: Free-text role of the agent (e.g., "curator", "author", "principal_investigator")
            custom_properties: Custom ontology properties as dict with format 'target:namespace:property'.
                              Targets: 'entity' (for attributed entities), 'agent' (for the agent).
                              Example: {'entity:myapp:quality': 'high', 'agent:myapp:dept': 'research'}
                              Namespace prefix must be declared in custom_namespaces.

        Returns:
            bool: True if successful, False if validation fails

        Raises:
            ValueError: If custom property format is invalid or namespace prefix is undeclared

        Examples:
            # Attribute to current user
            chain.add_attribution("manual_data.csv", capture_current_user=True, role="curator")

            # Attribute to external organization
            chain.add_attribution("census_data.csv", agent_name="US Census Bureau",
                                agent_type="prov:Organization")

            # Multiple files
            chain.add_attribution(["data1.csv", "data2.csv"], agent_name="dr.smith@example.org")
        """
        # Normalize to lists
        if isinstance(files, str):
            files = [files]
        if file_formats is None:
            file_formats = [None] * len(files)
        elif isinstance(file_formats, str):
            file_formats = [file_formats]

        # Validation
        if len(files) != len(file_formats):
            print(
                "Error: files and file_formats lists must have same length",
                file=sys.stderr,
            )
            return False

        # Validate agent specification - exactly one required
        if agent_name and capture_current_user:
            print(
                "Error: specify either agent_name or capture_current_user=True, not both",
                file=sys.stderr,
            )
            return False
        if not agent_name and not capture_current_user:
            print(
                "Error: must specify either agent_name or capture_current_user=True",
                file=sys.stderr,
            )
            return False

        # Validate agent_type
        if agent_type not in ["prov:Person", "prov:Organization"]:
            print(
                f"Error: agent_type must be 'prov:Person' or 'prov:Organization', got '{agent_type}'",
                file=sys.stderr,
            )
            return False

        # Parse custom properties by target if provided
        custom_props_by_target = {}
        if custom_properties:
            custom_props_by_target = self._parse_custom_properties(custom_properties)

        # Create or identify agent
        if capture_current_user:
            # Capture current user information
            executor = _capture_agent(user, hostname, agent_type=None)
            agent_id = (
                f"agent:person_{executor['user']}_{executor['hostname']}".replace(
                    " ", "_"
                )
            )

            # Create agent if not exists
            if agent_id not in self.data["agent"]:
                agent_data = {
                    "prov:type": "prov:Person",
                    "dataprov:user": executor["user"],
                    "dataprov:hostname": executor["hostname"],
                }

                # Add custom properties to agent if provided
                if "agent" in custom_props_by_target:
                    agent_data.update(custom_props_by_target["agent"])

                self.data["agent"][agent_id] = agent_data
        else:
            # Use provided agent name
            agent_id = f"agent:{agent_name}".replace(" ", "_")

            # Create agent if not exists
            if agent_id not in self.data["agent"]:
                agent_data = {"prov:type": agent_type}

                # Store the name in an appropriate field
                if agent_type == "prov:Organization":
                    agent_data["dataprov:name"] = agent_name
                else:  # prov:Person
                    agent_data["dataprov:name"] = agent_name

                # Add custom properties to agent if provided
                if "agent" in custom_props_by_target:
                    agent_data.update(custom_props_by_target["agent"])

                self.data["agent"][agent_id] = agent_data

        # Process each file
        for _i, (file_path, file_format) in enumerate(
            zip(files, file_formats, strict=True)
        ):
            # Auto-detect file format if not provided
            if file_format is None:
                file_format = Path(file_path).suffix.lstrip(".") or "unknown"

            entity_id = f"entity:{file_path}"

            # Create entity if not exists
            if entity_id not in self.data["entity"]:
                entity = {
                    "prov:type": "dataprov:DataFile",
                    "dataprov:format": file_format,
                }

                # Calculate checksum and size if file exists
                checksum = _calculate_file_checksum(file_path)
                if checksum:
                    entity["dataprov:checksum"] = checksum

                try:
                    path = Path(file_path)
                    if path.exists():
                        entity["dataprov:sizeBytes"] = path.stat().st_size

                        # Auto-detect created_at from file mtime if not provided
                        if created_at is None:
                            mtime = datetime.fromtimestamp(
                                path.stat().st_mtime, tz=timezone.utc
                            )
                            entity["dataprov:createdAt"] = mtime.isoformat().replace(
                                "+00:00", "Z"
                            )
                except (OSError, PermissionError):
                    pass

                # Use provided created_at if specified
                if created_at is not None:
                    entity["dataprov:createdAt"] = created_at

                # Add custom properties to entity if provided
                if "entity" in custom_props_by_target:
                    entity.update(custom_props_by_target["entity"])

                self.data["entity"][entity_id] = entity

            # Create attribution relationship
            attr_id = f"_:attr_{len(self.data['wasAttributedTo'])}"
            attribution = {"prov:entity": entity_id, "prov:agent": agent_id}

            # Add role if provided
            if role is not None:
                attribution["prov:role"] = role

            self.data["wasAttributedTo"][attr_id] = attribution

        # Update last_modified
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.data["dataprov:metadata"]["lastModified"] = now

        return True

    def save(self, filepath: str, input_prov: str = "reference"):
        """Save provenance chain to file in PROV-JSON format.

        Args:
            filepath: Path where to save the provenance JSON file
            input_prov: How to handle input provenance files: "reference" (default), "inline", or "both"
        """
        # Check if any activity is missing ended_at, update last_modified to current time if so
        has_incomplete_step = any(
            "prov:endedAtTime" not in activity
            for activity in self.data.get("activity", {}).values()
        )

        if has_incomplete_step:
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self.data["dataprov:metadata"]["lastModified"] = now

        # Make a deep copy to avoid modifying the original data
        import copy

        save_data = copy.deepcopy(self.data)

        # Inline provenance files if requested
        save_data = _inline_provenance_files(save_data, input_prov)

        with open(filepath, "w") as f:
            json.dump(save_data, f, indent=2)

    def get_steps(self) -> list[dict]:
        """Get all processing steps in the chain.

        Returns:
            List[Dict]: List of all processing steps (activities) with their metadata
        """
        steps = []
        for activity_id, activity in self.data.get("activity", {}).items():
            # Extract step number from activity_id
            step_num = int(activity_id.split("_")[-1]) if "_" in activity_id else 0

            # Find associated agent
            tool_agent = None
            for assoc in self.data.get("wasAssociatedWith", {}).values():
                if assoc["prov:activity"] == activity_id:
                    agent_id = assoc["prov:agent"]
                    tool_agent = self.data["agent"].get(agent_id)
                    break

            # Find inputs
            inputs = []
            for usage in self.data.get("used", {}).values():
                if usage["prov:activity"] == activity_id:
                    entity_id = usage["prov:entity"]
                    entity = self.data["entity"].get(entity_id, {})
                    input_info = {
                        "path": entity_id.replace("entity:", ""),
                        "format": entity.get("dataprov:format"),
                        "checksum": entity.get("dataprov:checksum"),
                        "size_bytes": entity.get("dataprov:sizeBytes"),
                    }

                    # Include provenance file reference if present
                    if "dataprov:hadProvenance" in usage:
                        prov_ref = usage["dataprov:hadProvenance"]
                        input_info["provenance_file"] = prov_ref

                        # Try to find the checksum from the bundle entity
                        # The prov_ref could be a bundle ID or a file path
                        if prov_ref.startswith("bundle:"):
                            bundle_entity = self.data["entity"].get(prov_ref, {})
                            checksum = bundle_entity.get("dataprov:bundleChecksum")
                            if checksum:
                                input_info["provenance_file_checksum"] = checksum
                        else:
                            # It's a file path, look for corresponding bundle
                            for _ent_id, ent in self.data["entity"].items():
                                if (
                                    ent.get("prov:type") == "prov:Bundle"
                                    and ent.get("dataprov:externalPath") == prov_ref
                                ):
                                    checksum = ent.get("dataprov:bundleChecksum")
                                    if checksum:
                                        input_info["provenance_file_checksum"] = (
                                            checksum
                                        )
                                    break

                    inputs.append(input_info)

            # Find outputs
            outputs = []
            for gen in self.data.get("wasGeneratedBy", {}).values():
                if gen["prov:activity"] == activity_id:
                    entity_id = gen["prov:entity"]
                    entity = self.data["entity"].get(entity_id, {})
                    outputs.append(
                        {
                            "path": entity_id.replace("entity:", ""),
                            "format": entity.get("dataprov:format"),
                            "checksum": entity.get("dataprov:checksum"),
                            "size_bytes": entity.get("dataprov:sizeBytes"),
                        }
                    )

            step = {
                "step_id": step_num,
                "started_at": activity.get("prov:startedAtTime"),
                "operation": activity.get("dataprov:operation"),
                "tool": {
                    "name": tool_agent.get("dataprov:toolName") if tool_agent else "",
                    "version": tool_agent.get("dataprov:toolVersion")
                    if tool_agent
                    else "",
                },
                "inputs": inputs,
                "outputs": outputs,
                "arguments": activity.get("dataprov:arguments", ""),
                "output_log": activity.get("dataprov:outputLog", ""),
                "warnings": activity.get("dataprov:warnings", ""),
            }

            # Only include ended_at if it exists
            if "prov:endedAtTime" in activity:
                step["ended_at"] = activity.get("prov:endedAtTime")

            if "dataprov:drl" in activity:
                step["drl"] = activity["dataprov:drl"]

            # Include agent information if present
            if tool_agent:
                if "dataprov:user" in tool_agent:
                    step["agent"] = {
                        "user": tool_agent.get("dataprov:user"),
                        "hostname": tool_agent.get("dataprov:hostname"),
                        "type": tool_agent.get("dataprov:agentType"),
                    }

                # Include environment information if present
                if "dataprov:runtime" in tool_agent:
                    step["environment"] = {
                        "runtime": tool_agent.get("dataprov:runtime"),
                        "runtime_version": tool_agent.get("dataprov:runtimeVersion"),
                        "platform": tool_agent.get("dataprov:platform"),
                        "machine": tool_agent.get("dataprov:machine"),
                        "processor": tool_agent.get("dataprov:processor"),
                    }

            steps.append(step)

        # Sort by step_id
        steps.sort(key=lambda s: s["step_id"])
        return steps

    def get_step(self, step_id: int) -> dict | None:
        """Get a specific step by ID.

        Args:
            step_id: The step ID to retrieve

        Returns:
            Optional[Dict]: The step data or None if not found
        """
        steps = self.get_steps()
        for step in steps:
            if step["step_id"] == step_id:
                return step
        return None

    def get_latest_step(self) -> dict | None:
        """Get the most recent step.

        Returns:
            Optional[Dict]: The latest step data or None if no steps exist
        """
        steps = self.get_steps()
        if steps:
            return steps[-1]
        return None

    def find_steps(
        self,
        tool_name: str | None = None,
        operation: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        drl_min: int | None = None,
        drl_max: int | None = None,
        user: str | None = None,
        hostname: str | None = None,
        file_pattern: str | None = None,
        log_regex: str | None = None,
    ) -> list[dict]:
        """Find steps matching specified criteria (all criteria must match - AND logic).

        Args:
            tool_name: Filter by tool name
            operation: Filter by operation name
            date_from: Filter by start date (ISO 8601 format)
            date_to: Filter by end date (ISO 8601 format)
            drl_min: Minimum Data Readiness Level
            drl_max: Maximum Data Readiness Level
            user: Filter by username
            hostname: Filter by hostname
            file_pattern: Filter by input/output file pattern (glob-style)
            log_regex: Filter by output log content (regex pattern)

        Returns:
            List[Dict]: List of matching steps (all criteria must match)
        """
        import fnmatch
        import re

        results = []
        steps = self.get_steps()

        for step in steps:
            matches = []

            # Tool name check
            if tool_name is not None:
                matches.append(step["tool"]["name"] == tool_name)

            # Operation check
            if operation is not None:
                matches.append(step["operation"] == operation)

            # Date range checks
            if date_from is not None:
                step_time = step.get("started_at", "")
                matches.append(step_time >= date_from)

            if date_to is not None:
                step_time = step.get("ended_at", "")
                matches.append(step_time <= date_to)

            # DRL checks
            if drl_min is not None:
                step_drl = step.get("drl")
                if step_drl is not None:
                    matches.append(step_drl >= drl_min)
                else:
                    matches.append(False)

            if drl_max is not None:
                step_drl = step.get("drl")
                if step_drl is not None:
                    matches.append(step_drl <= drl_max)
                else:
                    matches.append(False)

            # Agent checks (need to look at the agent data)
            if user is not None or hostname is not None:
                # Find the agent for this step
                activity_id = f"activity:step_{step['step_id']}"
                agent_id = None
                for assoc in self.data.get("wasAssociatedWith", {}).values():
                    if assoc["prov:activity"] == activity_id:
                        agent_id = assoc["prov:agent"]
                        break

                agent = self.data["agent"].get(agent_id, {}) if agent_id else {}

                if user is not None:
                    matches.append(agent.get("dataprov:user") == user)

                if hostname is not None:
                    matches.append(agent.get("dataprov:hostname") == hostname)

            # File pattern check
            if file_pattern is not None:
                file_match = False
                for f in step["inputs"] + step["outputs"]:
                    if fnmatch.fnmatch(f["path"], file_pattern):
                        file_match = True
                        break
                matches.append(file_match)

            # Log regex check
            if log_regex is not None:
                log_content = step.get("output_log", "")
                matches.append(bool(re.search(log_regex, log_content)))

            # Apply AND logic: all criteria must match
            if not matches:
                # No criteria specified, skip this step
                continue

            # AND: all criteria must match
            if all(matches):
                results.append(step)

        return results

    def validate(self) -> tuple[bool, list[str]]:
        """Validate chain integrity and schema compliance.

        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []

        # Check required top-level fields
        if "prefix" not in self.data:
            errors.append("Missing 'prefix' field")

        if "dataprov:metadata" not in self.data:
            errors.append("Missing 'dataprov:metadata' field")
        elif "version" not in self.data["dataprov:metadata"]:
            errors.append("Missing version in metadata")
        elif self.data["dataprov:metadata"]["version"] != DATAPROV_VERSION:
            errors.append(
                f"Invalid version: {self.data['dataprov:metadata']['version']}"
            )

        # Check activity sequence
        steps = self.get_steps()
        expected_id = 1
        for step in steps:
            if step["step_id"] != expected_id:
                errors.append(
                    f"Step ID mismatch: expected {expected_id}, got {step['step_id']}"
                )
            expected_id += 1

        return (len(errors) == 0, errors)

    def to_dot(self) -> str:
        """Generate GraphViz DOT format representation of the provenance chain.

        Returns:
            str: DOT format graph representation
        """
        lines = ["digraph provenance {"]
        lines.append("  rankdir=LR;")
        lines.append('  node [fontname="Arial"];')
        lines.append('  edge [fontname="Arial"];')
        lines.append("")

        # Collect all unique files
        files = set()
        for entity_id, entity in self.data.get("entity", {}).items():
            if entity.get("prov:type") == "dataprov:DataFile":
                file_path = entity_id.replace("entity:", "")
                files.add(file_path)

        # Add file nodes
        lines.append("  // File nodes")
        for file_path in sorted(files):
            label = Path(file_path).name
            # Escape quotes and backslashes for DOT format
            escaped_path = file_path.replace("\\", "\\\\").replace('"', '\\"')
            escaped_label = label.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(
                f'  "{escaped_path}" [shape=box, label="{escaped_label}", style=filled, fillcolor=skyblue];'
            )

        lines.append("")
        lines.append("  // Processing step nodes")

        # Add step nodes
        steps = self.get_steps()
        for step in steps:
            step_id = step["step_id"]
            tool_name = step["tool"]["name"]
            operation = step["operation"]

            # Escape for DOT format
            escaped_tool = tool_name.replace("\\", "\\\\").replace('"', '\\"')
            escaped_op = operation.replace("\\", "\\\\").replace('"', '\\"')

            # Include DRL if available
            drl_info = ""
            if "drl" in step:
                drl_info = f"\\nDRL: {step['drl']}"

            label = f"{escaped_tool}\\n{escaped_op}{drl_info}"
            lines.append(
                f'  "step_{step_id}" [shape=ellipse, label="{label}", style=filled, fillcolor=palegreen];'
            )

        lines.append("")
        lines.append("  // Edges (data flow)")

        # Add edges
        for step in steps:
            step_id = step["step_id"]

            # Input edges
            for inp in step["inputs"]:
                escaped_path = inp["path"].replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'  "{escaped_path}" -> "step_{step_id}";')

            # Output edges
            for out in step["outputs"]:
                escaped_path = out["path"].replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'  "step_{step_id}" -> "{escaped_path}";')

        lines.append("}")
        return "\n".join(lines)
