---
name: openalex
description: Query the OpenAlex research database using natural language. Search 240M+ works, 90M+ authors, 109K institutions. Get citation metrics, find research experts, analyze publication trends. Results auto-saved to /tmp/openalex-results/ as parquet + jsonl (dual format).
allowed-tools: Bash, Read, Glob, Grep, Write
---

# OpenAlex Research Database Skill

Query the OpenAlex open research database (240M+ works, 90M+ authors, 109K institutions, 32K funders) using natural language. All results are automatically saved as data tables.

## Online Documentation

When local docs are insufficient, refer to the official documentation:

| Resource | URL |
|----------|-----|
| **API Guide** | https://docs.openalex.org/ |
| **Works Entity** | https://docs.openalex.org/api-entities/works |
| **Authors Entity** | https://docs.openalex.org/api-entities/authors |
| **Institutions Entity** | https://docs.openalex.org/api-entities/institutions |
| **Filtering** | https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/filter-entity-lists |
| **Grouping** | https://docs.openalex.org/how-to-use-the-api/get-groups-of-entities |

## Quick Start

**Execution pattern:**
```bash
/opt/anaconda3/bin/conda run -n base python ~/.claude/skills/openalex/openalex_helper.py <command> [args]
```

**Results saved to:** `/tmp/openalex-results/` (default)

## Output Formats

Default: **dual** (saves both formats)
- `.parquet` - Binary columnar, typed columns, compressed (for data reuse)
- `.jsonl` - JSON Lines, human-readable, nested structures preserved (for peeking)

```bash
# Default dual output
search-works "machine learning" -m 1000

# Single format options
search-works "AI" --format parquet
search-works "AI" --format jsonl
search-works "AI" --format tsv

# Custom output directory
search-works "AI" --output-dir ./results/
search-works "AI" -o /path/to/output/
```

Peek at results:
```bash
head -3 /tmp/openalex-results/*.jsonl | jq
```

## Authentication

**No authentication required!** OpenAlex is free and open.

For better performance (polite pool), set your email:
```bash
export OPENALEX_EMAIL="you@example.com"
```

## Core Commands

| Command | Purpose |
|---------|---------|
| `search-works` | Search scholarly papers |
| `search-authors` | Search researchers |
| `search-institutions` | Search universities/orgs |
| `search-sources` | Search journals/repos |
| `search-funders` | Search funding organizations |
| `search-topics` | Search research topics |
| `get` | Get single entity by ID |
| `group` | Get aggregated statistics |
| `autocomplete` | Type-ahead search |

## Natural Language -> Command Translation

### Quick Reference

| User Says | Command |
|-----------|---------|
| "Find papers on X" | `search-works "X"` |
| "Recent papers on X" | `search-works --filter "publication_year:2023"` |
| "Papers from Stanford" | `search-works --filter "authorships.institutions.id:I97018004"` |
| "Highly cited papers" | `search-works --filter "cited_by_count:>100" --sort "cited_by_count:desc"` |
| "Open access papers" | `search-works --filter "is_oa:true"` |
| "Get 5000 results" | Add `--max-results 5000` (auto-paginates) |
| "Who works on X" | `search-authors "X"` |
| "Find institution" | `search-institutions "Harvard"` |

### Filter Patterns

| Natural Language | OpenAlex Filter |
|------------------|-----------------|
| recent / latest | `publication_year:2023` |
| last 5 years | `publication_year:>2019` |
| since 2020 | `from_publication_date:2020-01-01` |
| highly cited | `cited_by_count:>100` |
| open access | `is_oa:true` |
| gold OA | `oa_status:gold` |
| from [Org] | `authorships.institutions.id:I...` |
| funded by NIH | `grants.funder:F4320306076` |
| in Nature | `primary_location.source.id:S137773608` |

## Command Details

### 1. Search Works
```bash
search-works "QUERY" [OPTIONS]
  -f, --filter         Filter expression
  --search-field       Search specific field (title, abstract, fulltext)
  -s, --sort           Sort field (e.g., cited_by_count:desc)
  --select             Fields to return
  -l, --limit          Results per page (default: 25, max: 200)
  -p, --page           Page number
  -m, --max-results    Total results (auto-paginates)
  --format             Output format (dual, parquet, jsonl, tsv, csv)
  -o, --output-dir     Output directory
```

**Examples:**
```bash
# Basic search
search-works "machine learning"

# With filters
search-works "CRISPR" -f "publication_year:>2022" -l 50

# Large result set (auto-paginates)
search-works "cancer immunotherapy" -m 5000

# From specific institution
search-works -f "authorships.institutions.id:I97018004" -s "cited_by_count:desc"

# Highly cited recent papers
search-works "quantum computing" -f "publication_year:2023,cited_by_count:>50"

# Open access only
search-works "climate change" -f "is_oa:true,oa_status:gold"
```

### 2. Search Authors
```bash
search-authors "NAME" [OPTIONS]
  -f, --filter         Filter expression
  -s, --sort           Sort field
  -l, --limit          Results (default: 25)
  -m, --max-results    Total results
```

**Examples:**
```bash
# Find author by name
search-authors "Richard Feynman"

# Authors with high h-index
search-authors -f "summary_stats.h_index:>50" -s "summary_stats.h_index:desc"

# Authors at specific institution
search-authors -f "last_known_institutions.id:I97018004"

# Authors with ORCID
search-authors -f "has_orcid:true" -s "cited_by_count:desc"
```

### 3. Search Institutions
```bash
search-institutions "NAME" [OPTIONS]
  -f, --filter         Filter expression
  -s, --sort           Sort field
  -l, --limit          Results (default: 25)
```

**Examples:**
```bash
# Find institution by name
search-institutions "Stanford"

# Top US universities by output
search-institutions -f "country_code:us,type:education" -s "works_count:desc"

# Global South institutions
search-institutions -f "is_global_south:true" -s "cited_by_count:desc"
```

### 4. Group By (Aggregations)
```bash
group ENTITY_TYPE GROUP_FIELD [-f FILTERS]
```

**Examples:**
```bash
# Works by year
group works publication_year -f "authorships.institutions.id:I97018004"

# Works by institution
group works authorships.institutions.id -f "publication_year:2023"

# Works by OA status
group works oa_status -f "publication_year:2023"

# Works by topic
group works primary_topic.id -f "publication_year:2023"

# Authors by institution
group authors last_known_institutions.id -f "works_count:>10"
```

**Note:** The `group` command validates fields dynamically from the API. If you use an invalid field, you'll get a helpful error message with suggestions.

### 5. Get Single Entity
```bash
get ENTITY_TYPE ID
```

**Examples:**
```bash
# Get work by OpenAlex ID
get works W2741809807

# Get work by DOI
get works "doi:10.1038/nature12373"

# Get author by ORCID
get authors "orcid:0000-0001-6187-6610"

# Get institution by ROR
get institutions "ror:03vek6s52"
```

## Common Entity IDs

### Major Institutions
| Institution | OpenAlex ID |
|-------------|-------------|
| Stanford | I97018004 |
| MIT | I63966007 |
| Harvard | I136199984 |
| Oxford | I40120149 |
| Cambridge | I2799692020 |

### Major Funders
| Funder | OpenAlex ID |
|--------|-------------|
| NIH | F4320306076 |
| NSF | F4320306084 |
| European Commission | F4320306098 |
| Wellcome Trust | F4320332161 |

### Major Journals
| Journal | OpenAlex ID |
|---------|-------------|
| Nature | S137773608 |
| Science | S3880285 |
| PNAS | S125754415 |
| The Lancet | S49861241 |

## Output

Default output location:
```
/tmp/openalex-results/
├── works_QUERY_TIMESTAMP.parquet   # Binary, typed (for pandas/DuckDB)
├── works_QUERY_TIMESTAMP.jsonl     # Text, nested (for peeking)
├── authors_QUERY_TIMESTAMP.parquet
├── authors_QUERY_TIMESTAMP.jsonl
└── ...
```

JSON response includes:
- `total`: Total matching records
- `returned`: Records in this response
- `saved_to`: Path(s) to saved file(s)
- `query_params`: Parameters used in API call

## For Advanced Queries

### Local Documentation
- **API overview**: `~/Desktop/openalex-docs/01-api-overview.md`
- **Filtering**: `~/Desktop/openalex-docs/02-filtering.md`
- **Works fields**: `~/Desktop/openalex-docs/entity-works.md`
- **Authors fields**: `~/Desktop/openalex-docs/entity-authors.md`
- **Institutions fields**: `~/Desktop/openalex-docs/entity-institutions.md`

### Online Documentation
- **Full API Docs**: https://docs.openalex.org/
- **Entity Reference**: https://docs.openalex.org/api-entities/

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Rate limited (429) | Wait 1 minute, or add email for polite pool |
| Slow responses | Add `--email you@example.com` for polite pool |
| Too many results | Add filters to narrow down |
| Entity not found | Check ID format (use OpenAlex ID, DOI, ORCID, etc.) |
| Timeout | Add filters, reduce max_results |

## Limitations & Validation

This skill includes **dynamic parameter validation** that fetches valid fields from the OpenAlex API. Invalid parameters are rejected early with helpful error messages.

### group_by Restrictions

The `group` command only works with specific fields. **Deeply nested fields are NOT supported**:

| NOT Supported | Why |
|---------------|-----|
| `grants.funder` | Too deeply nested |
| `grants.award_id` | Too deeply nested |
| `referenced_works` | List field |

**Supported fields include:** `publication_year`, `type`, `is_oa`, `oa_status`, `authorships.institutions.id`, `authorships.institutions.country_code`, `primary_topic.id`, etc.

To see all valid group_by fields, try an invalid field - the error message will list alternatives.

### select Restrictions

The `--select` parameter cannot include complex nested objects:

| NOT Supported | Why |
|---------------|-----|
| `grants` | Complex nested structure |
| `authorships` | Complex nested structure |
| `locations` | Complex nested structure |
| `abstract_inverted_index` | Very large object |

**Workaround:** Fetch full records without `--select` and filter/process client-side.

### Grant/Funder Analysis Limitations

OpenAlex does not support grouping works directly by funder. To analyze funding:

1. **Search funders directly:**
   ```bash
   search-funders "NSF" -l 10
   ```

2. **Filter works by funder:**
   ```bash
   search-works -f "funders.id:F4320306076" -m 1000
   ```

3. **Process results client-side** to aggregate by funder from the returned data.
