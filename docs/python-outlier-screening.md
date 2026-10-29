# Univariate outlier screening core

`pyoutlierdetection` appears under **Descriptives Py → Data quality → Univariate
outlier screening (core)**. This is a partial baseline port, not the full umbrella
outlier-detection implementation. Existing R analyses and Python utilities are unchanged.

Select one to twenty numeric variables. The core screens every finite complete row
across those variables, using the same cohort for each variable. Missing measurements exclude the whole row; input/complete/excluded counts are explicit.
The Python engine also excludes nonfinite measurements, but the native jamovi numeric
option validator rejects source infinities before dispatch. Recode those values to missing
when using the native interface; rejection is not silently bypassed.
At least two complete rows are required. The maximum input is 10,000 rows; the core
rejects larger inputs rather than silently taking a random sample.

The core exposes three **univariate** methods. Its robust Z default corresponds to
the baseline's univariate selection. The baseline's overall composite default is
not implemented or imitated here.

| Method | Calculation | Default flag rule |
|---|---|---|
| Robust Z | Absolute deviation from median divided by `1.4826 × median absolute deviation` | Strictly greater than 3.29 |
| Standard Z | Absolute deviation from mean divided by sample SD (`n−1`) | Strictly greater than 3.29 |
| IQR | R type-7 quartiles, Q1/Q3 expanded by the IQR multiplier | Strictly outside `Q1−1.7×IQR` / `Q3+1.7×IQR` |

The limits shown are method-specific, not confidence intervals. A zero-spread Z score
is undefined at its center; a noncentral value has an infinite score and is flagged.
Undefined cases are counted separately. Zero-width IQR fences remain evaluable.
An any-variable row flag is 1 if any variable flags, 0 if at least one is evaluable
and none flags, and missing if all selected scores are undefined. Excluded source rows
also have missing flags. Numerical infinities are not serialized as ordinary finite scores.

Native outputs include per-variable centers/spreads/limits and flag/evaluable/undefined
counts, an optional first-1,000-row preview with original source IDs and flagged-variable
names, and an optional count plot. The full row-aligned nominal output is available
under **Save and Export**, including rows beyond the preview limit. No values are changed
and no cases are automatically deleted. Flagging is a descriptive prompt for review,
not proof of error or a clinical classification. Repeated subjects are supplied rows;
this core does not model their dependence.

Composite scoring, Mahalanobis/MCD/OPTICS/LOF, interval methods, transformations,
subsampling, automatic exclusion/recommendations, interactive exploration and full baseline
reporting are omitted. Broader clinical, method-parity and platform qualification remain open.

## Synthetic example

Data Library → ClinicoPathPj → **Univariate Screening Examples** contains 33 rows:
31 complete pairs (including one extreme pair) and two missing-measurement rows.
Select Marker_A and Marker_B. All three supported methods flag the extreme pair at
the retained default cutoffs. The CSV is reproducible with
`python3 data-raw/generate-outlier-screening-examples.py`.

## Validation gates

The test plan compares centers/limits/flags against independent base-R `median`, `mad`,
`sd`, type-7 `quantile` predicates and `performance::check_outliers` for supported interior
cases. It covers missing/nonfinite cohorts, strict ties, zero spread, sparse source IDs,
nominal output serialization, incomplete-input clearing/recovery and native raster rendering.
Numerical/compiler/packaged evidence will be recorded separately from desktop installation,
saved-file reopen/export and clinical qualification. The new analysis desktop gate is pending.


Current evidence (0.3.32): all 278 Python tests and five focused outlier tests pass,
including strict Z/IQR fence ties, empty/all-nonfinite inputs, zero spread and sparse
source identities. The native R suite passes 45 assertions against independent base-R
predicates and performance 0.18.2, including nominal saved flags, clearing/recovery,
source-infinity rejection and 800×500 raster rendering. All 19 packaged runtime cases
pass, including the new synthetic CSV under each of the three supported methods.
R printed `Operation not permitted` messages around completion, with zero test failures,
zero test warnings and exit status zero. Native desktop automation cannot start its
pipe, so new-analysis installation/OMV/export qualification remains pending. See
[separate validation record](validation-exports/python-outlier-screening-0.3.32-checks.json).


## Flagged measurement details — 0.3.33

Enable **Results and Interpretation → Flagged measurements (first 500)** to inspect
original source row, variable, observed value, lower/upper limits and flag basis. Values
and limits retain the original measurement units. Infinite Z scores from zero spread
are identified in words; no infinite numeric score is serialized.

The table contains flagged **measurements**, so two variables in one row produce two
records. It searches all retained rows, including rows beyond the separate first-1,000-row
preview. Records are shown in original source-row then selected-variable order, with a
maximum of 500 displayed matches. The accompanying text reports shown/total measurement
counts, including zero matches. A display limit does not change screening, per-variable
counts or the full saved flag column. The option is off by default.

New-table desktop installation/rendering/export/save-reopen qualification remains open
separately from Python/native bridge evidence.


Detail validation: all 281 Python tests pass, with eight focused outlier tests including
late source rows, multiple drivers, the 500-match cap, empty matches and output invariance.
After a SPEC-only option reorder preserving earlier scientific wrapper positions, focused
and native checks pass again. The native suite passes 59 assertions including original
row/value/limit mapping, optional/incomplete/recovery clearing and zero-spread labels.
All 19 packaged runtime cases pass. The statistical engine is byte-identical to 0.3.32.
See [detail validation](validation-exports/python-outlier-details-0.3.33-checks.json).
Desktop details-table/save/export qualification remains pending.


## Empirical distribution panels — 0.3.34

Enable **Plots and Interaction → Empirical percentile distributions and limits**.
Every selected variable gets a panel with its own measurement scale. The solid curve
connects 101 empirical percentiles (0–100), calculated by linear interpolation from all
common complete rows. Dashed horizontal lines show the lower and upper screening
limits; these are not confidence intervals. Coincident limits use one dashed line.

This is an aggregated distribution view, not individual-observation inspection.
Interpolated percentiles need not equal observed measurements. Use the flagged-detail
table for actual values and original source IDs. Flat zero-spread Z distributions do
not turn undefined center scores into nonflags. No data are sampled for calculations;
flags, tables and saved outputs are unchanged. All 1–20 variables are retained, with
a maximum of 2,020 plot records. Long panel titles may be shortened; full names remain
in the native summary. The option defaults to off.

New plot desktop installation, rendering, export and save/reopen qualification remains
pending while computer-use automation fails at native-pipe startup.

Validation: 285 full Python tests and 12 focused screening/plot tests pass. The native
R suite passes 69 assertions, including independent type-7 percentiles, cohort exclusion,
1,000×800 raster rendering and valid → incomplete → valid recovery. All 19 packaged
runtime cases pass, including rendering the new curve through the extracted runtime.
The screening engine is byte-identical to 0.3.33. Source/generator checks pass. Native
R emits environment-level “Operation not permitted” messages despite exit 0 and
zero failed/warning assertions. See the [separate validation record](validation-exports/python-outlier-distributions-0.3.34-checks.json)
and [locally rendered preview](validation-exports/python-outlier-distributions-0.3.34-preview.png).
These checks do not qualify the desktop, other platforms or clinical use.


## Bounded native lifecycle checks — 0.3.36

Installed through jamovi's GUI on macOS arm64 / jamovi 28.13. The synthetic 33-row
example retains 31 complete pairs and excludes two. Native details show source row 31,
Marker_A=200 and Marker_B=−100; both count and percentile plots render. Enabled the
nominal saved flag output, saved OMV, fully restarted, reopened and toggled details
off/on to force a fresh calculation. Details clear/restore and counts remain unchanged.
The saved column contains 30 not-flagged rows, one flagged row and two missing flags,
confirmed independently from the saved archive's row-aligned codes and labels.

The [native percentile PNG](validation-exports/python-outlier-distributions-0.3.36-native.png)
is 2000×1600. The [saved fixture](validation-exports/python-outlier-screening-0.3.36-desktop.omv)
retains tables, flags, plot options and plot snapshots across fresh-engine reopening.
The GUI configuration uses the default robust-Z method; the independent native R suite
covers all three methods. Other GUI methods, table export, themes/accessibility, further
platforms and clinical/release review remain separate gates. Earlier pending statements
above are historical; this bounded lifecycle gate supersedes them.

See the [0.3.36 native/core evidence](validation-exports/python-native-core-0.3.36-checks.json).
Persisted artifacts can be rechecked with `python3 tools/check-native-core-artifacts.py`.
