# Diagnostic meta-analysis: study review core

`pydiagnosticmeta` starts the oncology migration in **OncoPath Py → Evidence review →
Diagnostic study review**. This is a partial port of the frozen OncoPath 1.1.2
`diagnosticmeta` baseline. The existing R module and its calculations are unchanged.

## Implemented scope

Choose an exact text/factor study identifier and numeric TP, FP, FN and TN columns.
Each supplied row is a separate 2×2 table. The native individual-study table shows
raw counts, sensitivity TP/(TP+FN), specificity TN/(TN+FP), and pointwise Wilson
score intervals. Confidence defaults to 95%, with integer choices from 50–99%.
Zero cells remain zero: no continuity correction is applied. Both reference margins
must be positive. Intervals assume independent participants within each study.

The score intervals follow the [NIST formulation](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
and the baseline's individual-study Wilson calculation. The R reference fixtures
use `stats::prop.test(correct=FALSE)`, including zero/perfect proportions and
50%, 80%, 95% and 99% intervals. They are not exact Clopper–Pearson intervals.

The row audit reports supplied, retained, excluded and retained zero-cell rows,
plus unknown/repeated ID accounting across **all supplied rows**. Exclusion reasons
identify missing, negative, fractional or oversized counts and empty reference arms.
Counts are never rounded. Nonfinite counts and nonnumeric/date/matrix inputs are
rejected. A study total cannot exceed 2^53−1, the exact integer transport ceiling.
One to 200 aligned rows are supported without sampling. Numeric ID conversion is
explicit; leading zeros, literal NA and nonblank whitespace stay exact.

By default invalid rows are excluded and audited. **Reject missing or invalid
counts** instead blocks the calculation. If every row is excluded, the native audit
remains available with zero retained studies and no forest plots. Missing required
roles produce an informative pending state. These transitions clear previous results.

Unknown labels are displayed as Unnamed study; source-row IDs disambiguate every
row, including repeated labels. Repeated cohorts/readers/thresholds are never merged
or treated as evidence of independent studies. No automatic participant deduplication,
threshold choice or clinical inclusion rule is performed.

## Interface and plots

All five data roles are in the first variable supplier. Confidence and validation
controls stay expanded, followed by native table/report choices. Plot settings and
console diagnostics are secondary. Individual results and exclusion rows default
on so the implemented review core is immediately visible; this differs from the
full R analysis's optional individual-study display. Unsupported model controls are
omitted instead of silently ignored.

Optional native sensitivity and specificity forests use the same raw estimates
and intervals as the table. Their markers have equal size; no study weights or pooled
diamond are calculated. Forests display the first 20 retained source rows by default
(configurable 5–100), with explicit truncation disclosure. Tables retain all eligible
rows. Figures are constructed in Python and displayed/exported through jamovi Image
results. No model is fitted when drawing a plot. Linked interactive study/SROC
inspection remains planned; static export is qualified separately below.

## Feature and omission matrix

| Feature | This increment |
|---|---|
| Raw study inputs, exclusions and exact-label/source-row audit | Implemented |
| Study sensitivity/specificity and pointwise Wilson intervals | Implemented |
| Native study tables, descriptive report and static forests | Implemented |
| Reitsma bivariate REML/ML/fixed/moment models and summary uncertainty | Omitted |
| PHM SROC, prediction/confidence regions and pooled ratios | Omitted |
| Heterogeneity, moderators, Deeks/funnel analyses | Omitted |
| Continuity-correction sensitivity analyses | Omitted |
| Display-only linked forest inspection | Implemented in 0.3.56 |
| Applied study filters and SROC linking | Planned |
| Full baseline parity and clinical/platform release acceptance | Pending |

This review core is not a meta-analysis estimate. In particular, it does not pool
counts or average study proportions as a substitute for hierarchical synthesis.
[Cochrane's DTA software guidance](https://methods.cochrane.org/sdt/software-meta-analysis-dta-studies)
provides separate bivariate/HSROC modelling resources. These methods need their own
implementation, convergence and numerical-equivalence qualification.

The typed **Diagnostic Study Review Examples** dataset has twelve synthetic rows:
eight retained studies, four excluded rows, three retained zero-cell tables,
one unknown ID and one repeated cohort label. No patient data are included.

## Qualification

- All 50 focused Python/generator/registry/menu checks and all 415 full Python
  tests pass. The full run took 250.528 seconds with bounded numerical-library
  threads and unchanged runtime limits. The 100 base-R score fixtures include
  boundary proportions and multiple confidence levels.
- All 43 focused native R assertions pass against the completed build: raw counts,
  base-R intervals, sparse row IDs, numeric Nominal factor transport, a 3e9 cell,
  confidence changes and valid/pending/strict/all-excluded recovery. Plain text
  factors are rejected; genuine numeric factors use jamovi's numeric values metadata.
  Initial harness path/metadata errors are retained separately. Testthat reports
  no failures, errors, warnings or skips; sandbox diagnostics remain in the log.
- Full compiler/R build, final generator/status freshness and all 29 extracted
  package cases pass. Coverage-only registry metadata was refreshed after the
  build; every other archive member was verified byte-identical. Final packaged
  runtime checks were repeated. Installed manifest, UI, R database, helper, analysis,
  registry and typed dataset match the final archive byte-for-byte.
- macOS arm64 jamovi 28.13: GUI Sideload, Data Library example, five saved states,
  strict rejection, missing-role clearing, all-excluded audit and recovery pass.
  Only the separate all-excluded fixture deliberately changes TP to 1.5 throughout;
  all other source columns are retained. Original-source states retain every input.
- The recovered file was reopened in a fresh engine after final installation,
  explicitly recalculated by toggling the report, and saved again. Native HTML
  tables match expected row accounting, raw counts and displayed study estimates.
  Both embedded 1437 × 1277 forest PNGs were visually inspected. This verifies
  native HTML/image export, not a direct Save Image workflow.

Evidence: [qualification record](validation-exports/python-diagnostic-studies-0.3.55-checks.json).
Recheck artifacts with `python3 tools/check-diagnostic-study-artifacts.py`; reproduce
native checks with `PYTHONHOME=/Applications/jamovi.app/Contents/Resources Rscript
--vanilla tools/check-diagnostic-studies-native.R [completed-library-directory]`.

Full native inventory, additional platforms, assistive-technology certification,
clinical review and every pooled-model method remain unqualified.

## Linked study inspector — 0.3.56

Enable **Plots and Interaction → Linked study inspector (includes native forests)**.
Python supplies the existing raw counts and Wilson estimates/intervals. Local
JavaScript draws the paired forests and highlights precomputed rows; it performs
no statistical fitting or count-based recalculation. All retained rows are shown
(up to the existing 200-row input limit), without display sampling. Native forest
limits remain separate and are disclosed.

Select a study button or a forest point to highlight both intervals and inspect
TP, FP, FN and TN. Hovering previews another row; leaving that point restores the
selected row. Each label retains its original source-row ID, so repeated or
unknown study names remain distinguishable. Percentages in the local readout are
rounded to one decimal; native tables retain the computed values.

The study buttons have one remembered Tab stop. Up/Down arrows clamp at the
endpoints; Home/End reach the first/last study. Tab/Shift+Tab and native Enter/Space
activation remain available. First study resets local focus. Focus and row-band
highlighting supplement colour, and the readout is a live status region. Labels
are assigned as text; JSON escapes markup delimiters before entering the script.
All assets are local and no host-option or network API is called.

Selection is transient: it changes this inspector only and starts at the first
study after a backend rerun or saved-file reopening. Native study tables and
forests continue to describe the supplied cohort. Applied exclusions, saved study
filters and model changes are not provided by this display control.

Native sensitivity and specificity forests accompany the inspector even when
the separate forest checkbox is off, providing static export/save counterparts.
Turning the inspector off clears the HTML view; pending, strict-invalid and
all-excluded states clear it together with stale plots. The new display option
defaults off for older 0.3.55 saved analyses. Existing analysis option names and
defaults are retained, and the new option is appended to the literal SPEC.

Initial qualification: 54 focused Python/generator/registry/menu tests pass. The
synthetic jsdom harness verifies precomputed point geometry, paired hover/selection,
keyboard boundaries, native activation, one/200-row bounds, hostile labels, two
independent instances and no host/network calls. It uses an already installed
development dependency; no new runtime package is bundled. Final native, archive,
full-regression and desktop evidence is recorded below.


Qualification completed on macOS Apple Silicon / jamovi 28.13:

- Full Python regression: 419 tests pass; focused subset: 54 pass.
- Native R lifecycle: 52 assertions pass; final packaged runtime: 29 cases pass.
- Compiler/R build and generator/status freshness pass. The final archive includes
  one subsequent reviewed HTML scrolling fix; all other compiler-built archive
  members are unchanged. Final native/package checks used the refreshed asset.
- GUI Sideload, older 0.3.55 defaults, paired point/button selection, keyboard
  endpoints and pointer preview/restore pass. Pointer hover events were delivered
  with native drag movements. Local selection resets to study 1 after a fresh
  engine reopens the saved explorer fixture.
- Seven synthetic saved states retain their expected source inputs. The native
  HTML export preserves the audit and eight retained studies, with both static
  1437 × 1277 forests; PNG files are extracted from that GUI-produced export.

Native backend tests establish clearing of plot state on failure. The GUI clears
inspector content, but its accessibility tree retains named Image elements in
pending/strict states; blank-placeholder appearance has not been separately
visually certified. Direct Save Image, large-matrix desktop interaction, broader
accessibility/themes, Windows/Linux, full native module regression and clinical
review remain pending. Standalone native testing emitted sandbox permission
messages, with no failed assertions; these remain visible in its log. The initial
package check rejected a stale asset before runtime; final checks passed after
refresh, with that earlier guard log retained separately.

Reproducible artifact verification: `python3 tools/check-study-inspector-artifacts.py`.
Evidence and limits: [0.3.56 checks](validation-exports/python-study-inspector-0.3.56-checks.json).
This remains a partial study-review core; applied filtering and all pooling/SROC
methods are outside the implemented scope. Inventory remains 27 partial ports,
34 planned targets, 12 utilities and zero full-parity releases.
