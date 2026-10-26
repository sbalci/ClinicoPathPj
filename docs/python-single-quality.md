# Single Variable Quality Check — Python core

`pycheckdata` is under ClinicoPathPj → Descriptives. It implements a screening core
from the frozen checkdata baseline without changing the existing R analysis.

Import `data/python_single_quality_examples.csv` and select Measurement. The example
has 12 input rows, 11 observed measurements, one missing value, two distinct observed
values and nine excess repeats. Row 11 (100.5) is selected by z-score and IQR; MAD is
zero, so the modified z-score method is unavailable. Selecting Category illustrates
literal NA text versus genuinely missing cells; CSV import settings should retain NA
as a literal category if that comparison is required.

## Methods and denominators

All calculations run in Python. No observations are removed, imputed or changed.
Missing values are excluded from observed-value summaries and outlier calculations.
Sample SD and type-7 quartiles match base R. Scaled MAD is `1.4826 × median(|x−median|)`.
Population-moment skewness follows the baseline (zero at n < 3 or constant values).
CV is `100 × |SD/mean|`, suppressed at zero or below the minimum absolute mean; it is
appropriate only for ratio-scale measurements with a meaningful zero.

Numeric screening uses strict thresholds: |z| > 3, outside the 1.5 IQR fences, and
|modified z| > 3.5. Modified z divides by scaled MAD once; it is unavailable at n ≤ 3
or zero MAD. Constant-data z-scores are undefined. Zero-IQR fences are still applied,
matching this baseline, unlike the multi-variable quality port's zero-IQR rule.

At n < 3, screening is unavailable. At n = 3–9, one method can select a row, but these
flags are explicitly informative-only. At n ≥ 10, two methods must agree. Requested
log or square-root transformations affect screening only; raw values remain in tables
and plots. Unsupported domains fall back to raw-scale screening with a warning.

Numeric frequencies list repeated values only. Categorical/text frequencies list all
observed values, omitting unused levels. Percentages use observed rows; rare categories
are strictly below the entered percentage, without prior rounding. Repeated categories
do not identify duplicate patients. Missingness runs, longest missing run and trailing
missing count describe input order; sorting can change them.

## Interface, saving and display bounds

The variable is visible at the top. Screening controls are expanded; results, plots,
interaction and saving controls are grouped into separate sections.

The native outlier table lists the first 200 selected rows, while its note gives the
full-data selection count. Frequencies list at most 200 values. The static and optional
Observable row plots use the first 500 input rows; this ordered preview does not change
full-data summaries or saved flags. Categorical/text inspection provides a local table
without a numeric plot. Status filters and row search affect display only; changes to
screening methods use native jamovi options and rerun Python.

Enable Screening flag under Save to Data to create an analysis-owned nominal column:
Not selected / Selected. Original row alignment is preserved. Missing measurements,
categorical/text variables, disabled screening and n < 3 produce missing saved flags,
not zeros. At n < 10, Selected means an informative single-method flag. Review the
method notes before using these flags; no automatic exclusion is performed.

## Feature scope

| Baseline feature | This core |
|---|---|
| Completeness, distinct/repeated values | Implemented |
| Z/IQR/MAD flags, transforms and consensus | Implemented |
| Numeric distribution and CV guard | Implemented |
| Category frequencies and rare threshold | Implemented |
| Missingness position summaries | Descriptive counts only |
| Heuristic grades, severity and clinical-name ranges | Omitted |
| Runs-based missingness inference and dropout interpretation | Omitted |
| Category case/whitespace diagnostics | Omitted |
| Formal Little MCAR inference | Not applicable to one variable |
| Saved flags and local row inspection | Additional Python-port features |

This remains a partial migration entry. A selected flag is not a diagnosis, data error
or instruction to delete a record. Larger GUI payloads, additional platforms and the
omitted baseline features need separate qualification.

See [validation evidence](python-single-quality-validation.md) and the
[saved example](validation-exports/python-single-quality-0.3.6-validation.omv).
