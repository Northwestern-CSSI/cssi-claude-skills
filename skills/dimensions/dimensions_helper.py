#!/usr/bin/env python3
"""
Dimensions DSL API Helper Module
Provides high-level functions for interacting with the Dimensions research database.
Supports iterative queries for large result sets and automatic data export.

Output modes:
  - verbose (default): Step-by-step execution details with workflow summary
  - silent: Minimal output, only workflow summary and final JSON result

Output formats:
  - Default: dual save (parquet + jsonl)
  - parquet: Binary columnar, typed, compressed (primary storage)
  - jsonl: JSON Lines, human-readable, nested structures preserved (for peeking)
  - tsv: Tab-separated, peekable with head
  - csv: Universal compatibility (legacy)

Output location: /tmp/dimensions-results/ (default), or specify with --output-dir
"""

import sys
import json
import argparse
import os
from datetime import datetime
from pathlib import Path
import time

import dimcli
import pandas as pd

# ============================================================================
# OUTPUT MODE MANAGEMENT
# ============================================================================

class OutputMode:
    """Manages output verbosity and workflow tracking."""

    VERBOSE = 'verbose'
    SILENT = 'silent'

    def __init__(self, mode=VERBOSE):
        self.mode = mode
        self.start_time = None
        self.steps = []
        self.api_calls = 0
        self.records_retrieved = 0
        self.warnings = []
        self.dsl_query = None
        self.command = None
        self.args_summary = {}
        self.output_files = []

    def start(self, command, args_summary):
        """Start tracking a workflow."""
        self.start_time = time.time()
        self.command = command
        self.args_summary = args_summary
        self.steps = []
        self.api_calls = 0
        self.records_retrieved = 0
        self.warnings = []
        self.output_files = []

        if self.mode == self.VERBOSE:
            self._print_header(command, args_summary)

    def _print_header(self, command, args_summary):
        """Print workflow header."""
        print("\n" + "═" * 60, file=sys.stderr)
        print(f"  DIMENSIONS QUERY: {command}", file=sys.stderr)
        print("═" * 60, file=sys.stderr)
        for key, value in args_summary.items():
            if value is not None:
                print(f"  {key}: {value}", file=sys.stderr)
        print("─" * 60, file=sys.stderr)

    def step(self, step_num, total_steps, description, status="running"):
        """Log a workflow step."""
        self.steps.append({
            'step': step_num,
            'total': total_steps,
            'description': description,
            'status': status,
            'time': datetime.now().isoformat()
        })

        if self.mode == self.VERBOSE:
            if status == "running":
                print(f"  [{step_num}/{total_steps}] {description}...", file=sys.stderr)
            elif status == "done":
                print(f"  [{step_num}/{total_steps}] {description} ✓", file=sys.stderr)
            elif status == "error":
                print(f"  [{step_num}/{total_steps}] {description} ✗", file=sys.stderr)

    def step_done(self, step_num, total_steps, description):
        """Mark a step as done."""
        self.step(step_num, total_steps, description, status="done")

    def log(self, message):
        """Log a message in verbose mode."""
        if self.mode == self.VERBOSE:
            print(f"       → {message}", file=sys.stderr)

    def api_call(self, page, total_pages, records, duration):
        """Log an API call."""
        self.api_calls += 1
        self.records_retrieved += records

        if self.mode == self.VERBOSE:
            print(f"       API call {page}/{total_pages}: {records} records ({duration:.2f}s)", file=sys.stderr)

    def warn(self, message):
        """Log a warning."""
        self.warnings.append(message)
        if self.mode != self.SILENT:
            print(f"  ⚠ WARNING: {message}", file=sys.stderr)

    def set_query(self, dsl_query):
        """Set the DSL query being executed."""
        self.dsl_query = dsl_query
        if self.mode == self.VERBOSE:
            print(f"\n  DSL Query:", file=sys.stderr)
            print(f"    {dsl_query}", file=sys.stderr)
            print("", file=sys.stderr)

    def add_output_file(self, filepath, format_type, rows=None, size_bytes=None):
        """Record an output file."""
        self.output_files.append({
            'path': str(filepath),
            'format': format_type,
            'rows': rows,
            'size_bytes': size_bytes
        })

    def confirm(self, estimated_calls=1, estimated_records=None):
        """Always returns True - interactive mode disabled for better workflow."""
        return True

    def print_summary(self, result=None):
        """Print workflow summary (shown in all modes)."""
        duration = time.time() - self.start_time if self.start_time else 0

        print("\n" + "═" * 60, file=sys.stderr)
        print("  WORKFLOW SUMMARY", file=sys.stderr)
        print("═" * 60, file=sys.stderr)

        # Command info
        print(f"  Command:      {self.command}", file=sys.stderr)
        if self.dsl_query:
            # Wrap long queries
            if len(self.dsl_query) > 50:
                print(f"  DSL Query:    {self.dsl_query[:50]}", file=sys.stderr)
                print(f"                {self.dsl_query[50:]}", file=sys.stderr)
            else:
                print(f"  DSL Query:    {self.dsl_query}", file=sys.stderr)

        print("─" * 60, file=sys.stderr)

        # Execution stats
        print(f"  API Calls:    {self.api_calls}", file=sys.stderr)
        print(f"  Records:      {self.records_retrieved}", file=sys.stderr)
        print(f"  Duration:     {duration:.2f}s", file=sys.stderr)

        # Warnings
        if self.warnings:
            print("─" * 60, file=sys.stderr)
            print(f"  Warnings:     {len(self.warnings)}", file=sys.stderr)
            for w in self.warnings[:3]:  # Show first 3 warnings
                print(f"    • {w}", file=sys.stderr)

        # Output files
        if self.output_files:
            print("─" * 60, file=sys.stderr)
            print("  Output Files:", file=sys.stderr)
            for f in self.output_files:
                size_str = ""
                if f.get('size_bytes'):
                    size_mb = f['size_bytes'] / (1024 * 1024)
                    size_str = f" ({size_mb:.1f} MB)"
                rows_str = f" [{f['rows']} rows]" if f.get('rows') else ""
                print(f"    → {f['path']}{rows_str}{size_str}", file=sys.stderr)

        # Data loading hint
        if self.output_files:
            print("─" * 60, file=sys.stderr)
            print("  To load data:", file=sys.stderr)
            parquet_file = next((f['path'] for f in self.output_files if f['format'] == 'parquet'), None)
            if parquet_file:
                print(f"    df = pd.read_parquet('{parquet_file}')", file=sys.stderr)

        print("═" * 60 + "\n", file=sys.stderr)


# Global output mode instance
output = OutputMode()


# ============================================================================
# INITIALIZATION
# ============================================================================

# Lazy initialization for dimcli client
_client = None

def _get_client():
    """Lazy-initialize and return the dimcli client."""
    global _client
    if _client is None:
        dimcli.login()
        _client = dimcli.Dsl()
    return _client

# Cache for valid fields (fetched dynamically from API)
_valid_fields_cache = {
    'facets': {},     # source -> set of valid facet fields
    'filters': {},    # source -> set of valid filter fields
    'metrics': {},    # source -> set of valid metrics
}


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def _fetch_source_metadata(source):
    """Fetch metadata about a source from the API using describe."""
    if source in _valid_fields_cache['facets']:
        return  # Already cached

    try:
        output.log(f"Fetching schema for '{source}'...")
        dsl = f'describe source {source}'
        result = _get_client().query(dsl)
        fields_data = result.json.get('fields', {})
        metrics_data = result.json.get('metrics', [])

        facets = set()
        filters = set()
        metrics = set()

        # Extract facet and filter fields
        for field_name, field_info in fields_data.items():
            if isinstance(field_info, dict):
                if field_info.get('is_facet'):
                    facets.add(field_name)
                if field_info.get('is_filter'):
                    filters.add(field_name)

        # Extract valid metrics
        for metric in metrics_data:
            if isinstance(metric, dict):
                metric_name = metric.get('name')
                if metric_name:
                    metrics.add(metric_name)
            elif isinstance(metric, str):
                metrics.add(metric)

        _valid_fields_cache['facets'][source] = facets
        _valid_fields_cache['filters'][source] = filters
        _valid_fields_cache['metrics'][source] = metrics

        output.log(f"Schema loaded: {len(facets)} facets, {len(filters)} filters, {len(metrics)} metrics")

    except Exception as e:
        output.warn(f"Could not fetch metadata for {source}: {e}")


def validate_facet(source, facet):
    """
    Validate that the facet field is valid for the source.
    Fetches valid facets dynamically from the API.
    """
    _fetch_source_metadata(source)
    valid_facets = _valid_fields_cache['facets'].get(source, set())

    if not valid_facets:
        # If we couldn't fetch valid facets, let the API handle validation
        return

    if facet not in valid_facets:
        # Find similar fields for suggestions
        suggestions = [f for f in valid_facets if facet.split('_')[0] in f][:5]

        error_msg = f"Invalid facet '{facet}' for {source}.\n"
        if suggestions:
            error_msg += f"Similar valid facets: {', '.join(suggestions)}\n"
        error_msg += f"Valid facets: {', '.join(sorted(valid_facets)[:15])}...\n"
        error_msg += f"Use 'describe {source}' to see all available facets."
        raise ValueError(error_msg)

    output.log(f"Facet '{facet}' validated ✓")


def validate_aggregation_metrics(source, metrics_str):
    """
    Validate that aggregation metrics are valid for the source.
    Fetches valid metrics dynamically from the API.
    """
    if not metrics_str:
        return

    _fetch_source_metadata(source)
    valid_metrics = _valid_fields_cache['metrics'].get(source, set())

    if not valid_metrics:
        # If we couldn't fetch valid metrics, let the API handle validation
        return

    # Parse metrics (handle function syntax like sum(funding))
    metrics = [m.strip() for m in metrics_str.split(',')]
    invalid_metrics = []

    for metric in metrics:
        # Handle function syntax: sum(funding) -> funding, count -> count
        if '(' in metric:
            # Extract the inner part: sum(funding) -> funding
            inner = metric.split('(')[1].rstrip(')')
            base_metric = metric.split('(')[0]  # sum, avg, etc.
            # Check if it's a valid aggregate function with a valid field
            if base_metric not in ['sum', 'avg', 'count', 'min', 'max', 'median']:
                invalid_metrics.append(metric)
        else:
            if metric not in valid_metrics and metric != 'count':
                invalid_metrics.append(metric)

    if invalid_metrics:
        error_msg = f"Invalid metric(s) for {source}: {', '.join(invalid_metrics)}\n"
        error_msg += f"Valid metrics: {', '.join(sorted(valid_metrics))}\n"
        error_msg += f"Use 'describe {source}' to see all available metrics."
        raise ValueError(error_msg)

    output.log(f"Metrics validated ✓")


# ============================================================================
# FILE OPERATIONS
# ============================================================================

# Default output directory (use /tmp for stability)
OUTPUT_DIR = Path("/tmp/dimensions-results")
OUTPUT_DIR.mkdir(exist_ok=True)

# Default format: dual (parquet + jsonl)
DEFAULT_FORMAT = 'dual'


def generate_filename(prefix, query_terms=None):
    """Generate a timestamped filename for output."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if query_terms:
        # Clean query terms for filename
        clean_terms = "".join(c if c.isalnum() else "_" for c in query_terms[:30])
        return f"{prefix}_{clean_terms}_{timestamp}"
    return f"{prefix}_{timestamp}"


def clean_nested_for_parquet(obj):
    """
    Recursively clean nested structures for parquet compatibility.
    """
    if obj is None:
        return None
    elif isinstance(obj, str):
        return None if obj == '' else obj
    elif isinstance(obj, dict):
        return {k: clean_nested_for_parquet(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nested_for_parquet(item) for item in obj]
    else:
        return obj


def clean_for_parquet(df):
    """
    Clean DataFrame for parquet export by ensuring consistent types per column.
    """
    df_clean = df.copy()

    for col in df_clean.columns:
        if df_clean[col].dtype != 'object':
            continue  # Skip non-object columns (already typed)

        # Sample non-null values to detect types (exclude empty strings)
        non_null = df_clean[col].dropna()
        if non_null.empty:
            continue

        # Count type occurrences (treat empty string as not a real value)
        type_counts = {'list': 0, 'dict': 0, 'primitive': 0}
        for val in non_null:
            if isinstance(val, list) and val:  # Non-empty list
                type_counts['list'] += 1
            elif isinstance(val, dict) and val:  # Non-empty dict
                type_counts['dict'] += 1
            elif not isinstance(val, (list, dict)) and val != '':
                type_counts['primitive'] += 1

        # Find dominant type (only among actual values)
        dominant_type = max(type_counts, key=type_counts.get)

        # If no clear dominant, default to primitive
        if type_counts[dominant_type] == 0:
            dominant_type = 'primitive'

        # Create cleaner function for this specific column
        def make_cleaner(dominant):
            def clean_value(val):
                if val is None:
                    return None
                if dominant == 'list':
                    if isinstance(val, list) and val:
                        return clean_nested_for_parquet(val)
                    return None
                elif dominant == 'dict':
                    if isinstance(val, dict) and val:
                        return clean_nested_for_parquet(val)
                    return None
                else:  # primitive
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
    """
    Serialize nested structures to JSON strings for text formats (CSV, TSV).
    """
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

    # Clean DataFrame for parquet (ensure consistent types per column)
    df_clean = clean_for_parquet(df)

    if format == 'dual':
        # Save both parquet and jsonl
        parquet_path = OUTPUT_DIR / f"{filename}.parquet"
        jsonl_path = OUTPUT_DIR / f"{filename}.jsonl"

        try:
            df_clean.to_parquet(parquet_path, index=False)
        except Exception as e:
            output.warn(f"Native parquet failed ({e}), using serialized format")
            df_serialized = serialize_for_text_format(df)
            df_serialized.to_parquet(parquet_path, index=False)

        # JSONL from raw data (preserves original nested structures)
        if raw_data:
            with open(jsonl_path, 'w') as f:
                for record in raw_data:
                    f.write(json.dumps(record, default=str) + '\n')
        else:
            df.to_json(jsonl_path, orient='records', lines=True)

        # Record output files
        parquet_size = parquet_path.stat().st_size if parquet_path.exists() else None
        jsonl_size = jsonl_path.stat().st_size if jsonl_path.exists() else None
        output.add_output_file(parquet_path, 'parquet', rows=len(df), size_bytes=parquet_size)
        output.add_output_file(jsonl_path, 'jsonl', rows=len(df), size_bytes=jsonl_size)

        return {'parquet': str(parquet_path), 'jsonl': str(jsonl_path)}

    elif format == 'parquet':
        filepath = OUTPUT_DIR / f"{filename}.parquet"
        try:
            df_clean.to_parquet(filepath, index=False)
        except Exception as e:
            output.warn(f"Native parquet failed ({e}), using serialized format")
            df_serialized = serialize_for_text_format(df)
            df_serialized.to_parquet(filepath, index=False)
        output.add_output_file(filepath, 'parquet', rows=len(df),
                               size_bytes=filepath.stat().st_size if filepath.exists() else None)
    elif format == 'jsonl':
        filepath = OUTPUT_DIR / f"{filename}.jsonl"
        if raw_data:
            with open(filepath, 'w') as f:
                for record in raw_data:
                    f.write(json.dumps(record, default=str) + '\n')
        else:
            df.to_json(filepath, orient='records', lines=True)
        output.add_output_file(filepath, 'jsonl', rows=len(df),
                               size_bytes=filepath.stat().st_size if filepath.exists() else None)
    elif format == 'tsv':
        filepath = OUTPUT_DIR / f"{filename}.tsv"
        df_serialized = serialize_for_text_format(df)
        df_serialized.to_csv(filepath, index=False, sep='\t')
        output.add_output_file(filepath, 'tsv', rows=len(df),
                               size_bytes=filepath.stat().st_size if filepath.exists() else None)
    elif format == 'csv':
        filepath = OUTPUT_DIR / f"{filename}.csv"
        df_serialized = serialize_for_text_format(df)
        df_serialized.to_csv(filepath, index=False)
        output.add_output_file(filepath, 'csv', rows=len(df),
                               size_bytes=filepath.stat().st_size if filepath.exists() else None)
    else:
        # Default to parquet
        filepath = OUTPUT_DIR / f"{filename}.parquet"
        df_clean.to_parquet(filepath, index=False)
        output.add_output_file(filepath, 'parquet', rows=len(df),
                               size_bytes=filepath.stat().st_size if filepath.exists() else None)

    return str(filepath)


# ============================================================================
# QUERY FUNCTIONS
# ============================================================================

def query_iterative(dsl_query, max_results=None, batch_size=1000, save=True, save_format=None):
    """
    Execute a DSL query with automatic pagination to retrieve more than 1000 results.
    """
    batch_size = min(batch_size, 1000)  # API limit

    # Remove any existing limit/skip from query
    base_query = dsl_query.strip()
    for keyword in ['limit', 'skip']:
        if keyword in base_query.lower():
            import re
            base_query = re.sub(rf'\s+{keyword}\s+\d+', '', base_query, flags=re.IGNORECASE)

    all_results = []
    skip = 0
    total_count = None
    source_name = None

    # Detect source name from query
    for source in ['publications', 'grants', 'patents', 'clinical_trials',
                   'policy_documents', 'datasets', 'source_titles', 'reports',
                   'researchers', 'organizations']:
        if f'return {source}' in base_query.lower():
            source_name = source
            break

    if not source_name:
        for source in ['publications', 'grants', 'patents', 'clinical_trials']:
            if f'search {source}' in base_query.lower():
                source_name = source
                break

    if not source_name:
        source_name = 'results'

    output.set_query(base_query + f" limit {batch_size} [paginated]")

    # Estimate API calls for confirmation
    estimated_calls = (max_results // batch_size + 1) if max_results else "unknown"
    if not output.confirm(estimated_calls=estimated_calls, estimated_records=max_results):
        return {
            'total': 0,
            'retrieved': 0,
            'data': [],
            'dataframe': pd.DataFrame(),
            'saved_to': None,
            'query': dsl_query,
            'cancelled': True
        }

    output.step(2, 4, "Executing paginated API calls")

    page_num = 0
    while True:
        page_num += 1
        paginated_query = f"{base_query} limit {batch_size} skip {skip}"

        call_start = time.time()
        try:
            result = _get_client().query(paginated_query)
            call_duration = time.time() - call_start

            if total_count is None:
                total_count = result.count_total or 0
                if max_results:
                    total_count = min(total_count, max_results)
                total_pages = (total_count // batch_size) + 1

            batch_data = getattr(result, source_name, [])
            if not batch_data:
                batch_data = result.json.get(source_name, [])

            if not batch_data:
                break

            output.api_call(page_num, total_pages, len(batch_data), call_duration)

            all_results.extend(batch_data)
            skip += batch_size

            if len(all_results) >= total_count:
                break
            if max_results and len(all_results) >= max_results:
                break
            if len(batch_data) < batch_size:
                break

        except Exception as e:
            output.warn(f"Error at skip={skip}: {e}")
            break

    output.step_done(2, 4, f"Retrieved {len(all_results)} records")
    output.records_retrieved = len(all_results)

    # Convert to DataFrame
    output.step(3, 4, "Processing results")
    df = pd.DataFrame(all_results)

    if not df.empty:
        for col in df.columns:
            if df[col].dtype == 'object':
                sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if isinstance(sample, dict):
                    expanded = pd.json_normalize(df[col].apply(lambda x: x if isinstance(x, dict) else {}))
                    expanded.columns = [f"{col}.{c}" for c in expanded.columns]
                    df = pd.concat([df.drop(columns=[col]), expanded], axis=1)
                elif isinstance(sample, list):
                    df[col] = df[col].apply(lambda x: '; '.join(str(i) for i in x) if isinstance(x, list) else x)

    output.step_done(3, 4, "Results processed")

    # Extract query terms for filename
    query_terms = None
    if 'for "' in dsl_query:
        start = dsl_query.find('for "') + 5
        end = dsl_query.find('"', start)
        if end > start:
            query_terms = dsl_query[start:end]

    # Save results
    output.step(4, 4, "Saving results")
    saved_path = None
    if save and not df.empty:
        saved_path = save_results(df, source_name, query_terms, save_format, raw_data=all_results)
    output.step_done(4, 4, "Results saved")

    return {
        'total': total_count,
        'retrieved': len(all_results),
        'data': all_results,
        'dataframe': df,
        'saved_to': saved_path,
        'query': dsl_query
    }


def search_publications(query_terms, filters=None, fields=None, limit=20, skip=0,
                        iterative=False, max_results=None, save=True):
    """Search publications with optional filters."""
    dsl = f'search publications for "{query_terms}"'

    if filters:
        dsl += f' where {filters}'

    if fields:
        dsl += f' return publications[{fields}]'
    else:
        dsl += ' return publications'

    if iterative or (max_results and max_results > 1000):
        result = query_iterative(dsl, max_results=max_results, save=save)
        return {
            'total': result['total'],
            'returned': result['retrieved'],
            'saved_to': result['saved_to'],
            'publications': result['data'][:20],
            'query': result['query']
        }

    dsl += f' limit {limit}'
    if skip > 0:
        dsl += f' skip {skip}'

    output.set_query(dsl)

    # Confirm in interactive mode
    if not output.confirm(estimated_calls=1, estimated_records=limit):
        return {'total': 0, 'returned': 0, 'saved_to': None, 'publications': [], 'query': dsl, 'cancelled': True}

    output.step(2, 3, "Executing API call")
    call_start = time.time()
    result = _get_client().query(dsl)
    call_duration = time.time() - call_start

    publications = result.publications if hasattr(result, 'publications') else []
    output.api_call(1, 1, len(publications), call_duration)
    output.records_retrieved = len(publications)
    output.step_done(2, 3, f"Retrieved {len(publications)} publications")

    # Save to file
    output.step(3, 3, "Saving results")
    saved_path = None
    if save and publications:
        df = pd.DataFrame(publications)
        saved_path = save_results(df, 'publications', query_terms, raw_data=publications)
    output.step_done(3, 3, "Results saved")

    return {
        'total': result.count_total,
        'returned': len(publications),
        'saved_to': saved_path,
        'publications': publications,
        'query': dsl
    }


def search_grants(query_terms, filters=None, fields=None, limit=20, skip=0,
                  iterative=False, max_results=None, save=True):
    """Search grants with optional filters."""
    dsl = f'search grants for "{query_terms}"'

    if filters:
        dsl += f' where {filters}'

    if fields:
        dsl += f' return grants[{fields}]'
    else:
        dsl += ' return grants'

    if iterative or (max_results and max_results > 1000):
        result = query_iterative(dsl, max_results=max_results, save=save)
        return {
            'total': result['total'],
            'returned': result['retrieved'],
            'saved_to': result['saved_to'],
            'grants': result['data'][:20],
            'query': result['query']
        }

    dsl += f' limit {limit}'
    if skip > 0:
        dsl += f' skip {skip}'

    output.set_query(dsl)

    if not output.confirm(estimated_calls=1, estimated_records=limit):
        return {'total': 0, 'returned': 0, 'saved_to': None, 'grants': [], 'query': dsl, 'cancelled': True}

    output.step(2, 3, "Executing API call")
    call_start = time.time()
    result = _get_client().query(dsl)
    call_duration = time.time() - call_start

    grants = result.grants if hasattr(result, 'grants') else []
    output.api_call(1, 1, len(grants), call_duration)
    output.records_retrieved = len(grants)
    output.step_done(2, 3, f"Retrieved {len(grants)} grants")

    output.step(3, 3, "Saving results")
    saved_path = None
    if save and grants:
        df = pd.DataFrame(grants)
        saved_path = save_results(df, 'grants', query_terms, raw_data=grants)
    output.step_done(3, 3, "Results saved")

    return {
        'total': result.count_total,
        'returned': len(grants),
        'saved_to': saved_path,
        'grants': grants,
        'query': dsl
    }


def search_patents(query_terms, filters=None, fields=None, limit=20, skip=0,
                   iterative=False, max_results=None, save=True):
    """Search patents with optional filters."""
    dsl = f'search patents for "{query_terms}"'

    if filters:
        dsl += f' where {filters}'

    if fields:
        dsl += f' return patents[{fields}]'
    else:
        dsl += ' return patents'

    if iterative or (max_results and max_results > 1000):
        result = query_iterative(dsl, max_results=max_results, save=save)
        return {
            'total': result['total'],
            'returned': result['retrieved'],
            'saved_to': result['saved_to'],
            'patents': result['data'][:20],
            'query': result['query']
        }

    dsl += f' limit {limit}'
    if skip > 0:
        dsl += f' skip {skip}'

    output.set_query(dsl)

    if not output.confirm(estimated_calls=1, estimated_records=limit):
        return {'total': 0, 'returned': 0, 'saved_to': None, 'patents': [], 'query': dsl, 'cancelled': True}

    output.step(2, 3, "Executing API call")
    call_start = time.time()
    result = _get_client().query(dsl)
    call_duration = time.time() - call_start

    patents = result.patents if hasattr(result, 'patents') else []
    output.api_call(1, 1, len(patents), call_duration)
    output.records_retrieved = len(patents)
    output.step_done(2, 3, f"Retrieved {len(patents)} patents")

    output.step(3, 3, "Saving results")
    saved_path = None
    if save and patents:
        df = pd.DataFrame(patents)
        saved_path = save_results(df, 'patents', query_terms, raw_data=patents)
    output.step_done(3, 3, "Results saved")

    return {
        'total': result.count_total,
        'returned': len(patents),
        'saved_to': saved_path,
        'patents': patents,
        'query': dsl
    }


def search_clinical_trials(query_terms, filters=None, fields=None, limit=20, skip=0,
                           iterative=False, max_results=None, save=True):
    """Search clinical trials with optional filters."""
    dsl = f'search clinical_trials for "{query_terms}"'

    if filters:
        dsl += f' where {filters}'

    if fields:
        dsl += f' return clinical_trials[{fields}]'
    else:
        dsl += ' return clinical_trials'

    if iterative or (max_results and max_results > 1000):
        result = query_iterative(dsl, max_results=max_results, save=save)
        return {
            'total': result['total'],
            'returned': result['retrieved'],
            'saved_to': result['saved_to'],
            'clinical_trials': result['data'][:20],
            'query': result['query']
        }

    dsl += f' limit {limit}'
    if skip > 0:
        dsl += f' skip {skip}'

    output.set_query(dsl)

    if not output.confirm(estimated_calls=1, estimated_records=limit):
        return {'total': 0, 'returned': 0, 'saved_to': None, 'clinical_trials': [], 'query': dsl, 'cancelled': True}

    output.step(2, 3, "Executing API call")
    call_start = time.time()
    result = _get_client().query(dsl)
    call_duration = time.time() - call_start

    trials = result.clinical_trials if hasattr(result, 'clinical_trials') else []
    output.api_call(1, 1, len(trials), call_duration)
    output.records_retrieved = len(trials)
    output.step_done(2, 3, f"Retrieved {len(trials)} trials")

    output.step(3, 3, "Saving results")
    saved_path = None
    if save and trials:
        df = pd.DataFrame(trials)
        saved_path = save_results(df, 'clinical_trials', query_terms, raw_data=trials)
    output.step_done(3, 3, "Results saved")

    return {
        'total': result.count_total,
        'returned': len(trials),
        'saved_to': saved_path,
        'clinical_trials': trials,
        'query': dsl
    }


def search_researchers(query_terms=None, filters=None, fields=None, limit=20,
                       iterative=False, max_results=None, save=True):
    """Search researchers with optional filters."""
    if query_terms:
        dsl = f'search researchers for "{query_terms}"'
    else:
        dsl = 'search researchers'

    if filters:
        dsl += f' where {filters}'

    if fields:
        dsl += f' return researchers[{fields}]'
    else:
        dsl += ' return researchers'

    if iterative or (max_results and max_results > 1000):
        result = query_iterative(dsl, max_results=max_results, save=save)
        return {
            'total': result['total'],
            'returned': result['retrieved'],
            'saved_to': result['saved_to'],
            'researchers': result['data'][:20],
            'query': result['query']
        }

    dsl += f' limit {limit}'

    output.set_query(dsl)

    if not output.confirm(estimated_calls=1, estimated_records=limit):
        return {'total': 0, 'returned': 0, 'saved_to': None, 'researchers': [], 'query': dsl, 'cancelled': True}

    output.step(2, 3, "Executing API call")
    call_start = time.time()
    result = _get_client().query(dsl)
    call_duration = time.time() - call_start

    researchers = result.researchers if hasattr(result, 'researchers') else []
    output.api_call(1, 1, len(researchers), call_duration)
    output.records_retrieved = len(researchers)
    output.step_done(2, 3, f"Retrieved {len(researchers)} researchers")

    output.step(3, 3, "Saving results")
    saved_path = None
    if save and researchers:
        df = pd.DataFrame(researchers)
        saved_path = save_results(df, 'researchers', query_terms, raw_data=researchers)
    output.step_done(3, 3, "Results saved")

    return {
        'total': result.count_total,
        'returned': len(researchers),
        'saved_to': saved_path,
        'researchers': researchers,
        'query': dsl
    }


def aggregate_query(source, query_terms, facet, aggregate_by=None, filters=None,
                    limit=20, save=True):
    """Get aggregated statistics."""
    # Validate facet and metrics before making API call
    output.step(1, 3, "Validating schema")
    validate_facet(source, facet)
    if aggregate_by:
        validate_aggregation_metrics(source, aggregate_by)
    output.step_done(1, 3, "Schema validated")

    dsl = f'search {source} for "{query_terms}"'

    if filters:
        dsl += f' where {filters}'

    dsl += f' return {facet}'

    if aggregate_by:
        dsl += f' aggregate {aggregate_by}'

    dsl += f' limit {limit}'

    output.set_query(dsl)

    if not output.confirm(estimated_calls=1):
        return {'facet': facet, 'data': [], 'saved_to': None, 'query': dsl, 'cancelled': True}

    output.step(2, 3, "Executing API call")
    call_start = time.time()
    result = _get_client().query(dsl)
    call_duration = time.time() - call_start

    facet_data = getattr(result, facet, []) if hasattr(result, facet) else result.json.get(facet, [])
    output.api_call(1, 1, len(facet_data), call_duration)
    output.records_retrieved = len(facet_data)
    output.step_done(2, 3, f"Retrieved {len(facet_data)} {facet}")

    output.step(3, 3, "Saving results")
    saved_path = None
    if save and facet_data:
        df = pd.DataFrame(facet_data)
        saved_path = save_results(df, f'{source}_{facet}', query_terms, raw_data=facet_data)
    output.step_done(3, 3, "Results saved")

    return {
        'facet': facet,
        'data': facet_data,
        'saved_to': saved_path,
        'query': dsl
    }


def extract_concepts(text, return_scores=False):
    """Extract concepts from text."""
    text = text.replace('"', '\\"')
    if return_scores:
        dsl = f'extract_concepts("{text}", return_scores=true)'
    else:
        dsl = f'extract_concepts("{text}")'

    output.set_query(dsl)

    output.step(1, 1, "Extracting concepts")
    result = _get_client().query(dsl)
    output.api_calls = 1
    output.step_done(1, 1, "Concepts extracted")

    return {
        'concepts': result.json.get('extracted_concepts', []),
        'query': dsl
    }


def classify_text(title, abstract, system='FOR_2020'):
    """Classify text into research categories."""
    title = title.replace('"', '\\"')
    abstract = abstract.replace('"', '\\"')

    dsl = f'classify(title="{title}", abstract="{abstract}", system="{system}")'

    output.set_query(dsl)

    output.step(1, 1, "Classifying text")
    result = _get_client().query(dsl)
    output.api_calls = 1
    output.step_done(1, 1, "Classification complete")

    return {
        'system': system,
        'classifications': result.json.get(system, []),
        'query': dsl
    }


def extract_affiliations(affiliation_text):
    """Extract and resolve organization from affiliation text."""
    affiliation_text = affiliation_text.replace('"', '\\"')
    dsl = f'extract_affiliations(affiliation="{affiliation_text}")'

    output.set_query(dsl)

    output.step(1, 1, "Extracting affiliations")
    result = _get_client().query(dsl)
    output.api_calls = 1
    output.step_done(1, 1, "Affiliations extracted")

    return {
        'results': result.json.get('results', []),
        'query': dsl
    }


def identify_experts(concepts, source='publications', filters=None, annotate_with=None,
                     limit=20, save=True):
    """Identify experts based on concepts."""
    concepts_str = ', '.join([f'"{c}"' for c in concepts])
    dsl = f'identify experts from concepts [{concepts_str}] using {source}'

    if filters:
        dsl += f' where {filters}'

    if annotate_with:
        ids_str = ', '.join([f'"{id}"' for id in annotate_with])
        dsl += f' annotate organizational, coauthorship overlap with [{ids_str}]'

    dsl += f' return experts limit {limit}'

    output.set_query(dsl)

    if not output.confirm(estimated_calls=1, estimated_records=limit):
        return {'experts': [], 'saved_to': None, 'query': dsl, 'cancelled': True}

    output.step(1, 2, "Identifying experts")
    call_start = time.time()
    result = _get_client().query(dsl)
    call_duration = time.time() - call_start

    experts = result.json.get('experts', [])
    output.api_call(1, 1, len(experts), call_duration)
    output.records_retrieved = len(experts)
    output.step_done(1, 2, f"Found {len(experts)} experts")

    output.step(2, 2, "Saving results")
    saved_path = None
    if save and experts:
        df = pd.DataFrame(experts)
        saved_path = save_results(df, 'experts', '_'.join(concepts[:3]), raw_data=experts)
    output.step_done(2, 2, "Results saved")

    return {
        'experts': experts,
        'saved_to': saved_path,
        'query': dsl
    }


def describe_source(source_name):
    """Get metadata about a data source."""
    dsl = f'describe source {source_name}'

    output.set_query(dsl)

    output.step(1, 1, f"Fetching schema for '{source_name}'")
    result = _get_client().query(dsl)
    output.api_calls = 1
    output.step_done(1, 1, "Schema retrieved")

    return {
        'fields': result.json.get('fields', []),
        'fieldsets': result.json.get('fieldsets', []),
        'metrics': result.json.get('metrics', []),
        'search_fields': result.json.get('search_fields', []),
        'query': dsl
    }


def raw_query(dsl_query, save=True, iterative=False, max_results=None):
    """Execute a raw DSL query."""
    if iterative or (max_results and max_results > 1000):
        result = query_iterative(dsl_query, max_results=max_results, save=save)
        return {
            'total': result['total'],
            'retrieved': result['retrieved'],
            'saved_to': result['saved_to'],
            'json': {'data': result['data'][:100]},
            'query': result['query']
        }

    output.set_query(dsl_query)

    if not output.confirm(estimated_calls=1):
        return {'json': {}, 'total': None, 'saved_to': None, 'query': dsl_query, 'cancelled': True}

    output.step(1, 2, "Executing raw query")
    call_start = time.time()
    result = _get_client().query(dsl_query)
    call_duration = time.time() - call_start
    output.api_call(1, 1, result.count_total or 0, call_duration)
    output.step_done(1, 2, "Query executed")

    # Try to save results
    output.step(2, 2, "Saving results")
    saved_path = None
    if save:
        for source in ['publications', 'grants', 'patents', 'clinical_trials',
                       'researchers', 'organizations', 'datasets', 'reports']:
            data = result.json.get(source, [])
            if data:
                df = pd.DataFrame(data)
                saved_path = save_results(df, source, raw_data=data)
                output.records_retrieved = len(data)
                break

        if not saved_path:
            for key in ['year', 'funders', 'research_orgs', 'category_for']:
                data = result.json.get(key, [])
                if data:
                    df = pd.DataFrame(data)
                    saved_path = save_results(df, f'facet_{key}', raw_data=data)
                    output.records_retrieved = len(data)
                    break
    output.step_done(2, 2, "Results saved")

    return {
        'json': result.json,
        'total': result.count_total if hasattr(result, 'count_total') else None,
        'saved_to': saved_path,
        'query': dsl_query
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    # Common arguments shared by all subcommands
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('--no-save', action='store_true', help='Do not save results to file')
    common_parser.add_argument('--format', choices=['dual', 'parquet', 'jsonl', 'tsv', 'csv'],
                               default='dual', help='Output format (default: dual = parquet + jsonl)')
    common_parser.add_argument('--output-dir', '-o', type=str,
                               help='Output directory (default: /tmp/dimensions-results/)')

    # Output mode arguments
    mode_group = common_parser.add_mutually_exclusive_group()
    mode_group.add_argument('--verbose', '-v', action='store_true', default=True,
                            help='Verbose output with step-by-step details (default)')
    mode_group.add_argument('--silent', '-s', action='store_true',
                            help='Silent mode - minimal output, only final JSON')

    parser = argparse.ArgumentParser(
        description='Dimensions DSL Helper - Query the Dimensions research database',
        parents=[common_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Modes:
  --verbose, -v      Step-by-step execution details (default)
  --silent, -s       Minimal output, only final JSON result

Examples:
  %(prog)s search-publications "machine learning" -l 50
  %(prog)s search-grants "cancer" -f "funders.acronym=\\"NIH\\""
  %(prog)s aggregate publications "AI" -F funders -a "citations_avg"
  %(prog)s describe publications
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Search publications
    pub_parser = subparsers.add_parser('search-publications', help='Search publications',
                                       parents=[common_parser])
    pub_parser.add_argument('query', help='Search query')
    pub_parser.add_argument('--filters', '-f', help='DSL where clause filters')
    pub_parser.add_argument('--fields', help='Fields to return')
    pub_parser.add_argument('--limit', '-l', type=int, default=20)
    pub_parser.add_argument('--skip', type=int, default=0)
    pub_parser.add_argument('--iterative', '-i', action='store_true',
                            help='Use iterative query for large results')
    pub_parser.add_argument('--max-results', '-m', type=int,
                            help='Maximum results (enables iterative if >1000)')

    # Search grants
    grant_parser = subparsers.add_parser('search-grants', help='Search grants',
                                         parents=[common_parser])
    grant_parser.add_argument('query', help='Search query')
    grant_parser.add_argument('--filters', '-f', help='DSL where clause filters')
    grant_parser.add_argument('--fields', help='Fields to return')
    grant_parser.add_argument('--limit', '-l', type=int, default=20)
    grant_parser.add_argument('--iterative', '-i', action='store_true')
    grant_parser.add_argument('--max-results', '-m', type=int)

    # Search patents
    patent_parser = subparsers.add_parser('search-patents', help='Search patents',
                                          parents=[common_parser])
    patent_parser.add_argument('query', help='Search query')
    patent_parser.add_argument('--filters', '-f', help='DSL where clause filters')
    patent_parser.add_argument('--fields', help='Fields to return')
    patent_parser.add_argument('--limit', '-l', type=int, default=20)
    patent_parser.add_argument('--iterative', '-i', action='store_true')
    patent_parser.add_argument('--max-results', '-m', type=int)

    # Search clinical trials
    trial_parser = subparsers.add_parser('search-trials', help='Search clinical trials',
                                         parents=[common_parser])
    trial_parser.add_argument('query', help='Search query')
    trial_parser.add_argument('--filters', '-f', help='DSL where clause filters')
    trial_parser.add_argument('--fields', help='Fields to return')
    trial_parser.add_argument('--limit', '-l', type=int, default=20)
    trial_parser.add_argument('--iterative', '-i', action='store_true')
    trial_parser.add_argument('--max-results', '-m', type=int)

    # Aggregate query
    agg_parser = subparsers.add_parser('aggregate', help='Aggregation query',
                                       parents=[common_parser])
    agg_parser.add_argument('source', help='Data source')
    agg_parser.add_argument('query', help='Search query')
    agg_parser.add_argument('--facet', '-F', required=True, help='Facet field')
    agg_parser.add_argument('--aggregate', '-a', help='Aggregation metrics')
    agg_parser.add_argument('--filters', '-f', help='Filters')
    agg_parser.add_argument('--limit', '-l', type=int, default=20)

    # Extract concepts
    concept_parser = subparsers.add_parser('extract-concepts', help='Extract concepts from text',
                                           parents=[common_parser])
    concept_parser.add_argument('text', help='Text to extract concepts from')
    concept_parser.add_argument('--scores', action='store_true', help='Include relevance scores')

    # Classify
    classify_parser = subparsers.add_parser('classify', help='Classify text',
                                            parents=[common_parser])
    classify_parser.add_argument('--title', required=True, help='Title')
    classify_parser.add_argument('--abstract', required=True, help='Abstract')
    classify_parser.add_argument('--system', default='FOR_2020', help='Classification system')

    # Identify experts
    expert_parser = subparsers.add_parser('identify-experts', help='Identify experts',
                                          parents=[common_parser])
    expert_parser.add_argument('--concepts', '-c', nargs='+', required=True, help='Concepts')
    expert_parser.add_argument('--filters', '-f', help='Filter clause')
    expert_parser.add_argument('--limit', '-l', type=int, default=20)

    # Raw query
    raw_parser = subparsers.add_parser('raw', help='Execute raw DSL query',
                                       parents=[common_parser])
    raw_parser.add_argument('query', help='DSL query string')
    raw_parser.add_argument('--iterative', '-i', action='store_true')
    raw_parser.add_argument('--max-results', '-m', type=int)

    # Describe
    desc_parser = subparsers.add_parser('describe', help='Describe a source',
                                        parents=[common_parser])
    desc_parser.add_argument('source', help='Source name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Set output mode
    global output
    if getattr(args, 'silent', False):
        output = OutputMode(OutputMode.SILENT)
    else:
        output = OutputMode(OutputMode.VERBOSE)

    # Set output directory if specified
    global OUTPUT_DIR
    if hasattr(args, 'output_dir') and args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
        OUTPUT_DIR.mkdir(exist_ok=True)

    save = not getattr(args, 'no_save', False)

    # Build args summary for header
    args_summary = {}
    if hasattr(args, 'query'):
        args_summary['Query'] = args.query
    if hasattr(args, 'source'):
        args_summary['Source'] = args.source
    if hasattr(args, 'filters') and args.filters:
        args_summary['Filters'] = args.filters
    if hasattr(args, 'facet') and args.facet:
        args_summary['Facet'] = args.facet
    if hasattr(args, 'limit'):
        args_summary['Limit'] = args.limit
    if hasattr(args, 'max_results') and args.max_results:
        args_summary['Max Results'] = args.max_results

    # Start workflow tracking
    output.start(args.command, args_summary)
    output.step(1, 3, "Initializing query")

    result = None

    try:
        if args.command == 'search-publications':
            output.step_done(1, 3, "Query initialized")
            result = search_publications(
                args.query, args.filters, args.fields, args.limit, args.skip,
                iterative=args.iterative, max_results=args.max_results, save=save
            )
        elif args.command == 'search-grants':
            output.step_done(1, 3, "Query initialized")
            result = search_grants(
                args.query, args.filters, args.fields, args.limit,
                iterative=args.iterative, max_results=args.max_results, save=save
            )
        elif args.command == 'search-patents':
            output.step_done(1, 3, "Query initialized")
            result = search_patents(
                args.query, args.filters, args.fields, args.limit,
                iterative=args.iterative, max_results=args.max_results, save=save
            )
        elif args.command == 'search-trials':
            output.step_done(1, 3, "Query initialized")
            result = search_clinical_trials(
                args.query, args.filters, args.fields, args.limit,
                iterative=args.iterative, max_results=args.max_results, save=save
            )
        elif args.command == 'aggregate':
            output.step_done(1, 3, "Query initialized")
            result = aggregate_query(
                args.source, args.query, args.facet, args.aggregate, args.filters,
                args.limit, save=save
            )
        elif args.command == 'extract-concepts':
            output.step_done(1, 1, "Ready")
            result = extract_concepts(args.text, args.scores)
        elif args.command == 'classify':
            output.step_done(1, 1, "Ready")
            result = classify_text(args.title, args.abstract, args.system)
        elif args.command == 'identify-experts':
            output.step_done(1, 2, "Query initialized")
            result = identify_experts(args.concepts, filters=args.filters,
                                      limit=args.limit, save=save)
        elif args.command == 'raw':
            output.step_done(1, 2, "Query initialized")
            result = raw_query(args.query, save=save, iterative=args.iterative,
                              max_results=args.max_results)
        elif args.command == 'describe':
            output.step_done(1, 1, "Ready")
            result = describe_source(args.source)
        else:
            parser.print_help()
            return

    except Exception as e:
        output.warn(f"Error: {e}")
        result = {'error': str(e)}

    # Print workflow summary (always, for all modes)
    output.print_summary(result)

    # Clean result for JSON output (remove DataFrame)
    if result and 'dataframe' in result:
        del result['dataframe']

    # Print JSON result
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
