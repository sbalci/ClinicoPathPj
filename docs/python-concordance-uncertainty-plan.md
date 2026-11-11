# Next CCC increment: qualify uncertainty before exposing it

Status: **numerical prototype implemented; public inference deferred because of coverage limitations**. The installed 0.3.63 CCC method continues to report point
estimates only. Its confidence controls remain disabled. The source helper now implements both interval formulas, with numerical checks
and a known-population coverage study. It has no native UI, package or GUI
qualification; the installed analysis is unchanged.

## Confirmed reference contract

The frozen meddecide 1.1.2 `R/agreement.b.R` in
`docs/baselines/released-2026-10-25.tar.gz` explicitly calls
`DescTools::CCC(x, y, ci = "z-transform", conf.level = self$options$confLevel)`.
The same branch retains the ten-pair minimum. It also has a separately disclosed
local normal/Wald fallback when a transformed interval cannot be obtained. Its
notes distinguish mixed interval methods and unavailable uncertainty; undefined
intervals are not presented as a zero-width interval. Frozen source SHA-256:
`18939ee1429eaaba05a0fed64b9f175f659d1c269b2eadf87b4ad0ac157a5d71`.

The locally installed DescTools **0.99.60** implementation was inspected on
2026-11-11. Its default is `ci = "z-transform"`, using Lin's CCC variance with
location-shift terms and denominator `n - 2`, followed by transformation through
atanh and its inverse. Its `ci = "asymptotic"` branch is a different normal
interval; it is not a substitute reference for the transformed method.
The [package reference](https://andrisignorell.github.io/DescTools/reference/CCC.html)
and the frozen source remain the starting references. Recheck the exact reference
version when creating interval fixtures.

## Delivery sequence

1. Freeze an interval-specific method/default/omission matrix and reference script
   before implementing the Python interval engine. Decide how to expose intervals
   explicitly while preserving existing saved point-estimate analyses and the
   Bland–Altman default. Any Wald support must have its own disclosed method/status;
   never silently substitute it or label it a transformed interval.
2. Generate independent base-R and DescTools fixtures for the public n ≥ 10 cohort,
   with confidence levels 0.80, 0.90, 0.95, 0.975 and 0.99. Store unrounded point,
   variance/SE, transformed limits, final limits, warnings and explicit undefined
   statuses. Keep the reference builder independent of the Python implementation.
3. Add an isolated numerical helper without changing the public CCC results.
   Validate ordinary cases against both references, plus independently derived
   moments/known cases. Reuse the established population-moment CCC and audits;
   the array helper's three-pair fixture minimum does not authorize a lower public
   inference minimum.
4. Test negative concordance, location/scale shifts, missing pairs, near-zero
   Pearson r, exact zero r, constants, perfect/reversed linear relationships,
   extreme shared units, confidence boundaries and cancellation of tiny positive
   variances. Undefined or unresolved inference needs an explicit status and empty
   limits. Do not infer a valid CI from a mathematically removable division or
   collapse it to a point merely because the point estimate exists.
5. Investigate coverage using fixed, stored draws or resampling indices, reporting
   Monte Carlo uncertainty. Include the intended sampling assumptions and clearly
   separate normal-model coverage from skewed/outlier sensitivity. Agreement with
   a package alone does not establish population coverage or clinical usefulness.
6. Only after numerical qualification, connect controls and native CI/method/status
   outputs under the existing `pyagreement` identifier. Retain explicit same-unit,
   independent-case roles and complete-pair auditing. Verify point estimates do not
   change when confidence changes, and that inactive method controls have no effect.
7. Test native valid → incomplete/error → valid transitions, CCC/Bland–Altman/ICC
   switching, old point-only saved fixtures, fresh-engine reopen, recalculation and
   export. Keep numerical, package, GUI, platform and clinical gates separate.

## Unchanged limits

Repeated-case inference, multirater pooling, bootstrap intervals and clinical
acceptance bands remain outside this next increment. No new Python dependency or
runtime R statistical calculation is authorized by this plan. Python will calculate
the estimates; R remains the bridge and native-display layer.

## Implemented source prototype — 2026-11-11

`cpj_concordance_uncertainty.concordance_interval(x, y, confidence=.95,
method="z-transform")` supports explicit transformed or `asymptotic` (normal/Wald)
intervals. It preserves the existing point engine and its complete-pair audit.
There is no automatic method fallback, no clipping of normal limits and no zero-width
interval manufactured at an undefined boundary. Undefined CCC/precision, exact zero
Pearson r, absolute CCC equal to one, nonpositive/unresolved variance and unresolved
final limits return an unavailable status with empty uncertainty cells.

The helper uses scaled moments for ordinary values. When absolute CCC exceeds 0.99,
standard-library Decimal arithmetic at 80 digits resolves cancellation before the
same Lin formula and transform are evaluated. This changes arithmetic precision,
not the inferential method. Independent MPFR256 fixtures cover both parameter
boundaries and the transition cases that exposed errors below the original .999999
precision threshold. No new runtime package is needed.

The independent R builder created 31 datasets at five confidence levels. Its
DescTools/base-R comparisons are supplemented by MPFR256 references for six
near-boundary/transition datasets. **3,410 checks pass** across 35 datasets and
350 method/confidence runs (280 available, 70 explicitly unavailable). Absolute
comparison tolerance remains 1e-12; maximum discrepancy is about 5.11e-15.
Ten double-reference transformed-SE values were adjudicated using MPFR, not hidden
by changing the original fixtures or relaxing the tolerance. The initial failed
matrix and original oracle files are retained.

The coverage study reuses exactly the same generated arrays for both methods:
15 population/sample-size scenarios × 2,000 datasets, with true CCC known from
the generating distributions, input hashes, Monte Carlo SEs and Wilson intervals.
A single seed is not claimed to reproduce R and NumPy generators. At nominal 95%,
transformed-interval coverage was 0.885 for a shifted/scaled normal scenario at
n=10, improving to 0.9485 at n=100. Lognormal sensitivity scenarios had coverage
0.7925, 0.7635 and 0.691 at n=10, 30 and 100 respectively. These departures exceed
Monte Carlo uncertainty and prevent a general calibration claim.

**Next gate:** resolve the public method/domain policy for small samples and
nonnormal measurements before adding controls. Preserve the reference methods'
identity and explicitly disclose their approximation assumptions; any robust or
resampling alternative would be a separately specified and independently validated
method. It must not silently replace Lin's variance or be labelled its transformed
interval. The ten-pair frozen minimum does not prove 95% coverage at that size.

See the [numerical report](validation-exports/python-concordance-interval-numerical-20261111.json),
[coverage report](validation-exports/python-concordance-interval-coverage-20261111.json),
[contract](validation-exports/python-concordance-interval-contract-20261111.json) and
[prototype qualification](validation-exports/python-concordance-interval-qualification-20261111.json).

The final source regression suite passes **499 Python tests** (194.541 seconds),
including ten new interval tests. Replaying the complete coverage study produces
byte-identical JSON. No R bridge, native UI, package archive or installed module
was changed for this increment. The original point engine's file hash is unchanged.

Reproduce with jamovi's bundled interpreter:

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
/Applications/jamovi.app/Contents/MacOS/python -B -S tools/check-concordance-intervals.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
/Applications/jamovi.app/Contents/MacOS/python -B -S tools/check-concordance-interval-coverage.py
```

The R reference generators under `tests/reference/concordance-intervals*.R` require
existing developer DescTools/jsonlite/Rmpfr installations. They are not runtime
dependencies. Their expected values were generated independently of the Python
implementation; all three reference generators produced identical JSON on two runs.
