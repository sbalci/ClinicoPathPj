# Native SVG experiment validation — 0.3.7

Recorded 2026-10-26 with jamovi 28.13 on macOS arm64. The prototype's interaction and
current-view exports pass the checks below. **Native OMV saving with the Svg result
remains unresolved, so save/reopen and release acceptance are not complete.**

## Numerical, compiler and integration evidence

- Full bundled-Python suite: **217 tests passed**.
- Full installed-package R suite: **619 expectations passed**, zero failures/warnings/skips.
- Final focused checks after layout/initialization changes: **6 Python tests and
  20 installed-package R expectations passed**, including early script registration.
- All **24 entry points** compile; generator and migration-status freshness checks pass.
- All **14 packaged runtime cases** pass, including Svg transport and local-script integrity.
- Python comparisons cover both inequality directions, both interval methods and all
  three optimization criteria. Native tables/static plots equal the existing D3 entry
  point, through the same independently tested Python engine.
- Checks include ties, automatic/endpoint rules, missing pairs, undefined proportions,
  the 1,000-row payload, invalid settings and markup-bearing variable names.
- R compares five exact proportion intervals with independent `binom.test()` references,
  serializes Svg results, clears incomplete input and recovers after invalid settings.

The DOM harness loads the asset before inserting content, matching native jamovi's
ordering. It verifies linked numeric, window-captured drag and keyboard/ROC controls,
lookup boundaries, local snapshot labels, reset, invalid input and serialized drawing
content. Pointer geometry is stubbed only in that harness; native dragging was also
checked directly. The runtime payload is removed from the displayed SVG after parsing,
so image exports omit the full threshold lookup.

The first full run exposed two test-harness mistakes: the expected utility count needed
to increase from seven to eight, and a nested R6 assignment was invalid for that target.
Both were corrected before the passing full run. A focused runner also needed the
engine-like Python environment and explicit protobuf initialization; its final run passes.

## Native GUI interaction and export

Installed the standard `ClinicoPathPj_0.3.7.jmo` into the existing module using the GUI.
Fresh engines were used after bridge/asset changes; installed helper and JavaScript
bytes match the final source. Previous entry points and original saved comparisons are
retained.

The larger 180-row shared fixture gives TP 47, FP 10, FN 8, TN 115 at native cutoff 2.
Its numeric preview at 3 gives TP 30, FP 0, FN 25, TN 125 without changing native tables.

Final qualification uses `data/python_svg_cutoff_examples.csv` with six rows and a tie at 2:

- Native cutoff 2: TP 3, FP 2, FN 0, TN 1.
- Numeric preview 3: TP 2, FP 1, FN 1, TN 2; native rule remains 2.
- Dragging to about 4.055 changes the line, number and ROC point together:
  TP 2, FP 0, FN 1, TN 3.
- With the line focused, End selects the upper display endpoint 6.4:
  TP 0, FP 0, FN 3, TN 3.
- Clicking a ROC point selects its precomputed cutoff. Apply at preview 3 updates only
  the local snapshot label to TP 2, FP 1, FN 1, TN 2.

The final exports were made through the native Image → Export menu:

- [SVG preview](validation-exports/python-svg-cutoff-0.3.7-preview.svg): valid XML,
  980 × 720, saved native rule 2 and current preview/local snapshot 3; no runtime payload.
- [PNG preview](validation-exports/python-svg-cutoff-0.3.7-preview.png): 3136 × 2342,
  decoded and visually inspected with full axes, white background, controls and labels.

Earlier GUI attempts exposed inline layout, script timing, result-selection drag
interference and export styles depending on an HTML ancestor. These are corrected by
registering assets in `.init()`, initializing inserted roots once, handling dragging at
the window capture phase and emitting one self-contained SVG with scoped styles and
embedded controls. The earlier clipped/black PNG attempt is not the linked final export.

## Save/reopen gate remains open

A clean six-row dataset with no analysis saves successfully. The explicit
`python-svg-cutoff-0.3.7-data-only-control.omv` control is 2039 bytes and contains no
analysis; **it is not a saved-analysis example**. The similarly named validation OMV
is the same data-only control and must not be presented as evidence of Svg persistence.

After adding Svg, native Save/Save As (including the macOS Save dialog) did not update
the OMV with the analysis in the tested sessions. This occurred in the larger comparison
and the isolated six-row document. The cause is not established; numerical/R serialization
and current-view SVG/PNG export passing do not establish ordinary file-save compatibility.
Final analysis save/reopen and missing-module snapshot viewing therefore remain unverified.

An automatic approval review initially blocked discarding the unsaved synthetic window.
The user explicitly authorized discarding it, and testing continued in fresh engines.
That approval is resolved and is not the remaining save/reopen limitation.

The final evidence-only rebuild changes registry metadata, not the GUI-tested statistical,
bridge, renderer or JavaScript implementation. Additional architectures/platforms,
large native previews, exhaustive cancellation and clinical review remain outside this
qualification. See [methods and comparison](python-svg-cutoff.md).
