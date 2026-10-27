# Annotated IHC heatmap — pyihcheatmap

Experimental 0.3.10 core, inspired by Orange's annotated/linked exploration workflow.
Open **Descriptives Py → Biomarker panels → Annotated IHC heatmap**.
Import `data/python_ihc_heatmap_examples.csv` for synthetic illustrative values; no clinical
classification or biological association is implied by its invented groups.

Choose two to twenty numeric markers. Patient/specimen ID, diagnosis/group and region
are optional annotation columns. Each input row remains a supplied specimen or region;
repeated IDs are retained, never averaged or treated as an inferential sample-size multiplier.
Original jamovi row identities accompany the native row-order table and local inspector.

## Calculations and display

Raw values are the default. They share one numeric color scale; unlike units can dominate
that scale. Optional z scores center each marker by its observed retained-row mean and divide
by its observed sample SD (n−1). This is display standardization, not a clinical normal range.
Markers with zero or unavailable SD have observed z values set to zero with a warning.
Their missing values stay missing. Tables report raw means and sample SDs on the retained cohort.

Default missingness retains partial rows and displays gray missing cells. All-marker-missing
rows are excluded and counted. Complete-row mode removes any row missing a selected marker.
Every selected marker must have at least one retained observed value. Infinite values are rejected.

Row and/or marker clustering is optional, with average linkage and Euclidean distance on the
displayed values. It requires complete marker rows; select complete-row mode or disable clustering.
No imputation, hidden resampling or jitter is performed. Branch orientation can differ from R
while describing the same hierarchy. Optional **Dendrograms and merge inspection** (0.3.14) exposes these same trees; it does not
recluster or alter leaf ordering. It defaults off. Enable it under Plots and Interaction
after row and/or marker clustering. Native merge tables name leaf children by original
source row / marker and internal children by merge number, scoped to each clustered axis.
Native static tree plots put leaves in heatmap order. Heights are average-linkage distances
on displayed values, not p values, stability measures or clinical boundaries. A single
retained row has no row-tree merges; zero-distance merges are retained without jitter.

In the local inspector, focus or activate a branch to highlight its member rows or marker
columns. Row branches also highlight matching complete-pair scatter points; rows missing
scatter values remain highlighted in the heatmap. Marker branches highlight columns without
selecting specimen rows. Clear highlights resets both. Nothing is refitted, filtered or saved
by inspection. Labels may be shortened/thinned in tree plots; branch descriptions and native
merge tables retain identities. See [dendrogram validation](python-ihc-dendrogram-validation.md).

The maximum retained matrix is 200 rows × 20 markers. Larger matrices are rejected explicitly;
no hidden display sampling. The native static image contains all cells. Its row labels are shortened above 80 characters and thinned
above 25 rows; the native row-order table and local cell inspector retain every annotation.
Static colors follow the jamovi palette endpoints around white; the local inspector uses a
fixed blue/white/orange scale with the same symmetric numeric limits. Colors need not match.

## Outputs and interaction

- Native marker summary and row-order/annotation tables.
- Native Python-rendered heatmap for static output and jamovi export.
- Optional fully local cell inspector: click/focus a cell for source row, annotations and
  raw/displayed values. Search highlights matching row labels without removing observations.
  It makes no backend calls and changes neither the analysis cohort nor saved options.
- Native summary identifies input/retained/excluded rows, missing cells, scaling and clustering.

Version 0.3.12 adds **Linked marker scatterplot**, disabled by default. Enable it under
Plots and Interaction. Optional native X/Y roles must name distinct selected heatmap markers;
blank roles use the first and second markers in the original selection, regardless of
clustering order. The scatterplot uses the heatmap's displayed raw/z values, retaining only
complete pairs. Its native cohort table counts omitted pairs; the source-row table records
all plotted original row identities and displayed coordinates. No correlation or regression
is fitted. If no pairs remain, the heatmap remains available and a warning explains the
empty scatterplot.

With local inspection enabled, focus/click a heatmap cell or scatter point to highlight its
source row in both views. Enter/Space activates focused points; Clear highlights resets
selection. Repeated patient IDs do not merge source rows. Local X/Y dropdowns can inspect
other selected markers, counting their complete/missing pairs without backend calls.
Search highlights labels/points without removing them. Local pair choices and highlights
are transient; change native X/Y roles to persist the pair and update native outputs.
Overlapping points are not jittered; individual rows remain accessible in the heatmap.
Native plots use the saved X/Y pair, not a transient local pair.

Version 0.3.13 keeps supplier variables available for reuse in native scatter roles.
Native mouse linking, custom pair controls, fresh-engine save/reopen and PNG export have
been checked on macOS arm64 / jamovi 28.13; complete keyboard/theme/platform gates remain open.
See [linked-view validation and remaining gates](python-ihc-linked-validation.md).
Version 0.3.15 adds optional **Saved source-row selection** under Save Row Selection.
Enable it to preview source rows locally and commit them with **Apply source rows**. A row
or row-branch replaces the preview; Toggle individual rows adds/removes activated rows.
Marker branches inspect columns and cannot be applied as specimen selections. Restore applied
rows resets the preview without dispatch; clearing then applying commits an empty selection.
Native summary/selected-row tables report the applied selection, independent of later previews.

The native output control optionally creates `IHC_selection` (Not selected / Selected).
It retains original input row positions. Excluded rows are unassessed (missing), rather than
negative selections. Disabling the feature clears an enabled flag to missing. Applied
selections never subset or refit heatmap summaries, clustering or scatter calculations.

Selections are bound to all supplied marker/annotation rows and role choices, including
rows excluded from display. Edits, insertions, deletions, filtering or input-role changes
require review/reapplication; until then all flags are unassessed. Scaling, clustering,
scatter-pair and missing-row display choices do not change that input binding. This protects
against silently reusing positional source IDs after input changes; it is not a patient-ID
registry or proof of identity beyond the supplied view data. The saved definition is available
under Advanced Settings. Native tables are authoritative if the host panel field has not
refreshed; close options and reselect the analysis heading to refresh it.
See [selection validation and acceptance](python-ihc-selection-validation.md).

Other omissions:
cluster significance/stability, differential-expression tests, clinical
cutoffs, pathway analysis, automatic imputation, spatial inference and patient-cluster inference.
All rows/labels are embedded in local results; do not share a saved file containing identifiers
that should not be disclosed. No external service is called.

## Validation status

- Full Python suite: 228 tests passed for the initial core; seven focused IHC tests were
  rerun after final static-label transport/layout bounds. They cover transforms, missingness,
  original IDs, clustering grouping, native geometry and hostile annotations.
- Native R: 104 assertions passed, including 24 independently calculated base-R fixtures
  for raw/z-score transforms and missingness; original-row alignment, valid→incomplete→valid
  clearing, factor missingness and native raster rendering passed. Existing plot/bridge
  regression files also passed. The entire R suite was not rerun in this batch.
- Offline DOM harness: cell/keyboard inspection, literal labels, search-only highlighting
  and no-refit behavior passed. This is not an accessibility certification.
- Packaged runtime cases and source/template identity checks passed on the first build;
  final package: 16 extracted runtime cases, source/template/registry identity and bundled
  example-CSV identity checks passed; see `validation-exports/python-ihc-heatmap-0.3.10-package.json`.
- macOS arm64 jamovi 28.13 GUI: package installation, fresh engine, three markers and all
  annotation roles, raw→z-score rerun, missing-cell inspection, OMV save/fresh-engine reopen,
  complete-row clustering rerun (9 retained, 3 excluded) and native PNG export passed.
  Saved example: `validation-exports/python-ihc-heatmap-0.3.10-validation.omv` (partial-row,
  z-score settings). Export: `validation-exports/python-ihc-heatmap-0.3.10-native.png`.
- Static labels longer than 80 characters were subsequently shortened to protect layout;
  full annotations remain in the native table and local inspector. The final package includes
  this display-only adjustment. Large matrices, theme variants and other platforms remain pending.

This is an exploratory utility, not full baseline IHC heterogeneity parity, a validated
classifier, or clinical/release clearance. Cluster stability and inference require additional work.

## Applied selected marker data (0.3.16)

Under **Save Row Selection**, enable **Applied selected marker values** after enabling
saved selections. The native table lists one row per applied retained specimen/marker,
including source row, annotations, heatmap row order, raw value, displayed value and an
Observed/Missing label. The displayed value uses the full retained cohort's chosen scaling;
it is not standardized again within the selection. Both clustering axes' display orders
are preserved. Missing cells stay missing, and unavailable/excluded source rows contribute
no measurement rows. Local previews do not update this table until Apply. Empty or invalid
selections, disabled options and incomplete required inputs clear its rows.

The option defaults off; the existing 200-row × 20-marker bounds limit it to 4,000 records.
Use native table copying/export for the applied measurement data. Reopening/rerunning
reconstructs it from saved options and inputs. See the
[validation record and limits](python-ihc-selected-values-validation.md).

## Scatter rectangle row preview (0.3.17)

Expand **Rectangle row preview** below the local scatter marker controls. Enter finite
X/Y minimum and maximum bounds, then activate **Preview rectangle rows** (or press Enter
in a bounds field). Comparisons include both boundaries and use the displayed raw or z
values. Alternatively enable **Drag a rectangle to preview rows** and drag inside the plot.
The rectangle replaces the current preview, including when individual-row toggle mode is
on. Only complete pairs for the local X/Y markers are eligible; ties retain separate rows.
An empty valid rectangle clears the preview. Invalid bounds leave the preview unchanged.

Dragging starts only in the plot area, clamps to its edges, and commits the preview on
release. Escape or pointer cancellation abandons the in-progress drag. The point-click
shortcut is suppressed while drag mode is enabled; keyboard point inspection remains
available. Clear, restore, branch/cell inspection or changing the local marker pair removes
the rectangle. Marker-pair changes reset bounds but retain selected source identities.
These controls are transient. Enable saved selections and use **Apply** to update native
selection summaries, the optional nominal flag and selected-marker table. Full-cohort
analysis values and native X/Y roles are unaffected. See
[validation and limitations](python-ihc-brush-validation.md).

## Heatmap keyboard navigation (0.3.18)

Tab enters the matrix at its last focused/clicked cell, initially the first displayed cell.
The matrix contributes one Tab stop. Arrow keys move one cell horizontally/vertically;
movement stops at the current row/column boundary. Home/End move to the first/last marker
in the current row. Ctrl+Home/End (or Command+Home/End) move to the matrix endpoints.
Native Enter/Space activation is retained; Tab/Shift+Tab leave the matrix normally.

Focus follows displayed clustering order and inspects the original source row and marker,
including missing cells. As before, focus replaces the local row preview in ordinary mode.
When **Toggle individual rows on activation** is checked, focus inspects without changing
selected rows; Enter/Space or clicking toggles that source row. Apply remains the only
native write. Clear/Restore retain the remembered cell. Rerunning/reopening resets keyboard
position to the first cell; saved applied rows remain governed by the snapshot guard.
See [evidence and remaining accessibility gates](python-ihc-keyboard-validation.md).
