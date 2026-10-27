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

Holm adjustment remains the default. From 0.3.23, Bonferroni, Hochberg, Hommel,
Benjamini–Hochberg (BH), Benjamini–Yekutieli (BY) and no adjustment are supported.
Holm and Bonferroni control family-wise error under arbitrary dependence. Hochberg and
Hommel require independent or suitably positively dependent tests. BH controls false
discovery rate under independence or suitable positive dependence; BY allows arbitrary
dependence. Correlations sharing markers can have dependent tests: adjustment choice
does not remove the need to consider these assumptions. These adjustments apply only
to p-values, never to the displayed confidence intervals.
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

From 0.3.21 the local matrix has one remembered Tab stop. Arrow keys move across
cells without wrapping; Home/End select the first/last cell of a row, and Ctrl/Command
with Home/End select the first/last matrix cell. Enter/Space retain native button
activation; Tab and Shift+Tab leave the matrix. Modified arrow shortcuts remain available
to the host. Focus updates only local inspection. Three DOM fixtures cover 2, 3 and
20 variables, including unavailable cells. Native keyboard qualification of this extension
was completed on macOS in 0.3.22 after repairing host-event propagation;
see [keyboard finding and retest](python-correlation-keyboard-validation.md). The
0.3.20 numerical/export evidence retains its original scope.

The optional local matrix uses a fixed blue/white/orange scale and cell focus/click
inspection of the same results. Labels are literal escaped data. It makes no network or
native-option calls. Selection does not change cohorts or recalculate statistics. Native
options control methods and missingness. A linked raw-data scatterplot, saved selections,
cluster inference and correlation clustering are not included in this first core.

## Baseline features deliberately omitted

Robust/winsorized and Bayesian correlations, BF/posterior outputs, partial correlations,
grouped matrices, Spearman uncertainty and full umbrella
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

macOS arm64 jamovi 28.13 passed GUI installation, a fresh-engine run, Pearson/listwise
and pairwise/Spearman reruns, keyboard cell inspection, OMV save/reopen in a second fresh
engine, subsequent Pearson recalculation and native PNG export. The saved fixture retains
Spearman/pairwise options; the exported image depicts that configuration.
See [desktop evidence](python-correlation-desktop-validation.md). Additional platforms,
repeated-patient inference and clinical review remain unqualified.

## Expanded adjustment evidence — 0.3.23

The independent `tools/correlation-adjustment-reference.R` script constructs 1,533
base-R `p.adjust()` fixtures without loading ClinicoPathPj. The Python comparator
`tools/check-correlation-adjustments.py` agrees for all seven methods: empty/all-missing
families, zero/one and extreme p-values, ties, reordered tests and sizes through 190.
Unavailable planned tests remain unavailable while counting in the family size. Hommel
uses p=1 for unavailable family members, matching R. Seven focused Python tests pass;
706 native R assertions pass over 28 method/missingness/adjustment configurations,
including base-R correlation estimates, p-values/intervals, adjusted native table values,
stale-result clearing and native raster rendering. All 17 packaged runtime cases pass,
with additional checks for each new adjustment. R emitted three "Operation not permitted"
messages after completion; the runner exited zero with no failed assertions or test warnings.
The new adjustment controls still need native GUI qualification.
See [adjustment oracle report](validation-exports/python-correlation-adjustments-0.3.23-oracle.json).
