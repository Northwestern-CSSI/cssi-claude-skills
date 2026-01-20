#!/usr/bin/env python3
"""
Integration tests for Dimensions skill.
These tests run actual commands and verify behavior.
"""

import subprocess
import json
import os
import pytest

# Path to the helper script
HELPER_SCRIPT = os.path.expanduser('~/.claude/skills/dimensions/dimensions_helper.py')
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
        # Extract JSON from output (skip any dimcli login messages)
        stdout = result.stdout.strip()
        # Find the start of JSON (first { character)
        json_start = stdout.find('{')
        if json_start == -1:
            raise ValueError(f"No JSON found in output: {stdout[:200]}")
        json_str = stdout[json_start:]
        return json.loads(json_str)


class TestBasicSearch:
    """Tests for basic search functionality."""

    def test_search_publications_basic(self):
        """Basic publication search should return results."""
        data = run_command(['search-publications', 'machine learning', '-l', '5'])
        assert 'publications' in data
        assert data['total'] > 0

    def test_search_grants_basic(self):
        """Grant search should return results."""
        data = run_command(['search-grants', 'cancer', '-l', '5'])
        assert 'grants' in data


class TestAggregate:
    """Tests for aggregate functionality."""

    def test_aggregate_valid_facet(self):
        """Aggregate by valid facet should succeed."""
        data = run_command(['aggregate', 'publications', 'AI', '-F', 'year', '-l', '5'])
        assert 'data' in data
        assert len(data['data']) > 0

    def test_aggregate_grants_by_funder(self):
        """Aggregate grants by funder should work."""
        data = run_command(['aggregate', 'grants', 'quantum',
                          '-F', 'funder_org_acronym', '-a', 'funding', '-l', '5'])
        assert 'data' in data

    def test_aggregate_invalid_facet_fails(self):
        """Aggregate by invalid facet should fail with helpful error."""
        stderr = run_command(['aggregate', 'publications', 'AI',
                            '-F', 'invalid_facet'], expect_failure=True)
        assert 'Invalid facet' in stderr

    def test_aggregate_deprecated_metric_fails(self):
        """Aggregate with deprecated metric should fail."""
        stderr = run_command(['aggregate', 'publications', 'AI',
                            '-F', 'year', '-a', 'times_cited_avg'], expect_failure=True)
        assert 'Invalid metric' in stderr

    def test_aggregate_funders_for_grants_fails(self):
        """Using 'funders' facet for grants should fail (use funder_org_*)."""
        stderr = run_command(['aggregate', 'grants', 'quantum',
                            '-F', 'funders'], expect_failure=True)
        assert 'Invalid facet' in stderr


class TestDescribe:
    """Tests for describe functionality."""

    def test_describe_publications(self):
        """Describe publications should return field metadata."""
        data = run_command(['describe', 'publications'])
        assert 'fields' in data

    def test_describe_grants(self):
        """Describe grants should return field metadata."""
        data = run_command(['describe', 'grants'])
        assert 'fields' in data


class TestRawQuery:
    """Tests for raw DSL queries."""

    def test_raw_query_basic(self):
        """Basic raw query should work."""
        data = run_command(['raw', 'search publications for "AI" return publications limit 5'])
        assert 'json' in data


class TestOutputFormats:
    """Tests for output file generation."""

    def test_dual_format_creates_both_files(self):
        """Dual format should create both parquet and jsonl."""
        data = run_command(['search-publications', 'test query xyz', '-l', '5'])
        if data.get('saved_to'):
            saved = data['saved_to']
            if isinstance(saved, dict):
                assert 'parquet' in saved
                assert 'jsonl' in saved


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
