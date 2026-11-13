# Histogram geometry and native core — frozen increment contract

## Geometry contract (2026-11-12, before implementation)

Target ggstatsplot 1.1.1 width helper with ggplot2 4.0.3 stat_bin geometry, the
locally inspected dependencies called by the frozen jjhistostats wrapper. Preserve
its default automatic width `(max(x)-min(x))/sqrt(n)` on retained measurements;
manual width must be an explicit positive finite real number. One variable, no
splits/weights/transforms. Keep every retained observation and every empty bin.

With width w and original range [xmin,xmax], default boundary=w/2,
shift=floor((xmin-boundary)/w), origin=boundary+shift*w, upper=xmax+(1-1e-8)*w.
Use the R seq(origin,upper,by=w) sequence (minimum two edges). Right-closed
counting uses fuzzy edges: first edge minus f, all others plus f, where
f=1e-8*median(diff(raw_edges)). Both outside endpoints are included. This is a
separate geometry function; do not change the already validated exact no-fuzz
explicit-boundary histogram primitive.

Return raw and fuzzy edges, requested width, automatic/manual flag, plot bin
centers/widths/lower/upper/count/proportion/density and cohort/summary audit.
Plot lower/upper bounds are recomputed as center +/- width/2, as ggplot2 bin_out
does, and may differ from raw edges by floating-point rounding. Density uses
count/actual_bin_width/n. Counts must sum to retained n; proportions and integrated
density sum to one. Reject widths/edges that overflow, collapse or exceed the
existing renderer's 2,000-bin cap; no silent truncation or resampling.

Automatic constant/singleton data have width zero and ggplot2 returns an empty
panel with a warning. Return `geometry_status='constant_auto'`, no bins and a
reason recommending an explicit positive manual width; retain all summaries.
Manual constant/singleton data can have a valid histogram. Other numeric/size
failures raise InputError rather than approximate silently.

Independent R fixtures must be frozen before Python geometry implementation.
Use actual ggplot_build(geom_histogram(...,closed='right',pad=FALSE)) output and
independently inspect raw/fuzzy breaks. Verify actual gghistostats default width
and wrapper hashes. Include ordinary/negative/fractional values, missingness,
constant/singleton, automatic/manual widths, raw and fuzzy boundary ties and
adjacent doubles, sparse bins, shifted/large offsets and 1e-100/1e100 scales.
Serialize exact doubles (reuse the independent R 17-digit encoder). Keep warnings
and unavailable outcomes explicit. Bin counts/status/cohorts are exact; geometry
numbers use relative 1e-10 (zero absolute 1e-12). Preserve interval oracle tolerances
from the existing mean core; do not change them to fit geometry. Require deterministic
R replay and tests that reject omitted fuzz, altered origin and lost counts.

## Native interface contract

After geometry passes, implement reserved `pyjjhistostats` as a partial native
entry under Stats Plots Py → Distribution, preserving its py identifier. One
numeric outcome; optional exact subject-ID audit. Native tables for retained
cohort, summaries, binning/audit, optional bins and optional one-sample Student
results; static native Image histogram, with optional mean line. No interactive
view in this increment. Existing renderer/state/assets must remain local.

Preserve supported wrapper defaults: typestatistics=parametric, changebinwidth=FALSE,
binwidth=1.1, centralityline=FALSE, resultssubtitle=FALSE,
enableOneSampleTest=FALSE (custom null control), null=0, confidence=.95 and
two-sided alternative. The custom-null switch controls the null only; it is not
a test on/off switch. Statistical results off must not execute inference. Report
requested Student results in native tables; statistical plot subtitle annotations
are omitted explicitly in this first native renderer. Fixed plot size defaults
600×450. No Hedges effect, Shapiro-Wilk/normality classifier, clinical heuristics,
one-sided/nonparametric/robust/Bayesian methods, presets, splits/multiple outcomes,
KDE/QQ/ECDF or ggpubr alternatives. Reject unsupported restored requests.

All inference runs in Python. Warn about assumptions without a normality pretest
or automatic method switch. Show unavailable single/constant inference honestly.
For automatic constant data, leave the plot unpopulated and explain manual-width
recovery; do not hide a failed result dynamically or invent a width. UI sections
are generator-owned, with variable roles first and controls enabled only when
applicable. Existing released analyses/defaults remain unchanged.

Require adapter/reference comparisons, source Python regression/freshness,
compiler preparation and isolated native lifecycle/serialization/rendering checks.
Do not rebuild or replace qualified 0.3.69 before source gates pass; actual package,
GUI save/reopen/export, clinical review and other platforms are separate gates.

## Implemented source/native subset

`inst/python/cpj_histogram_geometry.py` implements the geometry separately from the
exact no-fuzz primitive. `cpj_histogram_adapter.py` presents it through the literal
`analyses/jjstatsplot/pyjjhistostats.py` SPEC. The generator owns the analysis/UI/
results YAML and R bridge; compiler preparation creates the header. The public
identifier remains `pyjjhistostats`, under Stats Plots Py → Distribution →
Histogram (core). Its registry status is **partial**, not full parity.

| Feature | Current behavior | Boundary |
|---|---|---|
| Data | One scalar numeric measurement; optional exact text/factor subject IDs | 1–100,000 source rows; retained IDs known/unique; IDs do not prove independence |
| Cohort/summaries | Source/retained/missing counts, n/mean/sample SD, type-7 quartiles/range | No groups, splits, weights, transformations or multiple outcomes |
| Binning | Automatic range/sqrt(n), or explicit positive manual width; right-closed fuzzy edges | Maximum 2,000 bins; preserve empty bins and all retained observations |
| Display | Native Image count histogram, optional dashed mean line; 600×450 logical default | Static only; no statistical plot subtitle, density/QQ/ECDF or ggpubr panels |
| Student results | Optional two-sided test, mean/reference contrast, separate mean and contrast CI rows | No standardized effects, rank, robust, Bayesian, one-sided or bootstrap methods |
| Optional audit rows | Bin frequencies/densities; up to 1,000 exact source/subject/value rows | Display limit disclosed; all retained measurements still contribute |
| Interpretation | Independent-case/normal-model assumptions; unavailable-state notices | No normality classifier, clinical presets/thresholds or automatic method selection |
| Lifecycle | Clear optional/invalid state; recover input, custom null, width and confidence | Native R6/serialized drawing-state evidence; desktop OMV lifecycle still pending |

Supported wrapper defaults are preserved. `resultssubtitle=FALSE` means no inference
is computed. `enableOneSampleTest=FALSE` selects reference zero; enabling it selects
`testValue`. It does not turn the test on. Native `testValue`/`conflevel` correspond
to the original R `test.value`/`conf.level` names. This is a new Python public entry;
there is no earlier released Python histogram option contract to rename. Student
and two-sided choices are fixed visible labels, not dropdowns offering unsupported
methods. Unsupported restored requests are rejected explicitly. Plot colors/theme
follow the existing jamovi bridge rather than exposing frozen wrapper styling options.

The synthetic Data Library CSV `data/python_histogram_examples.csv` contains 20
retained measurements and two missing rows. With manual width 2, counts are
**5, 7, 4, 1, 1, 1, 0, 0, 0, 1**: bars have unequal heights and empty bins remain.
These are invented measurements, not patient or clinical reference data.

## Independent numerical evidence and discrepancies

The blinded builder froze `tests/reference/histogram-geometry.R` and
`tests/fixtures/histogram-geometry.json` before target implementation. It runs
actual `ggplot_build` histogram and stat layers, checks the default ggstatsplot
width helper, and verifies all four archived wrapper hashes. Versions are local
R 4.6.0, ggplot2 4.0.3 and ggstatsplot 1.1.1; this does not establish dependency
versions inside a historical published JMO. The fixture has exact-double numeric
round-trips and replays byte-for-byte.

There are **20 datasets / 54 configurations**: 42 supported, four automatic
constant/singleton cases, eight expected refusals. The checker passes **3,502
geometry/cohort comparisons**, including 306 bin rows, with zero numeric difference
for supported geometry. Seven focused tests verify edge fuzz, bin origin, count/
density conservation, constants/manual recovery, identities, resource/numeric
refusals, exact arithmetic and three rejected geometry mutations. Six adapter
tests cover all 54 geometry configurations and all 210 original R Student runs,
option gating, original source identities, no inference when off and subprocess
execution. The original core's 6,538 R comparisons and 11 focused tests still pass.

Six R warnings are retained in the fixture. Refusals are deliberately separate:
three capped allocations, two overflow/numeric failures and three large-offset
count-loss cases. At `1e15 + c(-2,-1,0,1,2)`, actual ggplot2 counts only one of five
observations for three widths. Python rejects the unsafe geometry; it does not
copy those counts, silently re-center values or choose another width.
`geom_histogram`'s layer `width` aesthetic defaults to 0.9 and is not the statistical
bin width; the oracle uses the stat layer and verifies actual displayed bounds.

A separate summary-precision discrepancy remains in the frozen R fixture for
`fuzzy_edge_neighbors`. The initial scaled Python mean differed from R by
3.33e-16. A blinded exact `Fraction.from_float` sum establishes the true mean as
`1080863913 / 144115188075855872`, exactly representable as a double. Compensated
summation now returns this value exactly. R differs from it by 4.85722573273506e-17
(relative 6.4763e-9), so even the exact mean fails a relative 1e-10 comparison to
this R result. The fixture and tolerances were not revised to declare agreement.
Geometry checks do not count float summary means as geometry agreement; summaries/
inference retain the separate core references and the new exact-rational guard.
The precision repair is confined to this histogram helper; existing mean-comparison
engines and statistical defaults remain unchanged. If an unscaled sum overflows,
the already validated scaled-moment mean remains the fallback.

Fixture SHA-256: `e6e848f682b542e2bb1c40224db2b35ff5f7adeaf7421ce3f2937d4f9532cdd8`.
Oracle script SHA-256: `2bd287a90eaf92b8aebe269a4bf74a34b61b3a2e7b935ab9123cda226efb8fb7`.

## Reproduce source/native checks

From the ClinicoPathPj root, use jamovi's bundled interpreter (no package installs):

```sh
Rscript --vanilla tests/reference/histogram-geometry.R /private/tmp/geometry-replay.json
cmp tests/fixtures/histogram-geometry.json /private/tmp/geometry-replay.json
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-histogram-geometry.py
python3 tools/generate.py --check
python3 tools/migration-status.py --check
```

Prepare with the existing jamovi compiler, document and install into an isolated
R library, then run `tools/check-histogram-native.R <library>` with the same
`PYTHONHOME`. `tools/render-histogram-example.R <library> <output.png>` renders
the unequal-count example through native results. Native process supervision
requires an environment permitting processx's local supervisor; sandbox denial
is an environment failure, not a reason to weaken production cleanup.

## Final-source regression and native qualification

All **651 Python tests** pass in 285.163 seconds, with no failures/errors/skips.
Generator/status freshness, compiler preparation, roxygen documentation and an
isolated source installation pass. The four histogram Python source files in the
isolated R library match the final source bytes. The precision repair also has
an in-memory red/green replay: the prior scaled mean fails the exact-rational
expectation, and the repaired compensated mean passes; neither oracle fixture
was changed.

The final isolated native suite passes **671 assertions**, with zero failures,
errors, warnings or skips. It compares 21 original mean datasets and all 54
geometry configurations, checks exact retained source/subject IDs, custom-null
semantics and confidence changes, clears/restores optional and invalid results,
recovers constant/manual/automatic states and verifies a fresh unconfigured R6
analysis. Drawing-state RDS restoration followed by native PNG export works after
`private$.data` is removed. This is not an OMV serialization or desktop acceptance
claim. The earlier empty direct-wrapper failure is retained below.

The native synthetic example exports correctly and was visually inspected for
unequal count heights, empty bins and the mean line. The existing Image renderer
is unchanged. See the [native source example PNG](validation-exports/python-histogram-source.png)
(1200×900 export pixels for the 600×450 logical default). This is an automated
native export from the isolated library, not a desktop GUI export.

An initial direct R call with a data.frame and zero selected columns hit jmvcore's
`invalid 'row.names' length` in its `select()` initialization before the bridge.
That failed harness run is retained separately. The unconfigured-state test uses
fresh R6 options and dataset-source callbacks, as the GUI does; it does not change
production code to hide the framework error. Direct R callers should supply `dep`.
A Python adapter test also initially used exact binary equality for a
roundoff-sensitive mean line; the corrected test checks it numerically. No count,
edge, interval or independent-reference tolerance was relaxed.

The standard 0.3.69 JMO remains 23,231,003 bytes, SHA-256
`ba611d30509e94356641843597e30bcc2ff9c3971f01321d5a03323f33b8ad6b`.
All **1,454 installed files** still match it. The new histogram is source-only
until the next package qualification: build/archive execution, GUI Sideload,
fresh-engine rerun, OMV save/reopen/recalculation and table/plot export remain open.
Clinical review, full baseline methods and non-arm64 platforms are not established.

## 0.3.70 packaged and GUI qualification — 2026-11-13

This supersedes the source-only/package-pending checkpoint above. The feature
scope is still the bounded partial core, not the full frozen R baseline.

`ClinicoPathPj_0.3.70.jmo` is **23,368,579 bytes**, SHA-256
`a5f20c63d25e7cff154723151d1eb619a5a94bff871b7cdb927eab3f6b6ccfe5`.
The archive passes CRC, unique/safe member names, source/registry/UI/data checks
and bytecode exclusion. Its extracted histogram runtime passes **6,692 checks
across 270 configurations**: all 210 original Student configurations, 54 geometry
configurations and six public-option/refusal cases. The existing independent/
paired/standardized/Welch routes pass another **2,008 checks/102 configurations**
from that same actual JMO. These are complete-route checks, not timing comparisons.
The retained source regression gate is 651 tests; statistical analysis sources are
unchanged from that gate except for version/qualification metadata.

Both the built library and the module installed through **Modules → Manage
installed → Sideload** pass **671 native histogram assertions each**, with no
failures, errors, warnings or skips. All **1,461 archive files** match the installed
module. No separate module namespace or compatibility identifier was added.
The qualified 0.3.69 archive is retained in `packages/archive/` with its original
SHA-256. No commits, pushes or library submission are implied.

Manual desktop checks use **macOS arm64 / jamovi 28.17.0**. Two fresh jamovi sessions
(ports 58091 and 58337, without recording their access tokens) verify:

- Data Library → ClinicoPathPj loads the 22-row synthetic histogram example.
- Stats Plots Py → Distribution displays Histogram (core) exactly once; optional
  controls are disabled appropriately and data roles precede method/results controls.
- Manual width 2, optional exact subject ID, bins/cases/Student results and mean
  line produce the expected cohort, unequal bars and empty bins.
- Custom null 1 and confidence .90 recalculate the contrast to 3 while the mean
  stays 4; turning custom null off restores reference zero even though its stored
  numeric value remains 1. Output-off clears optional tables and plot.
- Removing/restoring the measurement clears/rebuilds computed rows and cached
  image; saved incomplete and recovered states are checked independently.
- A full app restart reopens the recovered OMV with tables and cached plot; a
  .95 → .90 → .95 confidence cycle forces fresh-engine recalculation before Save As.
- Native Image → Export produces PNG, and File → Export produces HTML with native
  tables and an embedded image. The GUI path uses no Svg result or interactive HTML.

The six saved profiles are `valid`, `custom`, `off`, `incomplete`, `recovered` and
`reopened`, in `docs/validation-exports/python-histogram-0.3.70-*.omv`.
`tools/check-histogram-artifacts.py` compares all seven populated native tables
against hand-counted bin expectations and `tests/reference/histogram-example.R`
(base-R mean/sd/quantile/t.test). Dataset, metadata and extended-data bytes remain
identical across all six files. Equivalent recovered/reopened tables match exactly.
Four corruption probes (count, confidence, subject identity, missing plot) are rejected.

The viewport-cached OMV image is **958×718**. Its pixels are identical across valid,
custom, recovered and reopened states and the HTML export. HTML re-encodes PNG bytes
without changing pixels. Native Export uses **1200×900** (600×450 logical default
at 2×); its bytes match the independently rendered source-native example exactly,
SHA-256 `356e5dfb05ff17c09605dc9a1cf387fe780f14f91a14b4b5c016665e2ac60c42`.
The initial artifact harness incorrectly compared pixels across these different
resolutions; that failure is retained separately. Validation now compares exact
pixels only between equal-resolution assets, without resampling or relaxed numeric
tolerances. The figures were also visually inspected in Results.

The package harness initially compared `/var/...` with its resolved `/private/var/...`
path and rejected a correct extracted runtime; canonicalizing both paths fixes the
harness. Intermittent Save As shortcut attempts were completed through the explicit
File menu. Final OMV/HTML/PNG files pass inspection; these observations are not
reported as module calculation failures.

Automatic-width and constant/manual recovery remain independently checked in the
Python/R native suites; this manual GUI example used width 2. Broader automatic/
constant GUI scenarios, themes/accessibility, Windows/Linux/other macOS architectures,
clinical review and omitted R baseline methods remain unqualified.

Reproduce the archive and artifact checks with bundled Python:

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B \
  tools/check-histogram-package.py ClinicoPathPj_0.3.70.jmo
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-histogram-artifacts.py
```

The next source target is a prespecified bounded `pyjjbarstats` core: freeze its
categorical roles, denominators, inference and bar geometry before implementation.
No robust/Bayesian or full statistical-plot parity is inferred from this histogram.
