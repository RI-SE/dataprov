# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[3.0.0]: https://github.com/RI-SE/dataprov/releases/tag/v3.0.0
