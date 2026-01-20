# Science of Science Agent Integration Protocol

**Purpose:** Define the workflow sequence, handoff documents, quality gates, and coordination protocols for the three specialized Science of Science agents.

---

## Agent Overview

| Agent | Primary Role | Key Outputs |
|-------|--------------|-------------|
| **LiteratureSpecialist** | Research question formulation, publication standards | Research question, hypothesis, paper outline |
| **DatabaseSpecialist** | Data extraction, cleaning, entity resolution | Clean dataset, validation report |
| **AnalyticsSpecialist** | Statistical analysis, visualization | Regression tables, figures, robustness report |

---

## Workflow Sequence

### Standard Research Workflow

```
Phase 1: Question Development
├── LiteratureSpecialist formulates research question
├── Applies 5 quality gates
├── Identifies essential tension
└── Produces: Research Question Specification

Phase 2: Data Preparation
├── DatabaseSpecialist receives specification
├── Extracts data using Dimensions/OpenAlex skills
├── Cleans, matches, engineers features
└── Produces: Clean Dataset + Validation Report

Phase 3: Analysis
├── AnalyticsSpecialist receives clean data
├── Runs descriptive analysis
├── Estimates regression models
├── Conducts robustness checks
└── Produces: Tables, Figures, Findings Report

Phase 4: Integration
├── LiteratureSpecialist receives results
├── Interprets findings through mechanism lens
├── Frames narrative for publication
└── Produces: Paper Draft / Narrative Summary
```

### Workflow Diagram

```
┌─────────────────────┐
│ LiteratureSpecialist│
│  (Question Phase)   │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Research     │
    │ Question     │
    │ Specification│
    └──────┬───────┘
           │
           ▼
┌─────────────────────┐
│ DatabaseSpecialist  │
│  (Data Phase)       │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Clean Dataset│
    │ + Validation │
    │ Report       │
    └──────┬───────┘
           │
           ▼
┌─────────────────────┐
│ AnalyticsSpecialist │
│  (Analysis Phase)   │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Tables       │
    │ Figures      │
    │ Findings     │
    └──────┬───────┘
           │
           ▼
┌─────────────────────┐
│ LiteratureSpecialist│
│  (Integration Phase)│
└─────────────────────┘
```

---

## Handoff Documents

### Handoff 1: LiteratureSpecialist → DatabaseSpecialist

**Document: Research Question Specification**

```markdown
## Research Question
[Clear, one-sentence research question]

## Hypothesis
[Specific, testable hypothesis with mechanism]

## Required Variables

### Outcome Variables
- [Variable 1]: [Description, expected source]
- [Variable 2]: [Description, expected source]

### Treatment Variable
- [Variable]: [Description, operationalization]

### Control Variables
- [Variable 1]: [Description, source]
- [Variable 2]: [Description, source]

### Moderating Variables
- [Variable 1]: [Description, how to construct]
- [Variable 2]: [Description, how to construct]

## Data Requirements
- **Granularity**: [paper-level / author-level / team-level]
- **Time Range**: [YEAR_START] - [YEAR_END]
- **Field Scope**: [All fields / specific fields]
- **Geographic Scope**: [All / US only / specific countries]
- **Minimum Sample Size**: [N observations]

## Quality Requirements
- **Entity Resolution**: [Required confidence level]
- **Coverage Threshold**: [Minimum coverage for key variables]

## Falsification Criteria
- [What would invalidate the hypothesis]
```

### Handoff 2: DatabaseSpecialist → AnalyticsSpecialist

**Document: Data Manifest**

```markdown
## Dataset Information
- **File Path**: [path/to/dataset.parquet]
- **Total Observations**: [N]
- **Date Range**: [YEAR_START] - [YEAR_END]
- **Last Updated**: [DATE]

## Variable Descriptions

| Variable | Type | Description | Source | Coverage |
|----------|------|-------------|--------|----------|
| [var1] | [type] | [description] | [source] | [X]% |
| [var2] | [type] | [description] | [source] | [X]% |

## Data Quality Summary

### Row Counts by Stage
- Raw input: [N]
- After cleaning: [N]
- After matching: [N]
- Final output: [N]

### Coverage Report
- DOI matched: [X]%
- Author disambiguated: [X]%
- Institution matched: [X]%
- Citation data available: [X]%

### Null Rates (Critical Variables)
- [var1]: [X]%
- [var2]: [X]%

## Known Limitations
- [Limitation 1]
- [Limitation 2]

## Validation Checks Passed
- [ ] No unexpected duplicates
- [ ] Null rates within threshold
- [ ] Distributions reasonable
- [ ] Entity matching validated
```

### Handoff 3: AnalyticsSpecialist → LiteratureSpecialist

**Document: Results Package**

```markdown
## Key Findings

### Main Effect
[One-sentence summary of main finding with coefficient and significance]

### Effect Size
[Interpretation of practical significance]

### Mechanism Evidence
[What the heterogeneity analyses reveal about mechanism]

## Results Summary

### Baseline Regression
| Outcome | Coefficient | SE | p-value | N |
|---------|-------------|-----|---------|---|
| [outcome1] | [coef] | [se] | [p] | [n] |

### Heterogeneity by Team Type
| Subgroup | Coefficient | 95% CI | Pattern |
|----------|-------------|--------|---------|
| Lab | [coef] | [CI] | [pattern] |
| Non-lab | [coef] | [CI] | [pattern] |

### Heterogeneity by Team Size
[Summary of pattern across team sizes]

## Robustness Summary
- [ ] Effect holds across all 9 outcome metrics
- [ ] Effect holds across team types
- [ ] Effect holds across time periods
- [ ] Alternative specifications confirm finding

## Figures Provided
1. [filename1.pdf] - [description]
2. [filename2.pdf] - [description]

## Tables Provided
1. [filename1.tex] - [description]
2. [filename2.tex] - [description]

## Anomalies or Concerns
- [Any unexpected findings or concerns]
```

---

## Quality Gates

### Gate 1: Question Gate (LiteratureSpecialist)

Before proceeding to data collection:

- [ ] **Quantifiable**: Can be measured with available data
- [ ] **Scalable**: Pattern testable at scale (>10,000 observations)
- [ ] **Surprising**: Contradicts conventional wisdom
- [ ] **Generalizable**: Not limited to narrow context
- [ ] **Policy-Relevant**: Informs real decisions

**Pass Condition:** All 5 criteria met

### Gate 2: Data Gate (DatabaseSpecialist)

Before proceeding to analysis:

- [ ] **Completeness**: All required variables present
- [ ] **Coverage**: Key variables have >95% coverage
- [ ] **Quality**: Null rates <5% on critical variables
- [ ] **Integrity**: No unexpected duplicates
- [ ] **Documentation**: All transformations logged

**Pass Condition:** All 5 criteria met

### Gate 3: Analysis Gate (AnalyticsSpecialist)

Before finalizing results:

- [ ] **Convergence**: All models converged successfully
- [ ] **Specification**: FE and clustering properly implemented
- [ ] **Robustness**: At least 3 alternative specifications tested
- [ ] **Heterogeneity**: Team type and team size splits examined
- [ ] **Documentation**: All specifications logged

**Pass Condition:** All 5 criteria met

### Gate 4: Narrative Gate (LiteratureSpecialist)

Before finalizing paper:

- [ ] **Alignment**: Narrative matches statistical findings
- [ ] **Mechanism**: Clear explanation of why pattern exists
- [ ] **Limitations**: Key limitations acknowledged
- [ ] **Policy**: Actionable implications stated
- [ ] **Novelty**: Contribution to literature clear

**Pass Condition:** All 5 criteria met

---

## Error Handling Protocols

### Data Quality Failure

If DatabaseSpecialist cannot meet data quality thresholds:

1. **Document the gap**: Specific variables and coverage levels
2. **Propose alternatives**: Different data sources or operationalizations
3. **Consult LiteratureSpecialist**: Revise research question if needed
4. **Proceed with caveats**: If gap is acceptable, document in limitations

### Analysis Failure

If AnalyticsSpecialist finds null or unexpected results:

1. **Verify data quality**: Re-check with DatabaseSpecialist
2. **Check specification**: Ensure correct model specification
3. **Explore heterogeneity**: Effect may exist in subgroups
4. **Report honestly**: Null findings are valid findings
5. **Consult LiteratureSpecialist**: Revise hypothesis if warranted

### Robustness Failure

If findings don't hold across specifications:

1. **Identify pattern**: Which specifications fail?
2. **Diagnose cause**: Why does specification matter?
3. **Report honestly**: Document which results are fragile
4. **Scope claims**: Limit claims to robust findings

---

## Coordination Patterns

### Parallel Execution

Some tasks can be executed in parallel:

```
LiteratureSpecialist: Literature review
        ↓ (provides variable requirements)
DatabaseSpecialist: Data extraction ──┬── AnalyticsSpecialist: Setup code
        ↓                             │
DatabaseSpecialist: Data cleaning ────┘
        ↓
AnalyticsSpecialist: Analysis
```

### Iterative Refinement

Complex projects may require iteration:

```
Iteration 1: Exploratory
├── Quick data pull
├── Preliminary analysis
└── Refine hypothesis

Iteration 2: Confirmatory
├── Full data preparation
├── Complete analysis
└── Robustness checks

Iteration 3: Publication
├── Final data validation
├── Polished figures
└── Paper draft
```

---

## Skill Usage Guidelines

### When to Use Dimensions Skill

- Querying publication metadata at scale
- Finding grant and funding information
- Getting citation metrics
- Finding clinical trial data

### When to Use OpenAlex Skill

- Broad bibliometric queries
- Open access data needs
- Institution and author coverage

### Cross-Skill Validation

When entities appear in both sources:
1. Query both sources
2. Compare results
3. Flag discrepancies
4. Use agreement for high-confidence matches

---

## Communication Templates

### Status Update

```
Agent: [Name]
Phase: [Current phase]
Status: [On track / Blocked / Complete]
Progress: [X]% complete

Completed:
- [Task 1]
- [Task 2]

In Progress:
- [Task 3]

Blocked:
- [Issue] - Need [resolution]

Next Steps:
- [Next task]
```

### Quality Gate Report

```
Gate: [Gate Name]
Status: [PASS / FAIL / PARTIAL]

Criteria:
- [Criterion 1]: [PASS/FAIL] - [Notes]
- [Criterion 2]: [PASS/FAIL] - [Notes]

Action Required:
- [If failed, what needs to happen]
```

---

## File Organization

All project files should follow this structure:

```
project/
├── data/
│   ├── raw/                 # Original data (never modify)
│   ├── interim/             # Intermediate processing
│   └── processed/           # Final clean data
├── code/
│   ├── R/                   # R modules
│   └── notebooks/           # Analysis notebooks
├── output/
│   ├── pdf/                 # Figures
│   ├── tex/                 # Tables
│   └── reports/             # Validation reports
├── docs/
│   ├── specifications/      # Handoff documents
│   └── notes/               # Working notes
└── agent_instructions/      # This folder
    ├── SCISCI_AGENT_LITERATURE_SPECIALIST.md
    ├── SCISCI_AGENT_DATABASE_SPECIALIST.md
    ├── SCISCI_AGENT_ANALYTICS_SPECIALIST.md
    └── SCISCI_AGENT_INTEGRATION_PROTOCOL.md
```

---

## Quick Reference: Agent Responsibilities

| Task | Primary Agent | Supporting Agent |
|------|---------------|------------------|
| Research question | LiteratureSpecialist | - |
| Hypothesis | LiteratureSpecialist | - |
| Data requirements | LiteratureSpecialist | DatabaseSpecialist |
| Data extraction | DatabaseSpecialist | - |
| Data cleaning | DatabaseSpecialist | - |
| Entity matching | DatabaseSpecialist | - |
| Feature engineering | DatabaseSpecialist | LiteratureSpecialist |
| Descriptive analysis | AnalyticsSpecialist | - |
| Regression analysis | AnalyticsSpecialist | - |
| Visualization | AnalyticsSpecialist | LiteratureSpecialist |
| Robustness checks | AnalyticsSpecialist | - |
| Interpretation | LiteratureSpecialist | AnalyticsSpecialist |
| Narrative framing | LiteratureSpecialist | - |
