---
name: dimensions
description: Query the Dimensions research database using natural language. Search publications, grants, patents, clinical trials. Find research experts. Get citation metrics and funding statistics. Results auto-saved to /tmp/dimensions-results/ as parquet + jsonl (dual format).
allowed-tools: Bash, Read, Glob, Grep, Write
---

# Dimensions Research Database Skill

Query the Dimensions research database (140M+ publications, 8M+ grants, 60M+ patents) using natural language. All results are automatically saved as data tables.

---

## IMPORTANT: Always Check Schema First

**Before running any queries, ALWAYS check the available fields, facets, and metrics for each data source using `describe`.**

Different data sources (publications, grants, patents, etc.) have **different field names**. For example:
- Publications use `funders` for funder facet
- Grants use `funder_org_acronym` for funder facet

### Required First Step

```bash
# Check schema BEFORE querying
/opt/anaconda3/bin/conda run -n base python ~/.claude/skills/dimensions/dimensions_helper.py describe publications
/opt/anaconda3/bin/conda run -n base python ~/.claude/skills/dimensions/dimensions_helper.py describe grants
```

### Quick Schema Reference

| Data Source | Common Facets | Common Metrics |
|-------------|---------------|----------------|
| `publications` | `funders`, `funder_countries`, `research_orgs`, `year` | `citations_avg`, `rcr_avg`, `citations_total` |
| `grants` | `funder_org_acronym`, `funder_org_countries`, `funder_org_name` | `funding`, `count` |

**Why this matters:** Field names change between API versions and differ across data sources. Checking the schema first prevents errors and wasted API calls.

---

## Online Documentation

When local docs are insufficient, refer to the official documentation:

| Resource | URL |
|----------|-----|
| **DSL Manual** | https://docs.dimensions.ai/dsl/ |
| **Query Syntax** | https://docs.dimensions.ai/dsl/language.html |
| **Data Sources** | https://docs.dimensions.ai/dsl/data-sources.html |
| **Functions** | https://docs.dimensions.ai/dsl/functions.html |
| **Examples** | https://docs.dimensions.ai/dsl/examples.html |
| **API Release Notes** | https://docs.dimensions.ai/dsl/release-notes.html |

## Quick Start

**Execution pattern:**
```bash
/opt/anaconda3/bin/conda run -n base python ~/.claude/skills/dimensions/dimensions_helper.py <command> [args]
```

**Results saved to:** `/tmp/dimensions-results/` (default)

## Output Formats

Default: **dual** (saves both formats)
- `.parquet` - Binary columnar, typed columns, compressed (for data reuse)
- `.jsonl` - JSON Lines, human-readable, nested structures preserved (for peeking)

```bash
# Default dual output
search-publications "AI" -m 1000

# Single format options
search-publications "AI" --format parquet
search-publications "AI" --format jsonl
search-publications "AI" --format tsv
search-publications "AI" --format csv

# Custom output directory
search-publications "AI" --output-dir ./results/
search-publications "AI" -o /path/to/output/
```

Peek at results:
```bash
head -3 /tmp/dimensions-results/*.jsonl | jq
```

## Authentication

Authentication is handled automatically via `~/.dimcli/dsl.ini`.

**To refresh or setup auth**, users should run:
```bash
pip install dimcli
dimcli --init
```

## Core Commands

| Command | Purpose |
|---------|---------|
| `search-publications` | Search scholarly papers |
| `search-grants` | Search research funding |
| `search-patents` | Search patent documents |
| `search-trials` | Search clinical trials |
| `identify-experts` | Find domain experts |
| `aggregate` | Get statistics |
| `raw` | Execute DSL directly |

## Natural Language → Command Translation

### Quick Reference

| User Says | Command |
|-----------|---------|
| "Find papers on X" | `search-publications "X"` |
| "Recent papers on X" | `search-publications "X" -f "year >= 2023"` |
| "Papers from Stanford" | `search-publications "X" -f "research_orgs.name~\"Stanford\""` |
| "NIH grants for X" | `search-grants "X" -f "funders.acronym=\"NIH\""` |
| "Get 5000 results" | Add `--max-results 5000` (auto-paginates) |
| "Who are experts in X" | `identify-experts -c "X" "Y"` |

### Filter Patterns

| Natural Language | DSL Filter |
|------------------|------------|
| recent / latest | `year >= 2023` |
| last 5 years | `year >= 2021` |
| since 2020 | `year >= 2020` |
| highly cited | `times_cited >= 100` |
| open access | `open_access in ["gold", "green_pub"]` |
| from [Org] | `research_orgs.name~"[Org]"` |
| funded by NIH | `funders.acronym="NIH"` |
| funded by NSF | `funders.acronym="NSF"` |

## Command Details

### 1. Search Publications
```bash
search-publications "QUERY" [OPTIONS]
  -f, --filters      DSL where clause
  -l, --limit        Results per page (default: 20, max: 1000)
  -m, --max-results  Total results (auto-paginates if >1000)
  -i, --iterative    Force pagination mode
  --fields           Specific fields to return
  --format           Output format (dual, parquet, jsonl, tsv, csv)
  -o, --output-dir   Output directory
```

**Examples:**
```bash
# Basic search
search-publications "machine learning"

# With filters
search-publications "CRISPR" -f "year >= 2022" -l 50

# Large result set (auto-paginates, saves parquet + jsonl)
search-publications "cancer immunotherapy" -m 5000

# From specific organization
search-publications "AI" -f "research_orgs.name~\"MIT\""

# Save to working directory
search-publications "AI" -o .
```

### 2. Search Grants
```bash
search-grants "QUERY" [OPTIONS]
  -f, --filters      DSL where clause
  -l, --limit        Results (default: 20)
  -m, --max-results  Total results
```

**Examples:**
```bash
search-grants "climate change" -f "funders.acronym=\"NSF\""
search-grants "cancer" -f "funding_usd >= 1000000 and start_year >= 2020"
```

### 3. Aggregations
```bash
aggregate SOURCE "QUERY" -F FACET [-a METRICS] [-f FILTERS]
```

**Examples:**
```bash
# Publications by year
aggregate publications "AI" -F year

# Top institutions by citations (use rcr_avg or citations_avg)
aggregate publications "quantum" -F research_orgs -a "rcr_avg, citations_avg" -l 20

# Funding by funder
aggregate grants "cancer" -F funder_org_acronym -a funding -l 20
```

**Note:** The `aggregate` command validates facets and metrics dynamically from the API using `describe`. Invalid parameters are rejected early with helpful error messages.

### 4. Identify Experts
```bash
identify-experts -c CONCEPT1 CONCEPT2 ... [-f FILTERS] [-l LIMIT]
```

**Example:**
```bash
identify-experts -c "CRISPR" "gene therapy" -l 15
```

### 5. Raw DSL Query
```bash
raw "DSL QUERY" [-i] [-m MAX_RESULTS]
```

**Examples:**
```bash
raw "search publications for \"AI\" return year aggregate count limit 10"
raw "search publications for \"cancer\" return publications" -m 3000
```

## Output

Default output location and format:
```
/tmp/dimensions-results/
├── publications_QUERY_TIMESTAMP.parquet   # Binary, typed (for pandas/DuckDB)
├── publications_QUERY_TIMESTAMP.jsonl     # Text, nested (for peeking: head -3 | jq)
├── grants_QUERY_TIMESTAMP.parquet
├── grants_QUERY_TIMESTAMP.jsonl
└── ...
```

JSON response includes:
- `total`: Total matching records
- `returned`: Records in this response
- `saved_to`: Path(s) to saved file(s)
- `query`: Executed DSL query

---

## CRITICAL: Reuse Saved Data Files

**All query results are saved to files for a reason - ALWAYS load from these files in subsequent workflows.**

### Why Data Reuse Matters

| Approach | Problem |
|----------|---------|
| Hardcoding values | Not reproducible, error-prone, requires manual updates |
| Re-querying API | Wastes API calls, slow, may hit rate limits |
| **Loading saved files** | Reproducible, fast, maintains data integrity |

### NEVER Do This

```python
# BAD - Hardcoded data values
pubs_data = pd.DataFrame({
    'Funder': ['NSFC', 'NSF', 'EC'],
    'Publications': [94868, 48828, 50257],  # Manually copied numbers = BAD
    'Citations': [2466146, 2896540, 2129299]
})
```

### ALWAYS Do This

```python
# GOOD - Load from saved parquet files
import pandas as pd
from glob import glob

# Find the most recent file matching your query
files = sorted(glob('/tmp/dimensions-results/publications_funders_*.parquet'))
pubs_data = pd.read_parquet(files[-1])  # Load most recent

# Or load specific file from query output
pubs_data = pd.read_parquet('/tmp/dimensions-results/publications_funders_quantum_computing_20260114_153330.parquet')
```

### Data Loading Examples

#### Python (pandas)
```python
import pandas as pd

# Load parquet (recommended - typed columns, fast)
df = pd.read_parquet('/tmp/dimensions-results/grants_funder_org_acronym_*.parquet')

# Load JSONL (preserves nested structures)
df = pd.read_json('/tmp/dimensions-results/grants_*.jsonl', lines=True)
```

#### Python (DuckDB - for large files)
```python
import duckdb

# Query parquet directly without loading into memory
result = duckdb.query("""
    SELECT funder, SUM(funding) as total_funding
    FROM '/tmp/dimensions-results/grants_*.parquet'
    GROUP BY funder
    ORDER BY total_funding DESC
""").df()
```

#### Command Line (quick peek)
```bash
# Preview JSONL
head -5 /tmp/dimensions-results/*.jsonl | jq

# Query parquet with DuckDB CLI
duckdb -c "SELECT * FROM '/tmp/dimensions-results/publications_*.parquet' LIMIT 10"
```

### Workflow Pattern

```
1. Query API  ──────►  2. Data saved to files  ──────►  3. Load files for analysis
   (run once)             (parquet + jsonl)               (reuse many times)
                                │
                                ▼
                    /tmp/dimensions-results/
                    ├── publications_*.parquet
                    └── grants_*.parquet
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  Visualization script   │
                    │  Statistical analysis   │
                    │  Report generation      │
                    │  Machine learning       │
                    └─────────────────────────┘
```

### File Naming Convention

Files are named with query context and timestamps:
```
{source}_{facet}_{query}_{timestamp}.{format}
```

Example: `publications_funders_quantum_computing_20260114_153330.parquet`

Use glob patterns to find files:
```python
from glob import glob

# Find all publication aggregations
pub_files = glob('/tmp/dimensions-results/publications_*.parquet')

# Find specific query results
quantum_files = glob('/tmp/dimensions-results/*quantum*.parquet')
```

---

## For Advanced Queries

### Local Documentation
- **Query syntax**: `~/Desktop/dimensions-dsl-docs/03-query-syntax.md`
- **Examples**: `~/Desktop/dimensions-dsl-docs/07-examples.md`
- **Publication fields**: `~/Desktop/dimensions-dsl-docs/datasource-publications.md`
- **Grant fields**: `~/Desktop/dimensions-dsl-docs/datasource-grants.md`

### Online Documentation
- **Full DSL Manual**: https://docs.dimensions.ai/dsl/
- **API Reference**: https://docs.dimensions.ai/dsl/language.html

Use `describe <source>` to see available fields:
```bash
describe publications
describe grants
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Auth expired (401) | User runs: `pip install dimcli && dimcli --init` |
| Rate limited (429) | Wait 1 minute, reduce batch size |
| Query syntax error (400) | Check DSL syntax at https://docs.dimensions.ai/dsl/language.html |
| Timeout | Add filters, reduce result count |

## Limitations & Validation

This skill includes **dynamic parameter validation** that fetches valid fields from the Dimensions API using the `describe` command. Invalid parameters are rejected early with helpful error messages.

### Facet Field Names

Facet names have changed over API versions. Common corrections:

| Old/Wrong | Correct |
|-----------|---------|
| `funders` | `funder_org_acronym` or `funder_org_name` |
| `research_orgs` | `research_org_name` or `research_org_countries` |

Use `describe <source>` to see all valid facets:
```bash
describe publications
describe grants
```

### Aggregation Metric Names

Some metrics have changed or been deprecated:

| Invalid/Deprecated | Valid Alternatives |
|--------------------|-------------------|
| `times_cited_avg` | `citations_avg`, `rcr_avg`, `fcr_gavg` |
| `times_cited` | `citations_total`, `citations_avg` |

**Valid publication metrics:** `count`, `altmetric_avg`, `altmetric_median`, `citations_avg`, `citations_median`, `citations_total`, `rcr_avg`, `fcr_gavg`, `recent_citations_total`

**Valid grant metrics:** `count`, `funding`

### Discovering Valid Fields

The best way to discover valid fields is to use `describe`:

```bash
# See all facets for a source
describe publications | jq '.fields | to_entries[] | select(.value.is_facet==true) | .key'

# See all metrics
describe publications | jq '.metrics'
```

Or simply try an invalid field - the error message will list alternatives.
