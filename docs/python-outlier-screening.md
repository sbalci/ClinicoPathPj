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
