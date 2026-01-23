<div align="center">
  <img src="docs/dataprov_logo.png" alt="dataprov logo" width="300"/>
</div>

# dataprov

[![CI](https://github.com/RI-SE/dataprov/actions/workflows/ci.yml/badge.svg)](https://github.com/RI-SE/dataprov/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/dataprov)](https://pypi.org/project/dataprov/)
[![GitHub Release](https://img.shields.io/github/v/release/RI-SE/dataprov)](https://github.com/RI-SE/dataprov/releases/latest)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A lightweight Python library for tracking data provenance through processing pipelines. Record tool executions, file transformations, and maintain complete lineage from raw data to final outputs using the W3C PROV standard (PROV-JSON format).

> [!NOTE]
> This open source project is maintained by [RISE Research Institutes of Sweden](https://ri.se/). See [LICENSE](LICENSE) file for open source license information.

## Features

- **W3C PROV Compliant**: Uses W3C PROV-JSON format for standards compliance and interoperability
- **Simple API**: Create and extend provenance chains with simple interface (PROV complexity hidden)
- **Complete Lineage**: Track inputs, outputs, transformations, and tool metadata as PROV entities and activities
- **File Integrity**: Automatic SHA256 checksums for data files and provenance references
- **Provenance Linking**: PROV Bundles for embedding or referencing upstream provenance chains
- **Data Readiness Levels**: Optional DRL (0-9) tracking per processing step
- **Execution Timing**: User-provided start/end timestamps (optional end time)
- **Agent Tracking**: Optional user/system tracking per step for accountability
- **Attribution Support**: Direct entity-to-agent relationships for manually created files, external data sources, and data ownership
- **Custom Ontologies**: Extend with domain-specific metadata using custom namespace prefixes (Dublin Core, FOAF, etc.)
- **Environment Capture**: Record execution environment per step for reproducibility
- **Schema-Compliant**: JSON Schema validation for PROV-JSON structure
- **CLI Tools**: Command-line utilities for chain management, conversion, visualization (GraphViz DOT graphs and HTML reports)
- **Zero Dependencies**: Uses only Python standard library

## Contents

- [dataprov](#dataprov)
  - [Features](#features)
  - [Contents](#contents)
  - [Installation](#installation)
    - [Using dataprov in Your Project](#using-dataprov-in-your-project)
    - [Local Development Install](#local-development-install)
  - [Quick Start](#quick-start)
    - [Creating a Provenance Chain](#creating-a-provenance-chain)
    - [Loading and Extending Chains](#loading-and-extending-chains)
    - [Access the W3C PROV-JSON schema](#access-the-w3c-prov-json-schema)
  - [Usage Examples](#usage-examples)
    - [Execution Timing](#execution-timing)
    - [Provenance File Inlining](#provenance-file-inlining)
    - [Agent Tracking](#agent-tracking)
    - [Attribution (wasAttributedTo)](#attribution-wasattributedto)
      - [Basic Usage](#basic-usage)
      - [Multiple Files](#multiple-files)
      - [Automation Features](#automation-features)
      - [Use Case Example](#use-case-example)
    - [Custom Ontologies](#custom-ontologies)
      - [Define Custom Namespaces](#define-custom-namespaces)
      - [Add Custom Properties with Target Prefixes](#add-custom-properties-with-target-prefixes)
      - [Add Custom Properties with add\_attribution()](#add-custom-properties-with-add_attribution)
      - [Add Top-Level Custom Metadata](#add-top-level-custom-metadata)
      - [Creating Your Own Ontology](#creating-your-own-ontology)
    - [Environment Capture](#environment-capture)
    - [Enhanced Queries](#enhanced-queries)
    - [Precise Input-Output Mapping](#precise-input-output-mapping)
    - [Visualization](#visualization)
  - [CLI Tools](#cli-tools)
    - [dataprov-new](#dataprov-new)
    - [dataprov-visualize](#dataprov-visualize)
    - [dataprov-add-attribution](#dataprov-add-attribution)
    - [dataprov-report](#dataprov-report)
  - [API Reference](#api-reference)
    - [ProvenanceChain Class](#provenancechain-class)
      - [Class Methods](#class-methods)
      - [Instance Methods](#instance-methods)
  - [Data Readiness Levels (DRL)](#data-readiness-levels-drl)
  - [W3C PROV-JSON Format](#w3c-prov-json-format)
    - [Structure Overview](#structure-overview)
    - [Example PROV-JSON File](#example-prov-json-file)
    - [PROV Bundles](#prov-bundles)
  - [Dataprov Ontology](#dataprov-ontology)
    - [Key Features](#key-features)
    - [Core Properties by Domain](#core-properties-by-domain)
    - [Ontology Documentation](#ontology-documentation)
  - [Use Case Examples](#use-case-examples)
    - [Video Processing Pipelines](#video-processing-pipelines)
    - [Linking Multiple Provenance Chains](#linking-multiple-provenance-chains)
  - [Comparison with Other Provenance Systems](#comparison-with-other-provenance-systems)
    - [W3C PROV-JSON Compatibility](#w3c-prov-json-compatibility)
  - [Project Structure](#project-structure)
  - [Testing](#testing)
  - [Schema Version](#schema-version)
  - [Acknowledgement](#acknowledgement)

## Installation

### Using dataprov in Your Project

**Install from PyPI:**

```bash
pip install dataprov
```

**Add to `pyproject.toml`:**

```toml
[project]
dependencies = [
    "dataprov>=3.0.0",
]
```

Or as an optional dependency:

```toml
[project.optional-dependencies]
provenance = ["dataprov>=3.0.0"]
```

**Alternative: Add to `requirements.txt`:**

```
dataprov>=3.0.0
```

### Local Development Install

**Using uv (recommended)**

```bash
# Clone the repository
git clone https://github.com/RI-SE/dataprov.git
cd dataprov

# Install package with development dependencies using uv
uv sync --dev
```

**Alternative: Using venv and pip**

```bash
# Clone the repository
git clone https://github.com/RI-SE/dataprov.git
cd dataprov

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package with development dependencies
pip install -e ".[dev]"
```

**Note**: This package has no external runtime dependencies (uses only Python standard library). Development dependencies (pytest, pytest-cov) are only needed for running tests.

## Quick Start

### Creating a Provenance Chain

```python
from dataprov import ProvenanceChain

# Initialize a new provenance chain
chain = ProvenanceChain.create(
    entity_id="dataset_001",
    initial_source="/data/raw_videos/",
    description="Video processing pipeline",
    tags=["video", "processing", "2024"]
)

# Add a processing step (you provide timestamps)
chain.add(
    started_at="2024-10-15T10:00:00Z",
    ended_at="2024-10-15T10:05:30Z",
    tool_name="video_stabilizer",
    tool_version="2.1.0",
    operation="video_stabilization",
    inputs=["/data/raw_video.mp4"],
    input_formats=["MP4"],
    outputs=["/data/stabilized_video.mp4"],
    output_formats=["MP4"],
    arguments="--method optical_flow --smooth 10",
    drl=3  # Data Readiness Level (optional)
)

# Save the provenance chain
chain.save("provenance.json")
```

### Loading and Extending Chains

```python
# Load existing chain
chain = ProvenanceChain.load("provenance.json")

# Add another step
chain.add(
    started_at="2024-10-15T11:00:00Z",
    ended_at="2024-10-15T11:03:00Z",
    tool_name="video_compressor",
    tool_version="1.5",
    operation="video_compression",
    inputs=["/data/stabilized_video.mp4"],
    input_formats=["MP4"],
    outputs=["/data/final_video.mp4"],
    output_formats=["MP4"],
    drl=5
)

# Save updated chain
chain.save("provenance.json")
```

### Access the W3C PROV-JSON schema

```python
from dataprov import get_schema

# Get the JSON schema for validation or inspection
schema = get_schema()
```

##  Usage Examples

### Execution Timing

**User-provided timestamps** - You provide the start and end times for each processing step, allowing you to record the actual data processing time (not the provenance tracking time):

```python
# Measure your data processing time
from datetime import datetime, timezone

start_time = datetime.now(timezone.utc)
# ... run your data processing tool ...
end_time = datetime.now(timezone.utc)

# Add the step with timing
chain.add(
    started_at=start_time.isoformat().replace("+00:00", "Z"),
    ended_at=end_time.isoformat().replace("+00:00", "Z"),
    tool_name="processor",
    tool_version="1.0",
    operation="processing",
    inputs=["input.txt"],
    input_formats=["TXT"],
    outputs=["output.txt"],
    output_formats=["TXT"]
)

# Or provide timestamps directly:
chain.add(
    started_at="2024-03-15T10:00:00Z",
    ended_at="2024-03-15T10:05:30Z",
    tool_name="processor",
    tool_version="1.0",
    operation="processing",
    inputs=["input.txt"],
    input_formats=["TXT"],
    outputs=["output.txt"],
    output_formats=["TXT"]
)
```

The `ended_at` timestamp is optional:

```python
# Add a step without an end time
chain.add(
    started_at="2024-10-15T10:00:00Z",
    tool_name="long_running_process",
    tool_version="1.0",
    operation="data_processing",
    inputs=["large_dataset.csv"],
    input_formats=["CSV"],
    outputs=["processed_data.csv"],
    output_formats=["CSV"]
)

# When you save, last_modified will be set to current time automatically
chain.save("provenance.json")
```

### Provenance File Inlining

**Combine multiple provenance files into one** - When merging datasets with their own provenance chains, you can provide a list of referenced provenance files and choose how to handle the referenced provenance files:

```python
# Reference mode (default) - keeps referenced file paths as-is
chain.save("output.json")
# or explicitly:
chain.save("output.json", input_prov="reference")

# Inline mode - embeds all referenced provenance files into a single JSON
chain.save("output.json", input_prov="inline")

# Both mode - inlines files AND keeps original paths for traceability
chain.save("output.json", input_prov="both")
```

When using inline or both mode:
- All referenced provenance files are embedded as PROV Bundles
- Nested provenance files are recursively inlined (preserving the hierarchy)
- Each inlined file gets a unique bundle ID based on its position:
  - Files referenced from the main chain: `bundle:step{N}_input{M}` (e.g., `bundle:step1_input0`, `bundle:step2_input1`)
  - Nested files (referenced within other provenance files): `bundle:nested_{N}` (e.g., `bundle:nested_0`, `bundle:nested_1`)
- SHA256 checksums are stored for all original provenance files
- Bundle references include the original file path for traceability

**Example with inlining:**

```python
# Create upstream provenance
upstream_chain = ProvenanceChain.create(
    entity_id="upstream_data",
    initial_source="/raw/sensor_data/"
)
upstream_chain.add(
    started_at="2024-10-15T08:00:00Z",
    ended_at="2024-10-15T08:30:00Z",
    tool_name="sensor_calibration",
    tool_version="1.0",
    operation="calibration",
    inputs=["/raw/sensor_data/raw.csv"],
    input_formats=["CSV"],
    outputs=["/processed/calibrated.csv"],
    output_formats=["CSV"]
)
upstream_chain.save("/processed/upstream_prov.json")

# Create main chain that references upstream
main_chain = ProvenanceChain.create(
    entity_id="merged_dataset",
    initial_source="/processed/"
)
main_chain.add(
    started_at="2024-10-15T09:00:00Z",
    ended_at="2024-10-15T09:15:00Z",
    tool_name="data_merger",
    tool_version="2.0",
    operation="merge",
    inputs=["/processed/calibrated.csv"],
    input_formats=["CSV"],
    outputs=["/final/merged.csv"],
    output_formats=["CSV"],
    input_provenance_files=["/processed/upstream_prov.json"]  # Reference upstream
)

# Save with inlining - creates a self-contained provenance file
main_chain.save("/final/complete_prov.json", input_prov="inline")
```

The resulting file will contain the complete provenance history in a single JSON, with the upstream chain embedded as a PROV Bundle.

When referencing provenance files, SHA256 checksums for the referenced filed are automatically calculated and stored. This allows you to verify that referenced provenance files haven't been altered.

### Agent Tracking

**Optional user/system tracking** - Track who executed each step for accountability:

```python
# Enable automatic agent capture
chain.add(
    started_at="2024-03-15T10:00:00Z",
    ended_at="2024-03-15T10:05:30Z",
    tool_name="processor",
    tool_version="1.0",
    operation="processing",
    inputs=["input.txt"],
    input_formats=["TXT"],
    outputs=["output.txt"],
    output_formats=["TXT"],
    capture_agent=True  # Auto-detect user and hostname
)

# Override automatic agent information
chain.add(
    started_at="2024-03-15T11:00:00Z",
    ended_at="2024-03-15T11:03:00Z",
    tool_name="processor",
    tool_version="1.0",
    operation="processing",
    inputs=["input.txt"],
    input_formats=["TXT"],
    outputs=["output.txt"],
    output_formats=["TXT"],
    capture_agent=True,
    user="service_account",
    hostname="processing-server-01"
)
```

### Attribution (wasAttributedTo)

**Direct entity-to-agent relationships** - Use `add_attribution()` to create `wasAttributedTo` relationships for files that were created, curated, or owned by agents without a computational activity. This is useful for:

- **Manually created/curated files** - Reference datasets, configuration files, manually annotated data
- **External data sources** - Census data, public datasets, third-party data
- **Data ownership/responsibility** - Establish who is responsible for or authored a dataset

Unlike `add()` which tracks computational activities (what process created a file), `add_attribution()` tracks attribution (who is responsible for or created a file).

#### Basic Usage

```python
# Attribute to current user (for manually curated data)
chain.add_attribution(
    files="reference/gene_names.csv",
    capture_current_user=True,
    role="curator"
)

# Attribute to external person
chain.add_attribution(
    files="data/patient_records.csv",
    agent_name="dr.smith@hospital.org",
    agent_type="prov:Person",
    role="principal_investigator"
)

# Attribute to organization (for external data)
chain.add_attribution(
    files="data/census_2020.csv",
    agent_name="US Census Bureau",
    agent_type="prov:Organization"
)
```

#### Multiple Files

Attribute multiple files to the same agent in one call:

```python
# Multiple files with same attribution
chain.add_attribution(
    files=[
        "reference/gene_ontology.csv",
        "reference/protein_database.csv",
        "reference/pathway_annotations.csv"
    ],
    agent_name="curator_team@university.edu",
    role="data_curator"
)
```

#### Automation Features

The method automatically:
- **Detects file format** from extension (can be overridden)
- **Calculates checksums** (SHA256) for existing files
- **Records file size** for existing files
- **Captures creation time** from file mtime (can be overridden)
- **Auto-detects user/hostname** when `capture_current_user=True`

```python
# With explicit format and creation time
chain.add_attribution(
    files="legacy_data.dat",
    file_formats="BINARY",
    agent_name="legacy_system",
    agent_type="prov:Organization",
    created_at="2020-01-15T00:00:00Z"
)
```

#### Use Case Example

Here's a complete example showing attribution for different types of data sources:

```python
from dataprov import ProvenanceChain

# Initialize chain
chain = ProvenanceChain.create(
    entity_id="genomics_study",
    initial_source="/project/data/",
    description="Multi-source genomics study"
)

# 1. Manual curation by current user
chain.add_attribution(
    files="config/analysis_parameters.yaml",
    capture_current_user=True,
    role="analyst"
)

# 2. External public dataset
chain.add_attribution(
    files="reference/public_genome_db.fasta",
    agent_name="NCBI GenBank",
    agent_type="prov:Organization"
)

# 3. Collaborator-provided data
chain.add_attribution(
    files=[
        "input/patient_cohort_A.vcf",
        "input/patient_cohort_B.vcf"
    ],
    agent_name="dr.johnson@med-center.org",
    agent_type="prov:Person",
    role="principal_investigator"
)

# 4. Now track the computational processing with add()
chain.add(
    started_at="2024-03-15T10:00:00Z",
    ended_at="2024-03-15T10:30:00Z",
    tool_name="variant_caller",
    tool_version="3.2",
    operation="variant_calling",
    inputs=[
        "input/patient_cohort_A.vcf",
        "input/patient_cohort_B.vcf",
        "reference/public_genome_db.fasta"
    ],
    input_formats=["VCF", "VCF", "FASTA"],
    outputs=["results/variants.vcf"],
    output_formats=["VCF"]
)

chain.save("genomics_provenance.json")
```

This creates a complete provenance record showing:
- **Attribution** (`wasAttributedTo`): Who created/provided each input file
- **Activity** (`add`): What computational process was performed

### Custom Ontologies

**Extend with domain-specific metadata** - Add custom namespace prefixes and properties from your own ontologies or standard vocabularies like Dublin Core, FOAF, etc.

#### Define Custom Namespaces

```python
# Create chain with custom ontology namespaces
chain = ProvenanceChain.create(
    entity_id="dataset_001",
    initial_source="/data/raw/",
    custom_namespaces={
        "myapp": "https://example.com/myapp/ontology/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "dcterms": "http://purl.org/dc/terms/"
    }
)
```

The namespace prefixes are added to the PROV-JSON `prefix` section alongside the required `dataprov`, `prov`, and `xsd` namespaces.

#### Add Custom Properties with Target Prefixes

Custom properties use the format `target:namespace:property` where target specifies what to add the property to:

- `entity` - All entities (both inputs and outputs)
- `input-entity` - Input entities only
- `output-entity` - Output entities only
- `activity` - The processing activity
- `agent` - The software/tool agent

```python
# Add processing step with custom properties on different targets
chain.add(
    started_at="2024-03-15T10:00:00Z",
    ended_at="2024-03-15T10:05:30Z",
    tool_name="image_processor",
    tool_version="2.1",
    operation="enhancement",
    inputs=["raw_image.jpg"],
    input_formats=["JPEG"],
    outputs=["enhanced_image.jpg"],
    output_formats=["JPEG"],
    custom_properties={
        # Properties on output entities
        "output-entity:myapp:qualityScore": 95,
        "output-entity:dcterms:license": "CC-BY-4.0",
        # Properties on the activity
        "activity:myapp:processingMode": "automatic",
        "activity:myapp:gpuUsed": True,
        # Properties on the agent
        "agent:myapp:licenseKey": "ABC-123"
    }
)
```

#### Add Custom Properties with add_attribution()

```python
# Attribute file with custom metadata
chain.add_attribution(
    files="survey_data.csv",
    agent_name="Dr. Jane Smith",
    agent_type="prov:Person",
    role="principal_investigator",
    custom_properties={
        # Properties on the entity
        "entity:myapp:fundingSource": "NSF Grant #12345",
        "entity:myapp:ethicsApproval": "IRB-2024-001",
        "entity:dcterms:created": "2024-01-15",
        # Properties on the agent
        "agent:myapp:department": "Biology",
        "agent:myapp:orcid": "0000-0002-1825-0097"
    }
)
```

#### Add Top-Level Custom Metadata

```python
# Add custom metadata sections at the top level
chain = ProvenanceChain.create(
    entity_id="dataset_001",
    initial_source="/data/raw/",
    custom_namespaces={
        "myapp": "https://example.com/myapp/ontology/"
    },
    custom_metadata={
        "myapp:projectId": "PROJ-12345",
        "myapp:funding": "NSF Grant #67890",
        "myapp:pi": "dr.smith@university.edu"
    }
)
```

#### Creating Your Own Ontology

See the [`ontology/`](ontology/) directory for a complete example of creating a domain ontology in Turtle (RDF) format. The dataprov ontology extends W3C PROV-O with data provenance-specific classes and properties. For detailed ontology documentation, see [ontology/README.md](ontology/README.md).

**Key points:**
- Define your ontology namespace URI (e.g., `https://example.com/myapp/ontology/`)
- Extend W3C PROV-O classes (`prov:Entity`, `prov:Activity`, `prov:Agent`)
- Define domain-specific properties with `rdfs:domain`, `rdfs:range`, and `rdfs:comment`
- Save as `.ttl` file for semantic web tools
- Pass namespace prefix/URI mapping to `create()` for use in dataprov

**Validation:**

**IMPORTANT:** The library performs minimal validation of custom properties:
- ✅ **Namespace prefix validation** - Checks that the prefix (e.g., `myapp` in `myapp:field`) is declared in `custom_namespaces`
- ✅ **Format validation** - Checks that properties use the `target:namespace:property` format
- ❌ **No ontology validation** - Properties are NOT validated against ontology definitions
- ❌ **No property existence check** - The library does NOT check if a property exists in the ontology
- ❌ **No type/range validation** - Property values are NOT validated against expected types or ranges
- ❌ **No domain validation** - The library does NOT check if properties are valid for their target (entity/activity/agent)

**Applications are responsible for ensuring that custom properties match their ontology definitions.** The library only ensures that namespace prefixes are declared - it does not load or validate against actual ontology files. This is to keep the dataprov implementation light and free of external dependences.

### Environment Capture

**Record execution environment** - Capture runtime, platform, and system info per step for reproducibility:

```python
# Capture environment for a specific step
chain.add(
    started_at="2024-03-15T10:00:00Z",
    ended_at="2024-03-15T10:05:30Z",
    tool_name="processor",
    tool_version="1.0",
    operation="processing",
    inputs=["input.txt"],
    input_formats=["TXT"],
    outputs=["output.txt"],
    output_formats=["TXT"],
    capture_environment=True  # Auto-detect python environment
)

# Override for non-Python applications
chain.add(
    started_at="2024-03-15T11:00:00Z",
    ended_at="2024-03-15T11:05:00Z",
    tool_name="node_processor",
    tool_version="2.0",
    operation="processing",
    inputs=["input.txt"],
    input_formats=["TXT"],
    outputs=["output.txt"],
    output_formats=["TXT"],
    capture_environment=True,
    runtime="Node.js",
    runtime_version="18.0.0"
)
```

### Enhanced Queries

**Advanced search with AND logic** - All specified criteria must match:

```python
# Find all steps by a specific tool
steps = chain.find_steps(tool_name="video_stabilizer")

# Find steps in a date range with high DRL
steps = chain.find_steps(
    date_from="2024-01-01T00:00:00Z",
    date_to="2024-12-31T23:59:59Z",
    drl_min=5
)

# Find steps by user
steps = chain.find_steps(user="testuser")

# Complex query with AND logic (all criteria must match)
steps = chain.find_steps(
    tool_name="processor",
    drl_min=5,
    user="testuser"
)

# Query by file pattern
steps = chain.find_steps(file_pattern="*.mp4")

# Query by log content (regex)
steps = chain.find_steps(log_regex="ERROR|WARNING")
```

Available query parameters:
- `tool_name`: Filter by tool name
- `operation`: Filter by operation name
- `date_from` / `date_to`: Filter by date range (ISO 8601 format)
- `drl_min` / `drl_max`: Filter by Data Readiness Level range
- `user`: Filter by username
- `hostname`: Filter by hostname
- `file_pattern`: Filter by input/output file pattern (glob-style)
- `log_regex`: Filter by output log content (regex)

### Precise Input-Output Mapping

**Control derivation relationships** - By default, all outputs derive from all inputs. For batch processing where specific inputs produce specific outputs, use `derivation_map`:

```python
# Example: Batch video processing with shared audio track
chain.add(
    started_at="2024-10-15T10:00:00Z",
    ended_at="2024-10-15T10:10:00Z",
    tool_name="batch_video_processor",
    tool_version="2.0",
    operation="mux_audio_to_videos",
    inputs=["video1.mp4", "video2.mp4", "video3.mp4", "audio.wav"],
    input_formats=["MP4", "MP4", "MP4", "WAV"],
    outputs=["final1.mp4", "final2.mp4", "final3.mp4"],
    output_formats=["MP4", "MP4", "MP4"],
    # Precise mapping: each video + audio -> corresponding output
    derivation_map={
        0: [0],      # video1.mp4 -> final1.mp4
        1: [1],      # video2.mp4 -> final2.mp4
        2: [2],      # video3.mp4 -> final3.mp4
        3: [0, 1, 2] # audio.wav -> all three outputs
    }
)
```

**Without `derivation_map`**, the provenance would incorrectly show:
- final1.mp4 deriving from video2.mp4 and video3.mp4 (wrong!)
- All 12 possible input-output combinations (4 inputs × 3 outputs)

**With `derivation_map`**, the provenance correctly shows:
- final1.mp4 derives from video1.mp4 and audio.wav only
- final2.mp4 derives from video2.mp4 and audio.wav only
- final3.mp4 derives from video3.mp4 and audio.wav only

This creates precise PROV `wasDerivedFrom` relationships that accurately reflect the actual data flow.

### Visualization

**Generate GraphViz DOT graphs**:

```python
# Generate DOT format
dot_graph = chain.to_dot()

# Save to file
with open("provenance.dot", "w") as f:
    f.write(dot_graph)

# Render with GraphViz (if installed):
# dot -Tpng provenance.dot -o provenance.png
# dot -Tsvg provenance.dot -o provenance.svg
```

## CLI Tools

### dataprov-new

Create a new provenance chain file:

```bash
dataprov-new \
    --initial-source /data/raw_videos/ \
    --output provenance.json \
    --entity-id dataset_001 \
    --description "Video processing pipeline" \
    --tags video,processing,2024
```

### dataprov-visualize

Generate GraphViz DOT visualization:

```bash
# Generate DOT file
dataprov-visualize provenance.json -o provenance.dot

# Generate PNG directly (requires graphviz installed)
dataprov-visualize provenance.json | dot -Tpng -o provenance.png

# Generate SVG
dataprov-visualize provenance.json | dot -Tsvg -o provenance.svg

# Hide nested provenance bundles (show only main chain)
dataprov-visualize provenance.json --flatten-bundles | dot -Tpng -o simple.png

# Normalize paths to handle path prefix mismatches between steps
dataprov-visualize provenance.json --normalize-paths | dot -Tpng -o normalized.png
```

### dataprov-add-attribution

Add attribution relationships for manually created or external files:

```bash
# Single file - attribute to current user
dataprov-add-attribution -p provenance.json -i reference/data.csv \
  --current-user --role curator

# Single file - attribute to organization
dataprov-add-attribution -p provenance.json -i census.csv \
  --agent-name "US Census Bureau" --agent-type organization

# Multiple files to same agent
dataprov-add-attribution -p provenance.json \
  -i file1.csv file2.csv file3.csv \
  --agent-name "dr.smith@hospital.org" --role "principal_investigator"

# Works with shell wildcards
dataprov-add-attribution -p provenance.json -i reference/*.csv \
  --agent-name "curator_team" --role "data_curator"

# Output to new file instead of in-place modification
dataprov-add-attribution -p provenance.json -i data.csv \
  --agent-name "curator" -o provenance_updated.json
```

Use this tool to attribute files that were:
- Manually created or curated (use `--current-user`)
- Obtained from external sources (use `--agent-name` with organization)
- Created by collaborators (use `--agent-name` with person)

### dataprov-report

Generate HTML report:

```bash
# Generate HTML report
dataprov-report provenance.json -o report.html

# Hide nested provenance bundles (show only main chain)
dataprov-report provenance.json --flatten-bundles -o simple_report.html
```

The HTML report includes:
- Chain metadata and timeline
- Detailed step-by-step breakdown
- Agent/user information per step
- Environment information per step
- File checksums and sizes
- Nested provenance bundles for inputs (showing how input files were created)
- Interactive styling

## API Reference

### ProvenanceChain Class

#### Class Methods

**`create(entity_id, initial_source, description="", tags=None, custom_namespaces=None, custom_metadata=None)`**

Create a new provenance chain.

- `entity_id` (str): Unique identifier for the data entity
- `initial_source` (str): Original source file or location
- `description` (str, optional): Human-readable description
- `tags` (list, optional): Tags for categorizing the data
- `custom_namespaces` (dict, optional): Custom ontology namespaces as {prefix: URI} dict
- `custom_metadata` (dict, optional): Custom top-level metadata with format {namespace:property: value}

Returns: `ProvenanceChain` instance

**`load(filepath)`**

Load an existing provenance chain from a JSON file.

- `filepath` (str): Path to the provenance JSON file

Returns: `ProvenanceChain` instance

**`load_or_create(filepath, **create_kwargs)`**

Load existing chain or create new one if file doesn't exist.

- `filepath` (str): Path to the provenance JSON file
- `**create_kwargs`: Arguments for `create()` if file doesn't exist

Returns: `ProvenanceChain` instance

#### Instance Methods

**`add(started_at, ended_at, tool_name, tool_version, operation, inputs, input_formats, outputs, output_formats, **optional)`**

Add a processing step to the chain.

Required parameters:
- `started_at` (str): ISO 8601 timestamp when processing started
- `ended_at` (str or None): ISO 8601 timestamp when processing ended (optional, can be None for ongoing/incomplete processing)
- `tool_name` (str): Name of the tool
- `tool_version` (str): Version of the tool
- `operation` (str): Description of the operation
- `inputs` (list): Input file paths
- `input_formats` (list): Input file formats
- `outputs` (list): Output file paths
- `output_formats` (list): Output file formats

Optional parameters:
- `source` (str): Tool source or organization
- `arguments` (str): Command line arguments
- `output_log` (str): Tool execution log output
- `warnings` (str): Warning messages
- `input_provenance_files` (list): Provenance files for inputs (checksums calculated automatically)
- `drl` (int): Data Readiness Level (0-9)
- `derivation_map` (dict): Precise input-output mapping {input_idx: [output_indices]} (default: None = all-to-all)
- `capture_agent` (bool): Capture user/system info (default: False)
- `user` (str): Override username
- `hostname` (str): Override hostname
- `capture_environment` (bool): Capture execution environment (default: False)
- `runtime` (str): Override runtime name (default: auto-detect)
- `runtime_version` (str): Override runtime version (default: auto-detect)
- `custom_properties` (dict, optional): Custom ontology properties with format `target:namespace:property`.
                        Targets: `entity`, `input-entity`, `output-entity`, `activity`, `agent`.
                        Example: `custom_properties={"output-entity:myapp:score": 95, "activity:myapp:mode": "fast"}`

Returns: `bool` - True if successful, False otherwise

**`add_attribution(files, file_formats=None, agent_name=None, agent_type="prov:Person", capture_current_user=False, **optional)`**

Add attribution relationships (wasAttributedTo) for files without requiring a computational activity.

Required parameters (specify exactly one agent option):
- `files` (str or list): Single file path or list of file paths to attribute
- `agent_name` (str): Name of external agent (person or organization) - mutually exclusive with `capture_current_user`
- `capture_current_user` (bool): If True, attribute to current user - mutually exclusive with `agent_name`

Optional parameters:
- `file_formats` (str or list): File format(s) - auto-detected from extension if not provided
- `agent_type` (str): Type of agent - "prov:Person" (default) or "prov:Organization"
- `user` (str): Override username for current user capture (default: auto-detect)
- `hostname` (str): Override hostname for current user capture (default: auto-detect)
- `created_at` (str): ISO 8601 timestamp when file was created (default: auto-detect from file mtime)
- `role` (str): Free-text role of the agent (e.g., "curator", "author", "principal_investigator")
- `custom_properties` (dict, optional): Custom ontology properties with format `target:namespace:property`.
                        Targets: `entity` (for attributed entities), `agent` (for the agent).
                        Example: `custom_properties={"entity:myapp:quality": "high", "agent:myapp:dept": "research"}`

Returns: `bool` - True if successful, False otherwise

**`save(filepath, input_prov="reference")`**

Save the provenance chain to a JSON file.

- `filepath` (str): Path where to save the file
- `input_prov` (str): How to handle input provenance files: "reference" (default), "inline", or "both"
  - `"reference"`: Keep file paths as-is (default)
  - `"inline"`: Embed provenance files into a single JSON
  - `"both"`: Inline files AND keep original paths

**`get_steps()`**

Get all processing steps in the chain.

Returns: `list` - All processing steps

**`get_step(step_id)`**

Get a specific step by ID.

- `step_id` (int): The step ID to retrieve

Returns: `dict` or `None` - Step data or None if not found

**`get_latest_step()`**

Get the most recent processing step.

Returns: `dict` or `None` - Latest step or None if no steps exist

**`find_steps(**criteria)`**

Find steps matching specified criteria. All criteria must match (AND logic).

- `**criteria`: Search criteria (see Enhanced Queries section above)

Returns: `list` - Matching steps

**`validate()`**

Validate chain integrity and schema compliance.

Returns: `tuple` - `(is_valid, list_of_errors)`

**`to_dot(include_bundles=True, normalize_paths=False)`**

Generate GraphViz DOT format visualization.

- `include_bundles` (bool): If True (default), render nested provenance bundles as subgraphs
- `normalize_paths` (bool): If True, match entities by filename when full paths don't match (helps with path prefix mismatches between processing steps)

Returns: `str` - DOT format graph

## Data Readiness Levels (DRL)

The library supports optional Data Readiness Level tracking per processing step. DRL values range from 0-9. The meaning is user-defined to be adapted to your specific use-case.

Example:
- **0**: Unassessed / Unknown readiness
- **1-3**: Raw to preliminary processing
- **4-6**: Processed and validated data
- **7-9**: Fully validated, production-ready data

DRL values are optional and can be omitted if not relevant to your workflow.

## W3C PROV-JSON Format

Provenance chains are stored as W3C PROV-JSON files. While the format is standards-compliant, the simple API hides PROV complexity.

### Structure Overview

PROV-JSON uses these core concepts:
- **Entities**: Data files and datasets
- **Activities**: Processing steps and transformations
- **Agents**: Tools, users, and systems
- **Relationships**: Usage, generation, derivation, and association

### Example PROV-JSON File

```json
{
  "prefix": {
    "dataprov": "https://ri-se.github.io/dataprov/ontology/dataprov.ttl",
    "prov": "http://www.w3.org/ns/prov#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "dataprov:metadata": {
    "version": "3.0",
    "created": "2024-10-15T10:30:00Z",
    "lastModified": "2024-10-15T12:45:00Z",
    "rootEntityId": "dataset_001",
    "description": "Video processing pipeline",
    "initialSource": "/data/raw_videos/",
    "tags": ["video", "processing"]
  },
  "entity": {
    "dataset_001": {
      "prov:type": "dataprov:RootEntity",
      "prov:atLocation": "/data/raw_videos/"
    },
    "entity:/data/raw_video.mp4": {
      "prov:type": "dataprov:DataFile",
      "dataprov:format": "MP4",
      "dataprov:checksum": "sha256:abc123...",
      "dataprov:sizeBytes": 102400
    },
    "entity:/data/stabilized_video.mp4": {
      "prov:type": "dataprov:DataFile",
      "dataprov:format": "MP4",
      "dataprov:checksum": "sha256:def456...",
      "dataprov:sizeBytes": 98304
    }
  },
  "activity": {
    "activity:step_1": {
      "prov:startedAtTime": "2024-10-15T11:00:00Z",
      "prov:endedAtTime": "2024-10-15T11:05:30Z",
      "dataprov:operation": "video_stabilization",
      "dataprov:arguments": "--method optical_flow --smooth 10",
      "dataprov:outputLog": "Processing completed successfully",
      "dataprov:warnings": "",
      "dataprov:drl": 3
    }
  },
  "agent": {
    "agent:tool_video_stabilizer_2.1.0": {
      "prov:type": "prov:SoftwareAgent",
      "dataprov:toolName": "video_stabilizer",
      "dataprov:toolVersion": "2.1.0",
      "dataprov:user": "fredrik",
      "dataprov:hostname": "workstation-01",
      "dataprov:agentType": "human",
      "dataprov:runtime": "CPython",
      "dataprov:runtimeVersion": "3.11.5",
      "dataprov:platform": "Linux-6.2.0-x86_64",
      "dataprov:machine": "x86_64",
      "dataprov:processor": "Intel(R) Core(TM) i7"
    }
  },
  "used": {
    "_:u_1_0": {
      "prov:activity": "activity:step_1",
      "prov:entity": "entity:/data/raw_video.mp4"
    }
  },
  "wasGeneratedBy": {
    "_:g_1_0": {
      "prov:entity": "entity:/data/stabilized_video.mp4",
      "prov:activity": "activity:step_1"
    }
  },
  "wasDerivedFrom": {
    "_:d_1_0_0": {
      "prov:generatedEntity": "entity:/data/stabilized_video.mp4",
      "prov:usedEntity": "entity:/data/raw_video.mp4",
      "prov:activity": "activity:step_1"
    }
  },
  "wasAssociatedWith": {
    "_:assoc_1": {
      "prov:activity": "activity:step_1",
      "prov:agent": "agent:tool_video_stabilizer_2.1.0"
    }
  }
}
```

### PROV Bundles

When provenance files are inlined (using `input_prov="inline"`), they are stored as PROV Bundles:

```json
{
  "entity": {
    "bundle:step1_input0": {
      "prov:type": "prov:Bundle",
      "dataprov:originalPath": "/upstream/prov.json",
      "dataprov:bundleChecksum": "sha256:..."
    }
  },
  "bundle": {
    "bundle:step1_input0": {
      "entity": { ... },
      "activity": { ... },
      "used": { ... },
      "wasGeneratedBy": { ... }
    }
  }
}
```

This enables complete provenance chains to be embedded while maintaining W3C PROV compliance.

## Dataprov Ontology

Dataprov extends the [W3C PROV Ontology](https://www.w3.org/TR/prov-o/) with domain-specific classes and properties for tracking data file provenance in processing pipelines.

**Namespace URI:** `https://ri-se.github.io/dataprov/ontology/dataprov.ttl#`
**Prefix:** `dataprov:`
**Version:** 3.0.0

### Key Features

The dataprov ontology adds specialized properties to W3C PROV for:

- **File tracking**: Checksums, formats, file sizes, creation timestamps
- **Processing metadata**: Operations, arguments, output logs, warnings
- **Tool information**: Tool names, versions, sources
- **Environment capture**: Runtime, platform, machine architecture
- **Data quality**: Data Readiness Levels (DRL 0-9)
- **Provenance linking**: Bundle support for chaining provenance files

### Core Properties by Domain

**Entity Properties** (files and datasets):
- `dataprov:checksum` - SHA256 file integrity verification
- `dataprov:format` - File format (CSV, JSON, MP4, etc.)
- `dataprov:sizeBytes` - File size in bytes
- `dataprov:createdAt` - Creation timestamp

**Activity Properties** (processing steps):
- `dataprov:operation` - Description of operation performed
- `dataprov:arguments` - Command-line arguments
- `dataprov:outputLog` - Console/log output
- `dataprov:drl` - Data Readiness Level (0-9)

**Agent Properties** (tools and users):
- `dataprov:toolName` / `toolVersion` / `toolSource` - Tool identification
- `dataprov:user` / `hostname` - User and system information
- `dataprov:runtime` / `runtimeVersion` - Execution environment
- `dataprov:platform` / `machine` / `processor` - Hardware details

### Ontology Documentation

For complete ontology documentation including and RDF/Turtle files, see:

**[ontology/README.md](ontology/README.md)**

The ontology directory contains:
- **dataprov.ttl** - Authoritative ontology in Turtle (RDF) format
- Complete property reference tables
- W3C PROV relationship documentation
- Validation examples

## Use Case Examples

### Video Processing Pipelines

Maintain lineage for video processing workflows.

```python
chain = ProvenanceChain.create(
    entity_id="video_project_001",
    initial_source="/footage/raw/",
    description="Drone footage processing",
    tags=["drone", "video", "aerial"]
)

# Stabilization step
chain.add(
    tool_name="drone_stabilizer",
    tool_version="2.0",
    operation="stabilization",
    inputs=["/footage/raw/flight_001.mp4"],
    input_formats=["MP4"],
    outputs=["/footage/stabilized/flight_001.mp4"],
    output_formats=["MP4"],
    drl=3
)

# Color correction step
chain.add(
    tool_name="color_corrector",
    tool_version="1.8",
    operation="color_correction",
    inputs=["/footage/stabilized/flight_001.mp4"],
    input_formats=["MP4"],
    outputs=["/footage/final/flight_001.mp4"],
    output_formats=["MP4"],
    drl=5
)
```

### Linking Multiple Provenance Chains

Track complex workflows where multiple inputs have their own provenance.

```python
# Each input video has its own provenance chain
chain = ProvenanceChain.create(
    entity_id="compilation_001",
    initial_source="multiple_sources",
    description="Video compilation from multiple sources"
)

chain.add(
    tool_name="video_merger",
    tool_version="1.0",
    operation="concatenation",
    inputs=[
        "/videos/video1.mp4",
        "/videos/video2.mp4",
        "/videos/video3.mp4"
    ],
    input_formats=["MP4", "MP4", "MP4"],
    outputs=["/videos/merged.mp4"],
    output_formats=["MP4"],
    # Link to provenance chains of input videos
    input_provenance_files=[
        "/videos/video1_prov.json",
        "/videos/video2_prov.json",
        None  # video3 has no provenance
    ],
    drl=4
)
```

## Comparison with Other Provenance Systems

The data provenance landscape includes formal standards, workflow systems, and specialized tools—each designed for different scales and use cases. **dataprov** occupies a specific niche: lightweight, retrospective file-level provenance for general-purpose data pipelines.

**Standards** like [W3C PROV](https://www.w3.org/TR/prov-overview/) provide comprehensive formal semantics. dataprov **implements a pragmatic subset of W3C PROV-JSON**, using the core entity/activity/agent model with five key relationships (used, wasGeneratedBy, wasDerivedFrom, wasAssociatedWith, wasAttributedTo). It omits advanced PROV features (collections, plans, delegation, activity-to-activity relationships) while extending PROV with domain-specific properties for file integrity (checksums, formats), execution tracking (logs, arguments), and data quality (DRL). This provides standards-based interoperability for core lineage while maintaining simplicity. [OpenLineage](https://openlineage.io/) offers a modern standard for capturing lineage metadata from data pipelines, focusing on integration with data orchestration tools like Airflow and Spark.

**ML/Data platforms** such as [DVC](https://dvc.org/), [MLflow](https://mlflow.org/), and [Pachyderm](https://www.pachyderm.com/) integrate versioning, experiment tracking, and pipeline execution. These require Git or database infrastructure and focus on reproducibility (prospective provenance: "what should run") rather than just lineage (retrospective: "what did run"). **Workflow systems** like [Nextflow](https://www.nextflow.io/), [Snakemake](https://snakemake.readthedocs.io/), and [CWL](https://www.commonwl.org/) embed provenance in scientific pipelines but couple it to workflow execution. **Enterprise lineage tools** like [Apache Atlas](https://atlas.apache.org/) and [Marquez](https://marquezproject.ai/) target large-scale data warehouses and require Hadoop or database infrastructure.

**dataprov** is designed for scenarios where you need simple, portable provenance without infrastructure dependencies: heterogeneous tool chains (Python, R, shell scripts), non-Git workflows, embedded systems, or cases where you want provenance files co-located with data. It trades comprehensive features for zero dependencies, human-readable JSON, and minimal learning curve—making it practical for quick integration into existing pipelines where heavier solutions would be overkill.

| Tool/Standard | Type | Dependencies | Granularity | Automation | Best For |
|---------------|------|--------------|-------------|------------|----------|
| [W3C PROV](https://www.w3.org/TR/prov-overview/) | Standard | Varies | Arbitrary | Manual | Formal interoperability, standards compliance |
| [OpenLineage](https://openlineage.io/) | Standard | None (spec) | Event-based | Automatic | Pipeline orchestration, enterprise lineage |
| [DVC](https://dvc.org/) | Platform | Git + storage | Commit | Automatic | ML versioning, experiment tracking |
| [MLflow](https://mlflow.org/) | Platform | Database | Run | Automatic | ML experiment tracking, model registry |
| [Pachyderm](https://www.pachyderm.com/) | Platform | Kubernetes | Commit | Automatic | Enterprise ML pipelines, data versioning |
| [Nextflow/Snakemake](https://www.nextflow.io/) | Workflow | Workflow engine | Task | Automatic | Scientific workflows, bioinformatics |
| [Apache Atlas](https://atlas.apache.org/) | Enterprise | Hadoop | Database/table | Automatic | Hadoop ecosystem, data governance |
| **dataprov** | Library | None (stdlib) | File + step | Manual | Lightweight pipelines, heterogeneous tools |

**Further Reading:**
- [W3C PROV Primer](https://www.w3.org/TR/prov-primer/)
- [OpenLineage Documentation](https://openlineage.io/docs/)
- [ML Provenance and Reproducibility (CMU)](https://mlip-cmu.github.io/book/24-versioning-provenance-and-reproducibility.html)
- [Data Lineage: State of the Art](https://medium.com/bliblidotcom-techblog/data-lineage-state-of-the-art-and-implementation-challenges-1ea8dccde9de)

### W3C PROV-JSON Compatibility

dataprov uses W3C PROV-JSON as its serialization format, implementing a focused subset:

**Included from W3C PROV:**
- Core types: `entity`, `activity`, `agent`, `bundle`
- Core relationships: `used`, `wasGeneratedBy`, `wasDerivedFrom`, `wasAssociatedWith`, `wasAttributedTo`
- Standard properties: `prov:type`, `prov:startedAtTime`, `prov:endedAtTime`, `prov:atLocation`

**Omitted from W3C PROV:**
- Advanced relationships: `wasInformedBy`, `actedOnBehalfOf`, `wasStartedBy`, `wasEndedBy`, collection operations
- Advanced features: Plans, roles, invalidation, revision, quotation, alternate/specialization

**dataprov-specific extensions (dataprov: namespace):**
- File integrity: `checksum`, `format`, `sizeBytes`
- Execution tracking: `operation`, `arguments`, `outputLog`, `warnings`
- Data quality: `drl` (Data Readiness Level 0-9)
- Environment: `toolName`, `toolVersion`, `user`, `hostname`, `platform`, `runtime`

This design provides PROV compatibility for core provenance graphs while optimizing for retrospective file-level lineage in data pipelines.

## Project Structure

```
dataprov/
├── dataprov/              # Main library package
│   ├── __init__.py        # Package exports
│   ├── dataprov.py        # Core ProvenanceChain class (PROV-JSON)
│   ├── dataprov_prov_schema.json  # JSON Schema for PROV-JSON (v3.0)
│   └── cli/               # Command-line tools
│       ├── __init__.py
│       ├── newprovchain.py   # CLI for creating chains
│       ├── visualize.py      # CLI for DOT visualization
│       └── report.py         # CLI for HTML reports
├── tests/                 # Test suite
│   ├── conftest.py        # Pytest fixtures
│   └── test_dataprov.py   # Unit tests (100+ tests)
├── pyproject.toml         # Package configuration (dependencies, metadata, CLI tools)
├── dataprov_logo.png      # Project logo
├── README.md              # This file
├── development.md         # Development roadmap and analysis
└── LICENSE                # License file
```

## Testing

Run the test suite with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dataprov --cov-report=term-missing

# Run specific test file
pytest tests/test_dataprov.py

# Run specific test class
pytest tests/test_dataprov.py::TestExecutionTiming

# Run specific test
pytest tests/test_dataprov.py::TestExecutionTiming::test_timing_fields_present
```

## Schema Version

Current provenance schema version: **3.0** (W3C PROV-JSON)

Schema location: `dataprov/dataprov_prov_schema.json`

**Note:** Versions of dataprov before 3.0 used a custom format not compliant to W3C PROV. This format is deprecated. Please use only dataprov v3+.


## Acknowledgement
<br><div align="center">
  <img src="docs/synergies.svg" alt="Synergies logo" width="200"/>
</div>

This package is developed as part of the [SYNERGIES](https://synergies-ccam.eu/) project.

<br><div align="center">
  <img src="docs/funded_by_eu.svg" alt="Funded by EU" width="200"/>
</div>

Funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or European Climate, Infrastructure and Environment Executive Agency (CINEA). Neither the European Union nor the granting authority can be held responsible for them.