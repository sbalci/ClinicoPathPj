# Unequal-variance standardized effects — source prototype

## Frozen contract (2026-11-12, before implementation)

This separate engine does not alter the installed 0.3.68 module, its menus,
Student/paired effects, or the default raw Welch analysis. Native Welch
standardized results remain deferred until the approximation is reviewed.

For independent normal populations the target is
`delta_RMS = (mu1-mu2)/sqrt((sigma1²+sigma2²)/2)`. Use sample variances with
Bessel correction; the denominator is the root mean variance, not the arithmetic
mean SD, reference-group SD, or sample-size-weighted pooled SD. Require explicit
`standardizer='rms_variance'`. Reuse the raw engine's complete cohort, exact factor
labels, orientation, original row indices, subject-ID validation and numeric guards.

Report `d_rms`, SD, Welch degrees of freedom, and the distinct moment-matched
SD degrees of freedom `(s1²+s2²)²/[s1⁴/(n1-1)+s2⁴/(n2-1)]`. For audit comparison
only, also report `welch_J` and `welch_J_point = J(df_Welch)*d_rms`, with
`correction_exact=False`. The gamma-function expression for J is evaluated
without a series approximation, but unbiasedness is not exact for the general
heteroscedastic denominator. Do not label this an exactly unbiased Hedges g.
If Welch df <= 1, J and its adjusted point are unavailable, not zero.

Intervals default to `interval='none'`. Explicit `interval='welch_nct_plugin'`
inverts a noncentral t with the observed Welch df and multiplies the NCP limits
by `observed_SE/observed_RMS_SD`. These are **approximate** limits for delta_RMS:
the denominator, transformation and df are random plug-in estimates. Do not
multiply delta limits by J or supply g-specific limits. Retain the previously
qualified inversion domain (df 2–100,000, |t| <= 40) and checked convergence criteria. The separate prototype uses complementary SF
for negative NCP bracket evaluations and tolerates at most eight ULPs of
probability-boundary roundoff; existing Student/paired code is unchanged.
Outside it retain finite point estimates with unavailable limits and a reason.
Raw degeneracy returns null standardized values. Invalid method/standardizer
arguments fail before computation; all results must serialize without NaN/Inf.

## Prespecified independent validation

Freeze base-R formulas, Welch t.test comparisons, pt/uniroot endpoints and
installed effectsize 1.0.3 nonpooled points/Cohen limits before implementing Python.
Use the existing independent raw-mean fixtures plus one-constant n=2, unequal-N,
unequal-variance, missingness, extreme-scale, zero-effect and reversal cases.
Point relative tolerance: 1e-10 (exact zero exact); NCP/delta endpoint scaled
absolute tolerance: 2e-7. Package inversion is a secondary check at 2e-4.
The J-scaled interval convention in effectsize is outside this contract.

Coverage screen: 12 independent-normal scenarios, 2,000 fixed draws each,
confidence .95, delta 0 or 1.5; balanced/unbalanced n, SD ratios 1 and 4 and
both allocations of the larger variance. R generates and freezes actual Z/Q
sufficient-statistic draws, not merely seeds. Compute sample variances from
independent chi-square draws and the mean difference from an independent normal.
Assess interval inclusion by NCT-CDF monotonicity at the true delta, independently
of root inversion. Compare every R probability against SciPy and audit selected
full engine intervals. Unsupported draws count as noncoverage.

Target nominal coverage is .95; the provisional minimum is .925. Use simultaneous
Clopper–Pearson bounds (Bonferroni across 12 profiles, family confidence .95).
A profile fails if its upper bound is below .925, passes this limited screen if
its lower bound is at least .925, otherwise is inconclusive. Passing this screen
is not universal coverage, clinical validation, native qualification or release
clearance. Freeze this rule before examining the generated outcomes.

## Primary sources and conventions

- [effectsize documentation](https://easystats.github.io/effectsize/reference/cohens_d.html)
  recommends nonpooled effects with Welch and describes NCP inversion.
- [effectsize source](https://github.com/easystats/effectsize/blob/main/R/cohens_d.R)
  is the package convention comparator; the installed 1.0.3 implementation is
  inspected and versioned in the independent fixture manifest.
- Delacre et al., [preprint record](https://doi.org/10.31234/osf.io/tu6mp):
  methodological background; full text was unavailable during this review,
  so no unverified formula is attributed to it.

## Implementation evidence

The final frozen-source suite passes **616 Python tests** in 249.662 seconds,
with no failures/errors/skips. Generator/status freshness and `git diff --check`
also pass. No native compilation or GUI claim applies to this source increment.

`inst/python/cpj_welch_standardized.py` is a separate source helper with no native
adapter or registry entry. `tests/reference/welch-standardized-effects.R` generated
all reference files before Python implementation; a repeat produces byte-identical
JSON/CSV. The CSV contains actual independent Z/chi-square draws and R CDF values.
Essential reference JSON is tracked; generated validation reports/logs are ignored.

`tools/check-welch-standardized.py` passes **1,224 numeric comparisons** across
22 datasets/110 configurations, with maximum scaled difference 1.01e-10. The
independent R reference additionally passes **88 package/base-R cross-checks**.
All 24,000 R/SciPy CDF comparisons agree within 7.53e-13, all inclusion counts and
simultaneous bounds agree, and 48 reconstructed-observation full-engine interval
checks agree with the independent sufficient-statistic inclusion calculation.
Eleven focused tests also check 230 independent R/mixture inversion cases, reject
five statistical mutations, test missingness/labels/IDs and df=1, and verify
numerical failures preserve points while programming errors propagate.

The initial Python comparison stopped on bundled SciPy returning NaN at
`t=6.448159123436948, df=148.59436616559083, NCP=-5.224079561718474`.
The complementary survival function is finite. A regression reproduces that
original failure when present and verifies the new solver against R endpoints.
The initial R fixture generator also stopped on rescaling all-zero observations;
its independent zero-scale guard was corrected before fixtures were frozen.

Coverage outcome: **11 pass, one inconclusive, zero fail**, under the prespecified
rule. The inconclusive profile has n1=20, n2=5, sigma1=1, sigma2=4, true delta=0:
1,883/2,000 intervals cover (94.15%), with simultaneous CP bounds
[92.4893%, 95.5489%]. The lower bound is just below the provisional 92.5% minimum.
Do not retroactively increase its draw count or relax the rule. A separately
prespecified [independent replication/sensitivity study](python-welch-standardized-replication.md)
now passes that normal replication but detects small-sample/nonnormal limits.
Generic intervals remain source-only; the next native candidate is RMS-SD point-only.
No profile here establishes exact coverage or unbiasedness.

The existing 0.3.68 JMO SHA-256 remains
`69f1a62d823a4718d493a6981669cb3fc833b1dd1f8c28eb1cdb57efaeba5088`;
all 1,453 installed files still match the archive. This is preservation evidence,
not desktop qualification of the new source prototype.

Reproduce from the module root:

```sh
Rscript --vanilla tests/reference/welch-standardized-effects.R
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-welch-standardized.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tests/python/test_welch_standardized.py
python3 tools/generate.py --check
python3 tools/migration-status.py --check
```
