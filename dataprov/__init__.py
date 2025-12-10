"""
Data Provenance Tracking Library

A simplified library for tracking data provenance through processing chains.
Records tool executions, file transformations, and maintains full lineage
from raw data to final outputs.

Example:
    from dataprov import ProvenanceChain

    chain = ProvenanceChain.create(
        entity_id="dataset_001",
        initial_source="/path/to/raw/data/",
        description="Video processing pipeline",
        tags=["video", "processing"]
    )

    chain.add(
        tool_name="video_processor",
        tool_version="1.0",
        operation="stabilization",
        inputs=["/path/to/input.mp4"],
        input_formats=["MP4"],
        outputs=["/path/to/output.mp4"],
        output_formats=["MP4"],
        drl=3
    )

    chain.save("provenance.json")
"""

import importlib.resources
import json

from dataprov.dataprov import ProvenanceChain

__version__ = "3.0.0"
__all__ = ["ProvenanceChain", "get_schema"]


def get_schema():
    """Return the W3C PROV-JSON schema as a dictionary.

    Returns:
        dict: The JSON schema for dataprov's W3C PROV-JSON format.

    Example:
        >>> from dataprov import get_schema
        >>> schema = get_schema()
        >>> print(schema['$schema'])
    """
    schema_text = (
        importlib.resources.files("dataprov")
        .joinpath("dataprov_prov_schema.json")
        .read_text()
    )
    return json.loads(schema_text)
