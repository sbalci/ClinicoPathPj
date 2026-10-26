# Single-variable quality validation — 0.3.6

Recorded 2026-10-25 with jamovi 28.13 on macOS arm64 and its bundled Python.
Evidence covers the implemented screening core, not full baseline parity or clinical clearance.

## Numerical and integration evidence

`tools/generate-single-quality-oracles.R` independently constructs 66 base-R fixtures.
The Python tests compare summaries, type-7 quartiles, sample SD, scaled MAD, strict
screening boundaries, transformations, missingness runs and selected original rows.
Fixtures include constant/zero-MAD data, small samples, unused factor levels, missing
codes, literal NA text, invalid domains and CV suppression. Saved flags retain original
row alignment and remain missing when screening is unavailable.

- Full Python suite: **211 tests passed**.
- Installed-package R suite: **600 expectations passed**, zero failures/warnings/skips.
- **23 entry points** compile; generator and migration-status freshness checks pass.
- **13 packaged runtime cases** pass; packaged helpers/templates match source.
- The offline DOM harness runs the actual bundled Observable libraries and checks status
  filtering, missing rows and original-row search without changing full-data results.
- Plot geometry checks preserve continuous values without categorical jitter.

A shared bridge lifecycle regression was reproduced before repair: clearing a required
variable retained saved output values. The repaired bridge stores its owned original-row
IDs and clears those outputs on the pending-input path. R regressions cover both new
screening flags and existing categorization outputs, including restoration.

## Native GUI evidence

Installed the standard 0.3.6 package into the existing ClinicoPathPj module, restarted
jamovi, and imported `data/python_single_quality_examples.csv`.

- Measurement reports 12 rows, 11 observed, one missing, two distinct values and nine
  excess repeats. Row 11 is selected by Z and IQR, while MAD is unavailable.
- Interactive Flagged filtering shows one preview row; native selection counts stay one.
- Enabling saved flags gives ten Not selected values, Selected at row 11 and missing at
  row 12. Clearing the required variable clears native results, HTML, plot and saved
  flags; restoring Measurement recalculates the results and flags.
- Saved [the synthetic OMV](validation-exports/python-single-quality-0.3.6-validation.omv),
  quit/restarted jamovi and reopened it in a fresh engine. Native tables, saved flags,
  static image and local Observable controls restored. Local status resets to All.
- Exported [the native plot](validation-exports/python-single-quality-0.3.6-screening.png)
  through Image → Export → PNG. The complete 1300 × 800 PNG passes chunk CRC checks;
  the OMV ZIP is valid and embeds its native image resource.

The final evidence-metadata rebuild retains the GUI-tested statistical, bridge,
renderer, UI and JavaScript bytes. The earlier interrupted PNG export was replaced by
this complete export before qualification.

## Remaining gates

The registry remains partial. Name-based clinical plausibility ranges, heuristic grades
and severity, category naming diagnostics and runs-based inference are omitted. Formal
Little MCAR inference is not applicable to a single variable. Large desktop previews,
additional platforms, exhaustive cancellation scenarios and clinical review remain open.
See [methods and omissions](python-single-quality.md).
