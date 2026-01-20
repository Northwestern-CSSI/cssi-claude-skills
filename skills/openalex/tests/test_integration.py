#!/usr/bin/env python3
"""
Integration tests for OpenAlex skill.
These tests run actual commands and verify behavior.
"""

import subprocess
import json
import os
import pytest

# Path to the helper script
HELPER_SCRIPT = os.path.expanduser('~/.claude/skills/openalex/openalex_helper.py')
CONDA_CMD = ['/opt/anaconda3/bin/conda', 'run', '-n', 'base', 'python', HELPER_SCRIPT]


def run_command(args, expect_failure=False):
    """Run a command and return the result."""
    result = subprocess.run(
        CONDA_CMD + args,
        capture_output=True,
        text=True,
        timeout=120
    )
    if expect_failure:
        assert result.returncode != 0, f"Expected failure but got success: {result.stdout}"
        return result.stderr
    else:
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        return json.loads(result.stdout)


class TestBasicSearch:
    """Tests for basic search functionality."""

    def test_search_works_basic(self):
        """Basic search should return results."""
        data = run_command(['search-works', 'machine learning', '-l', '5'])
        assert 'works' in data
        assert len(data['works']) <= 5
        assert data['total'] > 0

    def test_search_authors_basic(self):
        """Author search should return results."""
        data = run_command(['search-authors', 'Einstein', '-l', '5'])
        assert 'authors' in data

    def test_search_institutions_basic(self):
        """Institution search should return results."""
        data = run_command(['search-institutions', 'Stanford', '-l', '5'])
        assert 'institutions' in data

    def test_search_funders_basic(self):
        """Funder search should return results."""
        data = run_command(['search-funders', 'NSF', '-l', '5'])
        assert 'funders' in data


class TestGroupBy:
    """Tests for group_by functionality."""

    def test_group_by_valid_field(self):
        """Group by valid field should succeed."""
        data = run_command(['group', 'works', 'publication_year',
                          '-f', 'publication_year:>2020'])
        assert 'groups' in data
        assert len(data['groups']) > 0

    def test_group_by_oa_status(self):
        """Group by oa_status should work."""
        data = run_command(['group', 'works', 'oa_status',
                          '-f', 'publication_year:2023'])
        assert 'groups' in data

    def test_group_by_invalid_field_fails(self):
        """Group by invalid field should fail with helpful error."""
        stderr = run_command(['group', 'works', 'grants.funder'], expect_failure=True)
        assert 'Invalid group_by field' in stderr

    def test_group_by_nonexistent_field_fails(self):
        """Group by nonexistent field should fail."""
        stderr = run_command(['group', 'works', 'fake_field_xyz'], expect_failure=True)
        assert 'Invalid' in stderr


class TestSelectValidation:
    """Tests for select parameter validation."""

    def test_valid_select_succeeds(self):
        """Valid select fields should work."""
        data = run_command(['search-works', 'AI', '-l', '1',
                          '--select', 'id,title,publication_year'])
        assert 'works' in data

    def test_invalid_select_grants_fails(self):
        """Selecting grants should fail."""
        stderr = run_command(['search-works', 'AI', '-l', '1',
                            '--select', 'id,grants'], expect_failure=True)
        assert 'Invalid select field' in stderr or 'grants' in stderr


class TestGetEntity:
    """Tests for getting single entities."""

    def test_get_work_by_id(self):
        """Get work by OpenAlex ID should work."""
        data = run_command(['get', 'works', 'W2741809807'])
        assert 'id' in data
        assert 'title' in data

    def test_get_funder_by_id(self):
        """Get funder by ID should work."""
        data = run_command(['get', 'funders', 'F4320306076'])  # NSF
        assert 'id' in data
        assert 'display_name' in data


class TestOutputFormats:
    """Tests for output file generation."""

    def test_dual_format_creates_both_files(self):
        """Dual format should create both parquet and jsonl."""
        data = run_command(['search-works', 'test query xyz', '-l', '5'])
        if data.get('saved_to'):
            saved = data['saved_to']
            if isinstance(saved, dict):
                assert 'parquet' in saved
                assert 'jsonl' in saved


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
