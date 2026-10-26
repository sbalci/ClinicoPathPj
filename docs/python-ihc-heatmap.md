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
while describing the same hierarchy. This core displays the leaf ordering, not dendrograms.

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
source row in both views. Enter/Space activates focused points; Clear row highlight resets
selection. Repeated patient IDs do not merge source rows. Local X/Y dropdowns can inspect
other selected markers, counting their complete/missing pairs without backend calls.
Search highlights labels/points without removing them. Local pair choices and highlights
are transient; change native X/Y roles to persist the pair and update native outputs.
Overlapping points are not jittered; individual rows remain accessible in the heatmap.
Native plots use the saved X/Y pair, not a transient local pair.

See [0.3.12 validation and remaining desktop gates](python-ihc-linked-validation.md).
No saved selected-row column is supplied. Other omissions:
dendrogram interaction, cluster significance/stability, differential-expression tests, clinical
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
