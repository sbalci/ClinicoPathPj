# Correlation matrix — pyjjcorrmat, core through 0.3.25

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

Robust/winsorized and Bayesian correlations, BF/posterior outputs,
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
The new controls also pass macOS arm64 / jamovi 28.13 desktop qualification: all three
reruns match R in native tables and the local inspector; BY settings/results survive
separate OMV save and second fresh-engine reopen, followed by successful Hochberg
recalculation. See [desktop checks](validation-exports/python-correlation-adjustments-0.3.23-desktop.json).
Additional platforms and broader accessibility/theme qualification remain open.
See [adjustment oracle report](validation-exports/python-correlation-adjustments-0.3.23-oracle.json).

## Partial Pearson — 0.3.24

Enable **Partial Pearson** with at least three numeric variables, Pearson method and
one common complete-case cohort. Each pair controls every other selected variable;
there is no separate covariate selector. Other method/missingness combinations are
rejected explicitly, even if supplied through a restored or scripted option. The
zero-order default and Holm adjustment remain unchanged. In the supplied CSV, choose
Marker_A/Marker_B/Marker_C for a valid partial example; including Constant deliberately
produces an unavailable adjustment system.

Calculations use the inverse standardized covariance matrix on the common cohort.
For k controls, the two-sided t test uses df=n−k−2 and Fisher-z interval standard error
1/sqrt(n−k−3). Tests require positive df; intervals require n−k>=4. Native pair tables
and local details report k and df. Multiplicity still includes all planned unique pairs.
Constant variables, rank-deficient systems and insufficient residual degrees of freedom
leave all partial estimates unavailable with explicit reasons; no pseudoinverse or
silent dropping of controls is used. The diagonal is unavailable in such systems.

Classical t/Fisher-z inference assumes independent observations and an appropriate
multivariate-normal linear model. Conditioning on selected variables does not establish
causality or remove unmeasured confounding. Grouped, robust/Bayesian methods and Spearman intervals remain omitted; partial Spearman
is added in 0.3.25 below. Independent R residual-regression and
current GUI/package evidence are separate gates. The native suite passes 1,007 assertions,
including seven partial-adjustment configurations against independent base-R `lm.fit`
residuals, t tests and Fisher-z intervals, alongside the prior zero-order/lifecycle/raster
checks. Eight focused Python tests and the local keyboard DOM regression pass.

The final 0.3.24 archive passes source/registry integrity and all 17 runtime cases,
including an analytical fixture where zero-order r=0.5 becomes partial r=0, p=1, df=1
and the interval is unavailable at n=4 with one control. See the
[package report](validation-exports/python-correlation-partial-0.3.24-package.json).
On 2026-10-28, macOS arm64 jamovi 28.13 passed native partial-control qualification,
pairwise/constant-system rejection and valid recovery, new OMV save/second-engine
reopen, zero-order/partial reruns and native PNG export. See the
[desktop report](validation-exports/python-correlation-partial-0.3.24-desktop.json) and
[saved example](validation-exports/python-correlation-partial-0.3.24-validation.omv).
Additional platforms and broader accessibility/theme checks remain open.

## Partial Spearman — 0.3.25

The existing **Partial correlations** option now also supports Spearman. Choose at
least three variables and one common complete-case cohort. Each variable is ranked
within that retained cohort, using average ranks for ties, before computing the inverse
rank-covariance matrix. Every pair controls the other selected ranked variables. This
is a linear residual correlation of ranks, not a general nonlinear conditional-independence
test. Partial Pearson and all zero-order defaults remain unchanged.

The native table/inspector report control count k and df=n−k−2. Two-sided t p-values
are approximate for partial Spearman; no exact/permutation inference or confidence
interval is supplied. Singular, constant or insufficient ranked systems remain unavailable
with explicit reasons. Pairwise partial estimation is still rejected. The partial checkbox
remains editable so an unsupported configuration can be recovered without resetting the
analysis. Multiplicity uses the same planned-pair family and seven adjustment choices.

Nine focused Python tests cover ranked residual agreement, ties/missingness, common-cohort
ranking, df, unavailable intervals and singular ranks. Independent native R ranked-residual
comparisons pass in the expanded 1,308-assertion suite, including coefficients,
approximate p-values, control counts/df and unavailable intervals over all seven
adjustment choices. Final packaged checks are recorded separately; native desktop partial Spearman qualification
is not implied by the earlier Pearson desktop evidence.

The 0.3.25 archive passes integrity/source checks and all 17 runtime cases, including
a tied-rank fixture independently evaluated in R (partial r=0.1601592641029556,
p=0.7969540733546533, one control, df=3, unavailable CI). See the
[package report](validation-exports/python-correlation-partial-spearman-0.3.25-package.json).
On 2026-10-28, native tied-data controls, R agreement, second-engine
save/reopen/rerun and PNG export passed on macOS arm64 / jamovi 28.13. See
[desktop checks](validation-exports/python-correlation-partial-spearman-0.3.25-desktop.json)
and the [saved example](validation-exports/python-correlation-partial-spearman-0.3.25-validation.omv).
Import `data/python_partial_spearman_examples.csv` to reproduce the tied fixture.
Broader accessibility/theme and cross-platform qualification remain open.
