# Lollipop computation contract — 2026-11-15

Stable identifier `pylollipop`, released jjstatsplot 1.0.82.03, baseline commit
`4c3cbe8de39d6259ee61d5fde28704f45e9cc8ed`. Verify all four registry hashes
against the frozen archive before validating the engine. This increment supplies
source calculations only at its initial milestone; the native increment is recorded
below. No package replacement or desktop qualification is implied.

Accept one numeric vector and one labelled factor with aligned source rows.
Missing pairs are excluded and counted; genuine missing factor levels are missing,
whereas literal `NA` labels remain categories. Reject infinities rather than
silently discarding them (an explicit difference from the frozen R backend).
Require 2–100,000 source rows and at least two groups with complete observations;
retain at most 50 active groups and 1,000 declared levels. Unused levels are
reported but not drawn. No frequency weights or subject-level inference is supplied.

Support the baseline aggregations `mean` (default), `median`, `sum` and `none`.
Aggregated rows follow retained factor order before sorting; unaggregated rows
retain source order. Every point carries its original zero-based source indices.
Unaggregated plots are limited to 10,000 points; repeated categories are explicitly
flagged as overplotting. Summaries describe raw complete values and plotted values
separately: n, mean, median, sample SD, minimum, maximum, range and type-7 quartiles.
The mean reference is the unweighted mean of plotted values, never silently the
raw grand mean. No p-values, intervals or clinical classifications are inferred.

Support `original` (default), stable `value_asc`/`value_desc`, and `group_alpha`
sorting. Alphabetic order uses deterministic Unicode code-point order, equivalent
to UTF-8 byte order; compare R under `LC_COLLATE=C`, not the user's locale.
Original order preserves factor levels in both orientations. With explicit sorting,
the first sorted category is leftmost vertically and topmost horizontally; reverse
the horizontal axis levels, as the frozen baseline does. Report point order and
axis levels independently, including tied groups. Duplicate raw points can share
an axis position. Geometry uses one-based axis slots, a supplied finite baseline
(default 0), and each plotted value as the stem endpoint. No refit during drawing.

Freeze independent base-R `aggregate`, `quantile(type=7)` and actual ggplot2 stem
geometry before implementing Python. Include unequal group sizes, tied extrema,
stable ties, negative values, missing/unused levels, literal and genuine NA,
Unicode/order controls, constant values, singleton groups, offsets and scale.
Test all four aggregations, four sorts and two orientations. Compare counts,
indices, labels and orders exactly and finite numeric fields at a prespecified
2e-12 scaled tolerance. Reject unrepresentable derived summaries/geometry instead
of emitting nonfinite JSON. Use permutation, shift, scaling and membership checks
plus deliberate corruptions as additional evidence.

Rendering, native tables/UI, highlighting/conditional colors, style choices,
interpretation notices, saved-file lifecycle and interactive inspection require
later increments. Registry remains planned until native integration. Preserve the
qualified installed 0.3.72 and the uninstalled 0.3.73 GOF candidate.

## Independent source evidence

The frozen R reference supplies 12 datasets and 384 aggregation/sort/orientation
configurations. All **28,432 comparisons** pass; maximum scaled numeric difference
is **3.99614355576137e-16**, below the prespecified 2e-12 bound. All four archived
baseline hashes match. R fixture replay is byte-identical.

The final-source regression suite passes **714 Python tests** in **290.651 seconds**,
without failures/errors/skips. Generator/status freshness and diff checks pass.
All 1,473 installed 0.3.72 files remain byte-identical to the qualified archive;
the 0.3.73 candidate hash is unchanged. These are source-computation and regression
gates, not native lollipop installation or desktop acceptance.

Eleven focused tests pass, covering all reference configurations, raw versus
plotted means, missing-level/row membership, stable ties and reversed horizontal
axes, permutation/shift/scale identities, input/resource refusals, JSON finiteness,
representable extreme means/medians and five deliberately corrupted outputs.
The source does not infer statistical significance or patient-level independence
from these descriptive calculations.

During oracle preparation, the first ggplot2 segment call lacked an explicit
`yend` mapping; the final oracle explicitly maps each value to the baseline and
checks both endpoints. The fixture was frozen before implementing the target
Python engine. The initial log is retained locally. Before the final source gate,
numeric review replaced a sum-based median with linear interpolation and scaled
mean summation, avoiding overflow for constant 1e308 and premature underflow for
constant 1e-323. The final tests explicitly cover both signs and zero; tolerances
and the frozen independent fixture were unchanged.

Fixture SHA-256:
`43eef9232e64edaf5d5cae32d5b7c5ef53d20f2b3590f722f7a522e533ee1c80`.
Reference SHA-256:
`c29476bf5275c4e6252a6abffaef365244e975b5f413bd6973ebea699f1a63e4`.

```sh
Rscript --vanilla tests/reference/lollipop-core.R /private/tmp/lollipop-replay.json
cmp tests/fixtures/lollipop-core.json /private/tmp/lollipop-replay.json
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-lollipop-core.py
```

Next: native SPEC/run, organized data/aggregation/order/reference controls, separate
raw/plotted tables, bounded Python static rendering, lifecycle and serialized-state
export checks. Desktop installation/save/reopen/export must be qualified separately.

## Native source integration — 2026-11-15

The literal SPEC/run adapter now provides **Stats Plots Py → Group comparisons →
Lollipop Chart (Core, Python)**. The stable `pylollipop` registry entry is partial;
inventory advances to 36 partial / 25 planned / 15 utilities and 51 entries, with
no full-parity claim. The installed 0.3.72 and existing 0.3.73 GOF candidate remain
separate from this source increment.

The measurement and category roles stay visible. Expanded Analysis and Model
controls retain mean aggregation and original factor/source ordering by default.
Results controls expose point values and optional original source rows. Collapsed
plot controls select orientation, finite stem baseline, optional value labels and
the mean-of-plotted-values reference. All options have active consumers; no
unsupported inferential or interactive switches are shown.

Native tables provide cohort/missingness, separate raw/plotted summaries, all
declared nonmissing categories with complete-row counts, plotted values and an
optional source-to-point mapping. Physical row IDs come from the host transport,
not shortened-table positions. Point and case listings truncate explicitly at
1,000; all observations contribute and all supported points are drawn. The source
core's 10,000-point and 50-active-category limits remain in force. No aggregation
warns about overlapping observations. The eight-row synthetic CSV demonstrates
six complete observations with raw mean 30.67 and group-mean average 37.33.

The typed static drawing payload stores only labels, axis slots, values, baseline,
orientation, optional annotations and the calculated reference. Python constructs
stems and point markers using jamovi's supplied global palette/theme. R displays
the completed PNG. Rendering does not access source observations or call the
statistical engine. Bounds, mapping consistency, contiguity, finite spans and
orientation are checked before drawing.

Six adapter/renderer tests pass: all 384 independent configurations, source-ID
mapping, gated outputs/defaults, bounded listing disclosures, unsupported-option
refusal, a real subprocess, stem/scatter/axis agreement, no refit while drawing,
and corrupted-state refusals. An initial renderer test caught two reference lines:
the shared plot layer drew a horizontal line before the dedicated renderer drew
the orientation-aware line. The shared line now excludes only this new plot kind;
existing plot kinds retain their behavior. The corrected test requires exactly one
reference line in both orientations. The failed log is retained locally.

Compiler preparation, roxygen and isolated-source installation pass. The isolated
native suite passes **2,228 assertions**, without failures/errors/warnings/skips.
It checks 96 independent reference configurations across all 12 datasets (all
aggregations and both orientations), required/optional-output clearing, invalid
infinite values, recovery, reuse-versus-fresh design changes and source membership.
Both horizontal and vertical PNGs export after RDS state restoration and analysis
data removal. The 1300×900 figures were visually inspected; unequal stems, ordered
labels and a single correctly oriented mean reference are visible. All five
relevant installed Python implementation files byte-match source.

The final Python regression suite passes **720 tests in 356.119 seconds**, without
failures/errors/skips. Generator/status freshness and diff checks pass. No new JMO or GUI
installation is claimed for this increment. The existing GOF candidate remains
unchanged; actual native desktop save/reopen/export and platform acceptance remain
open, rather than being inferred from these isolated-library checks.

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  Rscript --vanilla tools/check-lollipop-native.R /private/tmp/cpj-lollipop-native-library
```

## Candidate 0.3.74 package gate — 2026-11-15

`ClinicoPathPj_0.3.74.jmo` builds successfully: **23,767,254 bytes**, 1,480 files,
SHA-256 `65692e95afad828ef1ce0ee419070eaaa578959560a106b90933afadf07ef2d5`.
All registered analysis identities/source files and shared `cpj*.py` helper bytes
match source. Metadata/UI bindings, single menu identity, unique safe archive paths,
CRC and absence of Python bytecode pass. Every shipped R-library file (1,397 files)
matches the tested build, both before and after execution.

The actual extracted Python runtime passes **25,016 lollipop checks across 390
configurations**, including all 384 independent statistical/order configurations
and actual Matplotlib stem/marker/axis/reference geometry. Maximum scaled difference
is 3.99614355576137e-16. Other actual archive routes pass 5,148 pie/GOF checks,
5,435 bar checks, 6,692 histogram checks and 2,008 mean-route checks: **44,299 checks
across 983 configurations** in total. The built native library passes 2,228
lollipop plus 1,027 pie/GOF assertions, with no failures/errors/warnings/skips.
Both native lollipop PNGs byte-match the visually inspected source exports.

The prior 720-test statistical-source gate is retained; packaging changes no
production calculations. Nine focused artifact-checker tests pass after adding
explicit version selection. Generator/status freshness and diff checks pass.

At build time GUI automation could not connect, so desktop acceptance was left
open. The subsequent restored-GUI qualification is recorded below; the build-only
report remains distinct from observed installation and saved-file evidence.

## Bounded desktop qualification — 2026-11-15

GUI Sideload installs 0.3.74 under the existing module identity; all 1,480 installed
files match its archive before and after testing. Three fresh sessions (ports
59511, 59870, 60608) verify the Data Library and single menu entry, older 0.3.72
pie compatibility, GOF controls and native lollipop behavior. Lollipop checks mean,
median, sum, unaggregated overlap disclosure, descending/horizontal layout,
optional-output clearing, missing-input clearing and recovery, fresh-engine reopen
and forced recalculation. The sum plot visibly has unequal stems 104, 50 and 30,
with the correctly oriented mean-of-plotted-values line at 184/3.

Six lollipop and nine GOF OMV profiles plus HTML/PNG exports pass independent
base-R checks. Dataset/metadata bytes remain unchanged; source-to-point mappings,
recovered tables and equal-resolution cached pixels agree. Direct lollipop PNG
byte-matches the installed-native CSV render after its values were checked against
base R; the GOF plot byte-matches the qualified descriptive PNG. Four corruptions
per analysis are rejected. Installed native suites pass the same 2,228 lollipop
and 1,027 pie/GOF assertions without failures/errors/warnings/skips.

The GOF export checker initially flagged percentage whitespace inserted by HTML
export. Its numeric-percent-only normalization preserves all digits and precision;
ten focused tests and the actual saved/exported artifacts pass. The original failed
comparison remains separate evidence; no numerical tolerance or production code changed.
Verified 0.3.72 rollback and prior runtime-only 0.3.73 candidate are archived.

See the [executed desktop protocol](python-lollipop-gui-checklist.md) and actual
[saved lollipop example](validation-exports/python-lollipop-0.3.74-reopened.omv).
Full methods, clinical review, additional platforms, broader themes/accessibility
and wrapping long secondary hints remain separate follow-ups.

## Help-layout patch — 0.3.75 (2026-11-15)

The two clipped secondary hints are replaced by five lines of at most 40
characters, including conditional sample-size/reference wording. All controls,
bindings, defaults, results and the run body match 0.3.74; all 56 shared Python
helpers and every other packaged analysis are byte-identical. The interface version
advances to 0.1.1, with no calculation changes.

The standard 0.3.75 archive passes 25,016 actual runtime/geometry checks across
390 configurations. GUI Sideload and fresh engine 59646 verify complete hints at
the pane width that clipped the previous version. A 0.3.74 file reopens, reruns and
saves separately as the [0.3.75 example](validation-exports/python-lollipop-0.3.75-reopened.omv).
All six native tables, dataset/metadata bytes and cached plot are unchanged; the
direct PNG is byte-identical (SHA-256
`2512daedeba75a898dcaabc6d5ae0757656cd10308cf9e2762c899d9692268d8`).
All 1,480 installed files match the archive, compiler/generator checks pass and
verified 0.3.74 is archived for rollback. Broader themes/accessibility, full methods,
clinical review and other platforms remain open; no broad suite rerun is claimed
for this text-only UI patch.
