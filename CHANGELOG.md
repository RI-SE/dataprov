# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `-q`/`--quiet` option for all CLI tools to suppress informational output; errors are
  still printed (#13)
- `create()`, `add()`, `add_attribution()`, `load()` and `save()` accept path-like objects
  (e.g. `pathlib.Path`) wherever a file path is expected; paths are stored as strings (#11)

### Changed

- `dataprov-new` prints its summary to stderr like the other CLI tools (was stdout), and its
  "next steps" hint now points to `dataprov-add` (#13)
- `create()`, `add()` and `add_attribution()` raise `TypeError` immediately if a
  `custom_metadata` or `custom_properties` value cannot be saved as JSON, instead of failing
  later in `save()` (#11)

### Fixed

- `save()` no longer truncates an existing provenance file when serialization fails (#11)

### Security

- `dataprov-report`: All values from the provenance file are now HTML-escaped, so a crafted or
  third-party provenance file can no longer inject HTML or scripts into the generated report

## [3.0.2] - 2026-01-23

### Added

- PyPI publishing in release workflow
- PyPI version badge in README

## [3.0.1] - 2026-01-23

### Fixed

- `dataprov-visualize`: Nested provenance bundles now rendered as subgraphs
- `dataprov-visualize`: Added `--normalize-paths` option to handle path prefix mismatches
- `dataprov-visualize`: Fixed tool name lookup to support both `dataprov:name` and `dataprov:toolName`
- `dataprov-report`: Inputs with nested provenance now show bundle contents

### Added

- `dataprov-visualize`: `--flatten-bundles` option to hide nested bundles
- `dataprov-report`: `--flatten-bundles` option to hide nested bundles
- Dashed "provenance" edges in DOT output connecting bundle outputs to main chain

## [3.0.0] - 2025-12-10

Initial public release.

### Features

- W3C PROV-JSON compliant provenance tracking
- `ProvenanceChain` class for managing data lineage
- Data Readiness Levels (DRL 0-9) for data quality tracking
- File integrity verification with SHA256 checksums
- Agent and environment capture (user, Python version, OS, runtime)
- Attribution relationships (`wasAttributedTo`)
- Custom ontology support with namespace management
- Custom properties on entities, activities, and agents
- Provenance file inlining (reference, inline, or both modes)
- Derivation mapping for precise input-output relationships
- Query methods with AND logic filtering
- PROV Bundle support for nested provenance

### CLI Tools

- `dataprov-new` - Create new provenance chains
- `dataprov-add-attribution` - Add attribution relationships
- `dataprov-visualize` - Generate GraphViz DOT visualizations
- `dataprov-report` - Generate HTML reports

### Documentation

- Comprehensive README with usage examples
- RDF/Turtle and JSON-LD ontology definitions
- W3C PROV-JSON schema included

[3.0.2]: https://github.com/RI-SE/dataprov/releases/tag/v3.0.2
[3.0.1]: https://github.com/RI-SE/dataprov/releases/tag/v3.0.1
[3.0.0]: https://github.com/RI-SE/dataprov/releases/tag/v3.0.0
