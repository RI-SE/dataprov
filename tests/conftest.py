"""
Pytest configuration and fixtures for dataprov tests.

Fixtures:
- tmp_path: Built-in pytest fixture for temporary directories
- sample_file: Creates a temporary test file with known content
- sample_files: Creates multiple temporary test files
"""

import pytest


@pytest.fixture
def sample_file(tmp_path):
    """Create a sample file for testing.

    Creates a temporary file with known content for testing
    file integrity tracking (checksums, sizes, etc.).

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        Path: Path to the created sample file
    """
    file_path = tmp_path / "sample.txt"
    file_path.write_text("This is a test file for dataprov testing.\n")
    return file_path


@pytest.fixture
def sample_files(tmp_path):
    """Create multiple sample files for testing.

    Creates multiple temporary files for testing multi-input
    processing steps.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        list[Path]: List of paths to created sample files
    """
    files = []
    for i in range(3):
        file_path = tmp_path / f"sample_{i}.txt"
        file_path.write_text(f"This is test file {i}.\n")
        files.append(file_path)
    return files


@pytest.fixture
def sample_provenance_chain(tmp_path):
    """Create a sample provenance chain file for testing.

    Creates a valid provenance chain JSON file that can be
    used for testing loading and validation.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        Path: Path to the created provenance chain file
    """
    from dataprov import ProvenanceChain

    chain = ProvenanceChain.create(
        entity_id="fixture_chain",
        initial_source="/test/fixture/",
        description="Test fixture chain",
        tags=["fixture", "test"],
    )

    filepath = tmp_path / "fixture_chain.json"
    chain.save(str(filepath))
    return filepath


@pytest.fixture
def large_sample_file(tmp_path):
    """Create a larger sample file for testing.

    Creates a file with more content to test checksum calculation
    and file size tracking with larger files.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        Path: Path to the created large sample file
    """
    file_path = tmp_path / "large_sample.txt"

    # Create a file with ~10KB of content
    content = "Line of text for testing.\n" * 400
    file_path.write_text(content)

    return file_path
