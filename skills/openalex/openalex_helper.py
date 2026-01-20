#!/usr/bin/env python3
"""
OpenAlex API Helper Module
Provides high-level functions for interacting with the OpenAlex research database.
Supports pagination for large result sets and automatic data export.

Output formats:
  - Default: dual save (parquet + jsonl)
  - parquet: Binary columnar, typed, compressed (primary storage)
  - jsonl: JSON Lines, human-readable, preserves nested structures (for peeking)
  - tsv: Tab-separated, peekable with head
  - csv: Universal compatibility (legacy)

Output location: /tmp/openalex-results/ (default), or specify with --output-dir
"""

import sys
import json
import argparse
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import requests
import pandas as pd

# API Configuration
BASE_URL = "https://api.openalex.org"
EMAIL = os.environ.get("OPENALEX_EMAIL", "user@example.com")  # For polite pool

# Cache for valid fields (fetched dynamically from API)
_valid_fields_cache = {
    'group_by': {},  # entity_type -> set of valid fields
    'select': {},    # entity_type -> set of valid fields
}


def _fetch_valid_group_by_fields(entity_type):
    """Fetch valid group_by fields from the API by parsing error messages."""
    if entity_type in _valid_fields_cache['group_by']:
        return _valid_fields_cache['group_by'][entity_type]

    try:
        # Make a request with an invalid field to get the list of valid fields
        params = {'group_by': '__invalid_field_to_get_valid_list__', 'per_page': 1}
        params['mailto'] = EMAIL
        url = f"{BASE_URL}/{entity_type}"
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 400:
            error_data = response.json()
            message = error_data.get('message', '')
            # Parse valid fields from error message
            if 'Valid fields are' in message:
                fields_part = message.split('Valid fields are')[1]
                # Extract field names (they list underscore/hyphenated versions)
                fields_str = fields_part.strip().rstrip('.')
                valid_fields = set()
                for field in fields_str.split(', '):
                    field = field.strip()
                    if field:
                        valid_fields.add(field)
                _valid_fields_cache['group_by'][entity_type] = valid_fields
                return valid_fields
    except Exception as e:
        print(f"Warning: Could not fetch valid group_by fields: {e}", file=sys.stderr)

    return set()  # Return empty set if we can't fetch


def _fetch_valid_select_fields(entity_type):
    """Fetch valid select fields from the API by parsing error messages."""
    if entity_type in _valid_fields_cache['select']:
        return _valid_fields_cache['select'][entity_type]

    try:
        # Make a request with an invalid select field to get the list of valid fields
        params = {'select': '__invalid_field__', 'per_page': 1}
        params['mailto'] = EMAIL
        url = f"{BASE_URL}/{entity_type}"
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 400:
            error_data = response.json()
            message = error_data.get('message', '')
            # Parse valid fields from error message
            if 'Valid fields for select are' in message:
                fields_part = message.split('Valid fields for select are:')[1]
                fields_str = fields_part.strip().rstrip('.')
                valid_fields = set()
                for field in fields_str.split(', '):
                    field = field.strip()
                    if field:
                        valid_fields.add(field)
                _valid_fields_cache['select'][entity_type] = valid_fields
                return valid_fields
    except Exception as e:
        print(f"Warning: Could not fetch valid select fields: {e}", file=sys.stderr)

    return set()  # Return empty set if we can't fetch


def validate_group_by_field(entity_type, group_field):
    """
    Validate that the group_by field is supported by the API.
    Fetches valid fields dynamically from the API.
    """
    valid_fields = _fetch_valid_group_by_fields(entity_type)

    if not valid_fields:
        # If we couldn't fetch valid fields, let the API handle validation
        return

    if group_field not in valid_fields:
        # Find similar fields for suggestions
        field_base = group_field.split('.')[0]
        suggestions = [f for f in valid_fields if field_base in f][:5]

        error_msg = f"Invalid group_by field '{group_field}' for {entity_type}.\n"
        if suggestions:
            error_msg += f"Similar valid fields: {', '.join(suggestions)}\n"
        error_msg += f"See https://docs.openalex.org/how-to-use-the-api/get-groups-of-entities for all valid fields."
        raise ValueError(error_msg)


def validate_select_fields(entity_type, select_str):
    """
    Validate that select fields are supported by the API.
    Fetches valid fields dynamically from the API.
    """
    if not select_str:
        return

    valid_fields = _fetch_valid_select_fields(entity_type)

    if not valid_fields:
        # If we couldn't fetch valid fields, let the API handle validation
        return

    fields = [f.strip() for f in select_str.split(',')]
    invalid_fields = []

    for field in fields:
        if field and field not in valid_fields:
            invalid_fields.append(field)

    if invalid_fields:
        error_msg = f"Invalid select field(s) for {entity_type}: {', '.join(invalid_fields)}\n"
        error_msg += f"Valid fields: {', '.join(sorted(valid_fields)[:20])}...\n"
        error_msg += "Tip: Complex nested objects like 'grants' cannot be selected. Fetch full records instead."
        raise ValueError(error_msg)

# Default output directory
OUTPUT_DIR = Path("/tmp/openalex-results")
OUTPUT_DIR.mkdir(exist_ok=True)

# Default format: dual (parquet + jsonl)
DEFAULT_FORMAT = 'dual'

# Rate limiting
REQUESTS_PER_SECOND = 10
last_request_time = 0


def rate_limit():
    """Ensure we don't exceed rate limits."""
    global last_request_time
    elapsed = time.time() - last_request_time
    if elapsed < 1.0 / REQUESTS_PER_SECOND:
        time.sleep(1.0 / REQUESTS_PER_SECOND - elapsed)
    last_request_time = time.time()


def api_request(endpoint, params=None):
    """Make a request to the OpenAlex API."""
    rate_limit()

    if params is None:
        params = {}

    # Add email for polite pool
    params['mailto'] = EMAIL

    url = f"{BASE_URL}/{endpoint}"

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}", file=sys.stderr)
        raise


def generate_filename(prefix, query_terms=None):
    """Generate a timestamped filename for output."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if query_terms:
        # Clean query terms for filename
        clean_terms = "".join(c if c.isalnum() else "_" for c in query_terms[:30])
        return f"{prefix}_{clean_terms}_{timestamp}"
    return f"{prefix}_{timestamp}"


def clean_for_parquet(df):
    """Clean DataFrame for parquet export by ensuring consistent types per column."""
    df_clean = df.copy()

    for col in df_clean.columns:
        if df_clean[col].dtype != 'object':
            continue

        non_null = df_clean[col].dropna()
        if non_null.empty:
            continue

        # Count type occurrences
        type_counts = {'list': 0, 'dict': 0, 'primitive': 0}
        for val in non_null:
            if isinstance(val, list) and val:
                type_counts['list'] += 1
            elif isinstance(val, dict) and val:
                type_counts['dict'] += 1
            elif not isinstance(val, (list, dict)) and val != '':
                type_counts['primitive'] += 1

        dominant_type = max(type_counts, key=type_counts.get)
        if type_counts[dominant_type] == 0:
            dominant_type = 'primitive'

        def make_cleaner(dominant):
            def clean_value(val):
                if val is None:
                    return None
                if dominant == 'list':
                    return val if isinstance(val, list) and val else None
                elif dominant == 'dict':
                    return val if isinstance(val, dict) and val else None
                else:
                    if isinstance(val, (list, dict)):
                        return None
                    if isinstance(val, str) and val == '':
                        return None
                    return val
            return clean_value

        cleaner = make_cleaner(dominant_type)
        df_clean[col] = df_clean[col].apply(cleaner)

    return df_clean


def serialize_for_text_format(df):
    """Serialize nested structures to JSON strings for text formats."""
    df_serialized = df.copy()
    for col in df_serialized.columns:
        if df_serialized[col].dtype == 'object':
            df_serialized[col] = df_serialized[col].apply(
                lambda x: json.dumps(x, default=str) if isinstance(x, (list, dict)) else x
            )
    return df_serialized


def save_results(df, prefix, query_terms=None, format=None, raw_data=None):
    """Save DataFrame to file and return the path(s)."""
    if format is None:
        format = DEFAULT_FORMAT

    filename = generate_filename(prefix, query_terms)
    df_clean = clean_for_parquet(df)

    if format == 'dual':
        parquet_path = OUTPUT_DIR / f"{filename}.parquet"
        jsonl_path = OUTPUT_DIR / f"{filename}.jsonl"

        try:
            df_clean.to_parquet(parquet_path, index=False)
        except Exception as e:
            print(f"Native parquet failed ({e}), falling back to serialized format", file=sys.stderr)
            df_serialized = serialize_for_text_format(df)
            df_serialized.to_parquet(parquet_path, index=False)

        if raw_data:
            with open(jsonl_path, 'w') as f:
                for record in raw_data:
                    f.write(json.dumps(record, default=str) + '\n')
        else:
            df.to_json(jsonl_path, orient='records', lines=True)

        return {'parquet': str(parquet_path), 'jsonl': str(jsonl_path)}

    elif format == 'parquet':
        filepath = OUTPUT_DIR / f"{filename}.parquet"
        try:
            df_clean.to_parquet(filepath, index=False)
        except Exception:
            df_serialized = serialize_for_text_format(df)
            df_serialized.to_parquet(filepath, index=False)
    elif format == 'jsonl':
        filepath = OUTPUT_DIR / f"{filename}.jsonl"
        if raw_data:
            with open(filepath, 'w') as f:
                for record in raw_data:
                    f.write(json.dumps(record, default=str) + '\n')
        else:
            df.to_json(filepath, orient='records', lines=True)
    elif format == 'tsv':
        filepath = OUTPUT_DIR / f"{filename}.tsv"
        df_serialized = serialize_for_text_format(df)
        df_serialized.to_csv(filepath, index=False, sep='\t')
    elif format == 'csv':
        filepath = OUTPUT_DIR / f"{filename}.csv"
        df_serialized = serialize_for_text_format(df)
        df_serialized.to_csv(filepath, index=False)
    else:
        filepath = OUTPUT_DIR / f"{filename}.parquet"
        df_clean.to_parquet(filepath, index=False)

    return str(filepath)


def fetch_all_with_cursor(endpoint, params, max_results=None):
    """
    Fetch all results using cursor pagination.

    Args:
        endpoint: API endpoint (e.g., 'works')
        params: Query parameters
        max_results: Maximum total results to retrieve (None for all)

    Returns:
        dict with 'total', 'retrieved', 'data' (list)
    """
    all_results = []
    params = params.copy()
    params['cursor'] = '*'
    params['per_page'] = 200

    total_count = None
    print(f"Fetching from {endpoint}...", file=sys.stderr)

    while True:
        try:
            response = api_request(endpoint, params)
            results = response.get('results', [])
            meta = response.get('meta', {})

            if total_count is None:
                total_count = meta.get('count', 0)
                if max_results:
                    total_count = min(total_count, max_results)
                print(f"Total available: {meta.get('count', 0)}, retrieving: {total_count}", file=sys.stderr)

            if not results:
                break

            all_results.extend(results)
            print(f"Retrieved {len(all_results)} / {total_count}...", file=sys.stderr)

            if len(all_results) >= total_count:
                break

            next_cursor = meta.get('next_cursor')
            if not next_cursor:
                break

            params['cursor'] = next_cursor

        except Exception as e:
            print(f"Error during pagination: {e}", file=sys.stderr)
            break

    return {
        'total': total_count,
        'retrieved': len(all_results),
        'data': all_results
    }


def search_works(query=None, filters=None, search_field=None, limit=25, page=1,
                 sort=None, select=None, max_results=None, save=True):
    """Search works with optional filters."""
    # Validate select fields before making API call
    if select:
        validate_select_fields('works', select)

    params = {}

    if query:
        if search_field:
            # Field-specific search
            if filters:
                params['filter'] = f"{search_field}.search:{query},{filters}"
            else:
                params['filter'] = f"{search_field}.search:{query}"
        else:
            params['search'] = query
            if filters:
                params['filter'] = filters
    elif filters:
        params['filter'] = filters

    if sort:
        params['sort'] = sort
    if select:
        params['select'] = select

    # Use cursor pagination for large results
    if max_results and max_results > 200:
        result = fetch_all_with_cursor('works', params, max_results)
        df = pd.DataFrame(result['data'])

        saved_path = None
        if save and not df.empty:
            saved_path = save_results(df, 'works', query, raw_data=result['data'])
            if isinstance(saved_path, dict):
                print(f"Saved to: {saved_path['parquet']} (parquet)", file=sys.stderr)
                print(f"          {saved_path['jsonl']} (jsonl)", file=sys.stderr)

        return {
            'total': result['total'],
            'returned': result['retrieved'],
            'saved_to': saved_path,
            'works': result['data'][:20],  # Return first 20 for display
            'query_params': params
        }

    # Standard paging
    params['page'] = page
    params['per_page'] = min(limit, 200)

    response = api_request('works', params)
    works = response.get('results', [])
    meta = response.get('meta', {})

    saved_path = None
    if save and works:
        df = pd.DataFrame(works)
        saved_path = save_results(df, 'works', query, raw_data=works)

    return {
        'total': meta.get('count', 0),
        'returned': len(works),
        'saved_to': saved_path,
        'works': works,
        'query_params': params
    }


def search_authors(query=None, filters=None, limit=25, page=1, sort=None,
                   select=None, max_results=None, save=True):
    """Search authors with optional filters."""
    # Validate select fields before making API call
    if select:
        validate_select_fields('authors', select)

    params = {}

    if query:
        if filters:
            params['filter'] = f"display_name.search:{query},{filters}"
        else:
            params['filter'] = f"display_name.search:{query}"
    elif filters:
        params['filter'] = filters

    if sort:
        params['sort'] = sort
    if select:
        params['select'] = select

    if max_results and max_results > 200:
        result = fetch_all_with_cursor('authors', params, max_results)
        df = pd.DataFrame(result['data'])

        saved_path = None
        if save and not df.empty:
            saved_path = save_results(df, 'authors', query, raw_data=result['data'])

        return {
            'total': result['total'],
            'returned': result['retrieved'],
            'saved_to': saved_path,
            'authors': result['data'][:20],
            'query_params': params
        }

    params['page'] = page
    params['per_page'] = min(limit, 200)

    response = api_request('authors', params)
    authors = response.get('results', [])
    meta = response.get('meta', {})

    saved_path = None
    if save and authors:
        df = pd.DataFrame(authors)
        saved_path = save_results(df, 'authors', query, raw_data=authors)

    return {
        'total': meta.get('count', 0),
        'returned': len(authors),
        'saved_to': saved_path,
        'authors': authors,
        'query_params': params
    }


def search_institutions(query=None, filters=None, limit=25, page=1, sort=None,
                        select=None, max_results=None, save=True):
    """Search institutions with optional filters."""
    # Validate select fields before making API call
    if select:
        validate_select_fields('institutions', select)

    params = {}

    if query:
        if filters:
            params['filter'] = f"display_name.search:{query},{filters}"
        else:
            params['filter'] = f"display_name.search:{query}"
    elif filters:
        params['filter'] = filters

    if sort:
        params['sort'] = sort
    if select:
        params['select'] = select

    if max_results and max_results > 200:
        result = fetch_all_with_cursor('institutions', params, max_results)
        df = pd.DataFrame(result['data'])

        saved_path = None
        if save and not df.empty:
            saved_path = save_results(df, 'institutions', query, raw_data=result['data'])

        return {
            'total': result['total'],
            'returned': result['retrieved'],
            'saved_to': saved_path,
            'institutions': result['data'][:20],
            'query_params': params
        }

    params['page'] = page
    params['per_page'] = min(limit, 200)

    response = api_request('institutions', params)
    institutions = response.get('results', [])
    meta = response.get('meta', {})

    saved_path = None
    if save and institutions:
        df = pd.DataFrame(institutions)
        saved_path = save_results(df, 'institutions', query, raw_data=institutions)

    return {
        'total': meta.get('count', 0),
        'returned': len(institutions),
        'saved_to': saved_path,
        'institutions': institutions,
        'query_params': params
    }


def search_sources(query=None, filters=None, limit=25, page=1, sort=None,
                   select=None, max_results=None, save=True):
    """Search sources (journals, repositories) with optional filters."""
    # Validate select fields before making API call
    if select:
        validate_select_fields('sources', select)

    params = {}

    if query:
        if filters:
            params['filter'] = f"display_name.search:{query},{filters}"
        else:
            params['filter'] = f"display_name.search:{query}"
    elif filters:
        params['filter'] = filters

    if sort:
        params['sort'] = sort
    if select:
        params['select'] = select

    if max_results and max_results > 200:
        result = fetch_all_with_cursor('sources', params, max_results)
        df = pd.DataFrame(result['data'])

        saved_path = None
        if save and not df.empty:
            saved_path = save_results(df, 'sources', query, raw_data=result['data'])

        return {
            'total': result['total'],
            'returned': result['retrieved'],
            'saved_to': saved_path,
            'sources': result['data'][:20],
            'query_params': params
        }

    params['page'] = page
    params['per_page'] = min(limit, 200)

    response = api_request('sources', params)
    sources = response.get('results', [])
    meta = response.get('meta', {})

    saved_path = None
    if save and sources:
        df = pd.DataFrame(sources)
        saved_path = save_results(df, 'sources', query, raw_data=sources)

    return {
        'total': meta.get('count', 0),
        'returned': len(sources),
        'saved_to': saved_path,
        'sources': sources,
        'query_params': params
    }


def search_funders(query=None, filters=None, limit=25, page=1, sort=None,
                   select=None, max_results=None, save=True):
    """Search funders with optional filters."""
    # Validate select fields before making API call
    if select:
        validate_select_fields('funders', select)

    params = {}

    if query:
        if filters:
            params['filter'] = f"display_name.search:{query},{filters}"
        else:
            params['filter'] = f"display_name.search:{query}"
    elif filters:
        params['filter'] = filters

    if sort:
        params['sort'] = sort
    if select:
        params['select'] = select

    if max_results and max_results > 200:
        result = fetch_all_with_cursor('funders', params, max_results)
        df = pd.DataFrame(result['data'])

        saved_path = None
        if save and not df.empty:
            saved_path = save_results(df, 'funders', query, raw_data=result['data'])

        return {
            'total': result['total'],
            'returned': result['retrieved'],
            'saved_to': saved_path,
            'funders': result['data'][:20],
            'query_params': params
        }

    params['page'] = page
    params['per_page'] = min(limit, 200)

    response = api_request('funders', params)
    funders = response.get('results', [])
    meta = response.get('meta', {})

    saved_path = None
    if save and funders:
        df = pd.DataFrame(funders)
        saved_path = save_results(df, 'funders', query, raw_data=funders)

    return {
        'total': meta.get('count', 0),
        'returned': len(funders),
        'saved_to': saved_path,
        'funders': funders,
        'query_params': params
    }


def search_topics(query=None, filters=None, limit=25, page=1, sort=None,
                  select=None, save=True):
    """Search topics with optional filters."""
    # Validate select fields before making API call
    if select:
        validate_select_fields('topics', select)

    params = {}

    if query:
        if filters:
            params['filter'] = f"display_name.search:{query},{filters}"
        else:
            params['filter'] = f"display_name.search:{query}"
    elif filters:
        params['filter'] = filters

    if sort:
        params['sort'] = sort
    if select:
        params['select'] = select

    params['page'] = page
    params['per_page'] = min(limit, 200)

    response = api_request('topics', params)
    topics = response.get('results', [])
    meta = response.get('meta', {})

    saved_path = None
    if save and topics:
        df = pd.DataFrame(topics)
        saved_path = save_results(df, 'topics', query, raw_data=topics)

    return {
        'total': meta.get('count', 0),
        'returned': len(topics),
        'saved_to': saved_path,
        'topics': topics,
        'query_params': params
    }


def get_entity(entity_type, entity_id):
    """Get a single entity by ID."""
    endpoint = f"{entity_type}/{entity_id}"
    return api_request(endpoint, {})


def group_by(entity_type, group_field, filters=None, save=True):
    """Get aggregated counts by a field."""
    # Validate group_by field before making API call
    validate_group_by_field(entity_type, group_field)

    params = {'group_by': group_field}

    if filters:
        params['filter'] = filters

    response = api_request(entity_type, params)
    groups = response.get('group_by', [])
    meta = response.get('meta', {})

    saved_path = None
    if save and groups:
        df = pd.DataFrame(groups)
        saved_path = save_results(df, f'{entity_type}_{group_field}', raw_data=groups)

    return {
        'total_count': meta.get('count', 0),
        'groups_count': meta.get('groups_count', len(groups)),
        'groups': groups,
        'saved_to': saved_path,
        'query_params': params
    }


def autocomplete(entity_type, query, filters=None):
    """Autocomplete search for entities."""
    params = {'q': query}
    if filters:
        params['filter'] = filters

    response = api_request(f'autocomplete/{entity_type}', params)
    return {
        'results': response.get('results', []),
        'query': query
    }


def main():
    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('--no-save', action='store_true', help='Do not save results')
    common_parser.add_argument('--format', choices=['dual', 'parquet', 'jsonl', 'tsv', 'csv'],
                               default='dual', help='Output format')
    common_parser.add_argument('--output-dir', '-o', type=str, help='Output directory')
    common_parser.add_argument('--email', type=str, help='Email for polite pool')

    parser = argparse.ArgumentParser(description='OpenAlex API Helper',
                                     parents=[common_parser])
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Search works
    works_parser = subparsers.add_parser('search-works', help='Search works',
                                         parents=[common_parser])
    works_parser.add_argument('query', nargs='?', help='Search query')
    works_parser.add_argument('--filter', '-f', dest='filters', help='Filter expression')
    works_parser.add_argument('--search-field', choices=['title', 'abstract', 'fulltext', 'title_and_abstract'],
                              help='Specific field to search')
    works_parser.add_argument('--sort', '-s', help='Sort field')
    works_parser.add_argument('--select', help='Fields to select')
    works_parser.add_argument('--limit', '-l', type=int, default=25, help='Results per page')
    works_parser.add_argument('--page', '-p', type=int, default=1, help='Page number')
    works_parser.add_argument('--max-results', '-m', type=int, help='Max results (enables cursor pagination)')

    # Search authors
    authors_parser = subparsers.add_parser('search-authors', help='Search authors',
                                           parents=[common_parser])
    authors_parser.add_argument('query', nargs='?', help='Search query (author name)')
    authors_parser.add_argument('--filter', '-f', dest='filters', help='Filter expression')
    authors_parser.add_argument('--sort', '-s', help='Sort field')
    authors_parser.add_argument('--select', help='Fields to select')
    authors_parser.add_argument('--limit', '-l', type=int, default=25)
    authors_parser.add_argument('--page', '-p', type=int, default=1)
    authors_parser.add_argument('--max-results', '-m', type=int)

    # Search institutions
    inst_parser = subparsers.add_parser('search-institutions', help='Search institutions',
                                        parents=[common_parser])
    inst_parser.add_argument('query', nargs='?', help='Search query (institution name)')
    inst_parser.add_argument('--filter', '-f', dest='filters', help='Filter expression')
    inst_parser.add_argument('--sort', '-s', help='Sort field')
    inst_parser.add_argument('--select', help='Fields to select')
    inst_parser.add_argument('--limit', '-l', type=int, default=25)
    inst_parser.add_argument('--page', '-p', type=int, default=1)
    inst_parser.add_argument('--max-results', '-m', type=int)

    # Search sources
    sources_parser = subparsers.add_parser('search-sources', help='Search sources (journals)',
                                           parents=[common_parser])
    sources_parser.add_argument('query', nargs='?', help='Search query (source name)')
    sources_parser.add_argument('--filter', '-f', dest='filters', help='Filter expression')
    sources_parser.add_argument('--sort', '-s', help='Sort field')
    sources_parser.add_argument('--select', help='Fields to select')
    sources_parser.add_argument('--limit', '-l', type=int, default=25)
    sources_parser.add_argument('--page', '-p', type=int, default=1)
    sources_parser.add_argument('--max-results', '-m', type=int)

    # Search funders
    funders_parser = subparsers.add_parser('search-funders', help='Search funders',
                                           parents=[common_parser])
    funders_parser.add_argument('query', nargs='?', help='Search query (funder name)')
    funders_parser.add_argument('--filter', '-f', dest='filters', help='Filter expression')
    funders_parser.add_argument('--sort', '-s', help='Sort field')
    funders_parser.add_argument('--select', help='Fields to select')
    funders_parser.add_argument('--limit', '-l', type=int, default=25)
    funders_parser.add_argument('--page', '-p', type=int, default=1)
    funders_parser.add_argument('--max-results', '-m', type=int)

    # Search topics
    topics_parser = subparsers.add_parser('search-topics', help='Search topics',
                                          parents=[common_parser])
    topics_parser.add_argument('query', nargs='?', help='Search query')
    topics_parser.add_argument('--filter', '-f', dest='filters', help='Filter expression')
    topics_parser.add_argument('--sort', '-s', help='Sort field')
    topics_parser.add_argument('--limit', '-l', type=int, default=25)

    # Get single entity
    get_parser = subparsers.add_parser('get', help='Get a single entity by ID',
                                       parents=[common_parser])
    get_parser.add_argument('entity_type', choices=['works', 'authors', 'institutions', 'sources', 'funders', 'topics'])
    get_parser.add_argument('entity_id', help='Entity ID (OpenAlex ID, DOI, ORCID, ROR, etc.)')

    # Group by
    group_parser = subparsers.add_parser('group', help='Group entities by field',
                                         parents=[common_parser])
    group_parser.add_argument('entity_type', choices=['works', 'authors', 'institutions', 'sources', 'funders'])
    group_parser.add_argument('group_field', help='Field to group by')
    group_parser.add_argument('--filter', '-f', dest='filters', help='Filter expression')

    # Autocomplete
    auto_parser = subparsers.add_parser('autocomplete', help='Autocomplete search',
                                        parents=[common_parser])
    auto_parser.add_argument('entity_type', choices=['works', 'authors', 'institutions', 'sources', 'funders'])
    auto_parser.add_argument('query', help='Autocomplete query')

    args = parser.parse_args()

    # Set global config
    global OUTPUT_DIR, EMAIL
    if hasattr(args, 'output_dir') and args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
        OUTPUT_DIR.mkdir(exist_ok=True)
    if hasattr(args, 'email') and args.email:
        EMAIL = args.email

    save = not getattr(args, 'no_save', False)

    if args.command == 'search-works':
        result = search_works(
            args.query, args.filters, args.search_field, args.limit, args.page,
            args.sort, args.select, args.max_results, save
        )
    elif args.command == 'search-authors':
        result = search_authors(
            args.query, args.filters, args.limit, args.page, args.sort,
            args.select, args.max_results, save
        )
    elif args.command == 'search-institutions':
        result = search_institutions(
            args.query, args.filters, args.limit, args.page, args.sort,
            args.select, args.max_results, save
        )
    elif args.command == 'search-sources':
        result = search_sources(
            args.query, args.filters, args.limit, args.page, args.sort,
            args.select, args.max_results, save
        )
    elif args.command == 'search-funders':
        result = search_funders(
            args.query, args.filters, args.limit, args.page, args.sort,
            args.select, args.max_results, save
        )
    elif args.command == 'search-topics':
        result = search_topics(
            args.query, args.filters, args.limit, args.page, args.sort,
            getattr(args, 'select', None), save
        )
    elif args.command == 'get':
        result = get_entity(args.entity_type, args.entity_id)
    elif args.command == 'group':
        result = group_by(args.entity_type, args.group_field, args.filters, save)
    elif args.command == 'autocomplete':
        result = autocomplete(args.entity_type, args.query)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
