# Categorical variable tree core

`pyvartree` appears once under **Descriptives Py → Descriptive plots → Categorical
variable tree (core)**. It implements a bounded categorical count-tree subset of the
frozen `vartree` baseline, not full vtree feature parity or a learned decision tree.

Select one to four nominal/ordinal variables in branching order. The first selected
variable branches from the complete cohort; each subsequent variable partitions every
observed parent branch. All depths use the same complete-case cohort across all selected
variables. Missing categories exclude a row from every depth; missingness is never a
negative category or a progressively changing denominator. Literal text `NA` is retained.
No patient identifiers, predictors, outcomes, weights or clinical cutoffs are inferred.

Nodes follow declared factor-level order in depth-first traversal. Only observed branches
appear; unused levels are counted in the input summary. Node IDs are display references
for the current selection/order, not stable patient IDs or saved classifications. The
native table records parent IDs, depth, variable/category, a JSON branch path, counts,
cohort percentages, parent percentages and leaf status. JSON paths distinguish literal
slashes/arrows within category labels. Root percentages are 100%; children partition their
parent and all leaves partition the common cohort.

The expandable local view uses native HTML `details`/`summary` controls. Expansion is
transient presentation state; it does not filter observations, recompute counts or save a
cohort selection. All labels are HTML escaped. No network resources, JavaScript libraries,
new Python packages or Orange desktop installation are required. Browser keyboard support
is intended through the native disclosure controls; native jamovi keyboard/accessibility
qualification remains pending.

The optional static native plot shows at most the 30 largest leaves, ties resolved in
traversal order. Its labels are node IDs, with full paths in the native table. If more
leaves exist, an information notice states the display limit; the table and expandable
view retain the entire tree. The plot is a count counterpart, not identical tree geometry.

The core accepts at most 10,000 input rows and 200 observed non-root nodes. It rejects
larger trees with guidance to select fewer variables or explicitly combine categories.
It does not silently sample rows, prune branches or pool categories. Empty/all-missing
cohorts are rejected; unconfigured native analyses use the normal module welcome state.

| Feature | Position |
|---|---|
| Observed categorical prefixes, counts, two percentage denominators | Implemented; independent count validation tracked separately |
| Native table, local expansion, static top-leaf counts | Implemented; new-analysis desktop qualification pending |
| Factor labels/order, unused/missing levels, literal `NA` | Explicit input/cohort policy |
| Baseline pruning/follow rules and missing-category branches | Omitted |
| Continuous node summaries and percentage-variable summaries | Omitted |
| Baseline styles, palettes, titles and DiagrammeR/SVG layout | Omitted |
| Saved row classifications, local row selection or inferential cohort filtering | Omitted |
| Inferential tests, clinical interpretation or prediction | Outside this core |

Use **Data Library → ClinicoPathPj → Categorical Tree Examples** for 36 synthetic
complete tumor/grade/stage profiles and two missing-category rows. Version 0.3.36 uses
Type C for the third tumor category: the earlier literal NA label was interpreted as
missing by jamovi CSV import, reducing the GUI cohort to 34. The original failure is
preserved; literal NA factor handling remains covered separately by engine tests.
Regenerate the example with `python3 data-raw/generate-variable-tree-examples.py`.

Counts describe supplied observations. Repeated specimens/patients remain repeated rows;
no independent-observation inference is made. This analysis does not establish diagnostic,
clinical or model-validation evidence.

## Validation and open gates

Six focused Python tests and all 291 Python regression tests pass. Independent native
R filtering of complete cases verifies prefix counts and both denominators at one, two
and three depths; all 78 native assertions pass, including raster rendering and
valid → incomplete → valid clearing/recovery. Native R emits environment-level
“Operation not permitted” messages despite exit 0 and no failed/warning assertions.
The initial looped R test accidentally passed an NSE-captured symbol as a column name;
using evaluated arguments through `do.call()` corrected the harness without changing
the engine. A package-test fixture also needed explicit missing factor codes.

Twenty extracted-package runtime cases pass, including the packaged synthetic CSV and
a 1,000×650 rendered tree-count PNG. The example has 15 nodes, six leaves with counts
12/6/4/5/7/2, 36 complete rows and two excluded rows. Its standalone HTML parses as
nine disclosure headings without scripts; the static PNG was visually inspected.
A jsdom check could not run because that package is unavailable in the shell environment;
no DOM/keyboard interaction evidence is claimed from parsing alone.

Frozen full-vtree agreement, desktop installation/keyboard/render/export/OMV reopening,
other platforms and clinical/release review remain pending. The tree is still partial.
See [separate validation record](validation-exports/python-variable-tree-0.3.35-checks.json).

## Native qualification and CSV repair — 0.3.36

Computer use recovered. Installed 0.3.35 and reproduced its CSV-token discrepancy in
jamovi 28.13/macOS arm64: 38 input, 34 complete, four excluded. The original fixture is
[retained](validation-exports/python-variable-tree-0.3.35-import-failure.omv). Replacing
the synthetic label NA with Type C restores 36 complete/two excluded under blank/NA
token parsing, without changing the Python engine. The R import fixture compares leaf
counts independently of importer-defined factor order; other fixtures verify level order.

Installed 0.3.36 via the GUI, fully restarted, loaded the corrected Data Library example
and selected Tumor → Grade → Stage. Native results show 15 nodes and six leaves, with
counts 12/7/6/5/4/2 when sorted for the plot. Mouse activation and Enter/Space on a
focused disclosure work. A second fresh engine reopens the saved OMV; toggling the plot
off/on forces recalculation and restores the same cohort/counts. Expansion is transient.
The native [PNG](validation-exports/python-variable-tree-0.3.36-native.png) is 2000×1300;
the [saved fixture](validation-exports/python-variable-tree-0.3.36-desktop.omv) retains 38 rows.

All 292 Python tests, seven focused tree tests, 83 native assertions and 20 packaged
cases pass. Native R still prints environment-level Operation not permitted messages
with exit 0 and no failed/warning assertions. Earlier pending-desktop statements above
record 0.3.35 history; this bounded native gate supersedes them. Broader Tab navigation,
screen readers, table export, long-label table width, themes, other platforms, full
vtree equivalence and clinical/release clearance remain open.

See the [0.3.36 native/core evidence](validation-exports/python-native-core-0.3.36-checks.json).
Persisted artifacts can be rechecked with `python3 tools/check-native-core-artifacts.py`.


## Compact native paths — 0.3.37

The default table shows node/parent IDs, depth, variable, category, count, both percentage
denominators and leaf status. Long JSON branch paths are hidden by default to reduce
width. Enable **Results and Interpretation → Full branch paths in table** to display
and include them when copying/exporting the native table. Each complete path remains
stored in the same `path` result column; no labels are shortened or removed.

In R, native `nodes$asDF` follows column visibility. Use `showPaths=TRUE` to include
paths in that data frame, or inspect `nodes$columns$path` for the retained hidden data.
Node IDs still map plot bars to the native table and parent/category columns define
the hierarchy in the compact view. This is presentation only: cohort, counts, percentages,
node order, local tree and static plot data are unchanged. Earlier four scientific R
wrapper arguments retain their positions; the new option is appended.

0.3.37 validation: all 293 Python tests (eight focused), 95 native R assertions and
20 packaged runtime cases pass. The count engine is byte-identical to 0.3.36.
Installed on macOS arm64 / jamovi 28.13; reopened the earlier 0.3.36 fixture and
forced recalculation. The compact nine-column table fits the inspected results pane.
True/false toggles retain the same cohort and all 15 node counts. Saved both states
separately; after full restart, each option state reopens and recalculates correctly.

Native [compact HTML](validation-exports/python-variable-tree-paths-0.3.37-compact.html)
omits paths; [expanded HTML](validation-exports/python-variable-tree-paths-0.3.37-expanded.html)
contains all paths. An independent read-only artifact checker verifies equal non-path
values, all 15 counts against CSV prefixes, and every path in both saved OMV archives.
Run `python3 tools/check-tree-path-artifacts.py`. See the
[validation record](validation-exports/python-tree-paths-0.3.37-checks.json).
Broader labels/themes/platforms/accessibility and full baseline parity remain open.
