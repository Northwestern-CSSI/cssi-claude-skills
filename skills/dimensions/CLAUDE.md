# Dimensions DSL Skills for Claude Code

This directory contains skills for interacting with the Dimensions research database via their DSL (Domain Specific Language) API.

## Available Skills

### /dimensions or /dims
Search the Dimensions research database using natural language. Converts queries to DSL and returns formatted results.

### /dimensions-search
Search for publications, grants, patents, clinical trials, datasets, and more.

### /dimensions-analytics
Get aggregated statistics and metrics from the research database.

### /dimensions-expert
Find research experts based on topics or abstract text.

### /dimensions-classify
Classify research text into standard taxonomies (FOR, SDG, HRCS, etc.).

### /dimensions-extract
Extract entities (concepts, affiliations, grants) from text.

## How to Use

When a user invokes a Dimensions skill, execute the appropriate command using the helper script.

### Command Execution Pattern
```bash
/opt/anaconda3/bin/conda run -n base python ~/.claude/skills/dimensions/dimensions_helper.py <command> [args]
```

### Available Commands

1. **search-publications** - Search scholarly publications
   ```bash
   dimensions_helper.py search-publications "query" [--filters "where clause"] [--fields "field+list"] [--limit N]
   ```

2. **search-grants** - Search research grants
   ```bash
   dimensions_helper.py search-grants "query" [--filters "where clause"] [--limit N]
   ```

3. **extract-concepts** - Extract concepts from text
   ```bash
   dimensions_helper.py extract-concepts "text" [--scores]
   ```

4. **classify** - Classify text into research categories
   ```bash
   dimensions_helper.py classify --title "title" --abstract "abstract" [--system FOR_2020]
   ```

5. **identify-experts** - Find research experts
   ```bash
   dimensions_helper.py identify-experts -c concept1 concept2 [--filters "where clause"] [--limit N]
   ```

6. **describe** - Get metadata about a data source
   ```bash
   dimensions_helper.py describe publications
   ```

7. **raw** - Execute raw DSL query
   ```bash
   dimensions_helper.py raw "search publications for \"AI\" return publications limit 5"
   ```

## Natural Language to DSL Translation

When users make natural language requests, translate them to appropriate DSL queries:

| User Request | DSL Translation |
|--------------|-----------------|
| "Find recent papers on X" | `search publications for "X" where year >= 2022` |
| "Papers from Harvard about Y" | `search publications for "Y" where research_orgs.name~"Harvard"` |
| "NIH-funded grants for Z" | `search grants for "Z" where funders.acronym="NIH"` |
| "Highly cited publications" | `where times_cited >= 100` |
| "Open access papers" | `where open_access in ["gold", "green_pub"]` |
| "Last 5 years" | `where year >= 2021` |

## Output Formatting

When displaying results to users:

1. **Publications**: Show title, authors (first 3), year, journal, citations, DOI
2. **Grants**: Show title, funder, amount, start date, PI name
3. **Experts**: Show name, affiliation, publication count, expertise score
4. **Aggregations**: Format as tables or charts where appropriate

## Reference Documentation

Full DSL documentation is available at:
`~/Desktop/dimensions-dsl-docs/`

Key files:
- `03-query-syntax.md` - Query language reference
- `06-data-sources-overview.md` - Available data sources
- `07-examples.md` - Query examples
- `datasource-*.md` - Individual source field references
