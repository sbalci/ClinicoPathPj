# Histogram and one-sample mean core — frozen source contract

This records the original source-only checkpoint. The subsequent native histogram
integration and geometry qualification are tracked in
[the geometry/native record](python-histogram-geometry.md). The source-only menu
statements below describe that earlier checkpoint, not the current registry.


## Scope frozen before implementation (2026-11-12)

Next baseline target: `pyjjhistostats`, currently planned. This first increment
adds reusable Python calculations outside individual analyses, not a menu entry.
The installed/qualified 0.3.69 module and all existing defaults remain unchanged.
Native integration follows only after automatic/manual bin placement, supported
options and rendering are explicitly specified against the frozen baseline.

Verify all four archived `jjhistostats` source hashes against the registry before
work. The reference is the frozen working-tree archive, not a claim about a published
JMO. Its YAML says the statistic selector does not compute Shapiro-Wilk, but its
backend computes Shapiro-Wilk in conditional warnings and clinical interpretation.
Record that discrepancy rather than treating the help sentence as statistical truth.
The registry's baseline methods remain unchanged; this increment implements no
normality classifier, clinical interpretation or automatic method switch.

## Data, summaries and one-sample mean test

Use the existing strict numeric/missingness and subject-ID policies: 1–100,000
source rows; finite real measurements with None/NaN missing; reject booleans,
strings, complex numbers, masked arrays, matrices and Inf. At least one retained
measurement is required. Keep source size, retained indices, missing count and
retained exact string IDs (if supplied). Missing IDs on excluded rows do not change
the outcome cohort. Retained IDs must be known/unique; IDs do not prove independence.

Summaries: n, arithmetic mean, Bessel sample SD (null at n=1), min, quartiles and
median (R quantile type 7), max. Preserve units. Detect nonfinite/underflowing
moments rather than reporting fake constant-data estimates.

Optional future native one-sample inference uses only an explicit two-sided
Student t-test. Source function defaults reference=0, confidence=.95; validate
finite real reference and confidence .50–.999. Estimate is mean minus reference;
SE=sample SD/sqrt(n); df=n-1; t=estimate/SE; p=2*t.sf(abs(t),df). Return both mean
CI and mean-minus-reference CI with unambiguous names. Independent observations
and a normal sampling model are the inferential assumptions; no pretest selects
another method, no clinical bands are assigned.

At n=1 retain summaries/contrast but null all inferential fields with
`status='insufficient_n'`. At zero SE or
`SE < 10*machine_epsilon*abs(sample_mean)` retain summaries/contrast, null all
inferential fields with `status='degenerate'`. Arithmetic overflow/underflow
raises InputError. This is the base-R one-sample t.test numerical guard; no
automatic continuity correction or zero-width interval. General standardized
effects, nonparametric/robust/Bayesian tests, one-sided tests, groups/multiple
endpoints, bootstrap methods and Shapiro-Wilk are outside this increment.

## Explicit-boundary histogram

Require explicit finite strictly increasing breaks (2–2,001 values, at most 2,000
bins), covering every retained observation, and explicit `closure='right'` or
`'left'`. Do not silently truncate observations outside the edges or merge sparse
bins. Right closure uses [e0,e1],(e1,e2],...; left closure uses [e0,e1),...,[ek-1,ek].
Thus both outermost endpoints are included, and an exact internal-edge tie has a
specified side. No tolerance/fuzz reassigns near-edge values.

Return each bin's bounds, closed-side flags, integer count, proportion count/n,
and density=count/(n*width), plus the same cohort audit and summaries. Empty bins
remain explicit zero counts. Every retained observation occurs exactly once;
counts sum to n, proportions to one, and density*width integrates to one. Reject
unrepresentable widths/densities and duplicate/unsorted/nonfinite breaks. Constant
and singleton observations can be counted given explicit valid edges; their lack
of inferential spread is handled separately by the mean-test function.

This is a deterministic binning primitive, not a claim of ggplot2/gghistostats
automatic bin-width/origin/floating-edge parity. Do not reuse NumPy's automatic
histogram policy as if it were the frozen umbrella default. Preserve the existing
plot-ready/native histogram renderer until a later explicit integration change.

## Prespecified independent validation

An independent R builder, without target Python code or expected outputs, freezes
fixtures before the engine. Histogram reference: stats::hist(...,right=closure,
include.lowest=TRUE,fuzz=0,plot=FALSE), independently cross-checked by direct bin
membership arithmetic. Summaries: mean/sd/quantile(type=7). Inference: stats::t.test
on the same complete values, two-sided, across references 0/nonzero and confidence
.50/.80/.95/.99/.999. Use a second explicit formula for t, df, p and t-quantile
limits. Preserve unavailable cases and warnings separately.

Include tiny hand-countable fixtures, internal/outer edge ties, values just to
either side of edges, nonuniform bins, negative values, zero/constant/singleton,
missingness, n=2, asymmetry, large offsets and 1e-100/1e100 scales, plus seeded
normal and skewed samples. R writes actual input values/breaks in the fixture;
a seed alone is not numerical agreement. Compare points/moments at relative
1e-10 (zero targets absolute 1e-12); interval endpoints at scaled absolute 2e-7;
counts/cohort identities/statuses exact. Compare all endpoints without shrinking
the case set after observing target output.

Require deterministic byte-identical R replay; mass/scale/shift/reversal and
reference-shift properties; invalid inputs and resource caps; JSON with no NaN/Inf;
and corruption/mutation probes for bin closure, lost counts, n versus n-1 SD,
reference subtraction and one-sided p values. Run the frozen full Python suite
and generator/status freshness. Preserve 0.3.69 archive/installed bytes. Native,
GUI, automatic binning, plotting geometry and full baseline parity remain separate.

## Executed source evidence

The independent builder generated `tests/reference/histogram-core.R` and froze
`tests/fixtures/histogram-core.json` before the target Python implementation.
All four archive hashes match the registry. Histogram counts agree between
base-R `hist(fuzz=0)` and explicit bin membership; available mean tests agree
between `t.test` and independently written t/quantile equations. The fixture
contains exact double-round-tripped observations and breaks, including adjacent
floating-point values; it is intentionally not rounded for display.

`inst/python/cpj_histogram.py` implements the two source functions.
`tools/check-histogram-core.py` passes **6,538 comparisons** over **21 datasets**,
**42 histograms** and **210 inference runs** (252 configurations; 142 bin rows).
The maximum scaled absolute difference is 1.62e-11, within the frozen tolerances.
Eleven focused tests additionally verify interval-endpoint ties, mass/density
conservation, exact identity/missingness, shift/scale/reflection properties,
confidence/reference behavior, resource caps, invalid input and JSON finiteness.
Five deliberate mutations (closure, lost count, n-denominator SD, missing reference
subtraction, one-sided p) are rejected by the independent checker.

Independent R replay is byte-identical, SHA-256
`54058633145b48688d2663908c9022f467b11c038dc8d4f706d2c72f570a5fe9`.
There are 160 available, 30 degenerate and 20 insufficient-n inference runs.
R emitted no warnings. Ten explicit base-R discrepancies are retained: at all-zero
data/reference 0, base R gives NaN t/p/limits; at reference .75 it gives -Inf t,
p=0 and NaN limits. The Python contract deliberately returns null inference and
`degenerate` in both cases. This is not a claim of parity with undefined R output.

The final frozen-source suite passes **638 Python tests** in 264.305 seconds,
with no failures/errors/skips. Generator/status freshness and whitespace checks
excluding compiler-owned `.h.R` output pass. No R bridge, native option/result,
renderer or installed runtime was modified; this does not establish native/GUI
or automatic-bin geometry qualification.

Source API example (using the bundled Python with `inst/python` on its import path):

```python
from cpj_histogram import histogram_core, one_sample_core

bins = histogram_core([0, 1, 2], breaks=[0, 1, 2], closure="right")
assert [row["count"] for row in bins["bins"]] == [2, 1]
test = one_sample_core([0, 1, 2], reference=0.75)
assert test["difference"] == 0.25
```

## Baseline decisions before native integration

Read-only local inspection finds ggstatsplot **1.1.1** and ggplot2 **4.0.3**.
The local `gghistostats` formals have binwidth=NULL, reference=0, confidence=.95,
and results.subtitle=TRUE. The frozen wrapper overrides results.subtitle with its
own option default FALSE. Its local `.binwidth(x)` helper is exactly
`(max(x,na.rm=TRUE)-min(x,na.rm=TRUE))/sqrt(length(x))`. These observations identify
the next oracle target; they do not replace the frozen wrapper or establish an
external dependency version for a historical published JMO.

Next freeze and independently compare bin origin, break padding, right-closure
and floating-edge handling through ggplot2's actual built histogram geometry,
for automatic and explicit manual width, including missing/constant/singleton
inputs and resource limits. Do not promote this no-fuzz primitive as if it already
matched that geometry. Then author the reserved `pyjjhistostats` SPEC/run interface
with organized data/model/results/plot controls, explicit inferential roles and
omissions, native tables/static histogram, and lifecycle validation. Preserve
statistical defaults and reject unsupported baseline methods/presets explicitly.
Split/multiple-variable panels, one-sided/robust/Bayesian/nonparametric inference,
Hedges effects, diagnostics/normality interpretation, KDE/QQ/ECDF and interaction
remain separate gates. The public registry stays planned and its source stays null.

The qualified 0.3.69 JMO SHA-256 remains
`ba611d30509e94356641843597e30bcc2ff9c3971f01321d5a03323f33b8ad6b`;
all 1,454 installed files still match. No package/UI/default/namespace change is
part of this source increment. The existing histogram renderer is unchanged.

Reproduce from the ClinicoPathPj root:

```sh
Rscript --vanilla tests/reference/histogram-core.R
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-histogram-core.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tests/python/test_histogram_core.py
python3 tools/generate.py --check
python3 tools/migration-status.py --check
```
