# Python multi-variable visual quality

Choose **ClinicoPathPj → Descriptives → Multi-Variable Visual Quality** (`pydataquality`).
Import `data/python_dataquality_examples.csv` for a synthetic 24-row example with one
repeated full record, three missing ages, two missing marker values and a high marker value.
Select all four variables, enable missing-value analysis, duplicates and row-level mode.
The expected complete-case count is 19; one row is an excess repeat of an earlier row.

## Accounting and controls

The always-visible native profile reports observed/missing/distinct counts, excess repeated
values, constants, high categorical/text cardinality and exploratory numeric IQR flags.
The completeness table uses all selected variables, without excluding or imputing rows.
Variables with no observations remain visible with unavailable repeat percentages.

- Missing-data flags compare missing counts with the entered percentage threshold before
  rounding, using a strict greater-than rule. Exactly 10% is not above a 10% threshold.
- Excess repeated values equal observed minus distinct observed. Missing codes are excluded;
  a literal text category such as NA is observed. Unused factor levels are not observations.
- With two or more selected variables, row-duplicate mode counts identical tuples, including
  equal missing positions. Excess duplicates exclude the first occurrence of each tuple.
  Evidence lists the first original row ID of each of the five largest repeated groups,
  sorted by occurrence count and then first occurrence. It does not display record values.
- With one variable, row mode falls back to observed-value counting with an explicit note,
  matching the R baseline. Missing values are excluded from that fallback count.
- Constants have exactly one distinct observed value; no near-zero-variance test is implied.
- High-cardinality flags apply only to categorical/text variables: more than 50 distinct
  observed values and more than half of observed values distinct.
- IQR flags use R type-7 quartiles and 1.5 IQR fences only above 10 observed numeric values.
  Zero IQR gives zero flags, matching the frozen baseline. This screening rule can miss an
  extreme value when most measurements are identical. Smaller cohorts have unavailable flags.

Repeated categories are often valid. Equal selected rows do not establish duplicate
patients or justify deleting a record. Recommendations name review tasks rather than
assigning a validated quality grade. Missingness patterns cannot determine MCAR/MAR/MNAR.

## Plots and local interaction

Native Data Overview and Missing Patterns maps show the first 200 rows and first 20 selected
variables, preserving original row IDs. The third plot counts declared variable types.
All tables use the full dataset. These display limits are disclosed in the results; the
preview is deterministic and is not a random or representative sample.

The optional interactive preview stores only row IDs, variable names and missing/observed
flags. It shows ten preview rows per page, supports variable filtering and filtering to
rows with missing cells in the preview, and exposes a cell's row/variable/status on focus,
hover or click. M/O text accompanies color. Controls are keyboard accessible and local;
no network access, data editing, fitting or cohort change occurs. The missing-only filter
uses any preview variable, including when the variable selector shows only one column. Its paired native static
map remains available for export and saved-file reopening. Display filters are not applied
to that static map or any table and are reset when the view is reconstructed.

The analysis accepts at most 200 variables and ten million selected cells per run. The
shared bridge rejects infinite numeric values; recode them as missing explicitly first.
One row should represent the intended observation unit. Filters in the dataset are honored
by the normal jamovi bridge, and previews retain the original row mapping.

## Scope relative to the frozen R analysis

This port replaces HTML tables and visdat drawing with native jamovi tables and Python
figures. The declared transported Numeric/Categorical/Ordinal/Text kinds are shown;
parsing-based `vis_guess` detection is omitted. Little's MCAR test and the original
heuristic quality-grade labels are omitted explicitly. No imputation, repeated-patient
inference or correction of the sheet is performed. Full baseline feature parity remains
false. Existing R modules and Python identifiers are retained.

See [validation evidence](python-dataquality-validation.md) for numerical, integration,
interactive, desktop and platform checks recorded separately.
