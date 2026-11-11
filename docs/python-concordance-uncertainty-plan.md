# Next CCC increment: qualify uncertainty before exposing it

Status: **planned**. The installed 0.3.63 CCC method continues to report point
estimates only. Its confidence controls remain disabled. This document does not
claim that any CCC interval has been ported, numerically validated or GUI-tested.

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
