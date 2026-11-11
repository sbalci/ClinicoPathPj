# Paired percentile CCC bootstrap experiment — 2026-11-11

The paired-resampling contract and coverage criteria were frozen before this
source-only implementation. The resulting prototype passes independent numerical
checks but **fails its prespecified general-coverage screen**. It is not exposed
by `pyagreement`. The installed 0.3.63 analysis remains point-only for CCC, and no
R/UI/package changes or additional migration entry were made.

## Exact method and limits

`cpj_concordance_bootstrap.bootstrap_concordance_interval(x, y, confidence=.95,
resamples=1999, seed=20261111)` computes an equal-tailed **paired percentile**
interval. It samples retained complete-pair indices with replacement, applying the
same indices to both columns. Every replicate uses the population-moment CCC;
limits use linear interpolation (R quantile type 7). The reported bootstrap SE is
the sample SD of the replicate coefficients, with divisor B−1. No Lin or
empirical-delta variance is used.

This is the [percentile bootstrap procedure](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html),
not BCa, a studentized bootstrap or a bias-corrected estimator. SciPy also documents
basic and BCa intervals; their availability does not qualify this percentile
implementation or establish CCC coverage. The source helper implements its own
bounded paired execution and checks SciPy separately in tests.

The point estimator and its complete-pair/source-position audit are unchanged.
Inputs require 10 complete pairs, at most 5,000 source rows, confidence .80–.99,
199–9,999 resamples and an integer seed from 0 to 2^32−1. Each call is limited to
10 million resampled pairs and processes batches of 64. A local PCG64 generator
leaves global NumPy RNG state unchanged. A checkpoint callback can interrupt
between batches; cancellation propagates and no partial interval is returned.
This is source-level cancellation testing, not desktop long-job acceptance.

For independent replay, supply an integer index matrix of shape `(B,n_complete)`.
Its zero-based indices address the retained cohort; original source row positions
remain in the point audit. Supplied indices override RNG and report a null seed.
Both generated and supplied indices carry a SHA-256 digest of row-major little
endian int64 values. Confidence changes reuse the same generated draws.

Inference is withheld for undefined/source-boundary CCC, any undefined or
unresolved bootstrap CCC, or a zero-width percentile interval. Undefined draws
are counted, never dropped or redrawn. A constant but unequal measurement pair
can produce a defined point CCC of zero but a degenerate bootstrap distribution;
its uncertainty remains unavailable. Bootstrap replicates at ±1 can be valid if
their CCC denominator is defined. A percentile interval need not contain the
original estimate; an independent fixture explicitly verifies that case without
widening or recentering its interval. Parameter limits are not clipped, except
for floating-point arithmetic overshoot of a replicate coefficient at ±1.

The method assumes independent identically distributed measurement pairs and
regular sampling conditions. Resampling does not repair repeated-patient
dependence, selection bias, missingness assumptions, unit mismatch or heavy-tail
estimation. It is not an outlier-resistant CCC estimator or an exact interval.
There is no automatic fallback to another inference engine.

## Independent reference and source checks

A blinded oracle author wrote the R reference from the method contract without
reading target source or outputs. It computes CCC from raw sums and cross-checks
every replicate against a centered-moment implementation; maximum discrepancy
between those R forms is about 1.39e-15, with identical undefined masks. The hand
fixture has CCC .4. Full resampling indices, coefficients, type-7 limits and SDs
are frozen for 17 datasets at confidence .80/.95/.99. Mathematical quantities and
policy withholding are stored separately, including raw boundary results.
Two R runs produced byte-identical final fixtures.

**10,071 independent checks pass**, covering 51 interval requests: 30 available
and 21 unavailable. Absolute tolerance remains 1e-12; the maximum target/reference
discrepancy is about 1.30e-15. Cases include asymmetric ties, missing pairs, zero
correlation, negative agreement, high concordance, constant columns, exact
boundaries, an induced undefined draw, a collapsed distribution and a nonzero-width
interval excluding its source estimate.

Before target comparison, the oracle author's own property check found that the
intended excluding-point fixture accidentally collapsed. The author corrected
its fixed indices and reran twice without reading the target. This independent
fixture-construction correction was not an adjustment to match target results.

Nine focused Python tests also cover SciPy paired-percentile agreement with the
same generator stream and an independently written statistic, seed replay, global
RNG preservation, explicit-index hashes, batch behavior, pair/row alignment,
swap/unit/offset invariance, confidence nesting, malformed indices, resource
limits, cancellation propagation and deterministic recovery.

The full source regression suite passes **517 Python tests** (184.004 seconds).
Generator freshness, registry/status freshness and whitespace checks pass.
The complete coverage replay is byte-identical and its engine hash matches final
source. Existing point/Lin/empirical engines and the qualified 0.3.63 archive have
unchanged hashes. No native R/GUI suite was rerun for this source-only addition.

## Prespecified coverage screen

The screen uses **34,000 independent paired datasets** across 17 scenarios,
2,000 datasets per scenario and 999 resamples per dataset. The exact observed-data
hashes match the prior Lin/empirical study for all 15 normal/lognormal scenarios
at n=10/30/100 and two common-scale-mixture scenarios at n=30/100. Resampling has
its own local seed stream. Prior method coverage is reported on these identical
observations; the study does not claim cross-language seed equivalence.

The contract's research criterion requires **every** scenario's unconditional
Wilson 95% Monte Carlo interval to lie entirely within [.93,.97], with at least
99% availability. Unavailable intervals count as noncoverage. Conditional
coverage is reported separately. These are prespecified engineering screening
criteria, not a universal statistical standard or clinical acceptance rule.

Selected observed coverage at nominal 95%:

| Population | Pairs | Lin transformed | Empirical transformed | Paired percentile |
|---|---:|---:|---:|---:|
| Normal, CCC .3 | 10 | 94.00% | 84.35% | 90.25% |
| Normal, CCC .9 | 10 | 93.45% | 83.30% | 87.15% |
| Shifted/scaled normal | 10 | 88.50% | 80.65% | 82.15% |
| Lognormal | 10 | 79.25% | 61.60% | 85.95% |
| Lognormal | 30 | 76.35% | 73.65% | 89.65% |
| Lognormal | 100 | 69.10% | 80.55% | 89.65% |
| Common normal scale mixture | 30 | 68.45% | 76.55% | 91.60% |
| Common normal scale mixture | 100 | 57.60% | 84.30% | 91.30% |
| Normal, CCC .9 | 100 | 95.40% | 94.85% | 94.90% |

All tested intervals were available. Only **2 of 17 scenarios** pass the screen.
The lognormal n=100 coverage .8965 has Wilson interval [.88238,.90910]; the
scale-mixture n=100 coverage .913 has interval [.89984,.92457]. Their deficits
are larger than Monte Carlo uncertainty. Bootstrap improves some skewed cases
but does not resolve the general calibration problem and can be worse than Lin
for small normal samples.

The first 20 observed datasets per scenario were also evaluated with 1,999
resamples, as a fixed subset selected before examining results. Coverage
classification changes in 2 of 340 comparisons; the maximum endpoint movement
is about .0657. This small subset is a finite-resample sensitivity check, not
proof that 999 or 1,999 draws are adequate, and not a new coverage qualification.

## Delivery decision and roadmap

Keep percentile, Lin and empirical-delta CCC intervals source-only. Do not expose
an apparently best method automatically, increase the minimum sample size based
on these few scenarios, or relabel an interval to hide its failed screen.

The next inference research candidate is a separately specified BCa or studentized
paired bootstrap, with independent reference construction, degenerate policies,
resource bounds and coverage evaluation frozen before target comparison. Neither
is presumed to fix the problem. CCC inference remains a research gate rather
than a prerequisite for continuing other migration features. Native controls,
saved-file compatibility, exports, platform qualification and clinical review
would still be required after a method/domain decision.

## Evidence and reproduction

- [Frozen method and coverage contract](validation-exports/python-concordance-bootstrap-contract-20261111.json)
- [Independent numerical matrix summary](validation-exports/python-concordance-bootstrap-numerical-20261111.json)
- [Coverage and resample-count sensitivity](validation-exports/python-concordance-bootstrap-coverage-20261111.json)
- [Source qualification and regression record](validation-exports/python-concordance-bootstrap-qualification-20261111.json)
- [Previous empirical-moment experiment](python-concordance-empirical.md)

From the repository root:

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
/Applications/jamovi.app/Contents/MacOS/python -B -S tools/check-concordance-bootstrap.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
/Applications/jamovi.app/Contents/MacOS/python -B -S tools/check-concordance-bootstrap-coverage.py
```

The R reference generator requires the existing developer jsonlite installation;
no R statistical calculation or additional package installation is used at runtime.
