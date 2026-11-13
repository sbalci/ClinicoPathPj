# Categorical bar core — frozen increment contract

## Scope frozen before implementation (2026-11-13)

Reserved identifier `pyjjbarstats`; frozen jjstatsplot wrapper version 1.0.82.03,
commit `4c3cbe8de39d6259ee61d5fde28704f45e9cc8ed`. Verify all four registry hashes.
The initial subset is one categorical outcome, one independent categorical group,
optional nonnegative integer frequencies and optional exact subject-ID audit for
unweighted records. Preserve supplied factor label order and true missingness;
a literal `"NA"` label is a category, an actual missing factor level is excluded.
No paired/repeated, split, multiple-outcome, Bayesian, per-bar goodness-of-fit,
clinical-preset/interpretation, balloon or interactive features in this increment.
All source calculations run in Python; no frequency expansion or extra dependencies.

Local primary-source inspection: ggstatsplot 1.1.1 / ggplot2 4.0.3 /
statsExpressions 2.1.1 / effectsize 1.0.3. ggbarstats uses identity bars with
position='fill', x=group and fill=outcome; percentages divide outcome-cell count
by the complete-data group total. Higher factor levels stack at the bottom.
The frozen wrapper overrides results.subtitle=FALSE, proportion.test=FALSE,
bf.message=FALSE; independent frequentist model and paired=FALSE are defaults.
Labels default to percentage with zero percentage decimals. Keep these supported
defaults. Native inference goes to tables rather than a plot subtitle.
Add an explicit count scale as a documented core extension, without changing the
100% stacked default. Count scale preserves group sample-size differences; the
percentage scale intentionally has equal total heights. Offer percentage/count/
both segment labels, with zero-count labels absent. Label rounding must not alter
numeric geometry or native table values. Static Python figures only initially.

## Source cohort and counts

1–100,000 source rows; two distinct factor roles with aligned valid integer codes.
Optional frequencies must be scalar finite nonnegative whole numbers or missing;
reject invalid known frequencies even on rows excluded for another missing role.
Complete rows require both factors and known frequency. Audit source/complete/
excluded/missing-by-role/zero-frequency/positive-frequency rows independently.
Only positive-frequency complete rows contribute; total N must be in 1..2^53-1.
Use integer accumulation, not observation replication. Unweighted frequency is one.
Retain original row indices and exact known/unique subject labels on contributing
rows. Subject audit with aggregated frequencies is unsupported; do not suggest an
aggregated row represents an independent subject.

Remove unused and zero-margin outcome/group levels from calculation and drawing,
retaining their declared labels/codes in a dropped-level audit. Preserve active
factor order, not alphabetical or frequency order. This explicit trimming prevents
zero expected-frequency failures; it does not establish full unused-legend parity
with ggstatsplot. Support at most 20 active outcome and 20 active group levels; bound each declared
factor-level list to 1,000 so the dropped-level audit remains bounded.
Require at least two active levels in both roles for this comparison core; reject
empty, all-zero, single-level and resource/numeric failures explicitly.
Return group totals, outcome totals, complete Cartesian cell grid including zero
cells, observed/expected counts, row/group and overall proportions, and row audit.

## Independent association and effect-size points

Source inference switch defaults off; no chi-square/Fisher/effect calculation when
off. Expected counts may still be computed as a denominator/assumption diagnostic.
When enabled, Pearson statistic is sum((O-E)^2/E), df=(r-1)(c-1), with no continuity
correction. Use Pearson p except in a 2x2 table with any expected count <5, where
the primary p is two-sided Fisher exact (probability ordering, as base R). Keep
Pearson statistic/df/p as separately named audit fields; do not attach its statistic
to Fisher's p. Larger sparse tables retain Pearson approximation with an explicit
warning, never a false claim of exact inference. No odds ratio or odds-ratio CI.

Point effects use the uncorrected Pearson statistic X2, irrespective of primary
Fisher selection: Vraw=sqrt((X2/N)/min(r-1,c-1)). Also return a distinct conventional
Bergsma bias-corrected point: phi2c=max(0,X2/N-(r-1)(c-1)/(N-1));
rc=r-(r-1)^2/(N-1), cc=c-(c-1)^2/(N-1), Vc=sqrt(phi2c/min(rc-1,cc-1)).
If the corrected denominator is nonpositive, return null with a reason, not zero.
Clamp only the analytically nonnegative corrected phi2; do not fabricate intervals.
Both effects are points only: no confidence/credible limits, p from an effect-size
test, magnitude bands, or clinical interpretation. The baseline requests corrected
V and a CI through statsExpressions/effectsize. Independently inspect its 2x2
continuity convention and record any discrepancy with the explicitly uncorrected
core target; do not silently imitate an inconsistent point/statistic combination.

## Plot geometry and native contract

Complete grid order: each group in active factor order, each outcome in active
factor order. Stack in reverse outcome order (last level bottom), matching ggplot2.
For each segment return count, group total, within-group proportion, overall
proportion, numeric lower/upper bounds and label center. Percentage bounds are
cumulative counts divided by group N, in [0,1]; counts bounds use exact cumulative
counts, in [0,group N]. Group x positions are 1..G; width .9, xmin=x-.45,xmax=x+.45.
Every group's final top is exactly 1 or N; no overlap, gaps or dropped zero cells.
A native table names the denominators and keeps counts/proportions numeric.

After source oracles pass, generate an organized SPEC/run interface under Stats
Plots Py → Categorical comparisons. Required data roles first, statistical results
off by default, explicit independent-design assumptions and point-only effects,
secondary tables/cases and plot/scale/label controls. Native static Image has a
serialized plot-only payload and must render after data removal. Retain baseline
style as an omission where the jamovi palette or static renderer differs.
Unconfigured GUI requests are quiet; incomplete/invalid requests clear stale
computed values, notes and plot state; recovery must match a fresh run.
No new JMO or installed-module replacement in this source increment: keep the
qualified 0.3.70 archive and all 1,461 installed files unchanged.

## Prespecified validation

A blinded independent oracle builder receives this contract and the archived
baseline, never target Python source or expected outputs. Freeze R fixtures before
engine implementation. Use base table/xtabs, uncorrected chisq.test, fisher.test,
explicit marginal/denominator equations and independent corrected-V equations;
cross-check effectsize on an uncorrected htest where supported. Compare actual
built ggplot2 stacked/fill bars, including a ggstatsplot shape reference, in both
scales. Record package versions, warnings, unsupported cases and baseline 2x2
continuity discrepancies. Preserve exact double JSON input round-trips.

Include unequal groups, reversed factor levels, ordinal/numeric-looking/Unicode
labels, literal NA and actual missing label, missing roles/frequencies, zero cells,
unused and zero-only levels, dense/sparse 2x2 and RxC, degenerate margins, huge
aggregated N without expansion, and invalid weights/roles/caps. Exact counts,
cohort/source identities, factor order, primary-method choices and unavailable
states; relative 1e-10 for numeric points/p/geometry (zero absolute 1e-12).
Require deterministic R replay, source-row/count-table equivalence, permutation/
label-order/scaling properties, mass conservation and rejected mutations for the
wrong denominator, stack order, continuity correction, primary Fisher selection,
frequency loss and missingness. Expose any oracle disagreement rather than
changing tolerances or fixtures after target execution.

Require full Python regression/freshness and focused native schema/lifecycle/
serialization/rendering evidence before calling the adapter partial. Actual-package,
GUI save/reopen/export, broader platforms, clinical review and full baseline
feature parity remain separate gates.

## Implemented subset and evidence

The literal `analyses/jjstatsplot/pyjjbarstats.py` SPEC generates organized native
controls/tables and the R bridge. Shared `cpj_barstats.py` contains the statistical
engine; `cpj_barstats_adapter.py` presents its outputs. A new `stackedbar` drawing
contract is added to the runtime/generator/R display bridge and Python renderer;
the existing grouped `bar` kind is unchanged. Native static construction remains
Python-only, with R displaying the completed raster and supplying jamovi palette/
theme settings. More outcomes than palette colors use a hatch as an additional
visual distinction, rather than hiding categories.

| Feature | Implemented partial core | Omitted / remaining gate |
|---|---|---|
| Inputs | One outcome/group pair; optional whole-number frequencies or unweighted exact subject IDs | Paired, splits, multiple outcomes, survey weights |
| Cohort | Source/complete/contributing/missing/zero-frequency/N audits, removed declared levels | No automatic clinical interpretations |
| Tables | Group totals, full cell grid, within-group and overall proportions; optional source rows | No saved derived dataset columns |
| Association | Statistics off by default; primary Pearson or sparse-2×2 Fisher, separate Pearson audit | Bayesian, per-bar GOF and larger exact/Monte Carlo tests |
| Effects | Raw and Bergsma-corrected V points, unavailable corrected denominator explicit | V intervals, magnitude bands and effect-size tests |
| Plots | 100% default, count-scale extension, count/percentage/both labels, reverse factor stacking | No ggplot statistical subtitle, balloon or interaction |
| Lifecycle | Isolated native valid → incomplete/invalid → valid, optional clearing, RDS drawing-state restore after data removal | Actual JMO, desktop OMV/HTML/PNG and wider platforms pending |

`resultssubtitle` now names optional native statistical tables; its default remains
false. Fixed independent frequentist design is visible text rather than unsupported
method choices. No confidence control is offered while effect intervals are omitted.
Frequency and subject-ID controls disable each other; restored unsupported options
are rejected, including paired/Bayesian, group splits and confidence requests. There
was no earlier released Python bar entry whose saved-option contract was renamed.

The independent builder froze `tests/reference/barstats-core.R` and
`tests/fixtures/barstats-core.json` before Python implementation. It verifies four
archived baseline hashes; constructs table/xtabs, uncorrected chisq.test and
fisher.test references; checks the Bergsma equations against effectsize; and checks
actual built ggplot2 fill/stack geometry for every successful dataset, plus a real
ggbarstats shape example. There are **28 datasets** (19 successful, nine actual
refusals), **47 configurations** with inference on/off, and **8,837 comparisons**.
Maximum scaled difference is 2.9421e-15, within the prespecified tolerances.

The oracle retains six sparse Pearson-approximation warnings. It confirms that
although effectsize initially constructs a Yates htest internally for a raw 2×2
table, its effect routine recomputes uncorrected Pearson counts. Raw table, Yates
htest and uncorrected htest all yield the same corrected point; there is **no point
convention discrepancy** to imitate or repair. Local versions: ggplot2 4.0.3,
ggstatsplot 1.1.1, effectsize 1.0.3, statsExpressions 2.1.1, jsonlite 2.0.0,
R 4.6.0. The bundled Python uses SciPy 1.17.1. These are executed local references,
not inferred historical dependency versions for a published JMO.

The correction formulas were also checked against
[Bergsma's primary manuscript, Section 2](https://stats.lse.ac.uk/bergsma/pdf/cramerV3.pdf).
The two-sided Fisher definition uses probability ordering conditional on margins,
as documented in the [official SciPy Fisher reference](https://docs.scipy.org/doc/scipy-1.13.1/reference/generated/scipy.stats.fisher_exact.html).
These references support method definitions; they do not establish clinical utility
or effect-size interpretation thresholds.

Eleven focused Python tests verify all oracle inputs, weighted-row expansion
identity on small tables, permutation/frequency-scale properties, source identities,
invalid/resource refusals, output gating and subprocess execution. Six mutations
(wrong denominator, stack direction, continuity statistic, Fisher selection,
frequency loss and missingness) are rejected by the frozen checker. Figure tests
compare every rectangle to the independent geometry, verify labels and raster
output, reject invalid geometry, and prove that re-rendering does not refit a model.
Label formatting is display-only Python decimal formatting; geometry/table values
remain unrounded. Full ggplot styling/label-format parity is not claimed.

The final isolated R library passes **390 native assertions**, without failures,
errors, warnings or skips. It compares all 19 successful datasets, genuine missing
factor levels, ordinal/Unicode labels, weighted denominators, primary test selection
and point effects; tests ID/required-role/optional-output recovery; and restores
serialized drawing state after removing analysis data before native PNG export.
Its five relevant Python source files match final source bytes. Compiler preparation,
roxygen documentation and generator/status freshness pass. These checks do not
establish desktop behavior or actual new-package execution.

The first native example run exposed a harness import difference: default base-R
read.csv retained an empty categorical field as a literal empty label, producing
N=52 instead of the intended N=50. Explicit empty/NA missing-value import repairs
the test input; no analysis missingness rule, oracle expectation or tolerance was
changed. The failed run is retained separately.

The synthetic CSV `data/python_barstats_examples.csv` has seven source rows:
four positive complete cells represent 50 observations, one complete row has zero
frequency and two rows have missing selected roles. Group totals are **20 and 30**.
The native [percentage preview](validation-exports/python-barstats-source-percentage.png)
has equal full heights; the [count preview](validation-exports/python-barstats-source-count.png)
has unequal heights. Both were exported and visually inspected; labels retain the
same per-group denominators in either scale.

Fixture SHA-256: `7625190c09221ee622ab312f09daa60ab7e4285dda651149fd815192e972f1d2`.
Oracle script SHA-256: `f97c7f89c7ad1a0fff08fe0c3457cf22bdab5e4ab624b902b2c1959c68cbf66b`.
R replay is byte-identical, including exact numeric JSON input round-trips.

Reproduce from the ClinicoPathPj root:

```sh
Rscript --vanilla tests/reference/barstats-core.R /private/tmp/barstats-replay.json
cmp tests/fixtures/barstats-core.json /private/tmp/barstats-replay.json
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-barstats-core.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tests/python/test_barstats_core.py
# After isolated source installation into <library>:
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  Rscript --vanilla tools/check-barstats-native.R <library>
```

The final frozen-source suite passes **662 Python tests** in 262.820 seconds,
with no failures/errors/skips. Generator/status freshness and whitespace checks
(excluding compiler-owned headers) pass. Installed 0.3.70 remains byte-identical
across all 1,461 files; its JMO SHA-256 is
`a5f20c63d25e7cff154723151d1eb619a5a94bff871b7cdb927eab3f6b6ccfe5`.
No new package was built, installed, committed or published for this increment.
Next build the next standard-version JMO, execute the archived bar runtime and
qualify Sideload/fresh-engine/OMV/export behavior before advancing GUI status.
