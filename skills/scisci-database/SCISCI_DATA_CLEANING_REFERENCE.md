# Science of Science Data Cleaning Pipeline Reference

A comprehensive guide for reusable data cleaning patterns extracted from faculty collaboration research pipelines.

---

## Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [Naming Conventions](#2-naming-conventions)
3. [Data Filtering Techniques](#3-data-filtering-techniques)
4. [Normalization Methods](#4-normalization-methods)
5. [Null Value Handling](#5-null-value-handling)
6. [Entity Matching & Validation](#6-entity-matching--validation)
7. [Name Disambiguation](#7-name-disambiguation)
8. [Feature Engineering Patterns](#8-feature-engineering-patterns)
9. [Quality Assurance](#9-quality-assurance)
10. [Reusable Code Templates](#10-reusable-code-templates)

---

## 1. Pipeline Overview

### Typical Workflow Sequence

```
00-* : Preprocessing (title/rank normalization)
01-* : Institution matching (cross-database alignment)
02-* : Author matching & disambiguation
03-* : Paper filtering (temporal, geographic, field constraints)
04-* : Feature engineering (author-level attributes)
05-* : Final aggregation (paper × field, author × paper)
99-* : Data validation & quality checks
```

### Key Data Sources in Science of Science

| Source | Purpose | Key Fields |
|--------|---------|------------|
| **AARC** | US faculty roster | PersonId, InstitutionId, FacultyTitle, RankTypeId |
| **Dimensions** | Publication metadata | doi, researcher_id, grid_id, citations |
| **ROR** | Organization registry | ROR ID, GRID ID, aliases, country |
| **OpenAlex** | Open bibliometric data | work_id, author_id, institution_id |

### Data Flow Pattern

```
Raw Faculty Data (AARC)
        ↓
Institution Matching (ROR + Dimensions API)
        ↓
Faculty-to-Researcher Matching (DOI → Name → Affiliation)
        ↓
Paper Filtering (Year, Geography, Field, Quality)
        ↓
Feature Enrichment (Gender, Rank, Citations, Novelty)
        ↓
Final Aggregation (Paper-level, Author-level tables)
```

---

## 2. Naming Conventions

### File Naming

```
{sequence}-{description}.ipynb           # Notebooks
{sequence}-{description}/{file}.parquet  # Intermediate outputs
```

### Column Naming

| Convention | Example | Usage |
|------------|---------|-------|
| snake_case | `researcher_id` | Standard columns |
| CamelCase | `PersonId`, `InstitutionId` | External source fields (AARC) |
| Prefixed | `AARC_PersonId`, `dim_researcher_id` | Source-specific columns |
| Suffixed | `_l0`, `_l1`, `_new` | Hierarchical levels |

### Variable Naming for Mappings

```python
# Dictionary naming: {source}_to_{target}
aarc_person_id_to_name = {}
dim_researcher_id_to_name = {}
grid_id_to_institution = {}

# DataFrame naming: df_{entity} or {entity}_{version}
df_faculty = pd.DataFrame()
papers_us_after_2011 = pd.DataFrame()
```

---

## 3. Data Filtering Techniques

### 3.1 Temporal Filtering

```python
# Year range filtering
papers = papers.filter('(year >= 2011) AND (year <= 2023)')

# Using pandas
papers = papers[papers.year.between(2011, 2023)]
```

### 3.2 Geographic Filtering

```python
# Filter by country (US domestic)
us_aff = {x: True for x in orgs[orgs['country_code'] == 'US'].id}

# Validate all authors have US affiliations
@udf(returnType=BooleanType())
def ValidPaper(authors):
    if len(authors) == 0:
        return False
    for author in authors:
        if author['researcher_id'] is None:
            return False
        if len(author['grid_ids']) == 0:
            return False
        for grid_id in author['grid_ids']:
            if us_aff.get(grid_id, False) == False:
                return False
    return True
```

### 3.3 Quality Thresholds

```python
# Minimum reference count (removes low-quality/non-research papers)
papers = papers[papers.num_references >= 5]

# Minimum paper count for author matching
if count_papers >= min_papers:  # typically min_papers=5
    if (count_0 == count_papers) and (count_1 < count_papers):
        return author_0
```

### 3.4 Field-Based Filtering

```python
# Define field inclusion/exclusion functions
def is_used(field_l0_name_new):
    return "Unused" not in field_l0_name_new

def is_biomedical(field_l0_name_new):
    return (("Biology" in field_l0_name_new) or
            ("Medicine" in field_l0_name_new)) and is_used(field_l0_name_new)

def is_non_biomedical(field_l0_name_new):
    return (("Biology" not in field_l0_name_new) and
            ("Medicine" not in field_l0_name_new) and
            is_used(field_l0_name_new))

# Apply field filter
papers = papers[papers["Field L0 Name New"].map(is_non_biomedical)]
```

### 3.5 Institution Allowlist Filtering

```python
# Create allowlist from matched institutions
general_allowed_grid_ids = final_mapping_general.grid_id.dropna().unique().tolist()
medical_allowed_grid_ids = final_mapping_medical.grid_id.dropna().unique().tolist()

# Filter papers to only include allowed institutions
def is_valid_paper(authors, allowed_grid_ids):
    for author in authors:
        for grid_id in author['grid_ids']:
            if grid_id not in allowed_grid_ids:
                return False
    return True
```

---

## 4. Normalization Methods

### 4.1 Name Normalization

```python
import re
from unidecode import unidecode

def format_name(name):
    """Remove non-alphabetic characters and convert to uppercase."""
    return re.sub(r'[^A-Za-z ]', '', unidecode(name).upper())

# Apply to create normalized full name
first_name_norm = df['first_name'].map(lambda x: format_name(x))
last_name_norm = df['last_name'].map(lambda x: format_name(x))
df['full_name'] = last_name_norm + ', ' + first_name_norm
```

### 4.2 DOI Normalization

```python
# Always lowercase DOIs for consistent matching
papers['doi'] = papers['doi'].str.lower()
publications['doi'] = publications['doi'].str.lower()
```

### 4.3 Text Cleaning for API Queries

```python
def keep_letters(s):
    """Keep only letters for affiliation search."""
    import re
    regex = re.compile('[^a-zA-Z]')
    return regex.sub(' ', s)

# Use in API queries
search_name = keep_letters(InstitutionName)
```

### 4.4 Field Code Normalization

```python
def integerize_fields(fields):
    """Convert pipe-separated field codes to integer list."""
    if fields is None:
        return []
    if type(fields) == str:
        if len(fields) > 0:
            fields = fields.split("|")
            fields = [int(i) for i in fields]
            return fields
    return []

papers["Field L0 Code"] = papers["field_l0"].map(integerize_fields)
```

---

## 5. Null Value Handling

### 5.1 Strategic Dropna

```python
# Drop rows missing critical identifiers
df = df.dropna(subset=['doi', 'researcher_id'])

# Drop rows missing matching keys
aarc_dim_matching = aarc_papers.dropna(subset=["doi", 'paper_id_dimensions', "ArticleMatchId"])
```

### 5.2 Default Value Dictionaries

```python
from collections import defaultdict

# Use defaultdict for safe lookups
dim_researcher_id_to_name = defaultdict(lambda: None) | (
    researchers
    .sort_values(by='full_name_length', ascending=False)
    .drop_duplicates(subset=['researcher_id'], keep='first')
    .set_index('researcher_id')['full_name'].to_dict()
)

# Access safely - returns None if key doesn't exist
name = dim_researcher_id_to_name[researcher_id]
```

### 5.3 Fill Missing Values

```python
# Fill citation counts with 0
for col in ["citation_3y", "citation_5y", "citation_10y", "citation_inf"]:
    paper_x_field[col] = paper_x_field[col].fillna(0)
```

### 5.4 Conditional Assignment with NA

```python
# Set NA for single-author papers (where multi-author metrics don't apply)
papers.loc[papers.num_pis == 1, 'multi_dep_pis'] = pd.NA
papers.loc[papers.num_pis == 1, 'multi_uni_pis'] = pd.NA
```

### 5.5 Progressive Filtering with NotNA Checks

```python
# Filter progressively, checking for valid data at each step
MatchedName2 = MatchedName2[~MatchedName2["grid_id"].isna()]
faculty_matched = all_faculty[all_faculty.researcher_id_dimensions.notna()]
```

---

## 6. Entity Matching & Validation

### 6.1 Multi-Source Institution Matching

```python
# Step 1: ROR API matching
r = requests.get(f'https://api.ror.org/organizations?affiliation={urllib.parse.quote(search_name)}')
return_df = pd.DataFrame(r.json()['items'])

# Step 2: Dimensions API matching
url = 'extract_affiliations(json=[{}])'.format(','.join(json_list))
results = requests.post('https://app.dimensions.ai/api/dsl.json', data=url, headers=headers)

# Step 3: Cross-validate matches
both_mapped = dim_ror_mapping.dropna(subset=['dimensions_id', 'ror_id'])
agreements = (both_mapped['dimensions_id'] == both_mapped['ror_id']).sum()

# Step 4: Keep only agreed matches (or fallback to one source)
final_mapping = pd.concat([
    dim_ror_mapping[(dim_ror_mapping.dimensions_id == dim_ror_mapping.ror_id)],
    dim_ror_mapping[dim_ror_mapping.ror_id.isna() & dim_ror_mapping.dimensions_id.notna()]
])
```

### 6.2 Match Quality Criteria

```python
# Filter by match type and score
exact_match = MatchedName2.matching_type == 'EXACT'
chosen_match = MatchedName2.chosen == True
high_score_match = MatchedName2.score == 1.0

MatchedName2 = pd.concat([
    MatchedName2[exact_match],
    MatchedName2[chosen_match],
    MatchedName2[high_score_match]
])
```

### 6.3 Parent Organization Resolution

```python
# Build parent organization hierarchy
parent_orgs_dict = defaultdict(lambda: []) | dict(
    orgs[orgs.organization_parent_ids.map(lambda x: len(x) >= 1)]
    [['id', 'organization_parent_ids']].to_numpy().tolist()
)

def to_root_ids(ids):
    """Traverse to root organizations."""
    temp = []
    for id in ids:
        id_parent_orgs = parent_orgs_dict[id]
        if len(id_parent_orgs) > 0:
            temp += id_parent_orgs
        else:
            temp += [id]
    if tuple(temp) != tuple(ids):
        return temp
    return ids

orgs['root_ids'] = orgs.id.apply(lambda x: to_root_ids([x]))
```

### 6.4 Coverage Validation

```python
# Report match rates at each stage
print(f"Total institutions: {len(dim_ror_mapping)}")
print(f"Institutions with both mappings: {(~dim_ror_mapping['dimensions_id'].isna() & ~dim_ror_mapping['ror_id'].isna()).sum()}")
print(f"Institutions with only Dimensions mapping: {(~dim_ror_mapping['dimensions_id'].isna() & dim_ror_mapping['ror_id'].isna()).sum()}")
print(f"Institutions with only ROR mapping: {(dim_ror_mapping['dimensions_id'].isna() & ~dim_ror_mapping['ror_id'].isna()).sum()}")
print(f"Institutions with no mapping: {(dim_ror_mapping['dimensions_id'].isna() & dim_ror_mapping['ror_id'].isna()).sum()}")
```

---

## 7. Name Disambiguation

### 7.1 Three-Stage Matching Strategy

```
Stage 1: DOI Matching
    - Find papers shared between AARC and Dimensions by DOI
    - Count researcher_id occurrences per PersonId
    - Accept if one researcher appears in ALL papers (min 5 papers)

Stage 2: DOI + Name Matching
    - For ambiguous DOI matches, use name similarity
    - Filter candidates by paper co-occurrence threshold
    - Apply fuzzy matching (difflib, cutoff=0.8)

Stage 3: Affiliation + Name Matching
    - For unmatched faculty, search within same institution
    - Filter by name initial (first 2 chars)
    - Apply same_last_first matching
```

### 7.2 Name Similarity Functions

```python
from difflib import get_close_matches
import Levenshtein
import jellyfish

def most_similar_name(name, candid_ids, method="close_match", priority="order"):
    """Find most similar name from candidates."""
    candid_id_names = [(id, dim_researcher_id_to_name[id]) for id in candid_ids]
    candid_id_names = [(id, name) for id, name in candid_id_names if name is not None]

    if len(candid_id_names) == 0:
        return None

    candid_ids, candid_names = zip(*candid_id_names)

    if method == "close_match":
        result_names = get_close_matches(name, candid_names, cutoff=0.8)
        if not result_names:
            return None
        if priority == "order":
            result_id, result_name = [(id, n) for id, n in candid_id_names if n in result_names][0]
        else:
            result_name = result_names[0]
            result_id = candid_ids[candid_names.index(result_name)]
        return {"id": result_id, "name": result_name}

    elif method == "levenshtein":
        candid_sim_list = [
            1 - Levenshtein.distance(name, i) / max(len(name), len(i))
            for i in candid_names
        ]
        idx = np.argmax(candid_sim_list)
        return {"id": candid_ids[idx], "name": candid_names[idx]}

    elif method == "jaro_winkler":
        candid_sim_list = [jellyfish.jaro_winkler_similarity(name, i) for i in candid_names]
        idx = np.argmax(candid_sim_list)
        return {"id": candid_ids[idx], "name": candid_names[idx]}
```

### 7.3 Name Comparison Helpers

```python
def same_last_first_initial(name1, name2):
    """Check if same last name + same first initial."""
    name1 = str(name1).split(', ')
    name2 = str(name2).split(', ')

    l1, l2 = name1[0].split(' ')[0], name2[0].split(' ')[0]
    f1 = name1[1][:1] if len(name1) > 1 else ''
    f2 = name2[1][:1] if len(name2) > 1 else ''

    return (l1 == l2) and (f1 == f2)

def same_last_first(name1, name2):
    """Check if same last name + same first name (first word)."""
    name1 = str(name1).split(', ')
    name2 = str(name2).split(', ')

    l1, l2 = name1[0].split(' ')[0], name2[0].split(' ')[0]
    f1 = name1[1].split(' ')[0] if len(name1) > 1 else ''
    f2 = name2[1].split(' ')[0] if len(name2) > 1 else ''

    return (l1 == l2) and (f1 == f2)
```

### 7.4 Disambiguation Quality Validation

```python
# Validate name matching quality
for col, col_name in [("matching_aff_name", "Affiliation + Name"),
                       ("matching_doi_name", "DOI + Name"),
                       ("matching_doi", "DOI")]:
    idx = df[col].notna()
    df.loc[idx, f"{col}_same_last_first"] = df[idx].apply(
        lambda x: same_last_first(x["PersonName"], x[col]["name"]), axis=1)

    print(f"==================== {col_name} ====================")
    print(f"% of same last + first name: {df[f'{col}_same_last_first'].mean():.4%}")
```

---

## 8. Feature Engineering Patterns

### 8.1 Gender Inference

```python
import nomquamgender as nqg

model = nqg.NBGC()
nqg_df = model.annotate(full_name_list, as_df=True)

# Categorize: M (0-0.5), F (0.5-1), U (unknown)
author_info["gender"] = temp.nomquamgender.map(
    lambda x: "M" if (0 <= x < 0.5) else "F" if (0.5 <= x < 1) else "U"
)
```

### 8.2 Career Stage Tracking

```python
# Track best (highest) rank ever achieved
best_title_ever = defaultdict(lambda: {})

for v in aarc_faculty_dict.to_dict('records'):
    researcher_id = v['AARC_researcher_id_dimensions']
    for year in range(v['AARC_Year'], max_year + 1):
        # Promote to better rank if achieved
        best_rank_type_id = min([v["AARC_RankTypeIdYifan"]
                                  for v in best_title_ever[researcher_id].values()])
        best_title_ever[researcher_id][year] = [
            v for v in best_title_ever[researcher_id].values()
            if v["AARC_RankTypeIdYifan"] <= best_rank_type_id
        ][-1]
```

### 8.3 Collaboration Distance

```python
from geopy.distance import geodesic
from itertools import combinations

def distance(authors, aff="best"):
    """Calculate mean pairwise distance between author affiliations."""
    if len(authors) < 2:
        return None

    coordinates = []
    for author in authors:
        if aff == "best":
            aff_data = max(author["affiliations"],
                          key=lambda x: x["ranking_wapman_k_hunter_et_al"])
        else:
            aff_data = author["affiliations"][0]
        coordinates.append([aff_data["lat"], aff_data["lon"]])

    distances = [geodesic(c1, c2).kilometers
                 for c1, c2 in combinations(coordinates, 2)]
    return np.mean(distances)
```

### 8.4 Multi-Institution Detection

```python
from functools import reduce

# Check if PIs share common affiliations
BrainAff = papers.pis.map(lambda x: [set(i['grid_ids']) for i in x])
CommonBrainAff = BrainAff.map(lambda x: list(reduce(lambda a, b: set(a) & set(b), x)))

# Multi-university if no common affiliation
papers['multi_uni_pis'] = CommonBrainAff.map(lambda x: len(set(x)) == 0)
```

### 8.5 PI/Non-PI Classification

```python
# RankTypeId: 1=Full, 2=Associate, 3=Assistant Professor
def SelectPIs(authors):
    return list(filter(lambda x: x.get('AARC_RankTypeIdYifan', 9) in [1, 2, 3], authors))

def SelectNonPIs(authors):
    return list(filter(lambda x: x.get('AARC_RankTypeIdYifan', 9) not in [1, 2, 3], authors))

papers['pis'] = papers.authors.map(SelectPIs)
papers['nonpis'] = papers.authors.map(SelectNonPIs)
```

---

## 9. Quality Assurance

### 9.1 Coverage Reporting Template

```python
print("=" * 60)
print("DATA COVERAGE SUMMARY")
print("=" * 60)

coverage_metrics = {
    "AARC Article ID": df.aarc_article_id.notna().mean(),
    "Citation counts": (df.citation_inf > 0).mean(),
    "Disruptiveness (CD)": df.CDINF.notna().mean(),
    # ... add all metrics
}

for metric, coverage in coverage_metrics.items():
    print(f"  {metric:.<40} {coverage:>6.2%}")
```

### 9.2 Matching Summary Statistics

```python
print("====================Final Matching Results Summary====================")
print(f"# Total faculty= {all_faculty.PersonId.nunique()}")
print(f"# Total faculty with papers= {faculty_wp.PersonId.nunique()}")
print(f"# Matched faculty (within total faculty) = {faculty_matched.PersonId.nunique()}")
print(f"% Matched faculty = {faculty_matched.PersonId.nunique() / all_faculty.PersonId.nunique():.2%}")
```

### 9.3 Year Distribution Check

```python
# Verify temporal coverage
papers[["paper_id", "year"]].drop_duplicates().year.value_counts().sort_index()
```

### 9.4 Deduplication Validation

```python
# Check for duplicates after merging
print(f"Unique papers: {papers.id.nunique()}")
print(f"Total rows: {papers.shape[0]}")

# Remove duplicates keeping first
df = df.drop_duplicates(subset=['InstitutionId'], keep='first')
```

---

## 10. Reusable Code Templates

### 10.1 Standard Imports

```python
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_columns', 50)

import json, os, pickle as pkl
from unidecode import unidecode
from glob import glob
from collections import Counter, defaultdict
from itertools import product, combinations
from copy import deepcopy

from functools import partial
from tqdm import tqdm, trange
tqdm.pandas(ncols=100, mininterval=1)
tqdm, trange = partial(tqdm, ncols=100, mininterval=1), partial(trange, ncols=100, mininterval=1)
```

### 10.2 Nested Dict Flattening

```python
def flatten_dict(d, parent_key='', sep='.'):
    """Flatten nested dictionary with dot notation keys."""
    items = []
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            items.extend(flatten_dict(v, new_key, sep=sep).items())
    elif isinstance(d, list):
        for i, v in enumerate(d):
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            items.extend(flatten_dict(v, new_key, sep=sep).items())
    else:
        items.append((parent_key, d))
    return dict(items)

def flatten_records(data):
    """Convert list of nested dicts to flat DataFrame."""
    flat = [flatten_dict(record) for record in data]
    return pd.DataFrame(flat)
```

### 10.3 Manual Override Pattern

```python
# Define manual mappings for edge cases that fail automated matching
intitution_id_to_search_name = {
    4: "Albany Medical Center Hospital",
    97: "Indiana University Indianapolis",
    163: "Pennsylvania State University",
    168: "Purdue University System",
    # ... add more edge cases
}

# Apply manual overrides
for InstitutionId in df_uni_id_to_uni_name.InstitutionId:
    if InstitutionId in intitution_id_to_search_name:
        search_name = intitution_id_to_search_name[InstitutionId]
        # ... perform matching with override name
```

### 10.4 Progress-Enabled Operations

```python
# Use progress_apply for long operations
df['result'] = df.progress_apply(lambda row: expensive_function(row), axis=1)

# Use progress_map for series operations
df['result'] = df['column'].progress_map(expensive_function)
```

### 10.5 Spark Setup for Large Data

```python
conf_list = [
    ('spark.app.name', 'SciSci-Pipeline'),
    ('spark.local.dir', '/tmp/spark'),
    ('spark.driver.memory', '1024g'),
    ('spark.driver.maxResultSize', '200g'),
    ('spark.master', 'local[48]'),
    ('spark.sql.adaptive.enabled', 'true'),
    ('spark.sql.adaptive.coalescePartitions.enabled', 'true'),
]

from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession

conf = SparkConf().setAll(conf_list)
sc = SparkContext(conf=conf)
sc.setLogLevel('ERROR')
spark = SparkSession.builder.config(conf=conf).getOrCreate()
```

---

## Quick Reference Cheat Sheet

| Task | Pattern |
|------|---------|
| **DOI matching** | `papers['doi'].str.lower()` |
| **Name normalization** | `unidecode(name).upper()` + `re.sub(r'[^A-Za-z ]', '', ...)` |
| **Safe dict lookup** | `defaultdict(lambda: None) \| existing_dict` |
| **Filter by year** | `df[df.year.between(2011, 2023)]` |
| **Geographic filter** | Build allowlist dict, check membership |
| **Quality filter** | `df[df.num_references >= 5]` |
| **Name similarity** | `get_close_matches(name, candidates, cutoff=0.8)` |
| **PI classification** | `RankTypeIdYifan in [1, 2, 3]` |
| **Coverage check** | `df.column.notna().mean()` |
| **Explode by field** | `df.explode('field_list')` |
| **Track progress** | `df.progress_apply()` or `progress_map()` |

---

## Best Practices Summary

1. **Always normalize identifiers** (lowercase DOIs, standardized names) before matching
2. **Use multiple data sources** for validation (ROR + Dimensions for institutions)
3. **Apply cascading matching strategies** (DOI → DOI+Name → Affiliation+Name)
4. **Report coverage at each stage** to track data loss
5. **Use defaultdict** for safe lookups in large mappings
6. **Handle parent organizations** to capture institutional hierarchies
7. **Validate name matches** with same_last_first checks
8. **Set NA appropriately** for metrics that don't apply (single-author papers)
9. **Document manual overrides** for edge cases
10. **Use progress bars** for operations over 10k+ rows
