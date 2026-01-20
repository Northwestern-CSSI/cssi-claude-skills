#!/usr/bin/env python3
"""
Unit tests for OpenAlex parameter validation.
These tests verify that validation catches invalid parameters before API calls.
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openalex_helper import (
    validate_group_by_field,
    validate_select_fields,
    _fetch_valid_group_by_fields,
    _fetch_valid_select_fields,
)


class TestGroupByValidation:
    """Tests for group_by field validation."""

    def test_valid_group_by_field_publication_year(self):
        """publication_year should be valid for works."""
        # Should not raise
        validate_group_by_field('works', 'publication_year')

    def test_valid_group_by_field_oa_status(self):
        """oa_status should be valid for works."""
        validate_group_by_field('works', 'oa_status')

    def test_valid_group_by_field_institutions(self):
        """authorships.institutions.id should be valid for works."""
        validate_group_by_field('works', 'authorships.institutions.id')

    def test_invalid_nested_grants_funder(self):
        """grants.funder should be invalid (too deeply nested)."""
        with pytest.raises(ValueError) as exc_info:
            validate_group_by_field('works', 'grants.funder')
        assert 'Invalid group_by field' in str(exc_info.value)

    def test_invalid_arbitrary_field(self):
        """Arbitrary nonexistent fields should be invalid."""
        with pytest.raises(ValueError) as exc_info:
            validate_group_by_field('works', 'nonexistent_field_xyz')
        assert 'Invalid group_by field' in str(exc_info.value)

    def test_error_message_contains_documentation_link(self):
        """Error messages should contain a link to documentation."""
        with pytest.raises(ValueError) as exc_info:
            validate_group_by_field('works', 'invalid_field')
        assert 'docs.openalex.org' in str(exc_info.value)


class TestSelectValidation:
    """Tests for select field validation."""

    def test_valid_select_fields(self):
        """Valid simple fields should pass validation."""
        validate_select_fields('works', 'id,title,publication_year,cited_by_count')

    def test_valid_single_field(self):
        """Single valid field should pass."""
        validate_select_fields('works', 'id')

    def test_invalid_grants_select(self):
        """grants should be invalid as a select field."""
        with pytest.raises(ValueError) as exc_info:
            validate_select_fields('works', 'id,title,grants')
        error_msg = str(exc_info.value)
        assert 'Invalid select field' in error_msg or 'grants' in error_msg

    def test_none_select_passes(self):
        """None select should pass (no validation needed)."""
        validate_select_fields('works', None)

    def test_empty_string_select_passes(self):
        """Empty string select should pass."""
        validate_select_fields('works', '')

    def test_error_message_helpful(self):
        """Error message should list valid fields."""
        with pytest.raises(ValueError) as exc_info:
            validate_select_fields('works', 'completely_fake_field')
        error_msg = str(exc_info.value)
        assert 'Valid fields' in error_msg or 'id' in error_msg


class TestFieldFetching:
    """Tests for dynamic field fetching from API."""

    def test_fetch_group_by_fields_returns_set(self):
        """_fetch_valid_group_by_fields should return a set."""
        fields = _fetch_valid_group_by_fields('works')
        assert isinstance(fields, set)

    def test_fetch_group_by_fields_contains_publication_year(self):
        """Fetched fields should contain publication_year."""
        fields = _fetch_valid_group_by_fields('works')
        assert 'publication_year' in fields

    def test_fetch_select_fields_returns_set(self):
        """_fetch_valid_select_fields should return a set."""
        fields = _fetch_valid_select_fields('works')
        assert isinstance(fields, set)

    def test_fetch_select_fields_contains_id(self):
        """Fetched select fields should contain id."""
        fields = _fetch_valid_select_fields('works')
        assert 'id' in fields

    def test_caching_works(self):
        """Fields should be cached after first fetch."""
        # First fetch
        fields1 = _fetch_valid_group_by_fields('works')
        # Second fetch should return same object (cached)
        fields2 = _fetch_valid_group_by_fields('works')
        assert fields1 is fields2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
