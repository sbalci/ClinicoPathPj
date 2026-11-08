# ICC(2,k) interval review and coverage study — 2026-11-07

This is developer validation of the balanced ICC prototype. It does not change
the installed module, public `pyagreement` options, frozen R baseline, or clinical
interpretation policy. ICC(2,k)'s public interval remains withheld.

## Algebraic review

The single- and average-rater parameters are related by

\[
 \rho_k = \frac{k\rho_1}{1+(k-1)\rho_1},\qquad
 \rho_1 = \frac{\rho_k}{k-(k-1)\rho_k}.
\]

Substitution in the single-rater nuisance coefficient gives

\[
 a_1=\frac{k\rho_1}{n(1-\rho_1)}
     =\frac{\rho_k}{n(1-\rho_k)},\qquad b=1+(n-1)a_1.
\]

This algebra supports reparameterizing the single-rater interval; inserting
`rho_k` into the original single-rater expression with its extra factor `k`
does not preserve that coefficient. The frozen irr average-rater branch does
use that extra factor. This explains the reference discrepancy but does not,
alone, establish finite-sample coverage or the right policy for inadmissible
estimated variance components.

The [psych maintainer documentation](https://personality-project.org/r/psych/help/ICC.html)
distinguishes the six designs and notes historical corrections to ICC(2,k)
limits. Source implementations are linked in the [prototype method review](python-icc-prototype.md).
The algebra above is our explicit derivation, not a quotation from those manuals.
Transforming bounds also requires checking the valid parameter domain: a lower
bound at or below `-1/(k-1)` crosses a pole. The prototype does not silently
clip such bounds or present an inverted interval.

## Simulation design and reproducibility

`tools/study-icc-coverage.py` draws Gaussian crossed random-effects matrices:

\[
Y_{ij}=S_i+R_j+E_{ij},\quad
\rho_k=\frac{\sigma_S^2}{\sigma_S^2+(\sigma_R^2+\sigma_E^2)/k}.
\]

Independent subject, rater and residual effects are sampled afresh for each
matrix. The 24 configurations cross n=6/20/60, k=2/4, subject variance=.1/1,
rater variance=0/.5, and residual variance=1. There are 2,000 replicates per
configuration, **48,000 matrices** total, with confidence fixed at .95.
Both candidates use the exact same matrix in each replicate, rather than separate
runs that merely share a seed. The ledger records the draw digest per configuration,
engine/script hashes, NumPy/SciPy versions and paired outcome counts.

Two distinct summaries prevent silently discarding unsuccessful intervals:

- **Returned-and-covering rate** (`unconditional_coverage` in JSON): returned
  intervals covering the target divided by all replicates. Withheld intervals
  count as noncoverage in this operational measure; it is not the conditional
  coverage of the intervals that were reported.
- **Conditional coverage:** covered divided by returned intervals, shown alongside
  the return rate and withheld count. This conditions on an outcome-dependent
  subset and cannot replace the first measure or establish general validity.

The 95% Monte Carlo intervals in the JSON describe binomial uncertainty in the
first rate, not uncertainty in a patient's ICC. Paired differences and their Monte
Carlo standard errors use the joint counts from the same replicates.

## Observed results

Values below are percentages. Each row has 2,000 replicates; the full 24-row
ledger is [available here](validation-exports/python-icc-coverage-2026-11-07.json).

| n / k / subject variance / rater variance | Candidate | Returned | Returned and covering | Conditional coverage |
|---|---|---:|---:|---:|
| 6 / 2 / .1 / 0 | Frozen irr | 70.05 | 66.90 | 95.50 |
| 6 / 2 / .1 / 0 | Transformed single | 72.00 | 69.65 | 96.74 |
| 6 / 4 / 1 / .5 | Frozen irr | 99.80 | 95.90 | 96.09 |
| 6 / 4 / 1 / .5 | Transformed single | 99.95 | 95.40 | 95.45 |
| 60 / 4 / 1 / .5 | Frozen irr | 100 | 94.95 | 94.95 |
| 60 / 4 / 1 / .5 | Transformed single | 100 | 93.50 | 93.50 |

Neither candidate dominates every scenario. The low-reliability n=6/k=2 scenario
illustrates why high conditional coverage alone conceals frequent withholding.
The n=60/k=4/subject=1/rater=.5 transformed-single result has no withheld intervals,
so its observed 93.50% is not an availability effect; its Monte Carlo interval is
approximately 92.33–94.54%. These are outcomes of this grid and seed, not a
universal ranking, a sample-size recommendation or a clinical cutoff.

## Independent checks and commands

The first exact matrix from each configuration is retained. A separate R script
checks those matrices against irr 0.85 and psych 2.6.5 without calling the Python
engine: **24 matrices, 48 coefficient comparisons and 48 candidate-interval
comparisons pass**. This extends, rather than replaces, the prior 90 fixed
reference configurations.

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/study-icc-coverage.py \
  > docs/validation-exports/python-icc-coverage-2026-11-07.json
Rscript --vanilla tools/check-icc-coverage.R
```

Four new coverage tests check parameterization, withholding denominators, paired
draw accounting and the recorded joint outcomes. Together with ICC, Bland–Altman,
generator and registry tests, **56 focused tests pass in bundled Python**.
The test report and independent R check are stored alongside the ledger.

## Decision and next implementation

The formula discrepancy is explained; the interval's release policy is not yet
qualified. Keep the transformed-single formula as the algebraically coherent
development candidate, retain frozen irr for explicit comparison, and continue
withholding the public ICC(2,k) interval. Do not choose a formula simply because
it attains the highest observed coverage on this grid. No existing R method or
saved Python analysis changes as a result of this study.

Next specify parameter-domain and nonreturn handling, review small-sample
uncertainty, and broaden validation beyond homoscedastic Gaussian errors. Native
case/rater controls, tables, lifecycle, packaging and fresh-engine qualification
remain separate integration work. Any initial public subset must explicitly
disclose unimplemented ICC(2,k) uncertainty rather than imply full parity.
