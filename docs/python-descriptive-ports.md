# Python descriptive ports — 0.3.1

Both analyses belong to ClinicoPathPj → Descriptives. Their identifiers start with `py`;
existing `pydescriptives`, `pyreportcat` and other utilities retain their identifiers.

## Continuous summaries: pysummarydata

Choose continuous variables, then optionally enable distribution diagnostics, outlier
reporting, draft sentences or guidance. Each variable uses its own observed values.
Native tables retain unrounded numbers; `decimal_places` formats narratives while jamovi's
global settings govern native table display.

- Mean, sample SD, min/max and R type-7 quartiles/median.
- Shapiro-Wilk W/p for 3–5000 nonconstant observations; missing test results carry a reason.
- Population-central-moment skewness and Pearson kurtosis (normal = 3), matching `moments`.
- Outlier fences Q1 − 1.5 IQR and Q3 + 1.5 IQR when n ≥ 4. Flagged rows retain original row IDs;
  observations are never removed automatically.
- Histograms use NumPy automatic bin selection and independent variable axes. Only aggregate
  bins enter saved plot state. Display is capped at 12 variables/2000 bins, with an explicit
  notice; numerical summaries retain all selected variables.

All-missing variables are excluded with a notice; an empty dataset is rejected. One observed
value has undefined SD. Constant data do not receive a misleading Shapiro-Wilk p = 1.
Distribution checks assume independent observations and are exploratory, without multiplicity
adjustment. Draft reports require study-specific units and context.

## Categorization: pycategorize

Configure the method and interval endpoints, review native frequencies and the first 200
input rows, then enable the native **Save to Data** control to create an analysis-owned
column. Once enabled, subsequent option changes update that column.

Equal intervals, type-7 quantiles, manual boundaries, mean ± k SD plus the mean, median
split, and exact Fisher-Jenks partitions are implemented. Duplicate quantiles collapse into
fewer categories with a notice. Unusable mean/SD bands are dropped and identified.

Manual boundaries are sorted/deduplicated and extended to cover the data by default.
Out-of-range exclusion keeps them unchanged. Right/left closure and inclusion of the open
outer endpoint match `cut()`. Missing source values and observed values excluded by bounds
or closure are counted separately. Percentages use categorized cases by default; disabling
`excl` uses all input rows. Zero denominators produce unavailable percentages.

Automatic, semantic, numeric, alphabetic and custom labels preserve interval order.
Invalid custom labels fall back with a notice. Saved columns retain that order, their
requested name, nominal/ordinal measure type and original row mapping, including missing
positions. The preview cap does not truncate saved values.

The exported R code applies **frozen displayed boundaries**, represented as hexadecimal
float literals so exact-threshold observations cannot move because of decimal rounding.
Names/labels are string-escaped; code is displayed, never executed by the module. Rerun the
analysis to derive boundaries for a different dataset. No R statistical execution is used.

## Current limits and differences from the frozen R baseline

| Feature | Status |
|---|---|
| Summary calculations, moment/normality diagnostics and IQR fences | Independent R fixtures |
| Interval methods, labels and closure assignments | 140 frozen-R fixtures |
| Jenks optimality | Independent exhaustive partitions on small inputs |
| Exact Jenks at 20,000 observations | Approximately 0.93 s in a local calculation benchmark |
| Saved names/order/row mapping | Native R protobuf checks; GUI qualification tracked separately |
| Jenks n > 20,000 with > 3,000 distinct values | Explicitly rejected; seeded R-style subsampling remains pending |
| Original categorization histogram with boundary lines | Pending; current native plot shows category counts |
| Original gt/HTML layouts | Replaced by native tables/text/plots |
| Categorization preview | First 200 rows; all input rows retained in saved output |
| More than 2,000 categories | Explicitly rejected |
| Full statistical/release parity | Pending; see the migration status matrix |

A seed is not used in the implemented exact Jenks branch. Its output note makes this
explicit. The retained seed option is reserved for the pending sampled branch.

## Synthetic examples

Use the existing **Python Core Examples** dataset or its CSV:

```r
d <- read.csv("data/python_core_examples.csv")
pysummarydata(data = d, vars = "Measurement", distr = TRUE,
              outliers = TRUE, report_sentences = TRUE)
pycategorize(data = d, var = "Measurement", method = "quantile", nbins = 4L)
pycategorize(data = d, var = "Measurement", method = "manual",
             breaks = "1,10,100,1000", labels = "numbered")
```

For a programmatically constructed variable name, use `do.call()` so jamovi's public
wrapper receives a literal name rather than interpreting an R symbol as a column name.
Saving columns uses jamovi's native output control rather than an R wrapper argument.

## Validation sources

`tools/generate-descriptive-oracles.R` regenerates the versioned fixture JSON from base R,
`moments`, `classInt`, and the archived categorization backend. Normal builds do not refresh
fixtures. Python tests cover those oracles, exhaustive partitions, invalid inputs and
runtime serialization. R tests cover native wrappers, exact exported code, original row
mapping and valid → pending → valid state transitions.

Detailed evidence and remaining GUI/platform gates: [validation report](python-descriptive-validation.md).
