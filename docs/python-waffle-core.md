# Waffle allocation core — 2026-11-15

## Packaged and scoped desktop qualification — 0.3.76

`ClinicoPathPj_0.3.76.jmo` is built and GUI-Sideloaded under the existing module
identity on macOS arm64 / jamovi 28.17.0. The archive is 23,899,248 bytes,
SHA-256 `6f275281f42fea9a095724dced1fb1d87391a96b0dc96de9310f3bf81674cb4f`.
All **1,487 installed files** match it before and after testing. All 1,402
shipped R-library files match the tested build. Verified 0.3.75 is retained in
`packages/archive/`; the superseded duplicate root package is removed.

Actual archived execution passes **216,200 waffle runtime/geometry checks over
420 configurations**, plus 25,016 lollipop checks/390 configurations and 5,148
pie/GOF checks/131 configurations: 246,364 checks over 941 configurations total.
Archive CRC, paths, unique entries, module version, single waffle menu entry,
all registered sources/shared helpers, compiled controls and example data pass
inspection. Both the built and GUI-installed R libraries pass **859 native
assertions each**, without test failures/errors/warnings/skips. The earlier
739-test statistical source gate remains applicable; production calculations
were unchanged for packaging, so no fresh full-suite rerun is claimed here.

Fresh engines 54245 and 54725 verify the Data Library example, one normal menu
entry, default/frequency/panel roles, legend/titles/source/explanation controls,
five/seven-row and flipped geometry, output clearing, required-input recovery,
optional-panel removal/restoration, Save As, reopening and forced recalculation.
Seven waffle OMV profiles and native HTML/PNG exports pass independent base-R
checks. Removing panels appropriately changes the denominator from 1,004 to
1,006 because the formerly missing-panel row becomes eligible. The original
source data/metadata bytes are identical across all option-only profiles.

Recovered/reopened native tables and cached pixels agree. The direct 1,800 ×
1,200 PNG is byte-identical to an independent-data native reference export.
The saved Results viewport uses a 1,437 × 958 cache; it matches a native render
at those exact dimensions, and exported HTML retains those same cached pixels.
No cross-resolution pixel equality or resampling tolerance is asserted. The
checker normalizes only numeric whitespace before `%` in the two proportion
columns, preserving every digit. It requires a real PNG image element, not just
base64 text. Four corruptions of counts, N, denominator and the image element
are rejected. Initial checker format/dimension/mutation assumptions and the
corrected final run remain in separate `/private/tmp/cpj-waffle-artifacts-*` logs.

The older 0.3.75 lollipop file reopens and recalculates under the installed
module. Its separately saved 0.3.76 compatibility fixture preserves dataset,
native tables and cached image pixels; the original file is unchanged.
See the [executed desktop protocol](python-waffle-gui-checklist.md) and ignored
dated qualification/artifact reports under `docs/validation-exports/`.

This qualifies the bounded descriptive implementation and synthetic lifecycle
on this Mac. Full baseline parity, fractional weights, interaction, broad
accessibility/clinical review, long-job cancellation and other platforms remain
open. Inventory remains 37 partial / 24 planned / 15 utilities / 52 entries,
with zero full-parity releases. Nothing was committed, pushed or submitted.

## Native source integration

The `pyjwaffle` SPEC/run adapter is now implemented under **Stats Plots Py →
Categorical comparisons**, with visible category/frequency/panel/subject roles,
five-row/no-flip/no-legend defaults and organized method, results and plot
sections. Native tables report source/complete/missing/zero-frequency counts,
active and inactive panel denominators, exact category proportions, tile counts,
signed allocation errors and rare-category omissions. Optional source rows are
bounded to 1,000; method explanations default off. The preserved baseline names
include `groups`, `counts`, `facet`, `rows`, `flip`, `show_legend`, `mytitle` and
`legendtitle`. Palette presets and fractional weights remain omitted explicitly.

The Python static renderer consumes serialized tile geometry, with no source
data access or core refit. It validates counts, per-panel totals, category maps,
exact allocation and grid coordinates, bounds saved payloads to 1 MB and draws
at most 800 squares. Category colors are consistent across panels; palette
repetition adds hatch patterns. It follows jamovi's global palette and theme;
panel N is always visible. Long labels wrap instead of disappearing. Titles are
bounded to 200 characters. Disabling the plot permits large tabular labels that
would exceed the drawing-payload limit.

Five adapter/renderer tests pass across all 140 independent configurations,
including an actual subprocess, source-row alignment, disabled outputs,
subject auditing, 1,000-row truncation, nine rejected saved-state corruptions,
both orientations and extreme aspect ratios. Compiler preparation, roxygen
documentation and isolated installation pass. All **739 Python tests pass** in
515.671 seconds, without failures/errors/skips. The final focused five-test
adapter run also passes, and a separate oversized-payload probe verifies an
actionable refusal with successful exact tables when the chart is disabled.

The final isolated native R suite passes **859 assertions**, with zero test
failures/errors/warnings/skips. Fifty-six reference configurations span every
dataset, five/seven rows and both orientations; they check cohort counts,
denominators, category labels, allocation and all tile coordinates. Native
missing-level codes follow the established R bridge's normalized category
order. The first configured run had four harness failures because the oracle
still used codes before normalization; the corrected test explicitly maps
those declared codes and separately verifies unchanged exact labels. No
statistical formula or reference values were changed.

Lifecycle checks cover optional outputs off, missing required input, invalid
frequencies, recovery, changed rows/orientation/panels, reuse versus fresh state,
and PNG export after state serialization/restoration and data removal. Standard,
flipped and synthetic unequal-population PNGs were inspected. Six isolated
Python implementation/SPEC files match source; generator/status freshness and
diff checks pass. No broad R-suite or desktop acceptance is inferred.

Environment evidence stays separate: the initial unconfigured R run failed
because PYTHONHOME was absent. Configuring jamovi's bundled interpreter resolved
that. Configured R runs still emit sandbox `Operation not permitted` process
diagnostics while assertions and exports succeed. This does not qualify process
inspection, long-job cancellation or platform support. Initial failure logs
remain in `/private/tmp/cpj-waffle-native-initial-*-20261115.log`; final logs and
the ignored dated `python-waffle-native-20261115.json` retain the evidence.

At the native source milestone, the registry became **37 partial / 24 planned /
15 utilities**, 52 executable entries and zero full-parity releases. Installed
0.3.75 was preserved until the subsequent packaging/desktop gate recorded above.
The earlier source milestone below records its historical planned status.

Synthetic example: `data/python_waffle_examples.csv`. Select Category, Frequency
and Panel to see populations of 4 and 1,000, an inactive zero-frequency panel
and a rare positive category with no tile. Exact counts remain visible.

Native check (after an isolated R package installation):

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  Rscript --vanilla tools/check-waffle-native.R /private/tmp/cpj-waffle-native-library
```

## Earlier source-only milestone

Reserved identifier `pyjwaffle`, family jjstatsplot. This is a source-only numerical
and geometry foundation: there is no new installed analysis, native UI, renderer,
interactive view or package/desktop acceptance. The registry stays planned with
`source: null`; inventory remains 36 partial / 25 planned / 15 utilities, 51
executable entries and zero full-parity releases. Installed 0.3.75 is retained.

## Baseline and allocation decision

The frozen source is jjstatsplot 1.0.82.03, commit
`4c3cbe8de39d6259ee61d5fde28704f45e9cc8ed`, in
`docs/baselines/released-2026-10-25.tar.gz`. The independent checker verifies all
four source hashes against the registry before comparing results. The installed
reference uses waffle 1.0.2. The wrapper defaults five rows, no flip and no legend;
it normalizes each panel independently with `make_proportional=TRUE`.

Waffle uses sum-preserving largest-remainder allocation. Later categories win
ties because R takes the tail of its stable remainder ordering. However, its
subsequent `as.integer((allocated / 100) * 100)` truncates allocated counts 29,
57 and 58 to 28, 56 and 57 in the inspected runtime. For example, counts 29 and
71 produce only 99 visible tiles. This is a verified baseline difference, not
agreement or a new statistical default attributed to the R implementation.

The Python core implements the intended exactly-100-tile allocation using
integer division and integer remainders of `100 * count / panel_total`. It
preserves the later-category tie rule while avoiding floating-point quota/tie
errors and the truncation defect. It never reconstructs counts from rounded
percentages. The reference fixture records actual baseline tile counts and
flags every difference; the checker refuses unexplained differences. Existing
R modules and their defaults are unchanged.

## Inputs and outputs

`waffle_core(group, weights=None, facet=None, rows=5, flip=False,
subject_ids=None)` accepts labelled nominal/ordinal factors and optional
nonnegative **integer observation frequencies**. Fractional, analytic and survey
weights are outside this core even though the released R wrapper accepts
fractional nonnegative weights. Frequencies are never expanded into records.

Support 1–100,000 source rows, at most 1,000 raw declared factor levels,
1–20 nonmissing category levels and 1–8 nonmissing facet levels. Choose 1–100
integer rows; reject booleans/nonintegers and invalid flip settings. Total
positive complete frequency must be 1 through 2^53−1. Known invalid frequencies
are refused even when a different selected role is missing.

Exclude the union of missing groups, facets and frequencies. True missing
factor-level labels are missing; literal `NA` remains a category. Preserve
declared order, unused categories and original zero-based row identities.
Audit overlapping role missingness separately, zero-frequency rows, positive
contributing rows and exact frequency totals. Empty/all-zero cohorts are
refused. Facets without positive complete frequency are listed as inactive;
they do not acquire artificial tiles or divide by zero. Single-category panels
are valid descriptive displays, unlike the broader R wrapper's global
two-category input restriction. Optional unique nonempty exact subject labels
audit unweighted contributing rows; they are unavailable with frequencies.

Each active panel returns its own population N, source indices, category counts,
exact proportions, integer tile counts, represented proportions, signed
allocation errors and an explicit flag when positive observations receive no
tile. Exact values remain available even when the rounded visualization omits a
rare category. Equal-size grids cannot convey differences in cohort size: each
panel's denominator must remain visible in the future native interface.

Return 100 unit-square coordinates per active panel, at most 800 tiles. Fill
bottom-to-top within a column, then move right; flip swaps x and y. Coordinates
are one-based; bounds are centers plus/minus 0.5. A nondividing row count such
as seven leaves the final column incomplete. No observations are repeated to
construct tiles. Versioned results include notices and remain strict JSON-safe.
No statistical inference, clinical bands, outlier deletion or independence
claim is derived from the descriptive display.

## Independent evidence

The R oracle was written and executed before the Python engine. It supplies
independent base-R complete-case grouped accumulation and integer-remainder
allocation, and executes actual `waffle::geom_waffle` builds for every active
panel/configuration. Actual baseline coordinates agree with the corresponding
prefix of the intended grid; actual baseline per-category allocations are
retained separately, including the known truncation losses.

Fourteen datasets × five row counts × two orientations give **140
configurations and 146,420 source comparisons**, with zero scaled numeric
difference. Of 170 actual R panel builds, 150 have matching allocations and 20
exhibit the identified truncation defect. The R reference replays byte-for-byte.
Fixture SHA-256:
`9d3efae5702e048df498a9b5cc687914ee8b64f6cc403938a6525b682769b642`.

Twelve focused tests cover the frozen oracle, independent rational arithmetic
at extreme valid totals, tied remainders, zero-addition branch, rare/unused
categories, facet denominators, missingness, exact IDs, expansion/permutation/
scaling invariants, orientation, incomplete columns, bounded output and explicit
invalid/resource refusals. Five corrupted count, denominator, allocation,
geometry and missingness implementations are rejected.

All **734 final-source Python tests pass** in 373.343 seconds, with no failures,
errors or skips. Generator/status freshness and diff checks pass. The installed
0.3.75 archive remains SHA-256
`a345fff09363a5b826208f3c5ce59cf8ec52b6701ca57364d98fcca4462435ed`;
all 1,480 installed files still match it. No native R suite, build or GUI rerun
is claimed for this source-only addition. The ignored dated
`docs/validation-exports/python-waffle-core-20261115.json` records these separate
evidence grades; functional reference fixtures remain version-controlled.

Reproduce from the project root:

```sh
Rscript --vanilla tests/reference/waffle-core.R /private/tmp/waffle-replay.json
cmp tests/fixtures/waffle-core.json /private/tmp/waffle-replay.json
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tools/check-waffle-core.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tests/python/test_waffle_core.py
```

## Feature and omission matrix

| Feature | Current evidence | Remaining gate |
|---|---|---|
| Counts, missingness, factor ordering, integer frequencies | Independent R, packaged runtime, native tables and scoped desktop lifecycle | Broader desktop edge cases and other platforms |
| Per-panel allocation and flip/row geometry | Independent R, packaged renderer and native/desktop cached and direct PNG export | Broader resize/platform qualification |
| Rare-category and unequal-panel disclosure | Native tables/notices and N labels; synthetic GUI/export figures checked | Broader accessibility review |
| Fractional weights | Omitted deliberately | Separate numerical and interpretive contract |
| Global colors, bounded titles, optional legend/explanation | Organized SPEC/UI, runtime and scoped desktop controls; inspected PNGs | Broader themes/accessibility; baseline palette presets omitted |
| Hover/highlight interaction | Omitted | Local-only bounded payload, keyboard access, static counterpart |
| Saved analysis and package delivery | 0.3.76 archive/runtime, GUI Sideload, fresh-engine save/reopen/rerun and native HTML/PNG exports | Other platforms and broader lifecycle scenarios |

The package/desktop follow-up is completed within the scoped 0.3.76 evidence
above. Continue remaining analysis/method ports and broader qualification; keep
fractional weights, interactive inspection and additional-platform acceptance as
separate feature contracts and evidence gates.
