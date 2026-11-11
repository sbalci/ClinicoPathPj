# Empirical ROC and paired DeLong core — 2026-11-11

This document records the initial source-only numerical qualification of
`inst/python/cpj_roc.py`, before its native adapter was added. The subsequent
[native partial integration](python-roc-native.md) now provides the generator-owned
SPEC, tables and static plot under `pyenhancedroc`, with registry status `partial`.
The numerical evidence below remains separate from that adapter's native tests.
The current installed module is now 0.3.64 with bounded macOS GUI acceptance;
the qualified 0.3.63 rollback archive remains preserved. See the native follow-up
for installation, saved-file and export evidence.

Paired AUC comparisons belong to `pyenhancedroc`. They are separate from the
binary-test `pydecisioncompare` baseline, which includes paired McNemar methods,
diagnostic differences and other categorical outputs. This helper does not claim
to implement that analysis or the full enhanced ROC baseline.

## Implemented contract

`roc_analysis(reference, markers, positive, directions=None, confidence=.95)`
accepts a runtime `Factor` reference with exactly two distinct labels and an
ordered mapping of one to three numeric score columns. The positive label must
be supplied explicitly; label order never determines the event. `higher` is the
default score direction, and each marker can explicitly use `lower`. Automatic
orientation is rejected: below-chance AUC remains below .5 rather than being
silently flipped. Original factor labels, including the literal label `"NA"`,
are preserved. Missing codes are distinct from labels.

Every selected score uses **one common complete-case cohort**. The returned audit
reports source/retained/excluded counts, class counts, missing reference/score
counts and original zero-based retained source positions. Missing counts can
overlap and are not added to obtain the exclusion count. Both outcome classes
must remain after common-cohort selection. Nonfinite scores other than missing
NaN are rejected, even in rows excluded for another reason. Numeric strings,
boolean scores, malformed factor codes and integer scores outside the exact
supported ±2^53 range are rejected. At most 5,000 source rows are supported.

Empirical AUC uses the case/control rank probability, with half credit for exact
ties. Each score also returns its complete ROC geometry and TP/FP/FN/TN at every
distinct observed score. Equality is positive: `>=` for higher and `<=` for lower.
The initial none-positive state uses a null cutoff plus an explicit rule label;
it never serializes an infinite threshold or invents a finite representable
cutoff beyond the maximum score. Subsequent thresholds are observed values.
pROC ordinarily reports midpoint thresholds: this core matches the classification
states and geometry, not those threshold labels. Trapezoid area agrees with AUC.

The core evaluates [DeLong's paired AUC covariance method](https://pubmed.ncbi.nlm.nih.gov/3203132/)
using case and control placement vectors. If `V10` is the case-placement matrix
and `V01` the control-placement matrix, with m cases and n controls, then

```text
S = sample_cov(V10) / m + sample_cov(V01) / n
AUC_j = mean(V10_j)
variance(AUC_a − AUC_b) = S_aa + S_bb − 2*S_ab
```

Placements are obtained from sorted scores without allocating an m×n kernel.
The difference variance is evaluated directly from placement differences to avoid
subtraction cancellation for nearly identical markers. Covariance across both
classes remains available for auditing. Cases must be independent; selected
markers are paired on the same cases. These are not unpaired, clustered or
repeated-patient tests.

At confidence .80–.99 (default .95), positive variance yields an asymptotic normal
AUC interval bounded at [0,1]; raw normal limits are retained separately. Paired
comparisons report first AUC minus second AUC, normal SE, signed z, two-sided p
and an **unbounded** normal difference interval. Pairwise p-values are unadjusted;
the result explicitly states `multiplicity="none"`. A public comparison interface
must name its testing family and adjustment policy rather than imply these are
adjusted results.

With fewer than two cases or two controls, descriptive AUC/geometry remains
available but uncertainty is withheld. Zero or unresolved marginal variance
withholds the corresponding AUC interval; zero or unresolved contrast variance
withholds that comparison's test and interval. A constant or perfect marker does
not receive an invented zero-width marginal interval. Identical models do not
receive a fabricated p=1; perfect versus inverted models do not receive p=0
from a division by zero. Raw pROC boundary values/warnings remain in the oracle
fixtures as documented policy differences. A comparison with one constant marker
can still have positive contrast variance; its availability follows that contrast,
not the separate marginal interval's status.

## Frozen baseline and independent numerical evidence

The registry's four `enhancedROC` baseline files were read at the frozen meddecide
commit and all four SHA-256 hashes match. Baseline methods, defaults, public
identifiers and native files remain unchanged. This source contract deliberately
selects a narrow empirical/DeLong core; it does not silently replace baseline
bootstrap, partial, smoothed, multiclass, calibration or validation features.

The independent oracle author received the method contract, not target source or
outputs. A literal case/control pairwise kernel supplies AUC, placement covariance,
normal limits and differences; installed [pROC](https://xrobin.github.io/pROC/)
supplies independent package checks. Threshold counts use direct comparisons at
the specified observed cutoffs. The hand AUC is 21/32 = .65625. R 4.6.0,
pROC 1.19.1 and jsonlite 2.0.0 were used; the local pROC installation warns that
it was built under R 4.6.1. Both reference runs produced byte-identical fixtures.

**16,689 checks pass** at absolute tolerance 1e-12, with maximum discrepancy about
1.98e-14. Seventeen datasets at three confidence levels produce 51 cohort runs,
114 available inference requests and 45 explicit unavailable requests. Fixtures
include asymmetric ties, negative covariance, below-chance scores, constants,
perfect/inverted markers, duplicate/affine models, distinct marker missingness,
reordered levels, literal `"NA"` labels, small classes, normal/skewed samples,
public pROC aSAH data and extreme finite scores.

The initial numerical harness incorrectly normalized the literal expected label
`"NA"` to missing. Its three label comparisons failed; no numerical formula
comparison failed. The harness was corrected to preserve labels, without changing
target calculations, frozen reference values or tolerance. The original failed
log, matrix and summary are retained.

Ten focused Python tests additionally exercise threshold ties, event/direction
reversal, factor-level reordering/renaming, common-cohort alignment, row permutation,
monotone transformations, paired contrast covariance, confidence nesting, bounded
versus raw limits, extreme-score JSON serialization and invalid input/resource
guards. These source checks do not establish public-wrapper or GUI behavior.

The final source suite passes **527 Python tests** (201.169 seconds). Generator
and registry/status freshness checks pass. Final-source simulation replay is
byte-identical. The qualified 0.3.63 archive hash is unchanged; no native R/GUI
acceptance or package build was performed for this source-only increment.

## Simulation and inferential limitations

A fixed-input simulation evaluates 12,000 independent datasets: 2,000 per each
of six scenarios, with 10, 30 or 100 observations per class. Two paired markers
have within-class correlation .7 and unit normal variance. Marker A has case
mean shift .8; marker B has shift .8 under the paired null or .4 under the
specified alternative. Population AUC is `Phi(shift/sqrt(2))`; each true AUC
difference is therefore known independently of the empirical method.

| Scenario | Per class | AUC A coverage | AUC B coverage | Difference coverage | Rejection rate |
|---|---:|---:|---:|---:|---:|
| Paired null | 10 | 91.95% | 92.55% | 96.60% | 3.40% |
| Paired alternative | 10 | 90.45% | 91.85% | 94.40% | 15.05% |
| Paired null | 30 | 94.10% | 93.85% | 95.15% | 4.85% |
| Paired alternative | 30 | 93.60% | 93.45% | 95.70% | 39.80% |
| Paired null | 100 | 94.90% | 94.15% | 94.80% | 5.20% |
| Paired alternative | 100 | 94.15% | 94.25% | 95.25% | 91.70% |

Coverage refers to nominal 95% intervals. Rejection uses two-sided p<.05 and
means type-I error only in null scenarios; under the alternative it is power.
The report records input hashes, availability, Monte Carlo SEs and Wilson
intervals. All simulated intervals/tests were available. Small-class marginal
coverage is materially below nominal; numerical parity does not repair that
normal-approximation limitation. Neither the two-per-class variance requirement
nor these six scenarios establish a clinically adequate minimum sample size.
Imbalanced, clustered, discrete/boundary and fitted-model performance remain
outside this simulation. No general nominal-coverage or clinical claim is made.

## Native implementation follow-up

The [native follow-up](python-roc-native.md) implements a narrow SPEC under the
preallocated **`pyenhancedroc`** identifier. The interface contract was: Keep essential reference,
positive level, selected scores and each direction visible in **Data and roles**.
Put fixed empirical/paired methods under **Analysis**, confidence and multiplicity
under **Uncertainty**, cohort/assumption reporting under **Results**, and local
ROC/threshold inspection with a native static counterpart under **Plots**.

Interactions may inspect already computed points. Any change to cohort, direction
or applied threshold must use the saved analysis options/Apply path; JavaScript
must not silently replace native estimates or refit models. Native integration
must disclose approximate uncertainty, small-class limitations, degeneracies and
unadjusted pairwise tests. Compatibility, valid→incomplete→valid clearing,
fresh-engine saved-file reopening and table/plot exports remain required.

`pydecisioncompare` still needs a separate binary paired-test contract and oracle.
CCC uncertainty research remains parked. The initial numerical core alone did not count as an executable menu port.
The subsequent native adapter advances partial status, without establishing
full parity or package/desktop release readiness.

## Reproduction and evidence

- [Frozen core/baseline contract](validation-exports/python-roc-contract-20261111.json)
- [Numerical matrix summary](validation-exports/python-roc-numerical-20261111.json)
- [Known-truth simulation](validation-exports/python-roc-coverage-20261111.json)
- [Source qualification and regression record](validation-exports/python-roc-qualification-20261111.json)

From the repository root:

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
/Applications/jamovi.app/Contents/MacOS/python -B -S tools/check-roc-delong.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
/Applications/jamovi.app/Contents/MacOS/python -B -S tools/check-roc-coverage.py
```

The R oracle requires the existing developer pROC/jsonlite installation only;
the Python runtime uses the module's existing NumPy/SciPy stack.
