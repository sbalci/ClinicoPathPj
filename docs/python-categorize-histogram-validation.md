# Categorization histogram — 0.3.11

Implemented 2026-10-26. This closes a plotting omission in the existing partial
`pycategorize` port; it adds no baseline target or new analysis entry point.

Enable **Continuous histogram with break points** under **Labels and Reporting**.
The option defaults to false, preserving existing analyses and their category-count plot.
Python computes 30 equal-width display bins spanning the observed minimum and maximum.
All observed values contribute, including uncategorized observations outside manual bounds
or on an excluded endpoint. Missing values do not contribute. Histogram bins use NumPy's
left-closed convention, with the final right endpoint included; these display bins do not
change the selected categorization method, boundaries, interval closure, or saved column.
Dashed lines use the exact unrounded boundaries from the native break-point table.

This is a Python/Matplotlib native Image, with jamovi palette and foreground/background
settings. The boundary vector travels with plot state so rendering needs no original dataset
or statistical refit. Existing saved plots without boundary metadata remain supported.
The result payload restricts these lines to histograms with at most 2,001 finite boundaries.
The original ggplot histogram's bin alignment and styling are not replicated.

Verification covers all six categorization methods; every combination of interval closure
and outer-endpoint inclusion; uncategorized tails; missingness; plot-default compatibility;
exact boundary geometry and dark-theme foreground; and invalid boundary payloads.
A native R test independently counts bins with `cut()`, compares break points and edges,
serializes/restores the R drawing state, renders it through the packaged Python renderer,
and checks enabled → disabled → incomplete → changed-valid state against a fresh analysis.
These R drawing-state checks are separate from desktop `.omv` qualification.

Executed checks:

- Full Python discovery run: 230 tests passed. The final focused descriptive/plot run
  passed 18 tests, including the additional method/payload checks added during the full run.
- Focused native R files: 90 expectations passed (49 descriptive, 10 renderer,
  31 single-variable/saved-output), zero testthat failures, warnings or skips.
  Process cleanup printed macOS `Operation not permitted` diagnostics in this environment.
- The full R run stopped in the pre-existing bridge process-lifecycle tests because macOS
  denied process inspection. It is not a full-suite pass.
- Compiler preparation/build and ZIP integrity passed for `ClinicoPathPj_0.3.11.jmo`.
  All 16 packaged-runtime smoke cases passed, including histogram counts and exact boundaries.
- Generator freshness, migration-status freshness and whitespace checks passed.
- Light/dark PNGs were produced; the dark rendering was visually inspected. These are
  renderer checks, not native GUI theme acceptance.

The original code fails the new feature/geometry checks (missing histogram and missing
boundary lines). Backups and execution logs are in
`/private/tmp/cpj-categorize-histogram/`.

Desktop fresh-engine interaction, `.omv` save/reopen and native export of this new histogram
remain pending. Prior category-column/summary-plot GUI evidence does not qualify the added
histogram. Full baseline parity, other platforms and clinical review remain pending.
