# Correlation keyboard follow-up

## Native finding in 0.3.21

On macOS arm64 / jamovi 28.13, the 0.3.21 package installed through the GUI and
recalculated the saved 0.3.20 fixture in a fresh engine. Arrow movement and row/matrix
endpoints updated the local inspector. Tab left the matrix and Shift+Tab returned to the
remembered cell. However, Left Arrow at the first cell moved to the row's last cell.
This is a failed keyboard-boundary acceptance check, not a numerical failure.

Handled navigation events called `preventDefault()` but still bubbled. A document-level
keydown regression observes the arrows and Home/End escaping the original handlers;
that regression fails before the repair. Version 0.3.22 also calls `stopPropagation()`
for handled navigation keys. The regression then passes. Tab, Enter/Space and unhandled
modified keys still propagate normally. This repair changes no calculations or saved options.

The 2/3/20-variable DOM fixtures, six focused Python checks and 17 packaged-runtime
checks for 0.3.21 remain evidence at their original scope; they did not detect the native
host interference. Native requalification of the 0.3.22 repair is recorded below when run.

## Repaired native result — 0.3.22

The repaired package was installed in the GUI and jamovi restarted. The frozen synthetic
fixture was opened and recalculated (Spearman to Pearson) to generate current-template
results. First-cell Left stayed at the first cell. Right/Down moved to the expected cell;
row End, Command+End and Control+Home reached their expected endpoints. Right/Down at
the last cell stayed there. Tab exited the matrix and Shift+Tab returned to the remembered
cell. Return and Space retained inspection behavior. No native cohort/method changes
were made by those interactions.

A separate Pearson/pairwise fixture was saved, jamovi quit and restarted again, and the
new OMV reopened. The restored cohort reported eight input and six common complete rows;
first-cell Left remained clamped and Right advanced correctly. The original 0.3.20 fixture
was preserved. Local focus position itself is transient and is not promised across reopening.

- [Saved repaired fixture](validation-exports/python-correlation-keyboard-0.3.22-validation.omv)
- [Desktop checks and fixture hash](validation-exports/python-correlation-keyboard-0.3.22-desktop.json)
- [Final package checks](validation-exports/python-correlation-keyboard-0.3.22-package.json)

Six focused Python tests, DOM fixtures at 2/3/20 variables, the compiler/freshness checks
and all 17 packaged-runtime cases pass. This closes the specified macOS keyboard gate,
not full assistive-technology/theme/platform certification. Native plot-export evidence
remains scoped to 0.3.20; no statistical calculations or saved options changed here.
