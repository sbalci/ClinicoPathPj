# Correlation matrix — pyjjcorrmat, 0.3.20 core

Open **Stats Plots Py → Associations → Correlation matrix (core)**. Select two to twenty
numeric variables; each row must represent an independent observation. Do not treat
multiple specimens per patient as independent evidence without a separate clustered method.
Import `data/python_correlation_examples.csv` for a small synthetic example.

## Supported calculations

Pearson is the default; Spearman uses average ranks with asymptotic two-sided p values,
including tied observations. Small-sample exact/permutation inference is not supplied.
Coefficients and tests require at least three complete, nonconstant pairs. Fewer pairs and
constant variables have blank coefficients/p values and a native reason, never an invented zero.
Infinite input values are rejected. Empty input is an error; all-missing cohorts produce
explicit unavailable results and a warning.

Default listwise deletion uses one complete-case cohort across all selected variables.
Pairwise mode uses each pair's observed rows and reports its own n and excluded count.
The summary also reports the common complete-case n. Pairwise matrices may not be positive
semidefinite; do not silently pass them to covariance-dependent modelling as valid covariance matrices.

Holm adjustment is the default. Bonferroni, Benjamini–Hochberg and no adjustment are supported.
The family contains every unique unordered selected-variable pair; unavailable tests remain
NA but still count in the family size. Validation uses `p.adjust(..., n=number_of_pairs)`.
Diagonal self-correlations are not tested or included in the adjustment family; diagonals
without enough nonconstant data remain blank. At most 190 unique comparisons are generated.

Pearson intervals use the standard Fisher-z approximation at the supplied confidence
proportion (0.95 default), requiring n>=4. They are pointwise and unadjusted. No Spearman
intervals are reported in this core. At n=3 Pearson coefficients/p values can appear while
interval cells remain blank. Perfect correlations use limiting endpoints. A confidence
interval or p value does not establish clinical utility or causality.

## Native output and interaction

The native table contains unique pairs, n, exclusions, coefficient, available limits,
raw/adjusted p values and unavailable reasons. The static Python-rendered matrix has a
symmetric numeric scale and a native color legend; diagonal values anchor it at [-1,1]
when defined. Gray cells indicate unavailable estimates, not zero relationships.
The existing heatmap renderer follows the jamovi palette endpoints. A fully unavailable
matrix remains gray; no estimates are fabricated to make a plot.

The optional local matrix uses a fixed blue/white/orange scale and cell focus/click
inspection of the same results. Labels are literal escaped data. It makes no network or
native-option calls. Selection does not change cohorts or recalculate statistics. Native
options control methods and missingness. A linked raw-data scatterplot, saved selections,
cluster inference and correlation clustering are not included in this first core.

## Baseline features deliberately omitted

Robust/winsorized and Bayesian correlations, BF/posterior outputs, partial correlations,
grouped matrices, Spearman uncertainty, Hochberg/Hommel/BY adjustment and full umbrella
plot styling remain outside this core. The frozen R baseline/provenance remains unchanged
in the registry. This port advances a planned target to partial; it is not full parity.
The established production R implementation is unchanged.

## Evidence

Six Python tests cover hand-calculated r/p values, ties, missingness, unavailable results,
comparison-family behavior, invalid/empty inputs and escaped labels. 406 native R assertions
pass: 16 method × missingness × adjustment configurations compare to base `cor.test()` and
`p.adjust()`, plus valid→incomplete→valid clearing and native raster rendering.
The DOM harness passes literal labels, keyboard/click inspection, n/exclusions, undefined
cells and no native dispatch. The complete stable Python suite passes 253 tests; the
module compiler and generator freshness checks pass. All 17 extracted packaged-runtime
cases pass, including correlation and packaged source/template integrity (see
[package report](validation-exports/python-correlation-0.3.20-package.json)).

An initial broader run overlapped dependency refresh during packaging and failed in 13
Pillow imports. The complete suite was rerun after the build finished and passed; avoid
concurrent dependency refresh and test execution. The preview PNG is a Python-rendered
artifact, not evidence of native desktop export.

Native desktop installation, valid reruns, save/fresh-engine reopen and native export for
this new entry remain pending. Additional platforms, repeated-patient inference and clinical
review are not qualified by these numerical/software checks.
