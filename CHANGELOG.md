# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Output roles: `add(output_roles=[...])` records what each output is for as `prov:role` on its generation
  (W3C PROV qualified generation); suggested roles in `OUTPUT_ROLES` (`primary`, `quality`, `log`, `metadata`).
  `get_steps()` shows the `role` of outputs, the new `get_outputs(role=...)` lists them across the chain, and
  `dataprov-add` has `--output-roles`
- `declare_namespaces()`, and `custom_namespaces` for `load()`; `load_or_create()` now declares its
  `custom_namespaces` also on a chain loaded from an existing file (previously only on create, so custom
  properties with those prefixes failed on existing chains)

## [3.3.0] - 2026-10-22

### Added

- `dataprov-report` shows custom metadata (collapsible section) and the custom properties of
  steps, tools and input/output files (#10)
- `get_steps()` includes custom properties as `custom_properties` on steps, tools and
  inputs/outputs, and the new `get_custom_metadata()` returns the custom top-level metadata (#10)
- `add()` detects file formats from file extensions when `input_formats`/`output_formats`
  are omitted or contain `None` entries, like `add_attribution()` already did; in
  `dataprov-add`, `--input-formats`/`--output-formats` are now optional (#12)
- `-q`/`--quiet` option for all CLI tools to suppress informational output; errors are
  still printed (#13)
- `--version` option for all CLI tools (#14)
- `create()`, `add()`, `add_attribution()`, `load()` and `save()` accept path-like objects
  (e.g. `pathlib.Path`) wherever a file path is expected; paths are stored as strings (#11)

### Changed

- `dataprov.__version__` is read from the installed package metadata (it was stuck at 3.0.2)
- `dataprov-new` prints its summary to stderr like the other CLI tools (was stdout), and its
  "next steps" hint now points to `dataprov-add` (#13)
- `create()`, `add()` and `add_attribution()` raise `TypeError` immediately if a
  `custom_metadata` or `custom_properties` value cannot be saved as JSON, instead of failing
  later in `save()` (#11)

### Fixed

- `add_attribution()` failed on Python 3.8 and 3.9 (used `zip(strict=True)`, which needs
  Python 3.10)
- `save()` no longer truncates an existing provenance file when serialization fails (#11)
- Python version badge in README

### Security

- `dataprov-report`: All values from the provenance file are now HTML-escaped, so a crafted or
  third-party provenance file can no longer inject HTML or scripts into the generated report

### Development

- Ruff pinned to 0.14.8 in CI and pre-commit; Markdown files excluded from ruff
- The pytest pre-commit hook runs via `uv run`; CONTRIBUTING.md describes setup with uv

## [3.2.0] - 2026-04-14

Version 3.1.0 was not released.

### Added

- `dataprov-add` CLI tool for recording processing steps, the CLI equivalent of
  `ProvenanceChain.add()`
- Pre-commit hooks for ruff linting/formatting and tests

### Changed

- The package can be installed on Python 3.8+ (development tools still require Python 3.10+)
- Code base linted and formatted with ruff

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

[3.3.0]: https://github.com/RI-SE/dataprov/releases/tag/v3.3.0
[3.2.0]: https://github.com/RI-SE/dataprov/releases/tag/v3.2.0
[3.0.2]: https://github.com/RI-SE/dataprov/releases/tag/v3.0.2
[3.0.1]: https://github.com/RI-SE/dataprov/releases/tag/v3.0.1
[3.0.0]: https://github.com/RI-SE/dataprov/tree/064f6b8c1e1eb38e662b1924529fc564efad74ee
