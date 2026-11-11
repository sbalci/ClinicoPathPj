# Empirical-moment CCC uncertainty experiment — 2026-11-11

This is an **unreleased source-only experiment**, separate from the Lin
normal-theory interval implementation. The installed 0.3.63 `pyagreement` analysis
continues to report CCC point estimates only. No R bridge, UI, archive or installed
module was changed for this experiment; the migration inventory is unchanged.

## Method contract

`cpj_concordance_empirical.empirical_concordance_interval(x, y, confidence=.95,
method="empirical-z")` uses an empirical influence variance for the ordinary
population-moment CCC estimator. Choose `empirical-z` (atanh transformation) or
`empirical-normal` (unclipped Wald limits) explicitly. There is no automatic
fallback, finite-sample correction, outlier removal, resampling or random seed.

The method assumes independent, identically distributed pairs, finite fourth
moments and nondegenerate first-order variance. It relaxes the normal-model
variance assumption; it does **not** make CCC resistant to outliers or establish
finite-sample coverage. This is a derived application of the multivariate
[delta method](https://www.cambridge.org/core/books/abs/asymptotic-statistics/delta-method/85F4D7D90259A601942FDB034A8DC703),
checked independently below. It is not labelled as a particular published
U-statistic or GEE procedure. [Carrasco et al.](https://pubmed.ncbi.nlm.nih.gov/17613647/)
motivate separating normal-model and alternative CCC inference; their study does
not validate this implementation.

Write the five raw moments as `(a,b,c,d,e) = (EX,EY,EX²,EY²,EXY)`.
With `D=c+d−2ab`, `N=2(e−ab)` and `rho=N/D`, the gradient is
`(−2b(1−rho), −2a(1−rho), −rho, −rho, 2)/D`.
The implementation uses its equivalent centered influence form to avoid raw-moment
cancellation. If `dx=x−mean(x)`, `dy=y−mean(y)` and `delta=mean(x)−mean(y)`, then

```text
IF_C = dx*dy − covariance
IF_D = dx² − vx + dy² − vy + 2*delta*(dx−dy)
phi = (2*IF_C − rho*IF_D) / (vx + vy + delta²)
variance = sum(phi²) / n²
```

All empirical moments use divisor `n`. No `n−1` or `n−2` correction is applied.
The frozen contract predates implementation. A hand fixture has CCC .4 and
variance .0368 (23/625), independently confirmed from the gradient.

The helper preserves the existing point engine and complete-pair/source-position
audit. It requires 10 complete pairs, at most 5,000 source rows, confidence .80–.99
and valid finite numeric measurements apart from missing values. Exact zero
Pearson correlation is supported when empirical first-order variance is positive.
Undefined CCC, exact absolute CCC of one, nonpositive/unresolved variance and
unresolved final limits produce an unavailable status with empty uncertainty
fields. They do not produce invented zero-width intervals. Ordinary computation
uses scaled float64 influences; absolute CCC above .99 uses standard-library
Decimal80 boundary arithmetic. No new runtime dependency is introduced.

## Independent numerical evidence

The blinded R oracle author derived the raw-moment gradient without reading the
Python target or its tests. Central finite differences, halved steps and a
centered influence cross-check support the derivation. MPFR256 supplies the
authoritative numerical fields; raw double-precision and matrix results remain
stored, including boundary cancellation differences. Two R runs produced
byte-identical fixtures.

Across 27 fixtures, five confidence levels and two methods, **1,895 checks pass**
at absolute tolerance 1e-12 (maximum discrepancy about 1.11e-14). The 270 requests
comprise 150 available, 50 unavailable and 70 invalid-input refusals. Fixtures
include missing pairs, ties, zero correlation, constants, boundaries, near-perfect
agreement and sample-size limits. Nine focused Python tests additionally check
unit/offset/swap invariance, extreme finite scales, row identity, confidence
nesting, unclipped normal limits, duplication scaling and invalid controls.

The retained initial failed test log records two harness corrections: R's
length-one JSON auto-unboxing required vector normalization, and an assumed
cross-boundary normal example was replaced with the independently frozen n=10
fixture that actually crosses one. The statistical formula, frozen expected
values and tolerance were not changed to make those checks pass.

## Matched-input coverage evidence

Each of 19 scenarios uses 2,000 independent paired datasets. All three methods
receive exactly the same observed arrays: **38,000 datasets and 114,000 interval
evaluations**. The original 15 input-tape hashes and Lin coverage counts match
the earlier study. A separate RNG stream supplies four extensions. Every report
row records input hashes, availability, Monte Carlo SE and a Wilson interval;
paired method differences use replicate-level coverage indicators. Identical
seeds across different language RNGs are not treated as matched inputs.

Selected observed coverage at nominal 95%:

| Population | Pairs | Lin transformed | Empirical transformed | Empirical normal |
|---|---:|---:|---:|---:|
| Normal, CCC .3 | 10 | 94.00% | 84.35% | 80.85% |
| Shifted/scaled normal | 10 | 88.50% | 80.65% | 80.40% |
| Normal, CCC .9 | 100 | 95.40% | 94.85% | 94.65% |
| Lognormal | 30 | 76.35% | 73.65% | 70.95% |
| Lognormal | 100 | 69.10% | 80.55% | 78.40% |
| Lognormal | 500 | 64.65% | 88.45% | 87.90% |
| Lognormal | 1,000 | 60.00% | 90.75% | 90.35% |
| Common normal scale mixture | 100 | 57.60% | 84.30% | 83.20% |

The scale mixture multiplies both normal measurements by 5 with probability .05
and by 1 otherwise; its true CCC is .8 and its fourth moments are finite.
The lognormal scenario exponentiates unit-variance jointly normal measurements
with latent correlation .6; its true CCC is `expm1(.6)/expm1(1)`.
All intervals in this simulation were available. Availability is not calibration.

Empirical moments improve some larger skewed/scale-mixture cases, but small
normal samples can perform worse than Lin. Lognormal empirical transformed
coverage at n=1,000 is .9075 (Monte Carlo SE about .0065), materially short of .95.
These scenarios do not justify a universal minimum sample size or method-selection
rule. Neither prototype meets a generic nominal-95% coverage claim.

The final full source regression suite passes **508 Python tests** (239.423 seconds).
Generator freshness and registry/status checks also pass. The coverage replay is
byte-identical; its engine hashes match the final source. Native R/GUI checks
were not rerun because this increment adds no native integration or package.

## Delivery decision and next gate

Keep both inference engines source-only and keep public CCC point-only. Before
another inferential implementation, freeze a separately labelled paired-resampling
contract, unavailable/degenerate policies, bounded runtime and coverage acceptance
criteria. Use independent reference construction and identical observed arrays
and resampling indices wherever possible. Bootstrap is a candidate to test, not
an assumed fix. Do not choose the best interval post hoc or add a fallback based
on the observed CCC, skewness or sample size.

Public delivery still requires method/domain decisions, native lifecycle and
compatibility checks, saved-file/export checks, platform qualification and
clinical review. Numerical source success does not satisfy those gates.

## Reproduction and evidence

Run from the repository root with jamovi's bundled interpreter:

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
/Applications/jamovi.app/Contents/MacOS/python -B -S tools/check-concordance-empirical.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
/Applications/jamovi.app/Contents/MacOS/python -B -S tools/check-concordance-empirical-coverage.py
```

The R reference generator `tests/reference/concordance-empirical.R` uses existing
developer jsonlite/Rmpfr installations; these are not analysis runtime dependencies.

- [Frozen contract](validation-exports/python-concordance-empirical-contract-20261111.json)
- [Numerical matrix summary](validation-exports/python-concordance-empirical-numerical-20261111.json)
- [Coverage and paired comparisons](validation-exports/python-concordance-empirical-coverage-20261111.json)
- [Qualification and regression evidence](validation-exports/python-concordance-empirical-qualification-20261111.json)
- [Overall uncertainty plan](python-concordance-uncertainty-plan.md)
