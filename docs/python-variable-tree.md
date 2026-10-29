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
| Continuous node summaries | Implemented in 0.3.39; valid/missing n, mean/sample SD and leaf/all-node locations |
| Reference-level percentage summaries | Implemented in 0.3.40, with explicit level and valid/missing denominators |
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


## Continuous node summaries — 0.3.39

Enable **Results and Interpretation → Continuous node summaries** and assign a numeric
variable to the optional summary role in the main supplier. **Summary location** follows
the frozen baseline: **Leaf nodes only** by default, or **All nodes** including the root.
Node IDs map the native numeric table to the categorical count table. The local
expandable tree appends the same statistics at the requested nodes; native tables retain
unformatted estimates while local labels use six significant digits.

The categorical cohort is unchanged. Missing summary values reduce only that node's
valid summary n; they do not remove observations from the tree or change parent/cohort
percentages. Mean uses observed values, SD uses n−1; mean is undefined at valid n=0
and SD at n<2. Reported missing n equals node n minus valid n. No imputation, automatic
exclusion, confidence intervals or tests are added. Repeated subjects remain supplied
rows. Numerical moments use anchored/scaled calculations; unrepresentable mean/SD is
rejected with rescaling guidance. Infinite source summary values are rejected rather
than treated as ordinary observations. Native jamovi also rejects source infinities
before Python dispatch.

With the feature enabled but no numeric role, the categorical results remain available
and an information notice requests the role. Disabling summaries or clearing that role
clears numeric tables and local annotations. Existing count/plot options and the first
five R wrapper arguments retain their positions. The generator permits appended roles
only with explicit UI; inferred-UI ordering safeguards remain in place.

**Data Library → ClinicoPathPj → Tree Node Summary Examples** contains eight synthetic
profiles: seven categorical complete rows, four valid scores and three node-local missing
scores. The category-missing row with score 999 is excluded from every node. For all
nodes, root mean is 18.5 and sample SD is √(227/3); leaves demonstrate n=2, n=1 and
all-missing summaries. The original categorical example and prior saved fixtures are
preserved. Full vtree missing-category, pruning/follow, percentage-variable and styling
parity remains omitted.

0.3.39 validation: 299 full Python tests, 43 focused tree/generator tests, 188 native R
assertions and 20 extracted-package cases pass. Independent Python statistics and base R
mean/sd fixtures agree for each node; valid/missing counts, singleton/all-missing nodes,
large/tiny moments, role clearing/recovery and unchanged categorical results are covered.
The initial unsupported UI-container enable property was corrected before the successful
compile, and a generator regression now rejects it. Native R continues to emit environment
Operation not permitted messages despite exit 0 and no failed/warning assertions.

Installed 0.3.39 through jamovi GUI on macOS arm64 / jamovi 28.13. Both summary locations,
waiting-for-role information, local annotations and on/off clearing work. After full
restart, both saved states reopen with the correct numeric role and location; all-node
results recalculate through leaf/all-node reversal. The earlier 0.3.37 categorical-only
file reopens with summaries off and retains 36 complete rows/six leaves after rerun; its
original file hash is unchanged. A separate compatibility copy preserves input values
and labels. Native HTML export agrees independently with all eight CSV-derived nodes
at displayed precision; raw numeric estimates are checked by the native R suite.

See [validation evidence](validation-exports/python-tree-summary-0.3.39-checks.json),
[native all-node export](validation-exports/python-tree-summary-0.3.39-allnodes.html) and
[saved example](validation-exports/python-tree-summary-0.3.39-allnodes.omv). Run
`python3 tools/check-tree-summary-artifacts.py` to recheck persisted artifacts.


## Reference-level percentages — 0.3.40

Enable **Reference-level percentages** and select a categorical reference variable and
its level explicitly in the main supplier. No level is guessed. Reference summaries
appear at every node. A reference variable can also be a categorical branching role;
it must be distinct from an assigned numeric summary role. Existing count and numeric
results remain available while a reference role/level is incomplete.

The denominator follows the public vtree 5.7.0 `%npct%` summary: **matches / valid
(nonmissing) reference values within that node**. It is independent of the categorical
node count and parent/cohort percentages. Missing reference observations stay in the
tree and are reported separately. All-missing reference nodes have undefined percentages;
a valid node with no matches has 0%. Literal labels, including spaces, punctuation and
text NA, are compared directly; true missing factor levels remain missing. No vtree
condition-string parsing or automatic reference recoding is used.

Native tables report node rows, valid/missing reference n, matches and percentage. Local
annotations keep the reference variable/level separate from numeric mean/SD labels. No
intervals or tests are added. Disabling the feature or clearing its role/level clears
reference annotations and tables without changing categorical or numeric results.

The new Level is explicitly optional in the SPEC. Jamovi's generated header still has
a required R formal; a generator-owned `R/zzz-optional-level-defaults.R` applies NULL
defaults after headers load. No compiler header is hand-edited, existing argument
positions remain, and other analyses' required event-level formals are unchanged.
This optional level does not use the bridge's global event gate, so incomplete
reference configuration does not suppress the independent categorical/numeric outputs.

**Data Library → Tree Reference Percentage Examples** has eight synthetic rows, seven
categorical complete rows, four valid references (two Positive) and three missing
references. Root percentage is 2/4 = 50%, while the node has seven rows. Numeric scores
still give mean 18.5 and SD √(227/3). Leaves illustrate 100%, 50%, 0% and undefined.
Pruning/follow rules, missing categorical branches, baseline styling and full vtree
parity remain outside this increment.


0.3.40 validation passes: 303 full Python tests (47 focused tree/generator), 251 native R
assertions, compiler/freshness and 20 extracted-package runtime cases. Base R masks and
public vtree 5.7.0 agree on the valid-reference denominator; true missing versus literal
NA, unused levels, all-missing nodes, same-variable roles and legacy R calls are covered.
Native R emits environment Operation not permitted messages despite exit 0, zero failed
assertions and zero test warnings. This remains separate from numerical evidence.

Installed 0.3.40 through jamovi GUI on macOS arm64 / jamovi 28.13, then restarted the
application. Explicit Positive level, incomplete-level information, combined numeric and
reference annotations, and reference-only clearing/restoration work. Root 2/4 = 50%
and leaf 100%/50%/0%/undefined agree. Native HTML export independently matches all
eight node reference counts/percentages and numeric statistics at displayed precision.
The saved document reopens after another full restart with all roles/options retained;
reference off/on forces fresh-engine recalculation and preserves numeric summaries.

See [evidence](validation-exports/python-tree-reference-0.3.40-checks.json),
[native HTML](validation-exports/python-tree-reference-0.3.40-desktop.html) and
[saved example](validation-exports/python-tree-reference-0.3.40-desktop.omv). Reproduce
with `python3 tools/check-tree-reference-artifacts.py`. No new static plot geometry was
introduced in this increment; earlier count-plot export evidence remains historical.
Full baseline, broader platform/accessibility and clinical/release gates remain open.
