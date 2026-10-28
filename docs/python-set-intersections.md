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
the expected counts. Long included-set labels crowd the optional membership preview;
layout refinement and broader theme/accessibility/platform qualification remain open.
See [desktop evidence](validation-exports/python-set-intersections-0.3.27-desktop.json)
and the [clean saved example](validation-exports/python-set-intersections-0.3.27-desktop.omv).
