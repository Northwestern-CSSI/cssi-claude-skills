# Science of Science Analysis & Visualization Reference

A comprehensive guide for reusable analysis patterns, regression strategies, and visualization conventions extracted from shared leadership research pipelines.

---

## Table of Contents

1. [Project Architecture](#1-project-architecture)
2. [Configuration Management](#2-configuration-management)
3. [Data Preparation Pipeline](#3-data-preparation-pipeline)
4. [Regression Analysis Framework](#4-regression-analysis-framework)
5. [Visualization System](#5-visualization-system)
6. [Output Management](#6-output-management)
7. [Reusable Code Templates](#7-reusable-code-templates)
8. [Best Practices](#8-best-practices)

---

## 1. Project Architecture

### Recommended Directory Structure

```
project/
├── R/
│   ├── 00_config.R        # Centralized configuration
│   ├── 01_libraries.R     # Package management
│   ├── 02_utils.R         # Utility functions
│   ├── 03_plotting.R      # Visualization functions
│   ├── 04_data.R          # Data loading/prep
│   └── 05_regression.R    # Regression functions
├── 01_publication.Rmd     # Descriptive analysis
├── 02_impact.Rmd          # Regression analysis
├── 03_organization.Rmd    # Heterogeneity analysis
├── output/
│   ├── pdf/               # Publication figures
│   ├── png/               # Web figures
│   ├── tex/               # LaTeX tables
│   └── docx/              # Word documents
└── data/
```

### Module Loading Pattern

```r
# Standard Rmd setup block
source(file.path("R", "00_config.R"))
source(file.path("R", "01_libraries.R"))
source(file.path("R", "02_utils.R"))
source(file.path("R", "03_plotting.R"))
source(file.path("R", "04_data.R"))
source(file.path("R", "05_regression.R"))

# Set output subdirectory for this analysis
set_output_subdir("impact")  # or "publication", "organization"
```

---

## 2. Configuration Management

### Centralized Parameters

```r
# ============================================================================
# CONFIGURATION FILE (00_config.R)
# ============================================================================

# Path configuration (relative for portability)
PROJECT_DIR <- getwd()
DATA_DIR <- file.path(dirname(dirname(PROJECT_DIR)), "data")
OUTPUT_DIR <- file.path(PROJECT_DIR, "output")

# Analysis parameters
YEAR_START <- 2011
YEAR_END <- 2023
YEAR_RANGE <- YEAR_START:YEAR_END

# Thresholds for binary outcomes
HIT_THRESHOLD <- 0.95       # Top 5% citation
NOVELTY_THRESHOLD <- 0.95   # Top 5% novelty
TEAM_SIZE_CAP <- 8          # Group 8+ as "8+"

# Publication types to include
PUB_TYPES_INCLUDE <- c("article", "chapter", "proceeding", "monograph")

# Field classifications
FIELDS_EXCLUDE <- c("Unused")
FIELDS_BIOMEDICAL <- c("Medicine", "Biology")
BIOMEDICAL_YEAR_START <- 2021  # Special handling for biomedical data

FIELDS_NONLAB <- c(
  "Mathematics",
  "Social and Political Sciences",
  "Economics and Management"
)

# Regression settings
FE_VARS <- c("author_id", "field", "year")  # Fixed effects
CLUSTER_VAR <- "author_id"                   # Clustering variable

# Random seed for reproducibility
RANDOM_SEED <- 42
set.seed(RANDOM_SEED)
```

### Color Palette Design

```r
# Semantic color palettes for field types
# Blues for non-lab/social sciences
PALETTE_BLUES <- c("#08306B", "#08519C", "#2171B5")

# Yellows/oranges for lab sciences
PALETTE_YELLOWS <- c(
  "#662506", "#993404", "#CC4C02", "#EC7014",
  "#FE9929", "#FEC44F", "#FDBF11", "#F59E0B", "#D97706"
)

# Team type colors (consistent across all figures)
PALETTE_TEAM <- c(
  "lab" = "#EC7014",
  "non-lab" = "#08519C"
)
```

### Figure Size Presets

```r
FIG_SIZES <- list(
  small  = list(width = 6, height = 6),
  medium = list(width = 8, height = 6),
  large  = list(width = 12, height = 8),
  wide   = list(width = 12, height = 6),
  tall   = list(width = 8, height = 10),
  square = list(width = 8, height = 8)
)

FIG_DPI <- 1200  # Publication quality
```

---

## 3. Data Preparation Pipeline

### One-Stop Data Loading

```r
#' Load, clean, and prepare data for analysis
#'
#' @param path Path to data file
#' @param include_org Include organizational context variables
#' @param min_authors Minimum authors (1=all, 2=teams only)
#' @return Prepared dataframe
prepare_analysis_data <- function(path = DATA_FILE,
                                  include_org = FALSE,
                                  min_authors = 1) {

  df <- load_raw_data(path) |>
    clean_dataset() |>
    dplyr::mutate(field = factor(field)) |>
    create_analysis_vars(min_authors = min_authors)

  if (include_org) {
    df <- create_org_context_vars(df)
  }

  # Attach color palette as attribute
  attr(df, "palette_fields") <- create_field_palette(df)
  df
}
```

### Variable Construction Patterns

```r
#' Create analysis variables with within-group percentile ranks
create_analysis_vars <- function(df, year_range = YEAR_RANGE, min_authors = 1) {

  df |>
    dplyr::filter(year %in% year_range) |>
    dplyr::filter(number_of_author >= min_authors) |>

    # Percentile ranks WITHIN year-field groups
    dplyr::group_by(year, field) |>
    dplyr::mutate(
      cit_pct = dplyr::percent_rank(citation_inf),
      nov_pct = dplyr::percent_rank(x10_pct_commonness),
      atyp_pct = dplyr::percent_rank(-atyp_comb_10_pct),  # Note: negative for atypicality
      dis_pct = dplyr::percent_rank(cdinf)
    ) |>
    dplyr::ungroup() |>

    # Binary outcomes and categorical variables
    dplyr::mutate(
      # Team size grouping (cap at 8+)
      number_of_author2 = ifelse(
        number_of_author >= TEAM_SIZE_CAP,
        paste0(TEAM_SIZE_CAP, "+"),
        as.character(number_of_author)
      ),
      # Treatment indicator
      multi_pi = ifelse(number_of_pi == 1, 0, 1),
      # Binary outcomes
      cit_bin = ifelse(cit_pct >= HIT_THRESHOLD, 1, 0),
      nov_bin = ifelse(x10_pct_commonness >= NOVELTY_THRESHOLD, 1, 0),
      atyp_bin = ifelse(atyp_comb_10_pct < 0, 1, 0),
      dis_bin = ifelse(cdinf > 0, 1, 0),
      # Team type classification
      team = ifelse(field %in% FIELDS_NONLAB, "non-lab", "lab")
    )
}
```

### Handling Multi-Field Papers

```r
#' Randomly assign single field per paper (for regression)
#' Ensures each paper appears once to avoid double-counting
assign_random_field <- function(df, seed = RANDOM_SEED) {
  set.seed(seed)

  df |>
    dplyr::group_by(paper_id) |>
    dplyr::mutate(random_field = sample(unique(field), 1)) |>
    dplyr::ungroup() |>
    dplyr::filter(field == random_field) |>
    dplyr::select(-random_field)
}
```

---

## 4. Regression Analysis Framework

### Standard Model Specification

```r
# Fixed effects regression with:
# - Author fixed effects (controls for individual ability)
# - Field fixed effects (controls for field-level differences)
# - Year fixed effects (controls for temporal trends)
# - Clustered standard errors at author level

#' Run baseline regression
#'
#' @param df Analysis dataframe
#' @param outcome Outcome variable name
#' @param treatment Treatment variable (default "multi_pi")
#' @param binary Use logit (TRUE) or OLS (FALSE)
#' @param include_teamsize Include team size controls
#' @param split_var Optional variable to split by (for heterogeneity)
run_regression <- function(df,
                           outcome,
                           treatment = "multi_pi",
                           binary = TRUE,
                           include_teamsize = TRUE,
                           split_var = NULL,
                           include_field_fe = TRUE) {

  # Control variables
  controls <- "mean_affiliation_ranking_author_best + log1p(collaboration_distance_km_author_best)"

  # Fixed effects
  fe <- if (include_field_fe) "author_id + field + year" else "author_id + year"

  # Build formula
  rhs <- if (include_teamsize) {
    paste(treatment, "+ factor(number_of_author2) +", controls)
  } else {
    paste(treatment, "+", controls)
  }

  fml <- as.formula(paste(outcome, "~", rhs, "|", fe))
  split_fml <- if (!is.null(split_var)) as.formula(paste("~", split_var)) else NULL

  # Choose estimator
  if (binary) {
    fixest::feglm(fml, data = df, split = split_fml,
                  cluster = CLUSTER_VAR, family = binomial())
  } else {
    fixest::feols(fml, data = df, split = split_fml,
                  cluster = CLUSTER_VAR)
  }
}
```

### Outcome Metric Specifications

```r
#' Standard outcome definitions for Science of Science
default_outcomes <- function() {
  list(
    # Binary outcomes (hit papers)
    "Citation (top 5%)" = list(var = "cit_bin", binary = TRUE),
    "Atypicality (bin)" = list(var = "atyp_bin", binary = TRUE),
    "Novelty (top 10%)" = list(var = "nov_bin", binary = TRUE),
    "Disruption (bin)" = list(var = "dis_bin", binary = TRUE),

    # Continuous outcomes (percentile ranks)
    "Citation pct" = list(var = "cit_pct", binary = FALSE),
    "Atypicality pct" = list(var = "atyp_pct", binary = FALSE),
    "Novelty pct" = list(var = "nov_pct", binary = FALSE),
    "Disruption pct" = list(var = "dis_pct", binary = FALSE),
    "Textual novelty" = list(var = "textual_novelty", binary = FALSE)
  )
}
```

### Heterogeneity Analysis Patterns

```r
# Split by team size
run_by_teamsize <- function(df, outcome, treatment = "multi_pi", binary = TRUE) {
  run_regression(
    df = df,
    outcome = outcome,
    treatment = treatment,
    binary = binary,
    include_teamsize = FALSE,  # Don't control for what we split by
    split_var = "number_of_author2"
  )
}

# Split by team type (lab vs non-lab)
run_by_teamtype <- function(df, outcome, treatment = "multi_pi", binary = TRUE) {
  run_regression(
    df = df,
    outcome = outcome,
    treatment = treatment,
    binary = binary,
    split_var = "team"
  )
}

# Split by field (remove field FE when splitting by field)
run_by_field <- function(df, outcome, treatment = "multi_pi", binary = TRUE) {
  run_regression(
    df = df,
    outcome = outcome,
    treatment = treatment,
    binary = binary,
    include_field_fe = FALSE,
    split_var = "field"
  )
}
```

### Batch Regression Pattern

```r
#' Run all 9 outcome regressions
run_all_outcomes <- function(df, treatment = "multi_pi", outcomes = NULL, split_var = NULL) {

  outcomes <- outcomes %||% default_outcomes()
  models <- list()

  for (name in names(outcomes)) {
    outcome_info <- outcomes[[name]]
    cat("Running:", name, "\n")

    tryCatch({
      models[[name]] <- run_regression(
        df = df,
        outcome = outcome_info$var,
        treatment = treatment,
        binary = outcome_info$binary,
        split_var = split_var
      )
    }, error = function(e) {
      cat("  Error:", e$message, "\n")
    })
  }

  models
}
```

---

## 5. Visualization System

### Unified Theme

```r
#' Publication-quality theme for all figures
theme_sl <- function(base_size = 15, legend_position = "none") {
  ggplot2::theme_minimal(base_size = base_size) +
    ggplot2::theme(
      # Legend
      legend.position = legend_position,
      legend.direction = "horizontal",
      # Axes
      axis.text = ggplot2::element_text(face = "bold", color = "black"),
      axis.title = ggplot2::element_text(face = "bold"),
      axis.title.x = ggplot2::element_text(hjust = 0.5),
      axis.title.y = ggplot2::element_text(hjust = 0.5),
      axis.ticks.y = ggplot2::element_blank(),
      # Facets
      strip.background = ggplot2::element_blank(),
      strip.text = ggplot2::element_text(face = "bold"),
      # Title
      plot.title = ggplot2::element_text(face = "bold"),
      plot.caption = ggplot2::element_text(hjust = 0, face = "italic"),
      # Grid
      panel.grid.minor = ggplot2::element_blank()
    )
}
```

### Trend Line Plots

```r
#' Plot trends by field with end-labels
plot_trend_by_field <- function(df, y_var, y_label, palette = NULL, show_labels = TRUE) {

  p <- ggplot2::ggplot(df, ggplot2::aes(x = year, y = {{ y_var }}, color = field)) +
    ggplot2::geom_line(linewidth = 1) +
    ggplot2::geom_point(size = 2.5, color = "white") +
    ggplot2::geom_point(ggplot2::aes(color = field), size = 1.5) +
    ggplot2::scale_x_continuous(
      breaks = seq(YEAR_START, YEAR_END, by = 3),
      limits = c(YEAR_START, if (show_labels) YEAR_END + 12 else YEAR_END)
    ) +
    ggplot2::labs(y = y_label, x = "", color = "") +
    theme_sl()

  if (show_labels) {
    p <- p +
      ggrepel::geom_text_repel(
        data = \(d) dplyr::filter(d, year == max(year)),
        ggplot2::aes(label = field),
        direction = "y",
        nudge_x = 1,
        hjust = 0,
        segment.size = 0.3,
        size = TEXT_SIZE_MEDIUM,
        fontface = "bold",
        show.legend = FALSE
      )
  }

  if (!is.null(palette)) {
    p <- p + ggplot2::scale_color_manual(values = palette)
  }

  p
}
```

### Coefficient Forest Plots

```r
#' Extract coefficients from split regression models
extract_split_coefs <- function(models, coef_name = "multi_pi") {
  extract_one <- function(model) {
    s <- summary(model)
    est <- s$coeftable[coef_name, 1]
    se <- s$coeftable[coef_name, 2]
    data.frame(
      coef = est,
      se = se,
      ci_low = est - 1.96 * se,
      ci_high = est + 1.96 * se
    )
  }

  df <- do.call(rbind, lapply(models, extract_one))
  df$sample <- trimws(sub(".*:(.*)$", "\\1", names(models)))
  df
}

#' Forest plot for regression coefficients
plot_coef_forest <- function(models, coef_name = "multi_pi",
                             title = NULL, xlab = "Coefficient (95% CI)") {

  df <- if (is.data.frame(models)) models else extract_split_coefs(models, coef_name)

  ggplot2::ggplot(df, ggplot2::aes(x = sample, y = coef)) +
    ggplot2::geom_hline(yintercept = 0, linetype = "dashed", color = "gray50") +
    ggplot2::geom_linerange(
      ggplot2::aes(ymin = ci_low, ymax = ci_high),
      linewidth = 3, alpha = 0.5
    ) +
    ggplot2::geom_point(size = 3, shape = 21, fill = "black", color = "white") +
    ggplot2::labs(x = "", y = xlab, title = title) +
    ggplot2::coord_flip() +
    theme_sl()
}
```

### Delta Arrow Plots (Effect Visualization)

```r
#' Plot delta arrows showing change from baseline
plot_delta_arrow <- function(df, delta_var, group_var = NULL,
                             facet_var = NULL, metric_labels = NULL) {

  p <- ggplot2::ggplot(df) +
    # Shaded triangle area
    ggplot2::geom_area(
      data = \(d) {
        d |>
          dplyr::mutate(.id = dplyr::row_number()) |>
          tidyr::expand_grid(x = c(1, 2)) |>
          dplyr::mutate(y = ifelse(x == 1, 0, {{ delta_var }}))
      },
      ggplot2::aes(x = x, y = y, group = .id),
      alpha = 0.30, fill = "grey80", color = NA
    ) +
    # Arrow showing direction
    ggplot2::geom_segment(
      ggplot2::aes(x = 1, y = 0, xend = 2, yend = {{ delta_var }}),
      arrow = grid::arrow(length = grid::unit(0.05, "npc"),
                          type = "closed", angle = 15),
      linewidth = 0.9, alpha = 0.9
    ) +
    ggplot2::geom_hline(yintercept = 0, linewidth = 1, linetype = 2, alpha = 0.7) +
    ggplot2::scale_y_continuous(labels = scales::percent) +
    ggplot2::scale_x_continuous(breaks = c(1, 2), labels = c("Single PI", "Multi PI")) +
    ggplot2::labs(y = expression(Delta ~ "(Multi - Single)"), x = "") +
    theme_sl()

  if (!is.null(facet_var)) {
    if (!is.null(metric_labels)) {
      p <- p + ggplot2::facet_wrap(facet_var, scales = "free",
                                   labeller = ggplot2::as_labeller(metric_labels))
    } else {
      p <- p + ggplot2::facet_wrap(facet_var, scales = "free")
    }
  }

  p
}
```

### Radial Gauge Plots

```r
#' Radial delta gauge (speedometer-style)
plot_delta_radial <- function(df, x_limits = c(-0.06, 0.06), metric_labels = NULL) {

  p <- ggplot2::ggplot(df, ggplot2::aes(x = delta)) +
    ggplot2::geom_hline(yintercept = 0.9, linewidth = 1, color = "#EBEBEB") +
    ggplot2::geom_segment(
      ggplot2::aes(xend = delta, y = 0, yend = 1),
      color = "black",
      arrow = ggplot2::arrow(length = ggplot2::unit(0.1, "npc"),
                             type = "closed", angle = 15),
      linewidth = 0.9, alpha = 0.9
    ) +
    ggplot2::geom_vline(xintercept = 0, linetype = "dashed", linewidth = 1) +
    ggplot2::geom_point(
      ggplot2::aes(x = 0, y = 0),
      size = 3, fill = "black", shape = 21, color = "white", stroke = 1
    ) +
    ggplot2::coord_radial(
      theta = "x",
      start = -pi/2,
      end = pi/2,
      expand = FALSE
    ) +
    ggplot2::scale_x_continuous(
      limits = x_limits,
      labels = scales::label_percent(accuracy = 0.1)
    ) +
    ggplot2::scale_y_continuous(limits = c(0, 1.15)) +
    ggplot2::labs(x = expression(Delta ~ "(Multi PI - Single PI)"), y = NULL) +
    theme_sl() +
    ggplot2::theme(
      axis.text.y = ggplot2::element_blank(),
      axis.ticks.y = ggplot2::element_blank()
    )

  if (!is.null(metric_labels)) {
    p <- p + ggplot2::facet_grid(~metric, labeller = ggplot2::as_labeller(metric_labels))
  } else {
    p <- p + ggplot2::facet_grid(~metric)
  }

  p
}
```

### Trajectory/Arrow Plots

```r
# Example: Team size vs PI trajectory over time
df_arrows <- df_wide |>
  dplyr::group_by(field) |>
  dplyr::arrange(year, .by_group = TRUE) |>
  dplyr::summarise(
    year_start = first(year),
    team_start = first(team_size),
    PIs_start = first(PIs),
    year_end = last(year),
    team_end = last(team_size),
    PIs_end = last(PIs),
    .groups = "drop"
  )

ggplot() +
  geom_abline() +  # Reference line
  geom_segment(
    data = df_arrows,
    aes(x = team_start, y = PIs_start, xend = team_end, yend = PIs_end, colour = field),
    arrow = arrow(type = "closed", length = unit(0.3, "cm"), angle = 15),
    linewidth = 1
  ) +
  geom_point(
    data = df_points |> filter(year == YEAR_START),
    aes(x = team_size, y = PIs, fill = field),
    size = 3, shape = 21, color = "white"
  )
```

---

## 6. Output Management

### Save Figure Function

```r
#' Save figure to PDF (and optionally PNG)
save_figure <- function(plot, filename,
                        width = FIG_SIZES$small$width,
                        height = FIG_SIZES$small$height,
                        dpi = FIG_DPI,
                        save_png = FALSE,
                        subdir = NULL) {

  # Use global OUTPUT_SUBDIR if not specified
  subdir <- subdir %||% OUTPUT_SUBDIR

  # Build paths with subdirectory
  pdf_dir <- if (nchar(subdir) > 0) file.path(OUTPUT_PDF_DIR, subdir) else OUTPUT_PDF_DIR

  # Ensure directory exists
  if (!dir.exists(pdf_dir)) dir.create(pdf_dir, recursive = TRUE)

  # Save PDF (publication quality)
  pdf_path <- file.path(pdf_dir, paste0(filename, ".pdf"))
  ggplot2::ggsave(
    filename = pdf_path,
    plot = plot,
    device = grDevices::cairo_pdf,
    width = width,
    height = height,
    units = "in"
  )
  cat("Saved:", pdf_path, "\n")

  invisible(plot)
}
```

### Save Regression Table

```r
#' Save regression table to LaTeX or Word
save_reg_table <- function(models, filename, format = "tex", subdir = NULL) {

  subdir <- subdir %||% OUTPUT_SUBDIR

  filepath <- switch(format,
    "tex" = {
      tex_dir <- if (nchar(subdir) > 0) file.path(OUTPUT_TEX_DIR, subdir) else OUTPUT_TEX_DIR
      if (!dir.exists(tex_dir)) dir.create(tex_dir, recursive = TRUE)
      path <- file.path(tex_dir, paste0(filename, ".tex"))
      modelsummary::modelsummary(models, output = path, stars = TRUE, fmt = smart_sci)
      path
    },
    "docx" = {
      path <- file.path(OUTPUT_DOCX_DIR, paste0(filename, ".docx"))
      ft <- flextable::autofit(modelsummary::modelsummary(models, output = "flextable"))
      doc <- officer::body_add_flextable(officer::read_docx(), value = ft)
      print(doc, target = path)
      path
    }
  )

  cat("Saved:", filepath, "\n")
  invisible(NULL)
}
```

---

## 7. Reusable Code Templates

### Standard Rmd Chunk Options

```r
knitr::opts_chunk$set(
  echo = TRUE,
  message = FALSE,
  warning = FALSE,
  fig.width = 8,
  fig.height = 6
)
```

### Package Loading Pattern

```r
#' Install and load packages
load_packages <- function(packages) {
  for (pkg in packages) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
      install.packages(pkg, dependencies = TRUE)
    }
    suppressPackageStartupMessages(library(pkg, character.only = TRUE))
  }
}

# Package categories
data_packages <- c("dplyr", "tidyr", "tidyverse", "arrow", "janitor")
viz_packages <- c("ggplot2", "ggpubr", "ggtext", "ggrepel", "scales")
stat_packages <- c("fixest")
report_packages <- c("modelsummary", "flextable")
```

### Formatting Utilities

```r
#' Smart scientific notation
smart_sci <- function(x, digits_fixed = 4, digits_sci = 3) {
  dplyr::case_when(
    is.na(x) ~ NA_character_,
    abs(x) >= 1e-4 & abs(x) < 1e5 ~ formatC(x, format = "f", digits = digits_fixed),
    TRUE ~ formatC(x, format = "e", digits = digits_sci)
  )
}

#' Abbreviate large numbers
format_abbrev <- function(x) {
  dplyr::case_when(
    abs(x) >= 1e9 ~ paste0(round(x / 1e9, 1), "B"),
    abs(x) >= 1e6 ~ paste0(round(x / 1e6, 1), "M"),
    abs(x) >= 1e3 ~ paste0(round(x / 1e3, 1), "K"),
    TRUE ~ as.character(round(x))
  )
}
```

### Metric Label Definitions

```r
# Consistent labels across all analyses
metric_labels <- c(
  cit_bin = "Citation (top 5%)",
  cit_pct = "Citation pct",
  atyp_bin = "Atypicality (bin)",
  atyp_pct = "Atypicality pct",
  nov_bin = "Novelty (top 10%)",
  nov_pct = "Novelty pct",
  dis_bin = "Disruption (bin)",
  dis_pct = "Disruption pct",
  textual_novelty = "Textual novelty"
)
```

---

## 8. Best Practices

### Regression Design

| Principle | Implementation |
|-----------|----------------|
| **Control for individual ability** | Author fixed effects |
| **Control for field differences** | Field fixed effects |
| **Control for temporal trends** | Year fixed effects |
| **Account for clustering** | Cluster SEs at author level |
| **Handle multi-field papers** | Randomly assign single field |
| **Binary vs continuous outcomes** | Use `feglm` vs `feols` |

### Visualization Principles

| Principle | Implementation |
|-----------|----------------|
| **Consistent styling** | Use `theme_sl()` everywhere |
| **Semantic colors** | Blues for non-lab, oranges for lab |
| **Direct labeling** | Use `geom_text_repel` instead of legends |
| **Publication quality** | cairo_pdf at 1200 DPI |
| **Organized output** | Subdirectories by analysis type |

### Reproducibility Checklist

1. **Set random seed** at config level (`set.seed(RANDOM_SEED)`)
2. **Use relative paths** for portability
3. **Document thresholds** (hit paper = top 5%, etc.)
4. **Version control** the R modules and Rmd files
5. **Include session info** at end of each Rmd

### Analysis Workflow

```
1. DESCRIPTIVE
   - Distribution plots (treemap, stacked area)
   - Trend lines by field
   - Raw difference calculations

2. BASELINE REGRESSION
   - Full sample with all controls
   - Both binary and continuous outcomes
   - Forest plot of coefficients

3. HETEROGENEITY ANALYSIS
   - Split by team size
   - Split by team type (lab/non-lab)
   - Split by field
   - Remove appropriate FE when splitting

4. OUTPUT
   - Save figures to PDF
   - Save tables to LaTeX
   - Document all specifications
```

---

## Quick Reference Cheat Sheet

| Task | R Code |
|------|--------|
| **Load data** | `DF <- prepare_analysis_data(min_authors = 2)` |
| **Get palette** | `palette_fields <- get_field_palette(DF)` |
| **Run regression** | `run_regression(df, "cit_bin", binary = TRUE)` |
| **Split by team size** | `run_by_teamsize(df, "cit_bin")` |
| **Split by team type** | `run_by_teamtype(df, "cit_bin")` |
| **Forest plot** | `plot_coef_forest(models, "multi_pi")` |
| **Trend plot** | `plot_trend_by_field(df, count, "N papers")` |
| **Save figure** | `save_figure(p, "filename", width = 8, height = 6)` |
| **Save table** | `save_reg_table(models, "table_name")` |

---

## Integration with Data Cleaning Reference

This document complements `SCISCI_DATA_CLEANING_REFERENCE.md` which covers:
- Data filtering and normalization
- Entity matching and disambiguation
- Null value handling
- Quality validation

Together they provide a complete pipeline from raw data to publication-ready results.
