# Six Python core analyses in ClinicoPathPj 0.2.0

These are Python implementations of a deliberately bounded statistical core, not feature-complete
copies of the umbrella analyses. All calculations run in jamovi's bundled NumPy/SciPy runtime;
R supplies native jamovi integration and Image rendering. No external Python installation is needed.
The existing analyses, including the interactive diagnostic dotplot, remain in the same module.

## Inputs and worked examples

Open **Data Library > ClinicoPathPj > Python Core Examples** for the saved six-analysis workbook,
or import `data/python_core_examples.csv` into jamovi. It contains 36 explicitly synthetic observations;
regenerate it with `python3 tools/generate-core-examples.py`.

| Analysis and menu | Example selections | Outputs and important limits |
|---|---|---|
| Diagnostic Accuracy (`pydecision`), Diagnostic tests | Reference = Reference, test = Test; explicitly choose Positive for both | Confusion counts; sensitivity, specificity, PPV, NPV and accuracy with exact Clopper-Pearson intervals; LR+, LR-, DOR and Youden index. Ratios are point estimates only. |
| Diagnostic Accuracy Calculator (`pydecisioncalculator`), Diagnostic tests | Enter TP=90, FP=30, FN=20, TN=80 | Identical accuracy engine to the row-data analysis. Counts must be nonnegative whole numbers with positive total. |
| Sequential Testing (`pysequentialtests`), Diagnostic tests | Default properties; optionally show costs and enter cost per test | Three strategy rows, combined accuracy, fractional expected classifications and second-test workload. Test costs only, not health economics. |
| Chi-Square Post-Tests (`pychisqposttest`), Comparisons | Rows = RowGroup, columns = ColumnGroup; optionally frequency = Frequency | Overall uncorrected Pearson test, Cramer's V, observed/expected cells, adjusted residuals and pairwise tests. Frequency entries represent independent-observation counts, not survey weights. |
| Benford Analysis (`pybenford`), Data quality | Measurement = Measurement; digits = 2 | Leading-digit counts/proportions, Pearson goodness of fit, descriptive MAD and native observed/expected bar plot. |
| Decision Curve Analysis (`pydecisioncurve`), Diagnostic tests | Outcome = Reference, event = Positive; models = RiskA and RiskB | Common-cohort net benefit, treat-all/none references, threshold counts and interventions avoided per 100. Input columns must already contain predicted probabilities. |

## Methods and conventions

### Diagnostic accuracy

Choose both positive levels explicitly; no level is guessed. Unused factor levels are preserved,
and genuinely missing factor levels are encoded as missing without turning a literal `NA` label
into missing data. Missing reference/test pairs are excluded and counted.

Both diagnostic interfaces use `inst/python/cpj_accuracy.py`. Confidence level defaults to 95%.
A proportion with a zero denominator has no estimate or interval. Ratios have an explicit status:
positive/zero is Infinite, zero/zero is Undefined, and zero/positive is zero. No continuity
correction is applied. The native numeric cell is blank for an infinite ratio; the adjacent
Value or Status column preserves its meaning.

Optional population-prevalence calculations appear in a separate table. They do not overwrite
sample PPV/NPV, and have no uncertainty intervals. Sensitivity and specificity must transport
to the intended population for these Bayes calculations to be meaningful. Sample predictive
values and accuracy may not estimate population quantities in case-control samples.

### Sequential testing

Assume conditional independence within diseased and nondiseased groups. Serial positive requires
both results positive and gives the second test only to first-test positives. Serial negative
retests first-test negatives and classifies either-positive as positive. Parallel applies both
tests to everyone with the same either-positive rule. Consequently serial negative and parallel
have identical combined sensitivity/specificity but different testing workload.

Input properties are treated as known; uncertainty is not propagated. Expected counts are
fractional projections. Costs are `N * first-test cost + expected second tests * second-test cost`.
Use the existing `pycotest` for the supported conditional-dependence model.

### Chi-square post-tests

Pearson statistics are uncorrected. Cramer's V uses the overall Pearson statistic. Residuals are
adjusted standardized residuals with two-sided normal p-values and Bonferroni adjustment across
all retained cells, independently of the pairwise family.

For dimensions with at least three levels, compare each pair of row levels across retained
columns, and each pair of column levels across retained rows. Remove zero margins within each
comparison and omit degenerate comparisons. Adjust all valid pairwise p-values together using
Bonferroni (default), Holm or BH; Disable pairwise tests omits the entire pairwise family.
More than 500 potential pairwise comparisons disables that family with a warning.

Sparse 2x2 pairwise tables use Fisher's exact p-value. Their Pearson statistic remains labelled
as Pearson. Larger tables use the asymptotic Pearson p-value with a sparse-count warning;
this core never labels a larger-table Monte Carlo estimate as exact Fisher. The overall test
is always Pearson. Tables above 10,000 cells are rejected to bound results size.

### Benford

For d digits, categories range from `10^(d-1)` through `10^d-1` with probabilities
`log10(1 + 1/category)`. Leading digits use the shortest round-trip decimal representation of
stored numbers, avoiding logarithmic boundary errors for values such as 0.3, powers of ten
and very small measurements. Default d=2; d=1 through 3 are supported.

Missing, zero and negative values are excluded with separate counts; infinite values are
rejected. Sparse expected counts trigger an approximation warning. A range below two orders
of magnitude triggers a suitability warning. Identifiers, imposed ranges and detection limits
may invalidate this model. A departure does not establish fraud or identify a cause.
The chart thins axis labels for large digit sets but retains every category and count.

### Decision curves

At threshold t, positive means prediction >= t and net benefit is
`TP/N - FP/N * t/(1-t)`. Treat all has net benefit `prevalence - (1-prevalence)*t/(1-t)`;
treat none has zero net benefit. Interventions avoided per 100 relative to treat all are
`100 * (model net benefit - treat-all net benefit) * (1-t)/t`.

Every model and reference uses the same complete-case cohort across outcome and all selected
probability columns. Both outcome classes must remain. Invalid probabilities are rejected,
not clipped. Model labels are prefixed separately from the reference-strategy labels, so a
column named Treat all cannot overwrite a reference curve.

Default thresholds are 0.05 through 0.50 by 0.01, a computational convenience rather than a
clinical recommendation. The grid follows the given step and need not include the maximum
when the step does not divide the interval. Decimal rounding at floating-point noise scale
preserves equal-threshold classifications. Grids are limited to 1,000 thresholds and combined
plot data to 20,000 points. No model fitting or recalibration is performed.

## Feature and omission matrix

| Core | Included | Explicitly omitted |
|---|---|---|
| Diagnostic accuracy | Exact proportion intervals, ratio point estimates, separate supplied-prevalence calculations | Ratio intervals, Fagan nomogram, spreadsheet classification output, multi-cutoff calculator, repeated-patient inference |
| Sequential testing | All three rules, workload, optional test costs, native accuracy plot | Dependence estimation, uncertainty propagation, decision-flow diagrams, outcome utilities |
| Chi-square | Counts, residual tests, pairwise adjustment, sparse 2x2 Fisher | Overall Fisher/Monte Carlo, larger-table Fisher, bootstrap V intervals, power calculations, survey design |
| Benford | 1-3 digits, goodness of fit, MAD, native bar plot | Fixed conformity labels, mantissa arc test, suspect-record classification |
| Decision curves | Observed-cohort net benefit, references, interventions avoided | Bootstrap bands, model-comparison inference, case-control prevalence correction, clinical impact/economic modelling |

All data-based intervals/tests assume independent observations. Repeated-patient or reader-cluster
inference is outside this batch. Numerical agreement does not establish clinical validation.

## Build and check

`Rscript --vanilla tools/build.R --build-only` regenerates specifications, synchronizes version/date
from DESCRIPTION and builds the single standard `ClinicoPathPj_0.2.0.jmo` without installation.
The original command without `--build-only` retains the development install workflow.

Install through Modules > Manage installed > Sideload. It updates the existing ClinicoPathPj module.
Use a fresh jamovi engine after replacing a loaded development build: the menu can update while
an older R namespace remains in memory. Preserve any unsaved work before restarting jamovi.

Validation sources and final results are recorded in `docs/python-core-validation.md`.
