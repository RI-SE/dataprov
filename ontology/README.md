# Dataprov Ontology

This directory contains the formal ontology for the Dataprov provenance tracking library.

## Overview

The Dataprov ontology extends the [W3C PROV Ontology](https://www.w3.org/TR/prov-o/) with additional classes and properties specifically designed for tracking data file provenance in processing pipelines.

**Namespace URI:** `https://github.com/RI-SE/dataprov/ontology/`
**Prefix:** `dataprov:`
**Version:** 3.0.0
**Format:** Turtle (RDF)

## Files

- **`dataprov.ttl`** - The authoritative ontology definition in Turtle format
- **`dataprov.jsonld`** - JSON-LD context for web applications (optional)
- **`README.md`** - This documentation file

## Classes

### dataprov:RootEntity

**Definition:** The initial source entity in a provenance chain, representing the starting point of data processing.

**Parent Class:** `prov:Entity`

**Usage:**
```json
{
  "entity": {
    "my_dataset": {
      "prov:type": "dataprov:RootEntity",
      "prov:atLocation": "/data/raw/"
    }
  }
}
```

### dataprov:DataFile

**Definition:** A file entity representing data at various stages in the processing pipeline.

**Parent Class:** `prov:Entity`

**Usage:**
```json
{
  "entity": {
    "entity:output.csv": {
      "prov:type": "dataprov:DataFile",
      "dataprov:format": "CSV",
      "dataprov:checksum": "sha256:abc123...",
      "dataprov:sizeBytes": 1024
    }
  }
}
```

## Properties

### File/Entity Properties

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `dataprov:checksum` | `prov:Entity` | `xsd:string` | SHA256 checksum for integrity verification |
| `dataprov:format` | `dataprov:DataFile` | `xsd:string` | File format (e.g., CSV, JSON, MP4) |
| `dataprov:sizeBytes` | `prov:Entity` | `xsd:nonNegativeInteger` | File size in bytes |
| `dataprov:createdAt` | `prov:Entity` | `xsd:dateTime` | ISO 8601 creation timestamp |
| `dataprov:originalPath` | `prov:Bundle` | `xsd:string` | Original path for bundled files |
| `dataprov:bundleChecksum` | `prov:Bundle` | `xsd:string` | Checksum of bundled provenance file |
| `dataprov:externalPath` | `prov:Bundle` | `xsd:string` | Path to external provenance file |

### Activity/Processing Properties

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `dataprov:operation` | `prov:Activity` | `xsd:string` | Description of operation performed |
| `dataprov:arguments` | `prov:Activity` | `xsd:string` | Command-line arguments used |
| `dataprov:outputLog` | `prov:Activity` | `xsd:string` | Console/log output |
| `dataprov:warnings` | `prov:Activity` | `xsd:string` | Warning messages |
| `dataprov:drl` | `prov:Activity` | `xsd:integer` | Data Readiness Level (0-9) |

### Agent/Tool Properties

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `dataprov:toolName` | `prov:SoftwareAgent` | `xsd:string` | Software tool name |
| `dataprov:toolVersion` | `prov:SoftwareAgent` | `xsd:string` | Tool version |
| `dataprov:toolSource` | `prov:SoftwareAgent` | `xsd:string` | Tool source/vendor |
| `dataprov:user` | `prov:Agent` | `xsd:string` | Username who executed |
| `dataprov:hostname` | `prov:Agent` | `xsd:string` | Hostname where executed |
| `dataprov:agentType` | `prov:Agent` | `xsd:string` | Agent type (human/automated) |
| `dataprov:name` | `prov:Agent` | `xsd:string` | Name of person/organization |

### Environment Properties

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `dataprov:runtime` | `prov:SoftwareAgent` | `xsd:string` | Runtime environment (Python, Node.js, etc.) |
| `dataprov:runtimeVersion` | `prov:SoftwareAgent` | `xsd:string` | Runtime version |
| `dataprov:platform` | `prov:SoftwareAgent` | `xsd:string` | OS platform (Linux, Windows, macOS) |
| `dataprov:machine` | `prov:SoftwareAgent` | `xsd:string` | Machine architecture (x86_64, arm64) |
| `dataprov:processor` | `prov:SoftwareAgent` | `xsd:string` | CPU processor information |

### Relationship Properties

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `dataprov:hadProvenance` | `prov:Usage` | `prov:Bundle` or URI | Link to provenance file/bundle |

## Usage Example

```json
{
  "prefix": {
    "dataprov": "https://github.com/RI-SE/dataprov/ontology/",
    "prov": "http://www.w3.org/ns/prov#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "entity": {
    "dataset_001": {
      "prov:type": "dataprov:RootEntity",
      "prov:atLocation": "/data/raw/"
    },
    "entity:output.csv": {
      "prov:type": "dataprov:DataFile",
      "dataprov:format": "CSV",
      "dataprov:checksum": "sha256:abc123...",
      "dataprov:sizeBytes": 2048,
      "dataprov:createdAt": "2024-01-15T10:30:00Z"
    }
  },
  "activity": {
    "activity:step1": {
      "prov:startedAtTime": "2024-01-15T10:00:00Z",
      "prov:endedAtTime": "2024-01-15T10:30:00Z",
      "dataprov:operation": "data_cleaning",
      "dataprov:arguments": "--remove-nulls --normalize",
      "dataprov:drl": 5
    }
  },
  "agent": {
    "agent:tool_cleaner_1.0": {
      "prov:type": "prov:SoftwareAgent",
      "dataprov:toolName": "data_cleaner",
      "dataprov:toolVersion": "1.0",
      "dataprov:runtime": "Python",
      "dataprov:runtimeVersion": "3.12"
    }
  }
}
```

## Relationship to W3C PROV

Dataprov extends W3C PROV-O with domain-specific properties while maintaining full compatibility:

- **Reuses** W3C PROV core classes: `prov:Entity`, `prov:Activity`, `prov:Agent`
- **Reuses** W3C PROV relationships: `prov:used`, `prov:wasGeneratedBy`, `prov:wasDerivedFrom`, `prov:wasAssociatedWith`, `prov:wasAttributedTo`
- **Extends** with domain properties for file tracking, tool information, and data readiness

## Extending with Custom Namespaces

You can add custom namespace properties to your provenance files:

```json
{
  "prefix": {
    "dataprov": "https://github.com/RI-SE/dataprov/ontology/",
    "prov": "http://www.w3.org/ns/prov#",
    "myapp": "https://myorganization.com/ontology/myapp#"
  },
  "entity": {
    "entity:data.csv": {
      "prov:type": "dataprov:DataFile",
      "dataprov:format": "CSV",
      "myapp:customProperty": "custom value"
    }
  }
}
```

## Validation

To validate your provenance files against this ontology, you can use RDF validation tools:

```bash
# Example with rapper (part of raptor2-utils)
rapper -i turtle -o ntriples dataprov.ttl > /dev/null

# Example with riot (part of Apache Jena)
riot --validate dataprov.ttl
```

## Data Readiness Level (DRL)

The `dataprov:drl` property tracks the maturity/quality of data using a 0-9 scale. How to use the scale is up to the specific use-case to define, an example can be:

| Level | Description |
|-------|-------------|
| 0 | Raw data |
| 1 | Tagged and timestamped data |
| 2 | Validated data |
| 3 | Quality controlled data |
| 4 | Curated data |
| 5 | Analyzed data |
| 6 | Consolidated data |
| 7 | Dataset complete |
| 8 | Vetted dataset |
| 9 | Published dataset |

See: [Data Readiness Level (Wikipedia)](https://en.wikipedia.org/wiki/Data_readiness_level)

## License

This ontology is released under the MIT License, consistent with the dataprov library.

## References

- [W3C PROV Overview](https://www.w3.org/TR/prov-overview/)
- [W3C PROV Ontology (PROV-O)](https://www.w3.org/TR/prov-o/)
- [W3C PROV-JSON](https://www.w3.org/Submission/prov-json/)
- [Dataprov Library](https://github.com/RI-SE/dataprov)
