"""
Test suite for dataprov library (v3.0 - PROV-JSON format).

Tests cover:
- ProvenanceChain creation and loading
- Adding processing steps
- File integrity tracking
- DRL support
- Chain validation
- Query methods

NOTE: Updated for v3.0 PROV-JSON format
- chain.data["provenance_version"] → chain.data["dataprov:metadata"]["version"]
- chain.data["root_entity"] → chain.data["dataprov:metadata"]
- chain.data["chain"] → chain.get_steps()
- Version "2.0"/"2.1" → "3.0"
- Backwards compatibility tests for v1.0 are skipped (use dataprov-convert for old files)
"""

import json

import pytest

from dataprov import ProvenanceChain


@pytest.fixture
def timestamps():
    """Provide standard timestamps for testing."""
    return {"started_at": "2024-10-15T11:00:00Z", "ended_at": "2024-10-15T11:05:30Z"}


class TestProvenanceChainCreation:
    """Test creating new provenance chains."""

    def test_create_basic_chain(self):
        """Test creating a basic provenance chain."""
        chain = ProvenanceChain.create(
            entity_id="test_001",
            initial_source="/test/data/",
            description="Test chain",
            tags=["test", "demo"],
        )

        assert chain.data["dataprov:metadata"]["version"] == "3.0"
        assert chain.data["dataprov:metadata"]["rootEntityId"] == "test_001"
        assert chain.data["dataprov:metadata"]["initialSource"] == "/test/data/"
        assert chain.data["dataprov:metadata"]["description"] == "Test chain"
        assert chain.data["dataprov:metadata"]["tags"] == ["test", "demo"]
        assert chain.get_steps() == []

    def test_create_minimal_chain(self):
        """Test creating chain with minimal parameters."""
        chain = ProvenanceChain.create(entity_id="minimal_001", initial_source="/data/")

        assert chain.data["dataprov:metadata"]["rootEntityId"] == "minimal_001"
        assert chain.data["dataprov:metadata"]["description"] == ""
        assert chain.data["dataprov:metadata"]["tags"] == []

    def test_timestamps_are_set(self):
        """Test that created and last_modified timestamps are set."""
        chain = ProvenanceChain.create(entity_id="time_test", initial_source="/test/")

        assert "created" in chain.data["dataprov:metadata"]
        assert "lastModified" in chain.data["dataprov:metadata"]
        assert (
            chain.data["dataprov:metadata"]["created"]
            == chain.data["dataprov:metadata"]["lastModified"]
        )


class TestProvenanceChainSaveLoad:
    """Test saving and loading provenance chains."""

    def test_save_and_load_chain(self, tmp_path):
        """Test saving and loading a chain."""
        filepath = tmp_path / "test_prov.json"

        # Create and save chain
        chain = ProvenanceChain.create(
            entity_id="save_test",
            initial_source="/test/",
            description="Save test",
            tags=["test"],
        )
        chain.save(str(filepath))

        # Load chain
        loaded_chain = ProvenanceChain.load(str(filepath))

        assert loaded_chain.data["dataprov:metadata"]["rootEntityId"] == "save_test"
        assert loaded_chain.data["dataprov:metadata"]["description"] == "Save test"
        assert loaded_chain.data["dataprov:metadata"]["tags"] == ["test"]

    def test_load_or_create_existing(self, tmp_path):
        """Test load_or_create with existing file."""
        filepath = tmp_path / "existing.json"

        # Create initial chain
        chain1 = ProvenanceChain.create(entity_id="existing", initial_source="/test/")
        chain1.save(str(filepath))

        # Load or create should load existing
        chain2 = ProvenanceChain.load_or_create(
            str(filepath), entity_id="different", initial_source="/other/"
        )

        assert chain2.data["dataprov:metadata"]["rootEntityId"] == "existing"

    def test_load_or_create_new(self, tmp_path):
        """Test load_or_create with non-existing file."""
        filepath = tmp_path / "new.json"

        # Load or create should create new
        chain = ProvenanceChain.load_or_create(
            str(filepath), entity_id="new_chain", initial_source="/test/"
        )

        assert chain.data["dataprov:metadata"]["rootEntityId"] == "new_chain"


class TestAddingSteps:
    """Test adding processing steps to chains."""

    def test_add_basic_step(self, tmp_path, sample_file, timestamps):
        """Test adding a basic processing step."""
        chain = ProvenanceChain.create(entity_id="step_test", initial_source="/test/")

        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_operation",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        assert success is True
        assert len(chain.get_steps()) == 1
        step = chain.get_steps()[0]
        assert step["step_id"] == 1
        assert step["tool"]["name"] == "test_tool"
        assert step["tool"]["version"] == "1.0"
        assert step["operation"] == "test_operation"

    def test_add_step_with_drl(self, tmp_path, sample_file, timestamps):
        """Test adding a step with Data Readiness Level."""
        chain = ProvenanceChain.create(entity_id="drl_test", initial_source="/test/")

        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_operation",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            drl=5,
        )

        assert success is True
        step = chain.get_steps()[0]
        assert step["drl"] == 5

    def test_add_step_with_optional_fields(self, tmp_path, sample_file, timestamps):
        """Test adding a step with all optional fields."""
        chain = ProvenanceChain.create(
            entity_id="optional_test", initial_source="/test/"
        )

        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_operation",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            source="Test Vendor",
            arguments="--arg1 value1",
            output_log="Processing completed",
            warnings="No warnings",
            drl=3,
        )

        assert success is True
        step = chain.get_steps()[0]
        # Note: source is stored on agent, not returned in step["tool"]
        assert step["arguments"] == "--arg1 value1"
        assert step["output_log"] == "Processing completed"
        assert step["warnings"] == "No warnings"
        assert step["drl"] == 3

    def test_add_multiple_steps(self, tmp_path, sample_file, timestamps):
        """Test adding multiple sequential steps."""
        chain = ProvenanceChain.create(entity_id="multi_test", initial_source="/test/")

        # Add first step
        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool1",
            tool_version="1.0",
            operation="op1",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            drl=2,
        )

        # Add second step
        chain.add(
            started_at="2024-10-15T12:00:00Z",
            ended_at="2024-10-15T12:05:00Z",
            tool_name="tool2",
            tool_version="2.0",
            operation="op2",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            drl=4,
        )

        assert len(chain.get_steps()) == 2
        assert chain.get_steps()[0]["step_id"] == 1
        assert chain.get_steps()[1]["step_id"] == 2
        assert chain.get_steps()[0]["drl"] == 2
        assert chain.get_steps()[1]["drl"] == 4

    def test_step_sequential_ids(self, tmp_path, sample_file, timestamps):
        """Test that step IDs are sequential."""
        chain = ProvenanceChain.create(entity_id="seq_test", initial_source="/test/")

        for i in range(5):
            chain.add(
                started_at=timestamps["started_at"],
                ended_at=timestamps["ended_at"],
                tool_name=f"tool{i}",
                tool_version="1.0",
                operation=f"op{i}",
                inputs=[str(sample_file)],
                input_formats=["TXT"],
                outputs=[str(sample_file)],
                output_formats=["TXT"],
            )

        assert len(chain.get_steps()) == 5
        for i, step in enumerate(chain.get_steps(), 1):
            assert step["step_id"] == i


class TestDRLValidation:
    """Test Data Readiness Level validation."""

    def test_drl_valid_range(self, tmp_path, sample_file, timestamps):
        """Test that valid DRL values (0-9) are accepted."""
        chain = ProvenanceChain.create(entity_id="drl_valid", initial_source="/test/")

        for drl in range(10):  # 0 to 9
            success = chain.add(
                started_at=timestamps["started_at"],
                ended_at=timestamps["ended_at"],
                tool_name=f"tool_{drl}",
                tool_version="1.0",
                operation=f"op_{drl}",
                inputs=[str(sample_file)],
                input_formats=["TXT"],
                outputs=[str(sample_file)],
                output_formats=["TXT"],
                drl=drl,
            )
            assert success is True

    def test_drl_invalid_negative(self, tmp_path, sample_file, timestamps):
        """Test that negative DRL values are rejected."""
        chain = ProvenanceChain.create(entity_id="drl_neg", initial_source="/test/")

        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            drl=-1,
        )

        assert success is False

    def test_drl_invalid_too_high(self, tmp_path, sample_file, timestamps):
        """Test that DRL values > 9 are rejected."""
        chain = ProvenanceChain.create(entity_id="drl_high", initial_source="/test/")

        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            drl=10,
        )

        assert success is False

    def test_drl_optional(self, tmp_path, sample_file, timestamps):
        """Test that DRL is optional."""
        chain = ProvenanceChain.create(
            entity_id="drl_optional", initial_source="/test/"
        )

        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        assert success is True
        step = chain.get_steps()[0]
        assert "drl" not in step


class TestFileIntegrity:
    """Test file integrity tracking (checksums and sizes)."""

    def test_file_checksum_calculated(self, tmp_path, sample_file, timestamps):
        """Test that file checksums are calculated."""
        chain = ProvenanceChain.create(
            entity_id="checksum_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        step = chain.get_steps()[0]
        input_file = step["inputs"][0]

        assert "checksum" in input_file
        assert input_file["checksum"].startswith("sha256:")
        assert len(input_file["checksum"]) > 7  # sha256: + hash

    def test_file_size_recorded(self, tmp_path, sample_file, timestamps):
        """Test that file sizes are recorded."""
        chain = ProvenanceChain.create(entity_id="size_test", initial_source="/test/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        step = chain.get_steps()[0]
        input_file = step["inputs"][0]

        assert "size_bytes" in input_file
        assert input_file["size_bytes"] > 0

    def test_missing_file_handling(self, tmp_path, timestamps):
        """Test handling of missing files."""
        chain = ProvenanceChain.create(
            entity_id="missing_test", initial_source="/test/"
        )

        missing_file = tmp_path / "nonexistent.txt"

        # Should still succeed but with None checksum/size
        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[str(missing_file)],
            input_formats=["TXT"],
            outputs=[str(missing_file)],
            output_formats=["TXT"],
        )

        # Based on the code, it should return the file_info even if missing
        assert success is True
        step = chain.get_steps()[0]
        input_file = step["inputs"][0]
        assert input_file["checksum"] is None
        assert input_file["size_bytes"] is None


class TestChainValidation:
    """Test provenance chain validation."""

    def test_validate_empty_chain(self):
        """Test validating an empty chain."""
        chain = ProvenanceChain.create(
            entity_id="validate_empty", initial_source="/test/"
        )

        is_valid, errors = chain.validate()
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_chain_with_steps(self, tmp_path, sample_file, timestamps):
        """Test validating a chain with steps."""
        chain = ProvenanceChain.create(
            entity_id="validate_steps", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        is_valid, errors = chain.validate()
        assert is_valid is True
        assert len(errors) == 0


class TestQueryMethods:
    """Test methods for querying provenance chains."""

    def test_get_steps(self, tmp_path, sample_file, timestamps):
        """Test getting all steps."""
        chain = ProvenanceChain.create(entity_id="query_test", initial_source="/test/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool1",
            tool_version="1.0",
            operation="op1",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool2",
            tool_version="2.0",
            operation="op2",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        steps = chain.get_steps()
        assert len(steps) == 2

    def test_get_step_by_id(self, tmp_path, sample_file, timestamps):
        """Test getting a specific step by ID."""
        chain = ProvenanceChain.create(
            entity_id="get_step_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool1",
            tool_version="1.0",
            operation="op1",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        step = chain.get_step(1)
        assert step is not None
        assert step["step_id"] == 1
        assert step["tool"]["name"] == "tool1"

    def test_get_step_invalid_id(self, tmp_path):
        """Test getting a step with invalid ID."""
        chain = ProvenanceChain.create(
            entity_id="invalid_id_test", initial_source="/test/"
        )

        step = chain.get_step(999)
        assert step is None

    def test_get_latest_step(self, tmp_path, sample_file, timestamps):
        """Test getting the latest step."""
        chain = ProvenanceChain.create(entity_id="latest_test", initial_source="/test/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool1",
            tool_version="1.0",
            operation="op1",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool2",
            tool_version="2.0",
            operation="op2",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        latest = chain.get_latest_step()
        assert latest is not None
        assert latest["step_id"] == 2
        assert latest["tool"]["name"] == "tool2"

    def test_get_latest_step_empty_chain(self, tmp_path):
        """Test getting latest step from empty chain."""
        chain = ProvenanceChain.create(
            entity_id="empty_latest", initial_source="/test/"
        )

        latest = chain.get_latest_step()
        assert latest is None

    def test_find_steps_by_tool_name(self, tmp_path, sample_file, timestamps):
        """Test finding steps by tool name."""
        chain = ProvenanceChain.create(entity_id="find_test", initial_source="/test/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool_a",
            tool_version="1.0",
            operation="op1",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool_b",
            tool_version="1.0",
            operation="op2",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool_a",
            tool_version="2.0",
            operation="op3",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        found = chain.find_steps(tool_name="tool_a")
        assert len(found) == 2
        assert all(step["tool"]["name"] == "tool_a" for step in found)

    def test_find_steps_by_operation(self, tmp_path, sample_file, timestamps):
        """Test finding steps by operation."""
        chain = ProvenanceChain.create(
            entity_id="find_op_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool1",
            tool_version="1.0",
            operation="calibration",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool2",
            tool_version="1.0",
            operation="processing",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        found = chain.find_steps(operation="calibration")
        assert len(found) == 1
        assert found[0]["operation"] == "calibration"


class TestInputValidation:
    """Test input validation for add() method."""

    def test_mismatched_input_lengths(self, tmp_path, sample_file, timestamps):
        """Test that mismatched input/format lists are rejected."""
        chain = ProvenanceChain.create(
            entity_id="mismatch_test", initial_source="/test/"
        )

        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[str(sample_file), str(sample_file)],
            input_formats=["TXT"],  # Only one format for two inputs
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        assert success is False

    def test_mismatched_output_lengths(self, tmp_path, sample_file, timestamps):
        """Test that mismatched output/format lists are rejected."""
        chain = ProvenanceChain.create(
            entity_id="mismatch_out_test", initial_source="/test/"
        )

        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file), str(sample_file)],
            output_formats=["TXT"],  # Only one format for two outputs
        )

        assert success is False


# =============================================================================
# Version 2.0 Feature Tests
# =============================================================================


class TestVersion2Features:
    """Test schema version 2.0 features."""

    def test_version_2_chain_creation(self):
        """Test that new chains are created with version 2.0."""
        chain = ProvenanceChain.create(entity_id="v2_test", initial_source="/test/")

        assert chain.data["dataprov:metadata"]["version"] == "3.0"


class TestExecutionTiming:
    """Test execution timing capture (started_at, ended_at)."""

    def test_timing_fields_present(self, tmp_path, sample_file, timestamps):
        """Test that started_at and ended_at are captured."""
        chain = ProvenanceChain.create(entity_id="timing_test", initial_source="/test/")

        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        assert success is True
        step = chain.get_latest_step()
        assert "started_at" in step
        assert "ended_at" in step
        assert "timestamp" not in step  # Old field should not be present

    def test_timing_chronological_order(self, tmp_path, sample_file, timestamps):
        """Test that started_at is before or equal to ended_at."""
        chain = ProvenanceChain.create(
            entity_id="timing_order_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        step = chain.get_latest_step()
        assert step["started_at"] <= step["ended_at"]

    def test_timing_iso8601_format(self, tmp_path, sample_file, timestamps):
        """Test that timestamps are in ISO 8601 format with Z suffix."""
        chain = ProvenanceChain.create(
            entity_id="timing_format_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        step = chain.get_latest_step()
        assert step["started_at"].endswith("Z")
        assert step["ended_at"].endswith("Z")
        assert "T" in step["started_at"]  # ISO 8601 has 'T' separator


class TestAgentTracking:
    """Test agent/user tracking features."""

    def test_agent_capture_disabled_by_default(self, tmp_path, sample_file, timestamps):
        """Test that agent info is not captured by default."""
        chain = ProvenanceChain.create(
            entity_id="no_agent_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        step = chain.get_latest_step()
        assert "agent" not in step

    def test_agent_capture_when_enabled(self, tmp_path, sample_file, timestamps):
        """Test that agent info is captured when enabled."""
        chain = ProvenanceChain.create(entity_id="agent_test", initial_source="/test/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            capture_agent=True,
        )

        step = chain.get_latest_step()
        assert "agent" in step
        assert "user" in step["agent"]
        assert "hostname" in step["agent"]
        assert "type" in step["agent"]
        assert step["agent"]["type"] in ["human", "automated"]

    def test_agent_override_values(self, tmp_path, sample_file, timestamps):
        """Test that agent values can be overridden."""
        chain = ProvenanceChain.create(
            entity_id="agent_override_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            capture_agent=True,
            user="custom_user",
            hostname="custom_host",
        )

        step = chain.get_latest_step()
        assert step["agent"]["user"] == "custom_user"
        assert step["agent"]["hostname"] == "custom_host"


class TestEnvironmentCapture:
    """Test environment capture features."""

    def test_environment_not_captured_by_default(
        self, tmp_path, sample_file, timestamps
    ):
        """Test that environment is not captured by default."""
        chain = ProvenanceChain.create(entity_id="no_env_test", initial_source="/test/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        step = chain.get_latest_step()
        assert "environment" not in step

    def test_environment_capture_when_enabled(self, tmp_path, sample_file, timestamps):
        """Test that environment is captured when enabled."""
        chain = ProvenanceChain.create(entity_id="env_test", initial_source="/test/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            capture_environment=True,
        )

        step = chain.get_latest_step()
        assert "environment" in step
        env = step["environment"]
        assert "runtime" in env
        assert "runtime_version" in env
        assert "platform" in env
        assert "machine" in env
        assert "processor" in env

    def test_environment_override_runtime(self, tmp_path, sample_file, timestamps):
        """Test that runtime can be overridden for non-Python applications."""
        chain = ProvenanceChain.create(
            entity_id="env_override_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            capture_environment=True,
            runtime="Node.js",
            runtime_version="18.0.0",
        )

        step = chain.get_latest_step()
        env = step["environment"]
        assert env["runtime"] == "Node.js"
        assert env["runtime_version"] == "18.0.0"


class TestEnhancedQuery:
    """Test enhanced query capabilities with AND/OR logic."""

    def test_query_by_tool_name(self, tmp_path, sample_file, timestamps):
        """Test querying by tool name."""
        chain = ProvenanceChain.create(entity_id="query_test", initial_source="/test/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool_a",
            tool_version="1.0",
            operation="op1",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool_b",
            tool_version="1.0",
            operation="op2",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        results = chain.find_steps(tool_name="tool_a")
        assert len(results) == 1
        assert results[0]["tool"]["name"] == "tool_a"

    def test_query_by_drl_range(self, tmp_path, sample_file, timestamps):
        """Test querying by DRL range."""
        chain = ProvenanceChain.create(
            entity_id="drl_query_test", initial_source="/test/"
        )

        # Add steps with different DRLs
        for drl in [1, 3, 5, 7, 9]:
            chain.add(
                started_at=timestamps["started_at"],
                ended_at=timestamps["ended_at"],
                tool_name="test_tool",
                tool_version="1.0",
                operation="test_op",
                inputs=[str(sample_file)],
                input_formats=["TXT"],
                outputs=[str(sample_file)],
                output_formats=["TXT"],
                drl=drl,
            )

        # Query for DRL >= 5
        results = chain.find_steps(drl_min=5)
        assert len(results) == 3  # DRL 5, 7, 9

        # Query for DRL <= 3
        results = chain.find_steps(drl_max=3)
        assert len(results) == 2  # DRL 1, 3

        # Query for DRL in range [3, 7]
        results = chain.find_steps(drl_min=3, drl_max=7)
        assert len(results) == 3  # DRL 3, 5, 7

    def test_query_by_user(self, tmp_path, sample_file, timestamps):
        """Test querying by username."""
        chain = ProvenanceChain.create(
            entity_id="user_query_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            capture_agent=True,
            user="alice",
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            capture_agent=True,
            user="bob",
        )

        results = chain.find_steps(user="alice")
        assert len(results) == 1
        assert results[0]["agent"]["user"] == "alice"

    def test_query_with_and_logic(self, tmp_path, sample_file, timestamps):
        """Test query with AND logic (all criteria must match)."""
        chain = ProvenanceChain.create(
            entity_id="and_query_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool_a",
            tool_version="1.0",
            operation="operation_x",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            drl=5,
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool_a",
            tool_version="1.0",
            operation="operation_y",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
            drl=3,
        )

        # Query: tool_name="tool_a" AND drl >= 5
        results = chain.find_steps(tool_name="tool_a", drl_min=5)
        assert len(results) == 1
        assert results[0]["operation"] == "operation_x"

    def test_query_by_file_pattern(self, tmp_path, timestamps):
        """Test querying by file pattern."""
        # Create sample files
        file1 = tmp_path / "data1.csv"
        file1.write_text("test")
        file2 = tmp_path / "data2.txt"
        file2.write_text("test")

        chain = ProvenanceChain.create(
            entity_id="pattern_query_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="process_csv",
            inputs=[str(file1)],
            input_formats=["CSV"],
            outputs=[str(file1)],
            output_formats=["CSV"],
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="process_txt",
            inputs=[str(file2)],
            input_formats=["TXT"],
            outputs=[str(file2)],
            output_formats=["TXT"],
        )

        # Query for CSV files
        results = chain.find_steps(file_pattern="*.csv")
        assert len(results) == 1
        assert results[0]["operation"] == "process_csv"


class TestVisualization:
    """Test DOT graph generation."""

    def test_to_dot_basic(self, tmp_path, sample_file, timestamps):
        """Test basic DOT graph generation."""
        chain = ProvenanceChain.create(entity_id="viz_test", initial_source="/test/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(sample_file)],
            output_formats=["TXT"],
        )

        dot_graph = chain.to_dot()

        # Check basic DOT structure
        assert "digraph provenance {" in dot_graph
        assert "}" in dot_graph
        assert "rankdir=LR" in dot_graph

    def test_to_dot_contains_nodes(self, tmp_path, timestamps):
        """Test that DOT graph contains file and step nodes."""
        file1 = tmp_path / "input.txt"
        file1.write_text("test")
        file2 = tmp_path / "output.txt"
        file2.write_text("result")

        chain = ProvenanceChain.create(
            entity_id="viz_nodes_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="processor",
            tool_version="1.0",
            operation="processing",
            inputs=[str(file1)],
            input_formats=["TXT"],
            outputs=[str(file2)],
            output_formats=["TXT"],
            drl=5,
        )

        dot_graph = chain.to_dot()

        # Should contain file nodes (as boxes)
        assert "shape=box" in dot_graph
        assert "input.txt" in dot_graph
        assert "output.txt" in dot_graph

        # Should contain step nodes (as ellipses)
        assert "shape=ellipse" in dot_graph
        assert "processor" in dot_graph
        assert "processing" in dot_graph

        # Should contain DRL info
        assert "DRL: 5" in dot_graph

    def test_to_dot_contains_edges(self, tmp_path, timestamps):
        """Test that DOT graph contains data flow edges."""
        file1 = tmp_path / "input.txt"
        file1.write_text("test")
        file2 = tmp_path / "output.txt"
        file2.write_text("result")

        chain = ProvenanceChain.create(
            entity_id="viz_edges_test", initial_source="/test/"
        )

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="processor",
            tool_version="1.0",
            operation="processing",
            inputs=[str(file1)],
            input_formats=["TXT"],
            outputs=[str(file2)],
            output_formats=["TXT"],
        )

        dot_graph = chain.to_dot()

        # Should contain edges (->)
        assert "->" in dot_graph
        # Input edge to step
        assert f'"{file1}" -> "step_1"' in dot_graph
        # Output edge from step
        assert f'"step_1" -> "{file2}"' in dot_graph


class TestOptionalEndedAt:
    """Test optional ended_at timestamp functionality."""

    def test_add_step_without_ended_at(self, tmp_path, sample_file, timestamps):
        """Test adding a step without ended_at (for ongoing processing)."""
        chain = ProvenanceChain.create(
            entity_id="incomplete_test", initial_source="/test/"
        )

        success = chain.add(
            started_at=timestamps["started_at"],
            ended_at=None,  # No end time
            tool_name="long_process",
            tool_version="1.0",
            operation="ongoing_processing",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
        )

        assert success is True
        assert len(chain.get_steps()) == 1

        step = chain.get_steps()[0]
        assert "started_at" in step
        assert "ended_at" not in step  # Should not be in the step
        assert step["started_at"] == timestamps["started_at"]

    def test_save_updates_last_modified_for_incomplete_steps(
        self, tmp_path, sample_file, timestamps
    ):
        """Test that save() updates last_modified when steps have no ended_at."""
        chain = ProvenanceChain.create(
            entity_id="incomplete_save_test", initial_source="/test/"
        )

        # Add step without ended_at
        chain.add(
            started_at=timestamps["started_at"],
            ended_at=None,
            tool_name="incomplete_tool",
            tool_version="1.0",
            operation="incomplete_op",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
        )

        original_last_modified = chain.data["dataprov:metadata"]["lastModified"]

        # Save the chain
        output_file = tmp_path / "incomplete_chain.json"
        chain.save(str(output_file))

        # last_modified should be updated to current time
        assert chain.data["dataprov:metadata"]["lastModified"] != original_last_modified

        # Load and verify
        with open(output_file) as f:
            saved_data = json.load(f)

        assert "lastModified" in saved_data["dataprov:metadata"]
        # Should be more recent than the started_at time
        assert (
            saved_data["dataprov:metadata"]["lastModified"] > timestamps["started_at"]
        )

    def test_mixed_complete_and_incomplete_steps(
        self, tmp_path, sample_file, timestamps
    ):
        """Test chain with both complete and incomplete steps."""
        chain = ProvenanceChain.create(entity_id="mixed_test", initial_source="/test/")

        # Add complete step
        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="complete_tool",
            tool_version="1.0",
            operation="complete_op",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output1.txt")],
            output_formats=["TXT"],
        )

        # Add incomplete step
        chain.add(
            started_at="2024-10-15T12:00:00Z",
            ended_at=None,
            tool_name="incomplete_tool",
            tool_version="1.0",
            operation="incomplete_op",
            inputs=[str(tmp_path / "output1.txt")],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output2.txt")],
            output_formats=["TXT"],
        )

        assert len(chain.get_steps()) == 2
        assert "ended_at" in chain.get_steps()[0]
        assert "ended_at" not in chain.get_steps()[1]


class TestProvenanceFileChecksums:
    """Test provenance file checksum functionality."""

    def test_provenance_file_checksum_added(self, tmp_path, sample_file, timestamps):
        """Test that checksums are added for input provenance files."""
        # Create an upstream provenance file
        upstream_chain = ProvenanceChain.create(
            entity_id="upstream", initial_source="/upstream/"
        )
        upstream_file = tmp_path / "upstream_prov.json"
        upstream_chain.save(str(upstream_file))

        # Create main chain that references upstream
        chain = ProvenanceChain.create(entity_id="main", initial_source="/main/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="combiner",
            tool_version="1.0",
            operation="combine",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
            input_provenance_files=[str(upstream_file)],
        )

        # Check that checksum was added
        assert len(chain.get_steps()) == 1
        step = chain.get_steps()[0]
        assert len(step["inputs"]) == 1

        input_info = step["inputs"][0]
        assert "provenance_file" in input_info
        assert input_info["provenance_file"] == str(upstream_file)
        assert "provenance_file_checksum" in input_info
        assert input_info["provenance_file_checksum"].startswith("sha256:")

    def test_provenance_checksum_missing_file(self, tmp_path, sample_file, timestamps):
        """Test that checksum is not added when provenance file doesn't exist."""
        chain = ProvenanceChain.create(entity_id="test", initial_source="/test/")

        nonexistent_prov = str(tmp_path / "nonexistent_prov.json")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
            input_provenance_files=[nonexistent_prov],
        )

        step = chain.get_steps()[0]
        input_info = step["inputs"][0]
        assert "provenance_file" in input_info
        # Checksum should not be present for missing file
        assert "provenance_file_checksum" not in input_info


class TestProvenanceInlining:
    """Test provenance file inlining functionality."""

    def test_save_with_reference_mode(self, tmp_path, sample_file, timestamps):
        """Test default reference mode (no inlining)."""
        # Create upstream provenance
        upstream_chain = ProvenanceChain.create(
            entity_id="upstream", initial_source="/upstream/"
        )
        upstream_file = tmp_path / "upstream_prov.json"
        upstream_chain.save(str(upstream_file))

        # Create main chain
        chain = ProvenanceChain.create(entity_id="main", initial_source="/main/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="combiner",
            tool_version="1.0",
            operation="combine",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
            input_provenance_files=[str(upstream_file)],
        )

        # Save with default mode (reference)
        output_file = tmp_path / "main_prov.json"
        chain.save(str(output_file))

        # Load and verify
        with open(output_file) as f:
            saved_data = json.load(f)

        # Should not have bundle section (no inlining in reference mode)
        assert "bundle" not in saved_data or len(saved_data.get("bundle", {})) == 0

        # Input should still have original path in used relationship
        # Find the usage relationship
        used_rels = saved_data["used"]
        assert len(used_rels) == 1
        usage = list(used_rels.values())[0]
        assert "dataprov:hadProvenance" in usage
        assert usage["dataprov:hadProvenance"] == str(upstream_file)

    def test_save_with_inline_mode(self, tmp_path, sample_file, timestamps):
        """Test inline mode (embeds provenance files)."""
        # Create upstream provenance
        upstream_chain = ProvenanceChain.create(
            entity_id="upstream", initial_source="/upstream/"
        )
        upstream_chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="upstream_tool",
            tool_version="1.0",
            operation="upstream_op",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "upstream_output.txt")],
            output_formats=["TXT"],
        )
        upstream_file = tmp_path / "upstream_prov.json"
        upstream_chain.save(str(upstream_file))

        # Create main chain
        chain = ProvenanceChain.create(entity_id="main", initial_source="/main/")

        chain.add(
            started_at="2024-10-15T12:00:00Z",
            ended_at="2024-10-15T12:05:00Z",
            tool_name="combiner",
            tool_version="1.0",
            operation="combine",
            inputs=[str(tmp_path / "upstream_output.txt")],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
            input_provenance_files=[str(upstream_file)],
        )

        # Save with inline mode
        output_file = tmp_path / "main_prov_inline.json"
        chain.save(str(output_file), input_prov="inline")

        # Load and verify
        with open(output_file) as f:
            saved_data = json.load(f)

        # Should have bundle section with inlined provenance
        assert "bundle" in saved_data
        assert len(saved_data["bundle"]) == 1

        # Check bundle entity
        bundle_id = "bundle:nested_0"
        assert bundle_id in saved_data["entity"]
        bundle_entity = saved_data["entity"][bundle_id]
        assert bundle_entity["prov:type"] == "prov:Bundle"
        assert "dataprov:bundleChecksum" in bundle_entity
        assert bundle_entity["dataprov:bundleChecksum"].startswith("sha256:")
        assert bundle_entity["dataprov:originalPath"] == str(upstream_file)

        # Check bundle content
        assert bundle_id in saved_data["bundle"]
        bundle_content = saved_data["bundle"][bundle_id]
        assert "entity" in bundle_content
        assert "upstream" in bundle_content["entity"]
        assert (
            bundle_content["entity"]["upstream"]["prov:type"] == "dataprov:RootEntity"
        )

        # Input should reference the bundle in used relationship
        usage = list(saved_data["used"].values())[0]
        assert usage["dataprov:hadProvenance"] == bundle_id

    def test_save_with_both_mode(self, tmp_path, sample_file, timestamps):
        """Test both mode (embeds and keeps original path)."""
        # Create upstream provenance
        upstream_chain = ProvenanceChain.create(
            entity_id="upstream", initial_source="/upstream/"
        )
        upstream_file = tmp_path / "upstream_prov.json"
        upstream_chain.save(str(upstream_file))

        # Create main chain
        chain = ProvenanceChain.create(entity_id="main", initial_source="/main/")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="combiner",
            tool_version="1.0",
            operation="combine",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
            input_provenance_files=[str(upstream_file)],
        )

        # Save with both mode
        output_file = tmp_path / "main_prov_both.json"
        chain.save(str(output_file), input_prov="both")

        # Load and verify
        with open(output_file) as f:
            saved_data = json.load(f)

        # Should have bundle section with inlined provenance
        assert "bundle" in saved_data
        assert len(saved_data["bundle"]) == 1

        # Check bundle entity has original path
        bundle_id = "bundle:nested_0"
        assert bundle_id in saved_data["entity"]
        bundle_entity = saved_data["entity"][bundle_id]
        assert bundle_entity["prov:type"] == "prov:Bundle"
        assert bundle_entity["dataprov:originalPath"] == str(upstream_file)

        # In "both" mode, the used relationship should have both bundle reference and original path
        usage = list(saved_data["used"].values())[0]
        # In both mode, hadProvenanceBundle points to the bundle
        assert "dataprov:hadProvenanceBundle" in usage
        assert usage["dataprov:hadProvenanceBundle"] == bundle_id
        # And hadProvenance keeps the original path
        assert "dataprov:hadProvenance" in usage
        assert usage["dataprov:hadProvenance"] == str(upstream_file)

    def test_inline_missing_file_fallback(self, tmp_path, sample_file, timestamps):
        """Test that missing provenance files fallback to reference mode."""
        chain = ProvenanceChain.create(entity_id="main", initial_source="/main/")

        nonexistent_prov = str(tmp_path / "nonexistent_prov.json")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool",
            tool_version="1.0",
            operation="op",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
            input_provenance_files=[nonexistent_prov],
        )

        # Try to save with inline mode
        output_file = tmp_path / "main_prov.json"
        chain.save(str(output_file), input_prov="inline")

        # Load and verify
        with open(output_file) as f:
            saved_data = json.load(f)

        # Should not have bundle section (file missing, fallback to reference mode)
        bundles = saved_data.get("bundle", {})
        assert len(bundles) == 0

        # Input should still have original path in used relationship (fallback)
        usage = list(saved_data["used"].values())[0]
        assert usage["dataprov:hadProvenance"] == nonexistent_prov


class TestNestedProvenanceInlining:
    """Test nested provenance file inlining."""

    def test_nested_inline_two_levels(self, tmp_path, sample_file, timestamps):
        """Test inlining with two levels of nesting."""
        # Level 0: Base provenance
        base_chain = ProvenanceChain.create(entity_id="base", initial_source="/base/")
        base_chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="base_tool",
            tool_version="1.0",
            operation="base_op",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "base_output.txt")],
            output_formats=["TXT"],
        )
        base_file = tmp_path / "base_prov.json"
        base_chain.save(str(base_file))

        # Level 1: Middle provenance (references base)
        middle_chain = ProvenanceChain.create(
            entity_id="middle", initial_source="/middle/"
        )
        middle_chain.add(
            started_at="2024-10-15T12:00:00Z",
            ended_at="2024-10-15T12:05:00Z",
            tool_name="middle_tool",
            tool_version="1.0",
            operation="middle_op",
            inputs=[str(tmp_path / "base_output.txt")],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "middle_output.txt")],
            output_formats=["TXT"],
            input_provenance_files=[str(base_file)],
        )
        middle_file = tmp_path / "middle_prov.json"
        middle_chain.save(str(middle_file))

        # Level 2: Top provenance (references middle)
        top_chain = ProvenanceChain.create(entity_id="top", initial_source="/top/")
        top_chain.add(
            started_at="2024-10-15T13:00:00Z",
            ended_at="2024-10-15T13:05:00Z",
            tool_name="top_tool",
            tool_version="1.0",
            operation="top_op",
            inputs=[str(tmp_path / "middle_output.txt")],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "top_output.txt")],
            output_formats=["TXT"],
            input_provenance_files=[str(middle_file)],
        )

        # Save with inline mode
        output_file = tmp_path / "top_prov_inline.json"
        top_chain.save(str(output_file), input_prov="inline")

        # Load and verify
        with open(output_file) as f:
            saved_data = json.load(f)

        # Should have both base and middle inlined as bundles
        assert "bundle" in saved_data
        assert len(saved_data["bundle"]) == 2

        # Check bundle IDs
        bundle_ids = list(saved_data["bundle"].keys())
        assert "bundle:nested_0" in bundle_ids  # middle file from top chain
        assert "bundle:nested_1" in bundle_ids  # base file (nested in middle)

        # Check bundle entities exist
        assert "bundle:nested_0" in saved_data["entity"]
        assert "bundle:nested_1" in saved_data["entity"]

        # Find the middle bundle and verify it references the base bundle
        middle_bundle = saved_data["bundle"]["bundle:nested_0"]
        assert "middle" in middle_bundle["entity"]

        # Middle's used relationship should reference base bundle
        middle_used = list(middle_bundle["used"].values())[0]
        assert "dataprov:hadProvenance" in middle_used
        # After inlining, the nested reference should point to the nested bundle
        assert middle_used["dataprov:hadProvenance"] == "bundle:nested_1"

    def test_nested_inline_three_levels(self, tmp_path, sample_file, timestamps):
        """Test deep nesting (three levels)."""
        # Create three levels of provenance chains
        files = {}

        # Level 0
        chain0 = ProvenanceChain.create(entity_id="level0", initial_source="/l0/")
        chain0.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="tool0",
            tool_version="1.0",
            operation="op0",
            inputs=[sample_file],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "out0.txt")],
            output_formats=["TXT"],
        )
        files[0] = tmp_path / "prov0.json"
        chain0.save(str(files[0]))

        # Level 1
        chain1 = ProvenanceChain.create(entity_id="level1", initial_source="/l1/")
        chain1.add(
            started_at="2024-10-15T12:00:00Z",
            ended_at="2024-10-15T12:05:00Z",
            tool_name="tool1",
            tool_version="1.0",
            operation="op1",
            inputs=[str(tmp_path / "out0.txt")],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "out1.txt")],
            output_formats=["TXT"],
            input_provenance_files=[str(files[0])],
        )
        files[1] = tmp_path / "prov1.json"
        chain1.save(str(files[1]))

        # Level 2
        chain2 = ProvenanceChain.create(entity_id="level2", initial_source="/l2/")
        chain2.add(
            started_at="2024-10-15T13:00:00Z",
            ended_at="2024-10-15T13:05:00Z",
            tool_name="tool2",
            tool_version="1.0",
            operation="op2",
            inputs=[str(tmp_path / "out1.txt")],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "out2.txt")],
            output_formats=["TXT"],
            input_provenance_files=[str(files[1])],
        )

        # Save with inline
        output_file = tmp_path / "deep_inline.json"
        chain2.save(str(output_file), input_prov="inline")

        # Verify all three levels are inlined as bundles
        with open(output_file) as f:
            saved_data = json.load(f)

        assert "bundle" in saved_data
        # Should have prov0 and prov1 inlined as bundles
        assert len(saved_data["bundle"]) == 2  # level0 and level1

        # Verify bundle entities
        assert "bundle:nested_0" in saved_data["bundle"]  # level1
        assert "bundle:nested_1" in saved_data["bundle"]  # level0

        # Verify entity IDs in bundles
        level1_bundle = saved_data["bundle"]["bundle:nested_0"]
        level0_bundle = saved_data["bundle"]["bundle:nested_1"]

        assert "level1" in level1_bundle["entity"]
        assert "level0" in level0_bundle["entity"]


class TestDerivationMapping:
    """Test precise input-output derivation mapping."""

    def test_default_all_to_all_derivation(self, tmp_path, sample_file, timestamps):
        """Test default behavior: all outputs derive from all inputs."""
        chain = ProvenanceChain.create(
            entity_id="default_test", initial_source="/test/"
        )

        # Create test files
        input1 = tmp_path / "input1.txt"
        input2 = tmp_path / "input2.txt"
        output1 = tmp_path / "output1.txt"
        output2 = tmp_path / "output2.txt"
        input1.write_text("input1")
        input2.write_text("input2")
        output1.write_text("output1")
        output2.write_text("output2")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input1), str(input2)],
            input_formats=["TXT", "TXT"],
            outputs=[str(output1), str(output2)],
            output_formats=["TXT", "TXT"],
        )

        # Check that all outputs derive from all inputs (2x2 = 4 relationships)
        assert len(chain.data["wasDerivedFrom"]) == 4

    def test_one_to_one_mapping(self, tmp_path, sample_file, timestamps):
        """Test 1:1 input-output mapping."""
        chain = ProvenanceChain.create(
            entity_id="one_to_one_test", initial_source="/test/"
        )

        # Create test files
        input1 = tmp_path / "input1.txt"
        input2 = tmp_path / "input2.txt"
        output1 = tmp_path / "output1.txt"
        output2 = tmp_path / "output2.txt"
        input1.write_text("input1")
        input2.write_text("input2")
        output1.write_text("output1")
        output2.write_text("output2")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input1), str(input2)],
            input_formats=["TXT", "TXT"],
            outputs=[str(output1), str(output2)],
            output_formats=["TXT", "TXT"],
            derivation_map={0: [0], 1: [1]},  # input1->output1, input2->output2
        )

        # Check that only 2 derivation relationships exist (1:1)
        assert len(chain.data["wasDerivedFrom"]) == 2

        # Verify the relationships are correct
        derivations = list(chain.data["wasDerivedFrom"].values())
        output1_entity = f"entity:{output1}"
        output2_entity = f"entity:{output2}"
        input1_entity = f"entity:{input1}"
        input2_entity = f"entity:{input2}"

        # Find derivation for output1
        output1_derivs = [
            d for d in derivations if d["prov:generatedEntity"] == output1_entity
        ]
        assert len(output1_derivs) == 1
        assert output1_derivs[0]["prov:usedEntity"] == input1_entity

        # Find derivation for output2
        output2_derivs = [
            d for d in derivations if d["prov:generatedEntity"] == output2_entity
        ]
        assert len(output2_derivs) == 1
        assert output2_derivs[0]["prov:usedEntity"] == input2_entity

    def test_one_to_many_mapping(self, tmp_path, sample_file, timestamps):
        """Test one input produces multiple outputs."""
        chain = ProvenanceChain.create(
            entity_id="one_to_many_test", initial_source="/test/"
        )

        # Create test files
        input1 = tmp_path / "input1.txt"
        output1 = tmp_path / "output1.txt"
        output2 = tmp_path / "output2.txt"
        output3 = tmp_path / "output3.txt"
        input1.write_text("input1")
        output1.write_text("output1")
        output2.write_text("output2")
        output3.write_text("output3")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input1)],
            input_formats=["TXT"],
            outputs=[str(output1), str(output2), str(output3)],
            output_formats=["TXT", "TXT", "TXT"],
            derivation_map={0: [0, 1, 2]},  # input1 -> all 3 outputs
        )

        # Check that 3 derivation relationships exist
        assert len(chain.data["wasDerivedFrom"]) == 3

        # All outputs should derive from input1
        input1_entity = f"entity:{input1}"
        for deriv in chain.data["wasDerivedFrom"].values():
            assert deriv["prov:usedEntity"] == input1_entity

    def test_many_to_one_mapping(self, tmp_path, sample_file, timestamps):
        """Test multiple inputs produce one output."""
        chain = ProvenanceChain.create(
            entity_id="many_to_one_test", initial_source="/test/"
        )

        # Create test files
        input1 = tmp_path / "input1.txt"
        input2 = tmp_path / "input2.txt"
        input3 = tmp_path / "input3.txt"
        output1 = tmp_path / "output1.txt"
        input1.write_text("input1")
        input2.write_text("input2")
        input3.write_text("input3")
        output1.write_text("output1")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input1), str(input2), str(input3)],
            input_formats=["TXT", "TXT", "TXT"],
            outputs=[str(output1)],
            output_formats=["TXT"],
            derivation_map={0: [0], 1: [0], 2: [0]},  # all inputs -> output1
        )

        # Check that 3 derivation relationships exist
        assert len(chain.data["wasDerivedFrom"]) == 3

        # All should point to output1
        output1_entity = f"entity:{output1}"
        for deriv in chain.data["wasDerivedFrom"].values():
            assert deriv["prov:generatedEntity"] == output1_entity

    def test_complex_mapping(self, tmp_path, sample_file, timestamps):
        """Test complex mixed mapping (like batch video processing with shared audio)."""
        chain = ProvenanceChain.create(
            entity_id="complex_test", initial_source="/test/"
        )

        # Create test files
        video1 = tmp_path / "video1.mp4"
        video2 = tmp_path / "video2.mp4"
        audio = tmp_path / "audio.wav"
        final1 = tmp_path / "final1.mp4"
        final2 = tmp_path / "final2.mp4"
        video1.write_text("video1")
        video2.write_text("video2")
        audio.write_text("audio")
        final1.write_text("final1")
        final2.write_text("final2")

        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="batch_processor",
            tool_version="2.0",
            operation="mux_audio",
            inputs=[str(video1), str(video2), str(audio)],
            input_formats=["MP4", "MP4", "WAV"],
            outputs=[str(final1), str(final2)],
            output_formats=["MP4", "MP4"],
            derivation_map={
                0: [0],  # video1 -> final1
                1: [1],  # video2 -> final2
                2: [0, 1],  # audio -> both outputs
            },
        )

        # Check that 4 derivation relationships exist (video1->final1, video2->final2, audio->final1, audio->final2)
        assert len(chain.data["wasDerivedFrom"]) == 4

        # Verify final1 derives from video1 and audio
        final1_entity = f"entity:{final1}"
        final1_derivs = [
            d
            for d in chain.data["wasDerivedFrom"].values()
            if d["prov:generatedEntity"] == final1_entity
        ]
        assert len(final1_derivs) == 2
        final1_sources = {d["prov:usedEntity"] for d in final1_derivs}
        assert f"entity:{video1}" in final1_sources
        assert f"entity:{audio}" in final1_sources

        # Verify final2 derives from video2 and audio
        final2_entity = f"entity:{final2}"
        final2_derivs = [
            d
            for d in chain.data["wasDerivedFrom"].values()
            if d["prov:generatedEntity"] == final2_entity
        ]
        assert len(final2_derivs) == 2
        final2_sources = {d["prov:usedEntity"] for d in final2_derivs}
        assert f"entity:{video2}" in final2_sources
        assert f"entity:{audio}" in final2_sources

    def test_invalid_input_index(self, tmp_path, sample_file, timestamps):
        """Test error on out-of-bounds input index."""
        chain = ProvenanceChain.create(
            entity_id="invalid_input_test", initial_source="/test/"
        )

        result = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
            derivation_map={5: [0]},  # Invalid: only 1 input (index 0)
        )

        # Should return False due to validation error
        assert not result
        assert len(chain.get_steps()) == 0

    def test_invalid_output_index(self, tmp_path, sample_file, timestamps):
        """Test error on out-of-bounds output index."""
        chain = ProvenanceChain.create(
            entity_id="invalid_output_test", initial_source="/test/"
        )

        result = chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
            derivation_map={0: [5]},  # Invalid: only 1 output (index 0)
        )

        # Should return False due to validation error
        assert not result
        assert len(chain.get_steps()) == 0


class TestAttribution:
    """Test wasAttributedTo functionality (add_attribution method)."""

    def test_add_attribution_to_current_user(self, tmp_path, sample_file):
        """Test attributing a file to the current user."""
        chain = ProvenanceChain.create(
            entity_id="attribution_test", initial_source="/test/"
        )

        success = chain.add_attribution(
            files=str(sample_file), capture_current_user=True
        )

        assert success is True
        # Check wasAttributedTo was populated
        assert len(chain.data["wasAttributedTo"]) == 1

        # Check entity was created
        entity_id = f"entity:{sample_file}"
        assert entity_id in chain.data["entity"]

        # Check agent was created
        assert len(chain.data["agent"]) == 1
        agent_id = list(chain.data["agent"].keys())[0]
        agent = chain.data["agent"][agent_id]
        assert agent["prov:type"] == "prov:Person"
        assert "dataprov:user" in agent
        assert "dataprov:hostname" in agent

    def test_add_attribution_to_external_person(self, tmp_path, sample_file):
        """Test attributing a file to an external person."""
        chain = ProvenanceChain.create(
            entity_id="external_person_test", initial_source="/test/"
        )

        success = chain.add_attribution(
            files=str(sample_file),
            agent_name="dr.smith@university.edu",
            agent_type="prov:Person",
        )

        assert success is True
        assert len(chain.data["wasAttributedTo"]) == 1

        # Check agent
        agent_id = "agent:dr.smith@university.edu"
        assert agent_id in chain.data["agent"]
        agent = chain.data["agent"][agent_id]
        assert agent["prov:type"] == "prov:Person"
        assert agent["dataprov:name"] == "dr.smith@university.edu"

    def test_add_attribution_to_organization(self, tmp_path, sample_file):
        """Test attributing a file to an organization."""
        chain = ProvenanceChain.create(entity_id="org_test", initial_source="/test/")

        success = chain.add_attribution(
            files=str(sample_file),
            agent_name="US Census Bureau",
            agent_type="prov:Organization",
        )

        assert success is True

        # Check agent
        agent_id = "agent:US_Census_Bureau"
        assert agent_id in chain.data["agent"]
        agent = chain.data["agent"][agent_id]
        assert agent["prov:type"] == "prov:Organization"
        assert agent["dataprov:name"] == "US Census Bureau"

    def test_add_attribution_multiple_files(self, tmp_path):
        """Test attributing multiple files at once."""
        # Create multiple test files
        file1 = tmp_path / "data1.csv"
        file2 = tmp_path / "data2.csv"
        file3 = tmp_path / "data3.csv"
        file1.write_text("data1")
        file2.write_text("data2")
        file3.write_text("data3")

        chain = ProvenanceChain.create(
            entity_id="multi_attr_test", initial_source="/test/"
        )

        success = chain.add_attribution(
            files=[str(file1), str(file2), str(file3)],
            agent_name="data_curator",
            agent_type="prov:Person",
        )

        assert success is True
        # Should have 3 attribution relationships
        assert len(chain.data["wasAttributedTo"]) == 3
        # Should have 3 entities
        assert f"entity:{file1}" in chain.data["entity"]
        assert f"entity:{file2}" in chain.data["entity"]
        assert f"entity:{file3}" in chain.data["entity"]

    def test_add_attribution_with_role(self, tmp_path, sample_file):
        """Test adding attribution with a role."""
        chain = ProvenanceChain.create(entity_id="role_test", initial_source="/test/")

        success = chain.add_attribution(
            files=str(sample_file), agent_name="researcher", role="curator"
        )

        assert success is True

        # Check attribution has role
        attr = list(chain.data["wasAttributedTo"].values())[0]
        assert attr["prov:role"] == "curator"

    def test_add_attribution_auto_detect_format(self, tmp_path):
        """Test auto-detecting file format from extension."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("col1,col2\n1,2")

        chain = ProvenanceChain.create(entity_id="format_test", initial_source="/test/")

        success = chain.add_attribution(files=str(csv_file), agent_name="analyst")

        assert success is True

        # Check format was auto-detected
        entity_id = f"entity:{csv_file}"
        entity = chain.data["entity"][entity_id]
        assert entity["dataprov:format"] == "csv"

    def test_add_attribution_explicit_format(self, tmp_path, sample_file):
        """Test explicitly specifying file format."""
        chain = ProvenanceChain.create(
            entity_id="explicit_format_test", initial_source="/test/"
        )

        success = chain.add_attribution(
            files=str(sample_file), file_formats="TXT", agent_name="analyst"
        )

        assert success is True

        # Check format
        entity_id = f"entity:{sample_file}"
        entity = chain.data["entity"][entity_id]
        assert entity["dataprov:format"] == "TXT"

    def test_add_attribution_checksum_calculated(self, tmp_path, sample_file):
        """Test that checksums are calculated for attributed files."""
        chain = ProvenanceChain.create(
            entity_id="checksum_test", initial_source="/test/"
        )

        success = chain.add_attribution(files=str(sample_file), agent_name="analyst")

        assert success is True

        # Check checksum
        entity_id = f"entity:{sample_file}"
        entity = chain.data["entity"][entity_id]
        assert "dataprov:checksum" in entity
        assert entity["dataprov:checksum"].startswith("sha256:")

    def test_add_attribution_created_at_auto_detect(self, tmp_path, sample_file):
        """Test auto-detection of file creation time from mtime."""
        chain = ProvenanceChain.create(
            entity_id="created_test", initial_source="/test/"
        )

        success = chain.add_attribution(files=str(sample_file), agent_name="analyst")

        assert success is True

        # Check created_at was set
        entity_id = f"entity:{sample_file}"
        entity = chain.data["entity"][entity_id]
        assert "dataprov:createdAt" in entity
        # Should be in ISO 8601 format with Z
        assert entity["dataprov:createdAt"].endswith("Z")

    def test_add_attribution_created_at_explicit(self, tmp_path, sample_file):
        """Test explicitly setting creation time."""
        chain = ProvenanceChain.create(
            entity_id="explicit_created_test", initial_source="/test/"
        )

        custom_time = "2024-01-15T10:30:00Z"
        success = chain.add_attribution(
            files=str(sample_file), agent_name="analyst", created_at=custom_time
        )

        assert success is True

        # Check created_at
        entity_id = f"entity:{sample_file}"
        entity = chain.data["entity"][entity_id]
        assert entity["dataprov:createdAt"] == custom_time

    def test_add_attribution_validation_no_agent_specified(self, tmp_path, sample_file):
        """Test error when neither agent_name nor capture_current_user is specified."""
        chain = ProvenanceChain.create(
            entity_id="no_agent_test", initial_source="/test/"
        )

        success = chain.add_attribution(files=str(sample_file))

        assert success is False
        assert len(chain.data["wasAttributedTo"]) == 0

    def test_add_attribution_validation_both_agents_specified(
        self, tmp_path, sample_file
    ):
        """Test error when both agent_name and capture_current_user are specified."""
        chain = ProvenanceChain.create(
            entity_id="both_agents_test", initial_source="/test/"
        )

        success = chain.add_attribution(
            files=str(sample_file), agent_name="analyst", capture_current_user=True
        )

        assert success is False
        assert len(chain.data["wasAttributedTo"]) == 0

    def test_add_attribution_validation_invalid_agent_type(self, tmp_path, sample_file):
        """Test error when invalid agent_type is specified."""
        chain = ProvenanceChain.create(
            entity_id="invalid_type_test", initial_source="/test/"
        )

        success = chain.add_attribution(
            files=str(sample_file), agent_name="analyst", agent_type="InvalidType"
        )

        assert success is False
        assert len(chain.data["wasAttributedTo"]) == 0

    def test_add_attribution_validation_format_mismatch(self, tmp_path, sample_file):
        """Test error when files and formats lists have different lengths."""
        chain = ProvenanceChain.create(
            entity_id="format_mismatch_test", initial_source="/test/"
        )

        success = chain.add_attribution(
            files=[str(sample_file), str(sample_file)],
            file_formats=["CSV"],  # Only one format for two files
            agent_name="analyst",
        )

        assert success is False
        assert len(chain.data["wasAttributedTo"]) == 0

    def test_add_attribution_reuses_existing_entity(
        self, tmp_path, sample_file, timestamps
    ):
        """Test that attribution reuses existing entity if it exists."""
        chain = ProvenanceChain.create(
            entity_id="reuse_entity_test", initial_source="/test/"
        )

        # First create entity through add()
        chain.add(
            started_at=timestamps["started_at"],
            ended_at=timestamps["ended_at"],
            tool_name="processor",
            tool_version="1.0",
            operation="process",
            inputs=[str(sample_file)],
            input_formats=["TXT"],
            outputs=[str(tmp_path / "output.txt")],
            output_formats=["TXT"],
        )

        # Now add attribution to the same file
        success = chain.add_attribution(files=str(sample_file), agent_name="analyst")

        assert success is True
        # Should still only have one entity for this file
        entity_id = f"entity:{sample_file}"
        assert entity_id in chain.data["entity"]
        # Count how many times this entity appears
        entity_count = sum(1 for k in chain.data["entity"] if k == entity_id)
        assert entity_count == 1

    def test_add_attribution_reuses_existing_agent(self, tmp_path, sample_file):
        """Test that attribution reuses existing agent if it exists."""
        chain = ProvenanceChain.create(
            entity_id="reuse_agent_test", initial_source="/test/"
        )

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("data1")
        file2.write_text("data2")

        # Add attribution to first file
        chain.add_attribution(files=str(file1), agent_name="curator")

        # Add attribution to second file with same agent
        chain.add_attribution(files=str(file2), agent_name="curator")

        # Should only have one agent
        assert len(chain.data["agent"]) == 1
        # But two attributions
        assert len(chain.data["wasAttributedTo"]) == 2

    def test_add_attribution_updates_last_modified(self, tmp_path, sample_file):
        """Test that add_attribution updates lastModified timestamp."""
        chain = ProvenanceChain.create(
            entity_id="last_mod_test", initial_source="/test/"
        )

        original_last_modified = chain.data["dataprov:metadata"]["lastModified"]

        # Add small delay to ensure timestamp differs
        import time

        time.sleep(0.01)

        chain.add_attribution(files=str(sample_file), agent_name="analyst")

        # lastModified should be updated
        assert chain.data["dataprov:metadata"]["lastModified"] != original_last_modified
        assert chain.data["dataprov:metadata"]["lastModified"] > original_last_modified

    def test_add_attribution_nonexistent_file(self, tmp_path):
        """Test attribution of nonexistent file (should still work for external files)."""
        nonexistent = tmp_path / "does_not_exist.csv"

        chain = ProvenanceChain.create(
            entity_id="nonexistent_test", initial_source="/test/"
        )

        success = chain.add_attribution(
            files=str(nonexistent),
            agent_name="external_source",
            agent_type="prov:Organization",
        )

        # Should succeed (useful for external files not on this system)
        assert success is True

        # Entity should be created
        entity_id = f"entity:{nonexistent}"
        assert entity_id in chain.data["entity"]

        # But checksum and size should not be present
        entity = chain.data["entity"][entity_id]
        assert "dataprov:checksum" not in entity
        assert "dataprov:sizeBytes" not in entity

    def test_add_attribution_with_user_override(self, tmp_path, sample_file):
        """Test overriding user when capturing current user."""
        chain = ProvenanceChain.create(
            entity_id="user_override_test", initial_source="/test/"
        )

        success = chain.add_attribution(
            files=str(sample_file),
            capture_current_user=True,
            user="custom_user@example.com",
            hostname="custom_host",
        )

        assert success is True

        # Check agent has custom values
        agent = list(chain.data["agent"].values())[0]
        assert agent["dataprov:user"] == "custom_user@example.com"
        assert agent["dataprov:hostname"] == "custom_host"


class TestCustomNamespaces:
    """Tests for custom ontology namespace support."""

    def test_create_with_custom_namespaces(self, tmp_path):
        """Test creating provenance chain with custom namespaces."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={
                "myapp": "https://example.com/myapp/",
                "foaf": "http://xmlns.com/foaf/0.1/",
            },
        )

        # Check that custom namespaces are in prefix section
        assert "myapp" in chain.data["prefix"]
        assert chain.data["prefix"]["myapp"] == "https://example.com/myapp/"
        assert "foaf" in chain.data["prefix"]
        assert chain.data["prefix"]["foaf"] == "http://xmlns.com/foaf/0.1/"

        # Check that default namespaces are still present
        assert "dataprov" in chain.data["prefix"]
        assert "prov" in chain.data["prefix"]
        assert "xsd" in chain.data["prefix"]

        # Check namespaces are stored in instance
        assert "myapp" in chain.namespaces
        assert "foaf" in chain.namespaces

    def test_reserved_prefix_conflict(self, tmp_path):
        """Test that reserved prefix conflicts are rejected."""
        with pytest.raises(ValueError, match="conflicts with reserved prefix"):
            ProvenanceChain.create(
                entity_id="test_entity",
                initial_source="/test/source",
                custom_namespaces={"prov": "https://example.com/custom/"},
            )

        with pytest.raises(ValueError, match="conflicts with reserved prefix"):
            ProvenanceChain.create(
                entity_id="test_entity",
                initial_source="/test/source",
                custom_namespaces={"dataprov": "https://example.com/custom/"},
            )

    def test_add_with_custom_properties_output_entity(self, tmp_path):
        """Test adding custom properties to output entities."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={"myapp": "https://example.com/myapp/"},
        )

        # Create test files
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("test")
        output_file.write_text("result")

        # Add step with custom properties using target prefix format
        success = chain.add(
            started_at="2024-01-01T10:00:00Z",
            ended_at="2024-01-01T10:05:00Z",
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input_file)],
            input_formats=["txt"],
            outputs=[str(output_file)],
            output_formats=["txt"],
            custom_properties={
                "output-entity:myapp:status": "validated",
                "output-entity:myapp:qualityScore": 95,
                "output-entity:myapp:reviewer": "john.doe@example.com",
            },
        )

        assert success is True

        # Check that custom properties are in output entity
        output_entity = chain.data["entity"][f"entity:{output_file}"]
        assert "myapp:status" in output_entity
        assert output_entity["myapp:status"] == "validated"
        assert "myapp:qualityScore" in output_entity
        assert output_entity["myapp:qualityScore"] == 95
        assert "myapp:reviewer" in output_entity
        assert output_entity["myapp:reviewer"] == "john.doe@example.com"

    def test_add_with_custom_properties_all_entities(self, tmp_path):
        """Test adding custom properties to all entities using 'entity' target."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={"myapp": "https://example.com/myapp/"},
        )

        # Create test files
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("test")
        output_file.write_text("result")

        # Add step with custom properties applied to all entities
        success = chain.add(
            started_at="2024-01-01T10:00:00Z",
            ended_at="2024-01-01T10:05:00Z",
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input_file)],
            input_formats=["txt"],
            outputs=[str(output_file)],
            output_formats=["txt"],
            custom_properties={"entity:myapp:verified": True},
        )

        assert success is True

        # Check that property is on both input and output entities
        input_entity = chain.data["entity"][f"entity:{input_file}"]
        assert "myapp:verified" in input_entity
        assert input_entity["myapp:verified"] is True

        output_entity = chain.data["entity"][f"entity:{output_file}"]
        assert "myapp:verified" in output_entity
        assert output_entity["myapp:verified"] is True

    def test_add_attribution_with_custom_properties(self, tmp_path):
        """Test add_attribution with custom properties."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={"myapp": "https://example.com/myapp/"},
        )

        # Create test file
        test_file = tmp_path / "manual_data.csv"
        test_file.write_text("col1,col2\nval1,val2")

        # Add attribution with custom properties
        success = chain.add_attribution(
            files=str(test_file),
            agent_name="Dr. Jane Smith",
            agent_type="prov:Person",
            role="curator",
            custom_properties={
                "entity:myapp:qualityLevel": "high",
                "entity:myapp:reviewStatus": "approved",
            },
        )

        assert success is True

        # Check that custom properties are in entity
        entity = chain.data["entity"][f"entity:{test_file}"]
        assert "myapp:qualityLevel" in entity
        assert entity["myapp:qualityLevel"] == "high"
        assert "myapp:reviewStatus" in entity
        assert entity["myapp:reviewStatus"] == "approved"

    def test_undeclared_prefix_error(self, tmp_path):
        """Test that using undeclared prefix raises error."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={"myapp": "https://example.com/myapp/"},
        )

        # Create test files
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("test")
        output_file.write_text("result")

        # Try to use undeclared prefix
        with pytest.raises(ValueError, match="Undeclared namespace prefix"):
            chain.add(
                started_at="2024-01-01T10:00:00Z",
                ended_at="2024-01-01T10:05:00Z",
                tool_name="test_tool",
                tool_version="1.0",
                operation="test_op",
                inputs=[str(input_file)],
                input_formats=["txt"],
                outputs=[str(output_file)],
                output_formats=["txt"],
                custom_properties={
                    "entity:otherapp:field": "value"  # otherapp not declared
                },
            )

    def test_invalid_property_format_error(self):
        """Test that property without target prefix raises error."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={"myapp": "https://example.com/myapp/"},
        )

        # Try to use invalid format (missing target prefix)
        with pytest.raises(ValueError, match="Invalid custom property format"):
            chain._parse_custom_properties({"myapp:field": "value"})

    def test_multiple_custom_namespaces(self, tmp_path):
        """Test using multiple custom namespaces simultaneously."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={
                "myapp": "https://example.com/myapp/",
                "foaf": "http://xmlns.com/foaf/0.1/",
                "dcterms": "http://purl.org/dc/terms/",
            },
        )

        # Create test files
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("test")
        output_file.write_text("result")

        # Add step with properties from multiple namespaces
        success = chain.add(
            started_at="2024-01-01T10:00:00Z",
            ended_at="2024-01-01T10:05:00Z",
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input_file)],
            input_formats=["txt"],
            outputs=[str(output_file)],
            output_formats=["txt"],
            custom_properties={
                "output-entity:myapp:status": "validated",
                "output-entity:foaf:name": "John Doe",
                "output-entity:dcterms:license": "MIT",
            },
        )

        assert success is True

        # Check that all custom properties are present
        output_entity = chain.data["entity"][f"entity:{output_file}"]
        assert output_entity["myapp:status"] == "validated"
        assert output_entity["foaf:name"] == "John Doe"
        assert output_entity["dcterms:license"] == "MIT"

    def test_save_and_load_custom_namespaces(self, tmp_path):
        """Test that custom namespaces persist through save/load."""
        prov_file = tmp_path / "test.prov.json"

        # Create chain with custom namespaces
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={
                "myapp": "https://example.com/myapp/",
                "foaf": "http://xmlns.com/foaf/0.1/",
            },
        )

        # Save
        chain.save(str(prov_file))

        # Load
        loaded_chain = ProvenanceChain.load(str(prov_file))

        # Check that custom namespaces are present
        assert "myapp" in loaded_chain.namespaces
        assert loaded_chain.namespaces["myapp"] == "https://example.com/myapp/"
        assert "foaf" in loaded_chain.namespaces
        assert loaded_chain.namespaces["foaf"] == "http://xmlns.com/foaf/0.1/"

        # Check that default namespaces are still present
        assert "dataprov" in loaded_chain.namespaces
        assert "prov" in loaded_chain.namespaces
        assert "xsd" in loaded_chain.namespaces

    def test_custom_properties_with_different_types(self, tmp_path):
        """Test that custom properties can have different value types."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={"myapp": "https://example.com/myapp/"},
        )

        # Create test files
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("test")
        output_file.write_text("result")

        # Add step with various property types
        success = chain.add(
            started_at="2024-01-01T10:00:00Z",
            ended_at="2024-01-01T10:05:00Z",
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input_file)],
            input_formats=["txt"],
            outputs=[str(output_file)],
            output_formats=["txt"],
            custom_properties={
                "output-entity:myapp:stringField": "text",
                "output-entity:myapp:intField": 42,
                "output-entity:myapp:floatField": 3.14,
                "output-entity:myapp:boolField": True,
            },
        )

        assert success is True

        # Check property types are preserved
        output_entity = chain.data["entity"][f"entity:{output_file}"]
        assert output_entity["myapp:stringField"] == "text"
        assert output_entity["myapp:intField"] == 42
        assert output_entity["myapp:floatField"] == 3.14
        assert output_entity["myapp:boolField"] is True

    def test_activity_properties(self, tmp_path):
        """Test adding custom properties to activities."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={"myapp": "https://example.com/myapp/"},
        )

        # Create test files
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("test")
        output_file.write_text("result")

        # Add step with activity properties
        success = chain.add(
            started_at="2024-01-01T10:00:00Z",
            ended_at="2024-01-01T10:05:00Z",
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input_file)],
            input_formats=["txt"],
            outputs=[str(output_file)],
            output_formats=["txt"],
            custom_properties={
                "activity:myapp:processingMode": "automatic",
                "activity:myapp:priority": "high",
            },
        )

        assert success is True

        # Check that properties are on the activity
        activity = list(chain.data["activity"].values())[0]
        assert "myapp:processingMode" in activity
        assert activity["myapp:processingMode"] == "automatic"
        assert "myapp:priority" in activity
        assert activity["myapp:priority"] == "high"

    def test_agent_properties(self, tmp_path):
        """Test adding custom properties to agents."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={"myapp": "https://example.com/myapp/"},
        )

        # Create test files
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("test")
        output_file.write_text("result")

        # Add step with agent properties
        success = chain.add(
            started_at="2024-01-01T10:00:00Z",
            ended_at="2024-01-01T10:05:00Z",
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input_file)],
            input_formats=["txt"],
            outputs=[str(output_file)],
            output_formats=["txt"],
            custom_properties={
                "agent:myapp:licenseKey": "ABC123",
                "agent:myapp:department": "research",
            },
        )

        assert success is True

        # Check that properties are on the agent
        agent = list(chain.data["agent"].values())[0]
        assert "myapp:licenseKey" in agent
        assert agent["myapp:licenseKey"] == "ABC123"
        assert "myapp:department" in agent
        assert agent["myapp:department"] == "research"

    def test_input_entity_properties(self, tmp_path):
        """Test adding custom properties to input entities only."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={"myapp": "https://example.com/myapp/"},
        )

        # Create test files
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("test")
        output_file.write_text("result")

        # Add step with input-entity properties
        success = chain.add(
            started_at="2024-01-01T10:00:00Z",
            ended_at="2024-01-01T10:05:00Z",
            tool_name="test_tool",
            tool_version="1.0",
            operation="test_op",
            inputs=[str(input_file)],
            input_formats=["txt"],
            outputs=[str(output_file)],
            output_formats=["txt"],
            custom_properties={
                "input-entity:myapp:annotation": "checked",
                "input-entity:myapp:reviewDate": "2024-01-01",
            },
        )

        assert success is True

        # Check that properties are on input entity only
        input_entity = chain.data["entity"][f"entity:{input_file}"]
        assert "myapp:annotation" in input_entity
        assert input_entity["myapp:annotation"] == "checked"
        assert "myapp:reviewDate" in input_entity
        assert input_entity["myapp:reviewDate"] == "2024-01-01"

        # Output entity should not have these properties
        output_entity = chain.data["entity"][f"entity:{output_file}"]
        assert "myapp:annotation" not in output_entity
        assert "myapp:reviewDate" not in output_entity

    def test_custom_metadata(self):
        """Test adding custom metadata sections."""
        chain = ProvenanceChain.create(
            entity_id="test_entity",
            initial_source="/test/source",
            custom_namespaces={"myapp": "https://example.com/myapp/"},
            custom_metadata={
                "myapp:projectId": "PROJ-001",
                "myapp:funding": "NSF Grant #12345",
                "myapp:contact": "pi@example.org",
            },
        )

        # Check that custom metadata is in the data
        assert "myapp:projectId" in chain.data
        assert chain.data["myapp:projectId"] == "PROJ-001"
        assert "myapp:funding" in chain.data
        assert chain.data["myapp:funding"] == "NSF Grant #12345"
        assert "myapp:contact" in chain.data
        assert chain.data["myapp:contact"] == "pi@example.org"

    def test_custom_metadata_validation(self):
        """Test that custom metadata validates namespace prefixes."""
        # Should raise error for undeclared prefix
        with pytest.raises(ValueError, match="Undeclared namespace prefix"):
            ProvenanceChain.create(
                entity_id="test_entity",
                initial_source="/test/source",
                custom_namespaces={"myapp": "https://example.com/myapp/"},
                custom_metadata={
                    "otherapp:field": "value"  # otherapp not declared
                },
            )

        # Should raise error for invalid format
        with pytest.raises(ValueError, match="Invalid custom metadata key"):
            ProvenanceChain.create(
                entity_id="test_entity",
                initial_source="/test/source",
                custom_namespaces={"myapp": "https://example.com/myapp/"},
                custom_metadata={
                    "invalidkey": "value"  # missing namespace prefix
                },
            )
