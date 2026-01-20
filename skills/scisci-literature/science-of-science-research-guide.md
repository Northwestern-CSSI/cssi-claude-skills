# Science of Science Research Guide for LLM Agents

A comprehensive guide to reproduce the research workflow, question framing, and methodological conventions of leading science of science researchers: **Dashun Wang** (Northwestern), **James Evans** (UChicago), and **Fengli Xu** (Tsinghua).

---

## Table of Contents
1. [Research Philosophy & Mindset](#1-research-philosophy--mindset)
2. [Question Formulation Patterns](#2-question-formulation-patterns)
3. [Data Sources & Requirements](#3-data-sources--requirements)
4. [Methodological Conventions](#4-methodological-conventions)
5. [Narrative & Framing Strategies](#5-narrative--framing-strategies)
6. [Reproducible Workflow Template](#6-reproducible-workflow-template)
7. [Key Papers Reference](#7-key-papers-reference)

---

## 1. Research Philosophy & Mindset

### 1.1 The Science of Science Paradigm

The field applies **scientific methods to science itself**—treating scientific discovery, careers, and knowledge production as empirical phenomena amenable to quantitative analysis. The goal is to uncover "universal and domain-specific laws" governing scientific discovery.

**Core philosophical commitments:**
- **Mechanism over correlation**: The field seeks to understand *why* patterns exist, not just document them
- **Prediction as validation**: Good theories should enable predictive models (e.g., the Q-model for scientific impact)
- **Policy relevance**: Research should yield actionable insights for improving science (funding, team composition, career development)

### 1.2 The Essential Tension

A recurring theme across all three researchers is the **tension between opposing forces**:

| Conservative Pole | Innovative Pole | Key Paper |
|-------------------|-----------------|-----------|
| Large teams | Small teams | Wu, Wang, Evans (2019) |
| Tradition | Innovation | Foster, Rzhetsky, Evans (2015) |
| Hierarchical teams | Flat teams | Xu, Wu, Evans (2022) |
| Development | Disruption | Park, Leahey, Funk (2023) |
| Consolidation | Exploration | Evans (2008) |

**Research strategy**: Identify a dimension where science operates in tension, then quantify both poles and their consequences.

### 1.3 Counter-Intuitive Findings

High-impact science of science papers often challenge conventional wisdom:

- **Setbacks can help**: Early-career near-misses predict *better* long-term outcomes than narrow wins (Wang, Jones, Wang 2019)
- **More papers ≠ more progress**: Large fields show *slowed* canonical progress (Chu & Evans 2021)
- **Online access narrows science**: Electronic publication may *reduce* the diversity of cited work (Evans 2008)
- **Hot streaks are random**: The timing of a scientist's best work is randomly distributed within their career (Liu et al. 2018)

---

## 2. Question Formulation Patterns

### 2.1 The Puzzle-First Approach

Science of science research typically begins with an **empirical puzzle** that contradicts intuition or prevailing theory.

**Pattern**: Observation → Puzzle → Quantification → Mechanism

**Examples:**

| Observation | Puzzle | Research Question |
|-------------|--------|-------------------|
| Teams are growing in science | Is bigger always better? | How does team size affect the *character* of knowledge produced? |
| Scientists face career setbacks | Do setbacks doom careers? | What is the long-term effect of early-career failure? |
| Online access increases | Does more access = more diversity? | How does electronic publication affect citation patterns? |
| Some scientists have "hot streaks" | Are hot streaks predictable? | Is there a systematic pattern to career hot streaks? |

### 2.2 Question Templates for LLM Agents

When generating science of science research questions, use these templates:

1. **Trade-off Questions**: "What is the trade-off between [X] and [Y] in [domain]?"
   - Example: "What is the trade-off between team size and innovation?"

2. **Mechanism Questions**: "Why does [unexpected pattern] occur despite [expected outcome]?"
   - Example: "Why does online access narrow rather than broaden citations?"

3. **Temporal Questions**: "How does [phenomenon] evolve over [career/time/field growth]?"
   - Example: "How does citation impact evolve over a scientist's career?"

4. **Structural Questions**: "How does [organizational structure] affect [outcome]?"
   - Example: "How does team hierarchy affect innovation?"

5. **Counter-Matthew Questions**: "When does [disadvantage] lead to [advantage]?"
   - Example: "When does early-career setback predict future success?"

### 2.3 Characteristics of Good Questions

A science of science question should be:

- **Quantifiable**: Operationalizable with existing data sources
- **Scalable**: Testable across large populations (thousands to millions of observations)
- **Surprising**: Counter-intuitive or challenging conventional wisdom
- **Generalizable**: Applicable across multiple domains (science, patents, art)
- **Policy-relevant**: Implications for how science is organized or funded

---

## 3. Data Sources & Requirements

### 3.1 Primary Data Sources

| Source | Coverage | Key Uses | Access |
|--------|----------|----------|--------|
| **Web of Science (WoS)** | 19.9M+ articles, 1900-present | Citations, authorship, institutional affiliation | Subscription |
| **Dimensions** | 130M+ publications | Publications, grants, patents, clinical trials | API available |
| **OpenAlex** | 240M+ works | Open alternative to WoS/Scopus | Free API |
| **Microsoft Academic Graph (MAG)** | Discontinued but archived | Historical analyses | Archived datasets |
| **PubMed/MEDLINE** | Biomedical literature | Medical/life sciences | Free |
| **USPTO Patents** | 2.1M+ patents | Innovation, technology | Free |
| **arXiv** | 2M+ preprints | Physics, CS, math, econ | Free |
| **GitHub** | 16M+ projects | Software, collaboration | API |

### 3.2 Author Contribution Data

For studying team dynamics, authorship contribution statements are critical:

- **PNAS** (2003-present): Detailed author contributions
- **Nature** (2006-present): Author contribution statements
- **Science** (2018-present): Author roles
- **PLOS ONE** (2006-present): CRediT taxonomy

The Xu et al. (2022) "Flat Teams" paper used 89,575 self-reported contribution statements.

### 3.3 Career and Funding Data

| Source | Use Case | Example Paper |
|--------|----------|---------------|
| NIH Reporter | Grant applications, near-miss analysis | Wang, Jones, Wang (2019) |
| NSF Award Search | Federal funding patterns | Various |
| AARC Faculty Database | US faculty career trajectories | Your project |
| ROR (Research Organization Registry) | Institution matching | University matching |

### 3.4 Data Scale Requirements

Science of science papers typically analyze:

- **Papers**: 10,000 - 90 million
- **Patents**: 100,000 - 5 million
- **Authors/Scientists**: 1,000 - 10 million
- **Citations**: 100 million - 1 billion

**Rule of thumb**: If you can't analyze at least 10,000 observations, the study may lack power for the field's standards.

---

## 4. Methodological Conventions

### 4.1 Key Metrics

#### Citation-Based Metrics

| Metric | Formula/Description | Use Case | Reference |
|--------|---------------------|----------|-----------|
| **Citation count** | Raw count of citations | Basic impact | Standard |
| **Relative citation impact** | Citations normalized by field and year | Cross-field comparison | Standard |
| **h-index** | h papers with ≥h citations | Career impact | Hirsch (2005) |
| **D-score (Disruption)** | Measures "idea eclipse" - how paper overshadows its references | Innovation vs. development | Funk & Owen-Smith (2017) |
| **CD Index** | Characterizes citation network changes | Disruptiveness | Park et al. (2023) |

#### The D-Score (Disruption Index)

Central to much science of science research:

```
D = (n_i - n_j) / (n_i + n_j + n_k)

Where:
- n_i = papers citing the focal paper but NOT its references
- n_j = papers citing both the focal paper AND its references
- n_k = papers citing only the references, not the focal paper

D ranges from -1 (consolidating) to +1 (disruptive)
```

#### Career and Productivity Metrics

| Metric | Description | Reference |
|--------|-------------|-----------|
| **Q-factor** | Individual ability parameter, stable across career | Sinatra et al. (2016) |
| **L-ratio** | Leadership ratio = leaders / total team size | Xu et al. (2022) |
| **Hot streak detection** | Clustering of high-impact works | Liu et al. (2018) |

### 4.2 Causal Identification Strategies

Science of science research employs quasi-experimental designs:

#### Regression Discontinuity Design (RDD)
- **Use case**: Near-miss vs. narrow-win analyses
- **Example**: NIH grant threshold (Wang, Jones, Wang 2019)
- **Key**: Identify sharp threshold that creates "as-if random" assignment

#### Difference-in-Differences (DiD)
- **Use case**: Policy changes affecting science
- **Example**: Journal digitization effects (Evans 2008)
- **Key**: Compare treated vs. control groups before/after intervention

#### Within-Person Comparisons
- **Use case**: Controlling for individual ability
- **Example**: Same scientist on different team sizes (Wu, Wang, Evans 2019)
- **Key**: Use person fixed effects to isolate treatment effect

#### Propensity Score Matching
- **Use case**: Comparing similar units
- **Example**: Matching papers/authors on observable characteristics
- **Key**: Balance covariates between treatment and control

### 4.3 Network Analysis Methods

| Method | Application | Example |
|--------|-------------|---------|
| Citation networks | Knowledge flow, disruption | Wu et al. (2019) |
| Collaboration networks | Team formation, productivity | Most team science papers |
| Co-authorship networks | Career trajectories | Sinatra et al. (2016) |
| Semantic networks | Research strategy mapping | Foster et al. (2015) |

### 4.4 Robustness Check Conventions

Standard robustness checks in the field:

1. **Alternative metrics**: Test findings with different operationalizations
2. **Different time windows**: Vary citation windows (5-year, 10-year, etc.)
3. **Subgroup analyses**: Split by field, time period, institution type
4. **Placebo tests**: Apply method to contexts where null effect expected
5. **Sensitivity analyses**: Vary threshold/bandwidth in RDD
6. **Multiple fixed effects**: Person, year, field, institution
7. **Alternative samples**: Exclude top/bottom percentiles

---

## 5. Narrative & Framing Strategies

### 5.1 Paper Structure Pattern

Science of science papers follow a consistent arc:

1. **Hook**: Provocative opening that challenges conventional wisdom
2. **Puzzle**: State the empirical puzzle clearly
3. **Data**: Describe massive-scale data (impress with scope)
4. **Method**: Explain measurement and identification strategy
5. **Main Finding**: Present core result (often in Figure 1)
6. **Mechanisms**: Explore why the pattern exists
7. **Robustness**: Extensive supplementary analyses
8. **Implications**: Policy recommendations for science

### 5.2 Contrarian Positioning

High-impact papers often position against established views:

| Established View | Counter-Finding | Paper |
|------------------|-----------------|-------|
| "Rich get richer" (Matthew Effect) | Early setbacks can strengthen | Wang et al. (2019) |
| "More is better" for teams | Small teams disrupt more | Wu et al. (2019) |
| "Growth enables progress" | Large fields stagnate | Chu & Evans (2021) |
| "Online access democratizes" | Electronic narrows citations | Evans (2008) |

### 5.3 Figure Conventions

Key figures in science of science papers:

1. **The Main Effect Figure**: Shows primary finding with clear comparison
2. **The Mechanism Figure**: Explains why effect occurs
3. **The Robustness Figure**: Demonstrates effect holds across conditions
4. **The Network/Visualization**: Shows structure of scientific knowledge

### 5.4 Writing Style

- **Active voice**: "We find that..." not "It was found that..."
- **Quantitative precision**: "10.2% more likely" not "significantly more likely"
- **Hedged conclusions**: "Our findings suggest..." not "This proves..."
- **Policy framing**: End with implications for improving science

---

## 6. Reproducible Workflow Template

### 6.1 Step-by-Step Research Process

```
Phase 1: Question Development (Week 1-2)
├── Identify empirical puzzle from literature or observation
├── Frame as tension between opposing forces
├── Verify question is quantifiable with available data
└── Check novelty against existing literature

Phase 2: Data Assembly (Week 3-6)
├── Identify primary data source(s)
├── Define sample selection criteria
├── Extract relevant variables
├── Clean and validate data
├── Document sample sizes and coverage
└── Create descriptive statistics

Phase 3: Metric Construction (Week 7-8)
├── Operationalize key concepts
├── Calculate primary metrics (D-score, Q-factor, etc.)
├── Validate metrics against known benchmarks
└── Document measurement decisions

Phase 4: Analysis (Week 9-12)
├── Exploratory analysis and visualization
├── Main specification estimation
├── Mechanism exploration
├── Robustness checks (extensive)
└── Heterogeneity analyses

Phase 5: Writing (Week 13-16)
├── Draft main text (3,000-4,000 words for Nature/Science)
├── Prepare figures (4-6 main figures)
├── Write extensive Supplementary Information
└── Prepare data/code repository
```

### 6.2 Decision Tree for Research Design

```
Is the treatment randomly assigned?
├── Yes → Randomized experiment (rare in science of science)
└── No → Quasi-experimental design
    ├── Is there a sharp threshold?
    │   └── Yes → Regression Discontinuity Design
    ├── Is there a policy change affecting some units?
    │   └── Yes → Difference-in-Differences
    ├── Can you observe same unit in different conditions?
    │   └── Yes → Within-person/unit comparison
    └── None of above → Matching + selection correction
```

### 6.3 Checklist for LLM Agents

Before finalizing a science of science study design:

- [ ] **Scale**: Is sample size > 10,000 observations?
- [ ] **Surprise**: Does finding challenge conventional wisdom?
- [ ] **Mechanism**: Can you explain *why* the pattern exists?
- [ ] **Identification**: Is there a credible causal identification strategy?
- [ ] **Generalizability**: Does pattern hold across multiple domains/fields?
- [ ] **Robustness**: Are there at least 5 robustness checks planned?
- [ ] **Policy relevance**: Are there clear implications for science policy?
- [ ] **Data availability**: Can analysis be reproduced?

---

## 7. Key Papers Reference

### 7.1 Foundational Reviews

| Paper | Authors | Journal | Year | Key Contribution |
|-------|---------|---------|------|------------------|
| Science of Science | Fortunato, Bergstrom, Evans, Wang, et al. | Science | 2018 | Comprehensive field review |
| Metaknowledge | Evans & Foster | Science | 2011 | Defines metaknowledge research program |

### 7.2 Dashun Wang - Key Empirical Papers

| Paper | Coauthors | Journal | Year | Key Finding |
|-------|-----------|---------|------|-------------|
| Large teams develop, small teams disrupt | Wu, Evans | Nature | 2019 | Team size affects innovation character |
| Hot streaks in careers | Liu, Sinatra, et al. | Nature | 2018 | Hot streaks are universal, timing random |
| Quantifying individual scientific impact | Sinatra, Barabási, et al. | Science | 2016 | Q-factor model of impact |
| Early-career setback | Jones | Nat. Comm. | 2019 | Near-misses predict better long-term outcomes |
| Quantifying failure dynamics | Yin, Evans | Nature | 2019 | Failure dynamics across domains |

### 7.3 James Evans - Key Empirical Papers

| Paper | Coauthors | Journal | Year | Key Finding |
|-------|-----------|---------|------|-------------|
| Tradition and Innovation | Foster, Rzhetsky | ASR | 2015 | Risk-reward trade-off in research strategies |
| Electronic Publication Narrowing | - | Science | 2008 | Online access narrows citations |
| Slowed canonical progress | Chu | PNAS | 2021 | Large fields show stagnation |
| Industry and Academic Science | - | AJS | 2010 | Industry induces narrower research |

### 7.4 Fengli Xu - Key Empirical Papers

| Paper | Coauthors | Journal | Year | Key Finding |
|-------|-----------|---------|------|-------------|
| Flat Teams Drive Innovation | Wu, Evans | PNAS | 2022 | Hierarchy reduces innovation |
| Urban Growth from Mobility | et al. | Nat. Comp. Sci. | 2021 | Mobility patterns predict urban growth |
| Mobility and Inequality | et al. | Nat. Hum. Behav. | 2022 | Mobility reveals urban inequality |

### 7.5 Related Important Papers

| Paper | Authors | Journal | Year | Key Finding |
|-------|---------|---------|------|-------------|
| Papers becoming less disruptive | Park, Leahey, Funk | Nature | 2023 | Declining disruptiveness over time |
| Disruption metric | Funk & Owen-Smith | Mgmt. Sci. | 2017 | Introduced D-score |

---

## Appendix A: Common Pitfalls to Avoid

1. **Confusing correlation with causation**: Always address selection and endogeneity
2. **Ignoring field heterogeneity**: Effects may differ across disciplines
3. **Citation window sensitivity**: Results may depend on citation window choice
4. **Survivorship bias**: Only observing "successful" scientists/papers
5. **Measurement error in author disambiguation**: Name disambiguation is imperfect
6. **Temporal confounds**: Secular trends may drive apparent effects
7. **Multiple testing**: Many robustness checks require correction

## Appendix B: Code and Data Conventions

- **Data repositories**: Harvard Dataverse, Zenodo, OSF
- **Code languages**: Python (pandas, networkx), R (tidyverse), Stata
- **Reproducibility**: All code should be documented and shareable
- **Package for bibliometric analysis**: `metaknowledge` (Python), `bibliometrix` (R)

---

*Guide compiled from analysis of 15+ key papers across three leading science of science researchers. Last updated: January 2026.*

**Sources:**
- [Dashun Wang Publications](https://www.dashunwang.com/academic-articles)
- [James Evans at UChicago](https://sociology.uchicago.edu/directory/james-evans)
- [Fengli Xu Publications](https://fenglixu.github.io/publications/)
- [Science of Science Review (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5949209/)
