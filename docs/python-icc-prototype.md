# Balanced ICC numerical prototype — 2026-11-07

`inst/python/cpj_icc.py` is a reusable numerical prototype for the next
`pyagreement` increment. This page records its numerical-foundation stage.
The subsequent [0.3.59 integration](python-icc-integration.md) exposes the supported
subset under the existing analysis, retaining Bland–Altman defaults and the
frozen R baseline. ICC(2,k) confidence limits remain unavailable; the numerical
prototype alone did not establish native or clinical acceptance.

## Implemented calculation contract

`calculate_icc(ratings, model='icc21', confidence=.95)` takes a wide numeric matrix:
independent cases in rows, balanced rater/measurement slots in columns. It accepts
1–5000 source rows and 2–20 columns; at least two complete cases must remain.
Rows missing any selected rating are excluded together, with retained zero-based
source indices and input/retained/excluded counts returned. Infinity, categorical
storage, invalid dimensions, models and confidence values are rejected. Confidence
is .80–.99; no imputation or outlier deletion is performed.

| Form | Meaning | Prototype uncertainty |
|---|---|---|
| ICC(1,1) | One-way random, single measurement | ANOVA F limits |
| ICC(1,k) | One-way random, mean of k measurements | ANOVA F limits |
| ICC(2,1) | Two-way random, absolute agreement, single rater | Approximate F/Satterthwaite limits |
| ICC(2,k) | Two-way random, absolute agreement, mean of k raters | Withheld; two named review candidates |
| ICC(3,1) | Two-way mixed, consistency, single rater | ANOVA F limits |
| ICC(3,k) | Two-way mixed, consistency, mean of k raters | ANOVA F limits |

The mapping follows the frozen meddecide agreement contract. ICC(3) measures
consistency and does not penalize a constant rater offset as absolute-agreement
ICC(2) does. These labels describe the assumed sampling design; the engine cannot
infer that design or prove row independence. Normal, homoscedastic ANOVA errors
and the relevant random/fixed rater assumptions underpin inference. A subsequent
Gaussian coverage study is linked below; clinical validation remains pending.

The engine computes centered subject, rater, residual and within-case sums of
squares in common scaled units to avoid overflow/underflow. Returned ANOVA mean
squares are explicitly **normalized**, not variances in the original units; the
normalization scale is returned separately. The coefficient and intervals are
dimensionless. Negative estimates are retained without clipping or qualitative
bands. A ratio above one is withheld as an inadmissible variance estimate, while
the raw ratio remains available for audit. Zero/numerically unresolved ANOVA
components suppress inferential limits. Identical columns may yield a point
estimate of one but are not presented with certainty about population reliability.

## Interval discrepancy identified before menu integration

The frozen baseline delegates ICC to `irr::icc()`. The independent fixtures use
installed **irr 0.85** and **psych 2.6.5**, with `psych::ICC(lmer=FALSE)`.
Their source implementations can be inspected in
[irr](https://github.com/cran/irr/blob/master/R/icc.R) and
[psych](https://github.com/cran/psych/blob/master/R/ICC.R).

On the six-case, three-rater example `three_raters`, the ICC(2,k) estimate is
approximately 0.9633822 in both packages. At 95% confidence, the baseline irr
formula gives approximately [0.806, 0.995], whereas transforming the single-rater
ICC limits gives approximately [0.8088504, 0.9946295], matching psych. The average
ICC estimate is used differently in the interval degrees-of-freedom calculation.
The fixture records full precision rather than these rounded illustrations.

Across the 15 ICC(2,k) configurations, **12 have different bounds**. The remaining
three two-case configurations return inverted bounds above one in both packages;
the prototype withholds those candidates. Therefore it does not select a public
ICC(2,k) interval silently. `interval` stays `None`, while `candidate_intervals`
exposes `frozen_irr` and `transformed_single` for developer comparison only.
Neither is designated correct or release-ready by this milestone.

## Reproducible evidence

`tests/reference/icc-balanced.R` generates 90 configurations: five designs × six
forms × confidence .80/.95/.99. It calls both R packages without the Python engine
or jamovi backend. `tests/fixtures/icc-balanced.json` freezes their versions and
full numerical outputs, including invalid intervals rather than replacing them.

Seven focused ICC tests cover both references, a separately constructed ANOVA,
common scaling by 1e±200, translation, sign/row/rater permutation, complete-case
source indices, negative estimates, inadmissible mean-rater ratios, zero variance,
identical raters, invalid storage/confidence and declared bounds. Together with
existing Bland–Altman, generator and registry tests, **52 tests pass in bundled
Python**. See the [evidence record](validation-exports/python-icc-prototype-2026-11-07.json).

## Remaining gates

The [48,000-matrix interval review](python-icc-coverage-study.md) now supplies
algebraic, paired simulation and independent R spot-check evidence. It explains
the formula discrepancy but does not establish a public ICC(2,k) interval policy.

1. Resolve and document the ICC(2,k) interval policy using methodological references
   and coverage simulation, including small samples and negative components.
2. Extend native qualification beyond the scoped 0.3.59 case-ID/role validation,
   model controls, lifecycle, packaged execution and saved-file/HTML checks.
3. Preserve the existing `pyagreement` identifier and Bland–Altman contracts in
   future extensions; do not allocate a duplicate entry.
4. Complete broader platform, pathological-data desktop and clinical review gates.
5. Keep repeated/unbalanced/hierarchical models, categorical agreement, CCC,
   bootstrap inference, clinical bands and cross-platform claims outside this core.
