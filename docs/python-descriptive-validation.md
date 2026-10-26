# Descriptive ports: validation evidence for 0.3.1

Recorded 2026-10-25 on macOS arm64 with jamovi 28.13 and its bundled Python/R.
This qualifies the tested core, not full parity or clinical use across all 61 targets.

## Numerical evidence

- `tests/fixtures/descriptive-oracles.json`: eight summary/moments/Shapiro fixtures and
  140 binning/label/closure fixtures produced by `tools/generate-descriptive-oracles.R`.
  The categorization oracle executes the archived R backend from the frozen baseline.
- Summary comparisons use base R and `moments`. Category comparisons use `cut()`, type-7
  quantiles and `classInt` Fisher partitions. Fixtures cover missingness, endpoint ties,
  duplicated quantiles, interval closure, manual extension/exclusion and labels.
- Fisher-Jenks also agrees with independently enumerated small-data partitions. A fixture
  exposed equal-objective partitions: stable extended-precision costs and deterministic
  tie handling reproduce the baseline boundary selection.
- All 176 Python tests pass. All 464 installed-package R expectations pass, with no
  warnings or skips. R checks include native Output protobuf values, original row IDs,
  missing positions, level order, output names, ordinal/nominal metadata and exact R-code
  boundary round trips.

## Integration and lifecycle evidence

The generator, migration-status freshness and whitespace checks pass. The compiler builds
all 18 entry points. Package inspection verifies the single ClinicoPathPj identity,
version, registry/source equality and helper bytes; eight packaged analyses execute in
jamovi's bundled Python, including the two new ports.

A native R lifecycle test reproduced duplicate table rows after successful reruns and an
old plot after input removal. The shared bridge now clears table rows/notes and plot state
when replacing a successful result or entering a known incomplete state. Computed notices
are reused and retired when no longer applicable. Errors remain visible. Tests cover
valid -> changed selection -> incomplete -> valid and notice replacement.

## Desktop evidence

The standard `ClinicoPathPj_0.3.1.jmo` was installed using Modules -> Sideload into the existing
module. A fresh jamovi process exposed both analyses once under Descriptives.

Using the existing 36-row synthetic core CSV:

- `pysummarydata` ran on RiskA and Measurement with diagnostics and outlier reporting.
  Measurement mean was 990.944, sample SD 2217.433; six flagged observations retained
  original row numbers 31-36. The histogram uses independent axes for the two variables.
- `pycategorize` produced four quantile groups of nine observations (25% each). Native
  Save to Data created `Measurement_cat` as an analysis-owned ordinal column.
- Saved `validation-exports/python-migration-0.3.1-descriptives.omv`, quit jamovi and reopened
  it in a fresh process. Both analyses and plots were present with the expected values.
  Archive metadata independently confirms 36 rows, the ordinal output column and its
  association with `pycategorize`/`addtodata`; both PNG resources are embedded.
- Exported the reopened summary histogram using jamovi's native Image -> Export -> PNG.
  `validation-exports/pysummarydata-0.3.1-native-export.png` was decoded and visually checked.

The final package rebuild changes registry evidence text only; calculations, bridge and
UI match the GUI-tested candidate. The installed candidate retains the earlier registry
coverage text until the rebuilt package is installed again.

## Remaining acceptance gates

Category-count plot export and exhaustive per-method desktop rerun/cancellation tests
remain pending. The sampled Fisher-Jenks branch (n > 20000 and distinct values > 3000) is
rejected explicitly; the original ggplot histogram bin alignment/style is not replicated. Version 0.3.11 adds an
optional native 30-bin histogram with exact break-point lines; see
[its separate validation record](python-categorize-histogram-validation.md).
Original gt HTML styling is replaced with native tables. Code export applies the displayed
frozen boundaries rather than recomputing them. Other architectures/operating systems,
full baseline parity and clinical review remain unqualified.
