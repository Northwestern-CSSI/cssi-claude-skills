# OpenAlex Skills for Claude Code

This directory contains skills for interacting with the OpenAlex open research database via their REST API.

## Available Skills

### /openalex
Query the OpenAlex research database using natural language. Converts queries to API calls and returns formatted results.

### /openalex-search
Search for works, authors, institutions, sources, funders, and topics.

### /openalex-analytics
Get aggregated statistics and metrics using group_by functionality.

## How to Use

When a user invokes an OpenAlex skill, execute the appropriate command using the helper script.

### Command Execution Pattern
```bash
/opt/anaconda3/bin/conda run -n base python ~/.claude/skills/openalex/openalex_helper.py <command> [args]
```

### Available Commands

1. **search-works** - Search scholarly publications
   ```bash
   openalex_helper.py search-works "query" [--filter "expression"] [--sort "field:order"] [--limit N]
   ```

2. **search-authors** - Search researchers
   ```bash
   openalex_helper.py search-authors "name" [--filter "expression"] [--limit N]
   ```

3. **search-institutions** - Search universities and organizations
   ```bash
   openalex_helper.py search-institutions "name" [--filter "expression"] [--limit N]
   ```

4. **search-sources** - Search journals and repositories
   ```bash
   openalex_helper.py search-sources "name" [--filter "expression"] [--limit N]
   ```

5. **search-funders** - Search funding organizations
   ```bash
   openalex_helper.py search-funders "name" [--filter "expression"] [--limit N]
   ```

6. **search-topics** - Search research topics
   ```bash
   openalex_helper.py search-topics "query" [--filter "expression"] [--limit N]
   ```

7. **get** - Get a single entity by ID
   ```bash
   openalex_helper.py get works W2741809807
   openalex_helper.py get authors "orcid:0000-0001-6187-6610"
   ```

8. **group** - Aggregate entities by field
   ```bash
   openalex_helper.py group works publication_year --filter "authorships.institutions.id:I97018004"
   ```

9. **autocomplete** - Type-ahead search
   ```bash
   openalex_helper.py autocomplete works "machine"
   ```

## Natural Language to API Translation

When users make natural language requests, translate them to appropriate API queries:

| User Request | API Translation |
|--------------|-----------------|
| "Find recent papers on X" | `search-works "X" -f "publication_year:2023"` |
| "Papers from Harvard about Y" | `search-works "Y" -f "authorships.institutions.id:I136199984"` |
| "NIH-funded papers on Z" | `search-works "Z" -f "grants.funder:F4320306076"` |
| "Highly cited publications" | `-f "cited_by_count:>100" -s "cited_by_count:desc"` |
| "Open access papers" | `-f "is_oa:true"` |
| "Gold OA papers" | `-f "oa_status:gold"` |
| "Last 5 years" | `-f "publication_year:>2019"` |
| "Authors at MIT" | `search-authors -f "last_known_institutions.id:I63966007"` |

## Output Formatting

When displaying results to users:

1. **Works**: Show title, authors (first 3), year, journal, citations, DOI
2. **Authors**: Show name, affiliation, works count, h-index, ORCID
3. **Institutions**: Show name, country, type, works count
4. **Sources**: Show name, type, publisher, works count, OA status
5. **Aggregations**: Format as tables showing group counts

## Reference Documentation

Full API documentation is available at:
`~/Desktop/openalex-docs/`

Key files:
- `01-api-overview.md` - API basics and parameters
- `02-filtering.md` - Filter syntax and operators
- `05-grouping.md` - Aggregation with group_by
- `entity-*.md` - Individual entity field references

## Key Differences from Dimensions

| Feature | OpenAlex | Dimensions |
|---------|----------|------------|
| Authentication | Not required | Required (dimcli) |
| Query Language | REST API with filters | DSL query language |
| Rate Limit | 100K/day, 10/sec | Varies by plan |
| Pagination | Cursor-based | Skip-based |
| Entity Types | Works, Authors, Institutions, Sources, Funders, Topics | Publications, Grants, Patents, Clinical Trials, Researchers |
