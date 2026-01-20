# CSSI Claude Skills

Specialized Claude Code skills for **Science of Science** research at the [Center for Science of Science & Innovation (CSSI)](https://www.kellogg.northwestern.edu/research/science-of-science.aspx) at Northwestern University.

## Skills Overview

### Research Database Skills

| Skill | Description |
|-------|-------------|
| **[dimensions](./skills/dimensions)** | Query the Dimensions database (140M+ publications, 8M+ grants, 60M+ patents). Natural language to DSL translation, auto-saved results as parquet + jsonl. |
| **[openalex](./skills/openalex)** | Query the OpenAlex open database (240M+ works, 90M+ authors, 109K institutions). No authentication required. |

### Science of Science Research Skills

| Skill | Description |
|-------|-------------|
| **[scisci-analytics](./skills/scisci-analytics)** | Statistical analysis, regression with fixed effects, visualization, and robustness checks for SciSci research. Includes forest plots, trend lines, and publication-ready figures. |
| **[scisci-database](./skills/scisci-database)** | Data extraction, cleaning, entity resolution (author disambiguation, institution matching), and quality validation pipelines. |
| **[scisci-literature](./skills/scisci-literature)** | Research question formulation, hypothesis framing, publication standards for top venues (Nature/Science/PNAS), and narrative design. |

### Utility Skills

| Skill | Description |
|-------|-------------|
| **[prompt-refiner](./skills/prompt-refiner)** | Improve instruction clarity using the CLEAR framework (Context, Limits, Examples, Action, Result). |
| **[claude-config-backup](./skills/claude-config-backup)** | Backup and migrate Claude Code configurations, settings, and skills. |

## Installation

### Via Claude Code CLI

```bash
# Add the CSSI marketplace
/plugin marketplace add Northwestern-CSSI/cssi-claude-skills

# Browse and install skills
/plugin install cssi-skills@Northwestern-CSSI/cssi-claude-skills
```

### Manual Installation

Clone directly to your Claude skills directory:

```bash
git clone https://github.com/Northwestern-CSSI/cssi-claude-skills.git ~/.claude/skills/cssi
```

Or copy specific skills:

```bash
git clone https://github.com/Northwestern-CSSI/cssi-claude-skills.git /tmp/cssi-skills
cp -r /tmp/cssi-skills/skills/dimensions ~/.claude/skills/
cp -r /tmp/cssi-skills/skills/openalex ~/.claude/skills/
```

## Quick Start Examples

### Query Research Databases

```bash
# Search Dimensions for recent AI papers
/dimensions search-publications "artificial intelligence" -f "year >= 2023" -m 1000

# Aggregate publications by funder
/dimensions aggregate publications "quantum computing" -F funders -a "citations_avg"

# Search OpenAlex for works by institution
/openalex search works "machine learning" --filter "institutions.ror:https://ror.org/000e0be47"
```

### Science of Science Analysis Workflow

```bash
# 1. Extract and clean bibliometric data
/scisci-database prepare dataset with author disambiguation and institution matching

# 2. Run regression analysis with fixed effects
/scisci-analytics run regression with author, field, and year fixed effects

# 3. Generate publication-ready figures
/scisci-analytics create forest plot for coefficient comparison

# 4. Frame findings for publication
/scisci-literature frame results using counter-intuitive pattern for Nature submission
```

## Requirements

| Skill | Requirements |
|-------|--------------|
| **dimensions** | Dimensions API access. Run `pip install dimcli && dimcli --init` to configure. |
| **openalex** | None (open database, no authentication required) |
| **scisci-*** | Python with pandas, numpy, scipy. R with fixest for regressions. |

## Skill Structure

Each skill follows the Agent Skills standard:

```
skill-name/
├── SKILL.md          # Main instructions with YAML frontmatter
├── CLAUDE.md         # Optional: additional context for Claude
├── helper.py         # Optional: helper scripts
└── tests/            # Optional: test files
```

## About CSSI

The **Center for Science of Science & Innovation** at Northwestern University's Kellogg School of Management advances understanding of how science works and how to accelerate scientific discovery. Our research examines the structure and dynamics of science, including:

- Team science and collaboration patterns
- Research impact and citation dynamics
- Funding and resource allocation
- Innovation and knowledge diffusion

## Contributing

To add or modify skills:

1. Fork this repository
2. Create or modify skills in the `skills/` directory
3. Follow the SKILL.md format with YAML frontmatter
4. Submit a pull request

## License

Apache 2.0
