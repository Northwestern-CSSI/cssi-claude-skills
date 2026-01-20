#!/usr/bin/env python3
"""
Unit tests for Dimensions parameter validation.
These tests verify that validation catches invalid parameters before API calls.
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dimensions_helper import (
    validate_facet,
    validate_aggregation_metrics,
    _fetch_source_metadata,
    _valid_fields_cache,
)


class TestFacetValidation:
    """Tests for facet field validation."""

    def test_valid_facet_year(self):
        """year should be valid for publications."""
        # Should not raise
        validate_facet('publications', 'year')

    def test_valid_facet_research_orgs(self):
        """research_orgs should be valid for publications."""
        validate_facet('publications', 'research_orgs')

    def test_valid_facet_funder_org_acronym(self):
        """funder_org_acronym should be valid for grants."""
        validate_facet('grants', 'funder_org_acronym')

    def test_invalid_facet_arbitrary(self):
        """Arbitrary nonexistent facets should be invalid."""
        with pytest.raises(ValueError) as exc_info:
            validate_facet('publications', 'nonexistent_facet_xyz')
        assert 'Invalid facet' in str(exc_info.value)

    def test_invalid_facet_funders_for_grants(self):
        """funders should be invalid for grants (use funder_org_*)."""
        with pytest.raises(ValueError) as exc_info:
            validate_facet('grants', 'funders')
        error_msg = str(exc_info.value)
        assert 'Invalid facet' in error_msg

    def test_error_message_contains_suggestions(self):
        """Error messages should contain valid facets."""
        with pytest.raises(ValueError) as exc_info:
            validate_facet('publications', 'invalid_field')
        error_msg = str(exc_info.value)
        assert 'Valid facets' in error_msg or 'describe' in error_msg


class TestMetricsValidation:
    """Tests for aggregation metrics validation."""

    def test_valid_metric_count(self):
        """count should always be valid."""
        validate_aggregation_metrics('publications', 'count')

    def test_valid_metric_rcr_avg(self):
        """rcr_avg should be valid for publications."""
        validate_aggregation_metrics('publications', 'rcr_avg')

    def test_valid_metric_funding(self):
        """funding should be valid for grants."""
        validate_aggregation_metrics('grants', 'funding')

    def test_invalid_metric_times_cited_avg(self):
        """times_cited_avg should be invalid (deprecated)."""
        with pytest.raises(ValueError) as exc_info:
            validate_aggregation_metrics('publications', 'times_cited_avg')
        error_msg = str(exc_info.value)
        assert 'Invalid metric' in error_msg

    def test_invalid_metric_arbitrary(self):
        """Arbitrary metrics should be invalid."""
        with pytest.raises(ValueError) as exc_info:
            validate_aggregation_metrics('publications', 'fake_metric_xyz')
        assert 'Invalid metric' in str(exc_info.value)

    def test_none_metrics_passes(self):
        """None metrics should pass (no validation needed)."""
        validate_aggregation_metrics('publications', None)

    def test_empty_metrics_passes(self):
        """Empty string metrics should pass."""
        validate_aggregation_metrics('publications', '')

    def test_function_syntax_sum_funding(self):
        """Function syntax like sum(funding) should be allowed."""
        # sum() is a valid aggregate function
        validate_aggregation_metrics('grants', 'sum(funding)')


class TestMetadataFetching:
    """Tests for dynamic metadata fetching from API."""

    def test_fetch_metadata_populates_cache(self):
        """_fetch_source_metadata should populate the cache."""
        _fetch_source_metadata('publications')
        assert 'publications' in _valid_fields_cache['facets']
        assert 'publications' in _valid_fields_cache['metrics']

    def test_fetched_facets_contains_year(self):
        """Fetched facets should contain year for publications."""
        _fetch_source_metadata('publications')
        facets = _valid_fields_cache['facets'].get('publications', set())
        assert 'year' in facets

    def test_fetched_metrics_contains_count(self):
        """Fetched metrics should contain count."""
        _fetch_source_metadata('publications')
        metrics = _valid_fields_cache['metrics'].get('publications', set())
        assert 'count' in metrics


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
