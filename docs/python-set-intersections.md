# Set intersections — pyvenn core, 0.3.27

Open **Descriptives Py → Sets and Overlaps → Set intersections (core)**. This is the
exact-count and membership portion of the frozen `venn` baseline, not a geometric Venn,
Euler or full UpSet implementation. No Orange dependency is installed.

## Inputs and cohort

Choose two to four distinct nominal/ordinal variables. Variable 1 and Variable 2 are
required; optional roles may be left empty. Explicitly choose each selected variable's
positive level. Every other nonmissing level is negative membership, including additional
categories in a multilevel variable. Unused positive levels can legitimately yield no
members. No level is guessed. Genuine missing values and genuine NA factor levels are
missing; the literal text label "NA" remains a selectable category.

Only selected variables define the common complete-case cohort. Missingness in any of
them excludes that row from all counts and saved membership; unselected columns do not
affect retention. No complete cases produces an explanatory error rather than a zero
or NaN denominator. Counts describe supplied rows: repeated patients/specimens are not
deduplicated and are not independently tested.

## Exact patterns and native results

Each digit follows the displayed Set Definitions order: 1 means the chosen positive
level; 0 means another nonmissing level. `110` means the first two sets only, excluding
the third. These are exclusive patterns. Marginal set sizes, the union and intersection
of all selected sets are also reported. Inclusive pairwise intersections can be recovered
by summing their matching exact patterns; they are not a separate inferential test here.

The all-zero pattern means **none of the selected sets**, not a missing row. It is
included in the cohort denominator and is always displayed, even when its count is zero.
Other zero-count patterns are optional. Percentages use all complete cases. The native
intersection-size bar plot uses these same counts and binary labels; refer to Set
Definitions for each digit's variable and positive level. It follows the jamovi palette.

The optional native membership preview shows the first 500 input rows, including
excluded-row status and original source row IDs. The limit is disclosed; all complete
rows contribute to counts. The native saved-column control writes a nominal membership
pattern for every input row. Excluded rows remain missing, while complete all-zero rows
receive the all-zero factor level. Sparse/filter-derived source IDs are preserved.

## Local inspection

Focus or activate an intersection button to inspect its count, complete-case percentage
and matching source IDs. The row preview is bounded at 100 matching IDs per pattern,
with the number omitted disclosed. All calculations occur in Python; the browser displays
precomputed counts. Local inspection never changes native options, the cohort, tables
or saved output. Labels/levels are escaped data and resources are local. Native tables
and the static image remain the export/reopen counterparts. Full keyboard/theme/GUI
qualification is separate from DOM checks.

## Examples and R calls

Data Library → ClinicoPathPj → **Set Intersection Examples** supplies four synthetic
binary markers containing all 16 four-set patterns plus two missing-value examples.
The source CSV is `data/python_set_intersection_examples.csv`. Select all four markers
with positive level `Positive`: 18 input rows, 16 complete, two excluded; each exact
pattern occurs once, each set has eight members, union=15 and all-four intersection=1.
With only Marker_A/B selected, missing Marker_C is irrelevant: 17 rows are complete.

Generated R wrappers require explicit Level arguments, including NULL for unused roles:

```r
ClinicoPathPj::pyvenn(data = d,
    var1 = 'Marker_A', var2 = 'Marker_B',
    var1true = 'Positive', var2true = 'Positive',
    var3true = NULL, var4true = NULL)
```

## Supported scope and omissions

Supported: two to four factor sets, explicit positive levels, common complete-case counts,
exclusive patterns including none, marginal sizes/union/all-set intersection, native
membership/count tables and static bar plot, bounded local inspection and row-aligned
nominal membership output. `showMembershipTable` retains the baseline false default;
existing ClinicoPath R analyses are unchanged.

Omitted: geometric Venn/Euler diagrams, full UpSet layouts, more than four sets, weighted
counts, inferential overlap/enrichment tests, arbitrary ID-list imports and full baseline
styling. This is a partial baseline port, not full parity or clinical validation.

## Evidence

Seven focused Python tests cover hand counts, all 16 four-set patterns, missingness,
optional roles, literal NA labels, validation, saved sparse IDs and bounded previews.
The DOM harness checks literal labels, focus/click inspection, correct none/overlap IDs
and absence of network/native updates. The full Python suite passes 265 tests.

The native R suite passes 86 assertions: independent base-R predicate counts and
percentages for two/three/four sets, genuine NA-level handling, saved nominal factor
codes/row IDs, valid→incomplete→valid clearing and raster rendering. An initial saved
column failed serialization because measurement type was unset; explicitly supplying
nominal metadata fixed it. The final compiler build and a repeat of all 86 native
assertions against its candidate library pass. Generator/status freshness checks and
all 18 extracted-package runtime cases pass, including the packaged synthetic dataset
and nominal saved-output metadata. The R process printed `Operation not permitted`
messages during/after completion, with exit status zero and no failed assertions or
test warnings. Native macOS arm64 desktop installation, four positive-level controls, count/local
inspection, nominal saved membership, second-engine OMV reopen/rerun and native PNG
export now pass. A missing positive level displays a prompt and restoring it recovers
the expected counts. Version 0.3.28 compacts the optional preview to source row, pattern and Included/Excluded
status. The full included-set column remains in the result contract but is hidden in this
preview; complete labels remain visible in the exact-pattern table and local inspector.
Native macOS arm64 verification of the compact layout and 0.3.27 saved-file reopen/rerun
passes in 0.3.28. Seven focused Python tests, 89 native assertions and 18 packaged cases
pass; the full 265-test suite above belongs to 0.3.27. Broader theme/accessibility/platform
qualification remains open. See [0.3.28 evidence](validation-exports/python-set-intersections-0.3.28-checks.json).
See [desktop evidence](validation-exports/python-set-intersections-0.3.27-desktop.json)
and the [clean saved example](validation-exports/python-set-intersections-0.3.27-desktop.omv).


## Optional intersection matrix — 0.3.29

Under **Plots and Interaction**, enable **Intersection membership matrix** to align
exact-pattern count bars with a membership-dot matrix. The first set is the top row;
filled dots and connecting lines indicate the sets included in each exclusive pattern.
The all-zero pattern has no filled dots: these rows are in the complete cohort but
outside every selected set. Gray background dots indicate absent membership.

Pattern order, zero-pattern visibility and counts match the native exact-pattern table.
The plot uses the existing common complete-case cohort; it does not merge inclusive
intersections, change positive levels, sort by significance or add inference. Long set
labels are shortened in the figure with disclosure; full names remain in Set Definitions.
The existing local inspector provides source-row inspection for the same patterns.

This optional static image has a native export counterpart through jamovi's usual image
export. It is a bounded 2–4-set UpSet-style view, not full UpSet/Euler/Venn parity:
set-size sidebars, arbitrary set counts, arbitrary ordering/customization and inferential overlap
remain omitted. Defaults and saved membership codes remain unchanged. Matrix macOS arm64 GUI/export/save-reopen checks now pass separately from the existing
0.3.27–28 set-count and compact-preview records. Broader platform/accessibility checks
remain open.


Matrix validation: 12 focused Python tests and all 270 Python tests pass. Independent
fixtures verify every active-dot coordinate and count-bar height for two, three and four
sets, none-only patterns, long labels, invalid signatures/counts and raster output. The
native suite passes 97 assertions, including matching matrix/table signatures and counts,
900×600 raster, disabled-state clearing and incomplete-input recovery. All 18 extracted
package runtime cases pass, including the optional matrix and its PNG asset. These bridge/runtime checks are supplemented by a separate macOS arm64 desktop record:
See [0.3.29 checks](validation-exports/python-set-matrix-0.3.29-checks.json) and
[Python-rendered preview](validation-exports/python-set-matrix-0.3.29-preview.png).


Desktop matrix qualification (macOS arm64, jamovi 28.13): GUI installation, rendering,
off/on control, 1800×1200 native PNG export, second-engine OMV restoration/recalculation
and missing-positive-level recovery pass. Counts and saved membership codes are unchanged.
See [desktop record](validation-exports/python-set-matrix-0.3.29-desktop.json),
[saved matrix example](validation-exports/python-set-matrix-0.3.29-desktop.omv) and
[native export](validation-exports/python-set-matrix-0.3.29-native.png). This is focused
platform evidence, not full accessibility/platform or clinical qualification.


## Why are all bars the same height?

The original **Set Intersection Examples** fixture deliberately contains every one of
16 patterns exactly once. Consequently each bar is 1; this verifies complete pattern
coverage rather than illustrating a typical frequency distribution.

Version 0.3.30 adds **Data Library → ClinicoPathPj → Set Intersections: Unequal Frequencies**.
Choose Marker_A–D and Positive for each set, enable the matrix and optionally Zero-count
patterns. Its 60 complete synthetic rows have exact counts, in displayed signature order:
`12, 8, 6, 10, 4, 5, 3, 2, 3, 1, 2, 1, 1, 0, 1, 1`.
Two additional rows are excluded for missing selected values. The none pattern has
12 rows, the union has 48 and the all-four pattern has 1. The zero-count pattern is
`1011`. The height is an exclusive-pattern row count, not the marginal size of a set.

The synthetic CSV is reproducible with
`python3 data-raw/generate-set-intersection-examples.py`. Its counts were checked against
independent raw-CSV predicates, the runtime matrix and saved nominal output. The varied
matrix was rendered/exported through jamovi using the unchanged 0.3.29 runtime; 0.3.30
packages the new CSV in the Data Library. See the
[varied-bar saved example](validation-exports/python-set-matrix-unequal-0.3.30-desktop.omv)
and [native PNG](validation-exports/python-set-matrix-unequal-0.3.30-native.png).

Nine focused set tests and all 18 packaged runtime cases pass in 0.3.30, including
the extracted unequal CSV and its exact matrix frequencies. Fresh-engine reopening and
forced rerun reproduce the varied bars. Analysis/renderer assets match 0.3.29 exactly.


## Pattern display order — 0.3.31

**Results and Interpretation → Pattern order** offers **Membership order** (unchanged
default) or **Frequency (largest first)**. Frequency sorting uses exact-pattern counts
from the same complete cohort; ties retain the original bit-code order. The all-zero
pattern remains included even when its count is zero; other zeros follow Zero-count
patterns. The exact-pattern table, both static plots and local inspector share one order.

Sorting changes presentation only. It does not reorder the source-row preview, change
set definitions or cohorts, or recode saved membership. Saved codes and their labels
continue to use canonical membership order, including when display sorting is reversed.
The native option reruns the backend; the local inspector only displays those results.
New control GUI/save-reopen qualification remains pending separately from the existing
matrix and unequal-example desktop records.


Ordering evidence: all 273 Python tests (11 focused set tests), two DOM harnesses, 106 native assertions
and 18 packaged runtime cases pass. Fixtures independently specify tie order and check
row/saved-code invariance, native reused-versus-fresh agreement and reversal to membership
order. The [Python-rendered sorted preview](validation-exports/python-set-order-0.3.31-preview.png)
uses the unequal example. Desktop automation failed to connect with native pipe startup
errors, including after reset, so the new control/save-reopen gate remains open. See
[ordering checks](validation-exports/python-set-order-0.3.31-checks.json).
