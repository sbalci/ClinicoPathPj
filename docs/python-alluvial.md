# Categorical alluvial flow core

`pyalluvial` lives in **Descriptives Py → Descriptive plots** within ClinicoPathPj.
Select two to four nominal/ordinal variables in axis order. Each supplied row follows
one complete categorical path. A path keeps its identity across adjacent axes; ribbon
thickness is its row count on one common scale. These are descriptive supplied-row
counts, without patient aggregation, inference, temporal or causal interpretation.

## Baseline and scope

The registry retains the frozen ClinicoPathDescriptives 1.0.82.03 source hashes at commit
`7162149586afc8992f1ba17e56887e2fbcb0835d`. This increment covers the unweighted
categorical count subset, not full easyalluvial/ggalluvial parity. Existing R modules
are unchanged; no additional Python dependency is required.

| Feature | Status |
|---|---|
| Two to four ordered categorical axes | Implemented |
| Counts and retained-row proportions for complete paths | Implemented |
| Native flow table, commonest first; declared-code ties | Implemented; off by default |
| Native axis-category counts and proportions | Implemented; off by default |
| Missing values retained by default (`excl=false`) | Implemented; collision-free label |
| Complete-case exclusion across all plotted axes | Implemented; explicit option |
| Declared factor order, literal labels and unused-level omission | Implemented |
| Python static count-scaled ribbons and node labels | Implemented |
| Local hover/select highlighting across linked path segments | Implemented |
| Weights and condensation variable/panel | Omitted |
| Numeric binning and marginal plot panels | Omitted |
| Alternative fill/orientation/curve and styling controls | Omitted |
| Full baseline parity | Pending |

## Missingness and denominators

Missing values remain a distinct category by default, matching the frozen baseline.
If `(Missing)` already appears among any declared labels, the core chooses `(Missing 2)`,
then increments until the label cannot collide. True missing factor levels and absent
codes are missing; literal `NA` remains recorded text. CSV import can interpret `NA` as
missing before analysis, so synthetic examples avoid that token.

With exclusion enabled, the same complete-case cohort feeds every axis and table.
Percentages use retained rows. Category counts sum to retained n on each axis; path
counts sum to retained n once. No weights or patient IDs are assumed. The native path
column uses JSON arrays so labels containing arrows/separators remain unambiguous.

## Interaction and export

Hovering a ribbon highlights every segment of that exact full path. A labelled select
provides the same operation through the keyboard. Leaving a hovered ribbon restores
the selected path; Clear restores all flows. Local highlighting is transient, including
after reopening; it changes no saved analysis options or native tables. Changes to
variables or the exclusion policy use jamovi's analysis controls and rerun Python.

The local SVG uses a fixed accessible palette, native control focus outlines and text
status. Static figures use jamovi's supplied palette/theme through the Python renderer.
The native static image is the plot-export counterpart; HTML interaction export and
accessibility certification are not claimed. Long/dense labels may require a wider
results pane and the exact native tables.

The implementation rejects more than 10,000 input rows, 60 observed paths or 20 observed
categories on any axis. It never samples, drops small flows or silently combines levels.

## Synthetic example and validation

**Data Library → ClinicoPathPj → Categorical Flow Examples** contains 22 synthetic
Diagnosis/Marker/Response profiles. Exclusion leaves 20 rows on four paths of sizes
12, 5, 2 and 1; inclusion retains two additional incomplete paths. It contains no
patient information. Regenerate with `python3 data-raw/generate-alluvial-examples.py`.

Eight focused Python tests cover independent Counter counts, marginals, common-scale
unequal ribbon widths, tiling/conservation, true/literal missing labels, collision-free
labels, four-axis/all-missing cases, escaped script-closing text and option invariance.
The offline event harness checks selection, linked segments, hover/restore and Clear:
`node tools/check-alluvial-interaction.js <generated-local-view.html>`.

Native R tests use independently filtered masks and counts, explicit-NA-level fixtures,
valid → unselected → valid transitions, exclusion rerun versus a fresh object and native
raster rendering. Full-suite/compiler, package and desktop qualification results are
recorded separately when completed. Broader platforms, accessibility, clinical/release
review and full baseline parity remain open.


0.3.41 qualification: 311 full Python tests, 71 native alluvial assertions and 21
extracted-package cases pass. Native tree/plot regression checks are recorded separately.
The compiler and generator/status freshness checks pass. Native R emits environment
Operation not permitted messages despite exit 0 and zero failed/warning assertions.

Installed in jamovi 28.13 on macOS arm64, with a full restart before testing. The
Data Library example yields 22 retained rows/six paths with inclusion, and 20 rows/four
paths with exclusion. Keyboard path selection and Clear work. Native HTML tables match
independent source-CSV counts/proportions, the native PNG is 2200×1400, and saved source
values/row order are unchanged. After another full restart, roles and settings restore;
exclusion reversal forces 20 → 22 → 20 recalculation, with local highlighting reset.

See [evidence](validation-exports/python-alluvial-0.3.41-checks.json),
[saved example](validation-exports/python-alluvial-0.3.41-desktop.omv),
[native table export](validation-exports/python-alluvial-0.3.41-desktop.html) and
[static PNG](validation-exports/python-alluvial-0.3.41-desktop.png). Recheck persisted
artifacts with `python3 tools/check-alluvial-artifacts.py`. Plot geometry is independently
checked against count widths; visual similarity to either R engine is not asserted.
