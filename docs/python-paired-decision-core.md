# Binary paired diagnostic comparisons — source contract, 2026-11-11

This document freezes the numerical source contract. Its subsequent
[native partial integration](python-paired-decision-native.md) now has a SPEC,
organized interface and lifecycle checks; the registry is **partial**.
The 0.3.66 partial core now has bounded local macOS arm64 GUI Sideload,
save/reopen/recalculation and HTML/PNG export acceptance. Existing R analyses
are unchanged.

## Frozen baseline and intended scope

The frozen `meddecide` 1.1.2 manifest identifies `decisioncompare` at commit
`c343bf8a2f9f711e7a0f6ed3941415170d1e3f58`. Its archived backend SHA-256 is
`752f0325ac1b725e7ddf5ed16a5806ad108217277b177d3302de792e9904c110`.
Verify archived bytes, rather than resnapshotting the mutable sibling checkout.
The baseline JSON's option definitions offer **mid-p (default)** and asymptotic
McNemar without continuity correction. The registry's broader prose mentioning
exact tests is not a third frozen public selector.

The backend calls `pairedProportionDifference`, but that reusable helper is not
present in the four-file baseline archive. Its method-10 implementation is now
[pinned separately from the original commit](python-paired-difference-intervals.md).
The mutable sibling helper did not become the frozen reference.

The proposed numerical engine uses two or three binary tests and one reference,
with an explicit positive **and negative** level for every factor. Extra unused
levels are retained in provenance. Observed levels outside the selected pair
cause an error unless exclusion is explicitly requested. Missing values and
outside-pair values are counted separately per role; missingness takes precedence
in the mutually exclusive cohort exclusion totals. Invalid codes are errors.
The numerical API reserves `reference` as its reference audit key; test names
must be distinct nonempty strings other than that key. Inputs are bounded to
100,000 rows; the standalone discordance helper accepts up to 1,000,000 pairs.

All selected roles use **one common complete, determinate cohort**. This is an
explicit narrow-core choice, not a reproduction of the R analysis's per-test
available cohorts and pair-specific comparisons. The engine reports retained
original zero-based positions, missing/outside-pair counts, retained class sizes
and the mappings used. No implicit one-versus-rest conversion is allowed.

## Calculations

For each test, return TP, FP, FN, TN and sensitivity, specificity, PPV, NPV and
accuracy with Clopper–Pearson intervals through the shared accuracy engine.
Confidence defaults to 95%; the source contract accepts 80–99%. Empty
denominators yield undefined estimates/intervals. These sample estimates do not
apply a supplied population prevalence.

For each pair, compare **correctness** on all retained cases (accuracy), positive
calls within reference-positive cases (sensitivity), and negative calls within
reference-negative cases (specificity). Return both-success, first-only,
second-only and neither-success counts; paired N; both marginal proportions;
first-minus-second difference; discordant N; and McNemar result/status.
PPV and NPV are not tested with ordinary McNemar because their denominators differ.
Paired-difference confidence intervals remain omitted by default. A separately
validated source-only `difference_intervals=True` option now calculates Newcombe
method-10 limits; its small-sample coverage screen fails six scenarios, so no
jamovi interval control is exposed. See the [interval evidence and boundary](python-paired-difference-intervals.md).

Let `b` and `c` be first-only and second-only counts, `m=b+c`, `k=min(b,c)`.

- Mid-p follows Fagerland et al. equations (5) and (6): for unequal counts,
  `min(1, 2*BinomialCDF(k; m, .5)) - BinomialPMF(k; m, .5)`; for a nonzero
  equal split, `1 - .5*BinomialPMF(b; m, .5)`.
- Asymptotic uses `(b-c)^2/m` against chi-square(1), without continuity correction.
- A separately named exact-conditional option exists only in the numerical
  helper for reference checking; it adds no frozen public UI option.
- With no discordance, p=1 is a convention, the statistic is undefined and status
  says **no discordance**. This does not demonstrate equivalence.
- With no observations in a reference stratum, all comparison estimates/tests
  for that stratum are undefined, with **absent class** status.
- Apply Holm adjustment only across accuracy comparisons with discordance;
  no-discordance rows retain their conventional p=1. Sensitivity/specificity
  p-values remain explicitly unadjusted, as in the frozen baseline. An explicit
  source-level `none` adjustment is available; it does not change the R defaults.
  `holm_family` records informative accuracy pairs, and `holm_applied` is true
  only when Holm is selected and that family contains more than one comparison.

Cases must be independent across rows and tests paired within each case.
Repeated lesions/specimens require a clustering-aware method. Accuracy depends
on sample case mix; disease interpretation additionally requires a defensible
disease reference. No best-test verdict, equivalence claim or clinical cutoff is
produced. Mid-p and asymptotic tests are not exact size-controlled tests.

## Validation and remaining gates

Freeze R references **before** writing the Python implementation:
`tests/reference/paired-decision.R` uses base `binom.test`, `mcnemar.test`,
`p.adjust` and independently enumerated binomial probabilities. It covers the
discordance grid, zero/equal/one-sided/extreme counts, published examples,
common-cohort missingness, explicit exclusions, reordered/unused factor levels,
absent reference classes and duplicate tests. Unit checks additionally exercise
invalid input, label orientation and test-order reversal.

The engine now passes **27,552 independent R checks**, covering 445 discordance
cases and 13 paired datasets at 80%, 95% and 99% confidence. Maximum absolute
difference is `4.857780844247372e-13` against a `1e-12` tolerance. The frozen
reference SHA-256 remains
`04253456ba378096d0542ab6206e7c6d40b462d73635d3d28be8fc76c7d4129b`.
All 14 focused Python tests pass. Five temporary in-memory mutations are caught
by assertion failures: positivity substituted for correctness, wrong equal-split
mid-p, inclusion of no-discordance pairs in Holm, ignored test missingness and
silent outside-pair exclusion. The repository implementation is unchanged by
those probes. Run `tools/check-paired-decision.py` in bundled Python to reproduce
the numerical check; generated reports and logs remain local and ignored.
The complete Python regression suite passes 547 tests. A separate final focused
run passes all 14 tests, including aligned invalid-factor probes, and a fresh
independent R replay produces a byte-identical fixture. Generator/status freshness
checks pass. No installed-module or native GUI checks are claimed for this engine.

Numerical agreement does not qualify interval coverage, a jamovi analysis,
clinical use, saved-file compatibility or any platform. The interval prototype
now passes independent numerical checks but fails its broad small-sample screen.
The subsequent [native partial integration](python-paired-decision-native.md) adds
explicit cohort/comparator roles, synthetic examples, packaged execution and
lifecycle checks, with bounded local macOS arm64 desktop save/reopen/export
acceptance. Broader platform and full-parity gates remain open. Cochran Q, OPA/non-inferiority,
stratification, prevalence scenarios, radar/heatmap and full report parity remain
omitted. The full 61-analysis denominator remains fixed; the native increment moves this
entry from planned to partial (30 partial / 31 planned).

Primary method sources: [Fagerland, Lydersen and Laake (2013), equations 5–6](https://pmc.ncbi.nlm.nih.gov/articles/PMC3716987/),
[SciPy binomial test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html),
and [statsmodels McNemar reference](https://www.statsmodels.org/dev/generated/statsmodels.stats.contingency_tables.mcnemar.html).
