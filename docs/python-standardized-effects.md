# Standardized raw-mean effects — source contract (2026-11-12)

The core source/reference gate is complete and the existing analyses now have
[optional native source integration](python-standardized-native.md). These added results are now packaged and locally GUI-qualified in 0.3.68;
the separate native record identifies the precise macOS acceptance boundary.

## Estimands and supported models

- Independent: explicitly request `standardizer="pooled"`. Use the sample-size
  weighted pooled sample SD, Student df = n1+n2-2, and first minus second.
  Population target delta = (mu1-mu2)/sigma under independent normal populations
  with a common variance. This does not supply a Welch-compatible unequal-variance
  effect or switch the native Welch default.
- Paired: explicitly request `standardizer="difference"`. Use sample SD of the
  within-row differences, df = n-1, and first minus second. Population target
  delta_z = E(first-second)/SD(first-second), assuming independent normal
  subject-level differences. This is d_z; it is not d_av or a marginal-SD effect.

Report Cohen d (or d_z), exact Hedges correction
J(df) = Gamma(df/2) / [sqrt(df/2) Gamma((df-1)/2)], and the bias-corrected point
J*d (or J*d_z). Do not report conventional small/medium/large or clinical bands.

The two-sided population-delta interval inverts the noncentral t CDF at the
observed Student/paired t, then multiplies the noncentrality limits by
sqrt(1/n1+1/n2) or 1/sqrt(n). Its limits describe the population standardized
mean contrast, not the raw mean. They are not multiplied by J. Hedges g is a
second point estimator of that same population target; this increment does not
provide separately labelled g limits. In particular, it does not claim numerical
parity with effectsize's J-scaled g intervals.

The [effectsize documentation](https://easystats.github.io/effectsize/reference/cohens_d.html)
distinguishes pooled independent and difference-standardized paired effects and
uses noncentral-t inversion. Its installed 1.0.3 implementation also multiplies
g confidence bounds by J. The [MBESS ci.smd contract](https://rdrr.io/cran/MBESS/man/ci.smd.html)
explicitly targets population delta with a pooled denominator and equal variances.
The frozen plotting baselines delegate effect sizes to statsExpressions; matching
all their method-specific choices remains a later parity gate.

## Cohort, degeneracy and numerical contract

Reuse the checked raw-mean engine's exact source cohort, labels, optional subject
IDs, numeric-storage validation, missingness policy and minimum N. Never pair by
sorting or independently remove missing measurements. No existing calculation is
changed. Production uses the already bundled NumPy/SciPy; effectsize and MBESS
are development reference packages only, with no new user dependency. Raw-degenerate inputs leave all standardized estimates and limits null.
An invalid standardizer is an input error, with no fallback.

The noncentral-t interval solver checks its probability residuals and finite,
ordered endpoints. Supported inversion range is |t| <= 40, df >= 2, with the raw
core's confidence range 0.50–0.999 and source-row cap. Outside that numerical range,
or if convergence checks fail, retain finite standardized point estimates but
return null interval limits with explicit `interval_unavailable` status and a
reason. Do not use normal approximations, truncate limits or invent zero-width
intervals. All outputs must serialize as strict JSON.

## Acceptance gates

Freeze independently generated R fixtures before the Python implementation:
32 existing independent input datasets, five confidence levels; a separate t/df
inversion grid including negative/zero/large t and low/high df; numerical mixture
integration for selected difficult tails; interior comparisons with effectsize
and MBESS. Reproduce the R fixture byte-for-byte. Test denominator choice,
contrast reversal, paired covariance, scaling, missingness/ID alignment, exact
J versus the approximation, degeneracy and solver failure. Retain any oracle
limitations and failures explicitly. Then run the full Python regressions and
freshness checks before considering native integration.


## Native integration contract

Keep standardized results off by default. For independent analyses, expose pooled
results only with an explicit equal-variance model; do not rewrite the raw Welch
choice. For paired analyses, label d_z/g_z and the difference-SD denominator.
Separate Cohen population-delta limits from Hedges point-only output in both the
control labels and table columns. Clearing a model/effect option must clear its
own outputs without changing the raw tables. Validate reuse-versus-fresh results,
source alignment, serialized rendering and new-package desktop acceptance before
marking any standardized effect as native/GUI qualified.

## Source implementation and evidence

`inst/python/cpj_standardized.py` exposes `between_standardized` and
`within_standardized`, with a mandatory explicit standardizer. Each returns the
unchanged raw result plus a separate standardized block. The shared native adapter
now imports this helper only when standardized output is requested under the
qualified Student/paired models. Noncentral-t inversion uses SciPy with checked bracket/root/CDF
residuals, explicit solver convergence status and symmetry for negative t. Root
residual tolerance is 2e-10; exhausted-iteration probes verify null limits with
finite points. The standardized result also carries its design assumptions. An
unqualified numerical range or solver failure returns explicit interval-unavailable
status while preserving finite point estimates; unrelated programming errors propagate.

`tests/reference/standardized-effects.R` freezes 32 independent input datasets and
160 confidence configurations. Independent base-R `pt`/`uniroot` provide 210
additional t/df configurations. Twenty tail cases, including t=40 and df up to
99,998, use a separate normal/chi-square integral. All **420 final pt-grid
endpoints** additionally satisfy that independent integral, with maximum probability
residual **3.49e-11** (screen tolerance 2e-8). R's pt-based oracle emits precision warnings during inversion; these are retained
in logs and do not substitute for the independent final-endpoint audit. Ordinary-scale Cohen d and Hedges g points, Cohen delta intervals
and MBESS intervals pass **126 package cross-checks** (maximum difference 1.93e-7;
package-comparison tolerance 2e-4).

The first quantile-probability mixture integration failed near a steep endpoint.
Before freezing numeric targets or writing the Python implementation, it was
replaced by integration conditional on a standard normal variate over [-12,12],
with omitted normal-tail mass below 4e-33. Base-R chi-square survival probabilities
supply the conditional integrand. The later 420-endpoint audit added evidence
fields without changing any numerical target; the pre-audit fixture is retained
locally. No target Python values generate reference targets. The final audited fixture
replays byte-for-byte, SHA-256
`7f68a5deb5d7f5cad9c3d11cd1d5b5b8c86bc466940cc2f5d11a5b46aa18fd46`.

`tools/check-standardized-effects.py` passes **2,060 numerical comparisons**, with
maximum absolute difference scaled by max(1,abs(target)) **2.61e-9**. Prespecified
point tolerance is 1e-10 relative (exact zero targets); interval tolerance is 2e-7
scaled absolute. These are numerical tolerances, not clinical acceptance bands.
Eleven focused tests cover all fixtures, denominator/J formulas, raw default
preservation, exact labels/pair alignment, scale/reversal/confidence properties,
invalid inputs, degenerate data, unavailable-range and forced solver failures.
Five in-memory mutations are rejected: reference-group SD substitution,
approximate J, J-scaled delta limits, reversed contrast and lost paired covariance.

Reproduce with R `tests/reference/standardized-effects.R` and bundled Python
`tools/check-standardized-effects.py` / `tests/python/test_standardized_effects.py`.
The bundled interpreter omits unittest's `__main__`; run the test file directly or
use an imported unittest runner. Logs and generated validation JSON remain ignored.

Native controls/tables/plots and 0.3.68 package/save/reopen/export qualification
are recorded separately in the native record. The 0.3.67 rollback is archived; this source milestone does not increase the
32 partial / 29 planned / 15 utility inventory counts or establish full parity.


Minimal source usage (no jamovi UI change):

```python
from cpj_standardized import within_standardized
result = within_standardized(
    [10, 12, 8, 15, 9, 18], [8, 11, 9, 12, 7, 14],
    standardizer="difference", confidence=.95,
)
raw = result["raw"]
effect = result["standardized"]
# Check effect["status"] before using delta_lower / delta_upper.
# effect["hedges_g"] is a point estimate, with no g-specific CI fields.
```


Final regression gate: **599 Python tests pass** against the final convergence-guarded
source, including all 11 focused tests; generator/status freshness and whitespace
checks pass. The initial 599-test run also passed before guard hardening. An
in-memory red/green replay verifies that the initial solver raised RuntimeError
on zero allowed iterations, while the hardened solver retains finite points and
returns explicit unavailable limits. Unexpected programming errors still
propagate. At that source gate, the installed 0.3.67 archive and all 1,452 files were unchanged;
0.3.68 subsequently completed the separate package/native GUI qualification.
This records the source/reference gate; native integration evidence is tracked
separately in the native record.
