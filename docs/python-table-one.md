# Overall-cohort Table One: Python standard-format core

`pytableone` is **Descriptives Py → Summaries → Table One (core)**, within the single
ClinicoPathPj module. Select numeric, categorical, text or logical variables. This is an
overall descriptive table: it has no group variable, hypothesis tests, confidence
intervals, SMDs, plots or interactive graphics. Native table operations provide copying
and export.

## Frozen baseline and supported subset

The registry retains ClinicoPathDescriptives 1.0.82.03 at commit
`7162149586afc8992f1ba17e56887e2fbcb0835d`, including its original source hashes. The
supported subset follows the standard `t1` engine. Other style engines are omitted
rather than displayed as working choices. Existing R modules and saved Python analysis
identifiers are unchanged.

| Feature | Core behavior |
|---|---|
| Overall numeric summaries | Mean/sample SD by default, or median/type-7 quartiles |
| Numeric codes with few distinct values | Remain measurements; no automatic categorical recoding |
| Binary factor display | Second declared level only, named explicitly |
| All-levels option | Displays both binary levels without changing counts/cohort |
| Categorical denominator | Recorded values within retained rows |
| Missing percentage | Missing count divided by retained rows |
| Missingness policy | Per-variable by default; optional listwise exclusion |
| All-missing variables | Omitted before listwise exclusion |
| Unsupported scalar storage classes | Omitted with a reason before exclusion |
| Matrix/array/list columns | Rejected before flattened values can enter statistics |
| Units and variable labels | Metadata annotations retained when supplied; no conversion |
| Other engines/styles and frequency-weight controls | Omitted |
| Full baseline parity | Pending |

The Python interface uses `cont=mean/median`, consistent with `pycrosstable`; these map
to the frozen standard style's `nonnormal=FALSE/TRUE`. There was no earlier installed
`pytableone` option contract to replace. Unlike the grouped cross-table default, this
standard Table One keeps numeric variables numeric even when they have only two values.

## Accounting and interpretation

Every supplied row is one record. Missing group-like values are ordinary variable
missingness here; no grouping role implicitly removes them. An entirely uncollected
variable does not make every row incomplete: the core omits it before constructing the
common complete-case mask. Unsupported scalar classes likewise do not affect that
mask. With no eligible variables, retained/excluded counts are undefined and the scope
text explains that exclusion was not applied. When listwise exclusion leaves zero rows,
the zero-row cohort is reported and no summaries or copy-ready statistical report are
produced.

Native continuous and categorical tables disclose valid/missing n and missing
percentages. A binary row's Counted Level is essential: it identifies the actual
numerator rather than implying that a particular value is the event. Declared factor
order and unused zero-count levels are retained. True missing factor levels remain
missing; literal NA and Unknown text remain recorded categories. Raw text/logical
categories use deterministic Unicode lexical order; use factors to specify an order
explicitly. Locale-dependent text ordering may differ from an R formatter.

SD uses n−1 and is undefined for a singleton. No automatic imputation, unit conversion,
patient deduplication, weighting or inference is performed. Convert dates/durations
explicitly to measurements with stated units or to intentional categories. Inputs
already expanded by the host remain supplied rows, not unique patients.

## Bridge and organized controls

The bridge appends optional storage classes, dimensions, original column row count,
units and label metadata. Python still receives the same numeric arrays, Factor values
and text lists; metadata is a separate dictionary attribute. Existing calculations do
not consume it. The Table One engine uses it to distinguish dates/custom classes from
plain text and prevent matrix/list data being summarized after transport flattening.
Older requests without metadata remain supported.

All calculations, type eligibility and cohort transformations run in Python. R provides
transport and native presentation. Generator-owned List visibility switches mean/SD
versus median/Q1/Q3 columns. Optional input completeness, explanation and descriptive
report text have separate controls. Eligibility is measured on the input rows, while
the primary tables describe retained rows; these counts can legitimately differ.

## Examples and validation

The synthetic example contains 25 source profiles, continuous Age/Code, two binary
categories, and an entirely missing NeverCollected variable. Default retention is 25
rows; listwise exclusion across included variables retains 21, despite the assigned
uncollected variable. Age has 23 valid values with overall mean 41; Code remains a
numeric measurement. The original CSV is reproducible using
`python3 data-raw/generate-table-one-examples.py` and contains no patient data. A typed
GUI-saved example avoids integer CSV measure-type inference.

Python fixtures independently check means, quartiles, categorical numerators,
denominators, binary orientation, zero complete cases, genuine/literal missingness,
storage metadata, units/labels and old decoded value types. Native R fixtures compare
base R and the installed `tableone` 0.13.2 object, including raw rather than merely
rounded formatter values. Numerical, compiler, GUI, compatibility, platform and
clinical/release evidence are tracked separately. Dated results are appended below
when qualification is complete.


## Qualification — 2026-10-29 / 0.3.43

- Python: 335 full-suite tests passed; after a report-wording correction, all 38
  focused Table One/runtime tests passed again. No statistical calculation changed.
- Native R: 267 focused assertions passed against base R and `tableone` 0.13.2,
  including metadata and valid → invalid → restored lifecycle checks. The full
  native suite passed 3,775 assertions but exited with five errors: macOS sandbox
  restrictions prevented `ps::ps_pids()` process inspection in existing cancellation
  fixtures. These are retained failures. A separate focused bridge run with process-inspection
  permission subsequently passed all 25 assertions, covering cancellation, timeout,
  restart, abrupt exit and child cleanup. The entire R suite was not repeated
  outside the sandbox.
- Native R matrix columns reach the existing row-identity guard before the new
  structured-storage guard. List columns can be rejected by jmvcore selection before
  the bridge. Both are rejected, but those early host errors are less specific than
  the direct Python storage messages.
- Compiler, generator/status freshness and 23 packaged-runtime smoke cases passed.
- On macOS arm64 / jamovi 28.13, the single ClinicoPathPj package was installed through
  Modules → Sideload. Native controls changed mean/SD to median/quartiles and toggled
  25/21-row retention and binary second/all levels. Saved files preserved the options;
  fresh-engine recalculation used the installed Python code.
- Native HTML tables and both .omv inputs are independently checked against source
  CSV counts, Python statistics and original row order by
  `python3 tools/check-table-one-artifacts.py`. All 25 input profiles remain saved.
  This analysis introduces no plot, so no plot-export claim is made.

The [machine-readable evidence](validation-exports/python-table-one-0.3.43-checks.json)
records separate gates and retained initial failures. Other table engines/styles,
frequency weights, full baseline parity, broader platforms/accessibility and
clinical/release review remain open.
