# Separate D3 cutoff experiment — validation evidence

Recorded 2026-10-25 on jamovi 28.13/macOS arm64. This evidence covers an experimental
utility, not clinical release clearance, all-platform qualification or baseline parity.

## Numerical evidence

Seven focused Python tests exercise 20 seeded, tied-marker fixtures in both directions.
Every evaluated boundary and additional interior/exterior cutoffs are checked against
independent Boolean classification counts. AUC is compared with all positive/negative
pairs, with half credit for ties. Errors, Youden and weighted-error optima are minimized
independently, including lowest-cutoff tie resolution.

Exact 90% intervals agree with R `binom.test()` and Wilson intervals with uncorrected
`prop.test()`. Native R tests additionally compare 95% intervals. At the same marker,
event, direction and cutoff, the existing dotplot and new function agree on counts,
proportions and exact intervals. Edge checks include missing pairs, undefined PPV/NPV,
single-class data, invalid confidence/cost/cutoff settings and the 1,000-row cap.

The shared-demo fixture has 180 rows (55 positive, 125 negative). At >= 2 it yields
TP 47, FP 10, FN 8, TN 115 and AUC 0.962472727272727. Automatic errors selects
2.126422511030663, with two optimal evaluated boundaries. `tools/make-d3-cutoff-example.py`
reproduces the CSV without requiring the original downloaded script.

## Integration evidence

- 199 Python tests pass across the module, including the seven new tests.
- The full installed-package R suite passes 526 expectations with no failures, warnings
  or skips. The subsequent focused R file passes 27 expectations, including the added
  lifecycle checks. It covers native
  results, reversed direction/Wilson intervals, valid → missing event → valid and
  invalid cutoff → valid transitions. Pending results clear tables, HTML and image
  states. Invalid-input errors retain prior native results for jamovi's normal greyed
  error display, while HTML clears; this preserves the existing bridge contract.
- All 21 entry points compile; generator and migration-status freshness pass.
- The archive has one ClinicoPathPj identity and includes the new registry entry,
  helper, analysis, template, official D3 and license byte-for-byte. Eleven packaged
  analysis runtimes execute successfully, including the new experiment.
- HTML tests check script-closing labels, JavaScript syntax, absence of native option
  writeback hooks/statistical fitting, and the 1.5 MB payload bound at 1,000 rows.

## Native GUI evidence

Installed `ClinicoPathPj_0.3.4.jmo` via Modules → Manage installed → Sideload and restarted
jamovi before adding the analysis. Existing dotplot and new D3 experiment appear separately
under Medical Decisions within the same module.

On the synthetic CSV, the explicitly saved cutoff of 2 produced the expected native counts
and AUC. Numeric preview 3 changed the linked view to TP 30, FP 0, FN 25, TN 125; Apply
updated its HTML snapshot while native counts stayed 47/10/8/115. Dragging moved the numeric
preview to 2.1286394862082547 and updated the ROC point. Clicking the ROC then selected
1.6893194035432166 and updated the dotplot/input/classification preview.

Saved `validation-exports/python-d3-cutoff-0.3.4-validation.omv`, quit/restarted jamovi,
and reopened from Recent files. The HTML preview restored the saved cutoff 2 and
47/10/8/115 counts; both native plots remained available. ZIP integrity passes and the
file embeds two native PNG resources. Image → Export → PNG produced
`validation-exports/python-d3-cutoff-0.3.4-roc.png`, decoded and visually inspected.

The final documentation rebuild retains identical analysis, helper, template and D3
bytes to the GUI-tested installation. The superseded 0.3.3 artifact is archived under
`build/previous-artifacts/`; the root package uses the standard 0.3.4 filename.

## Comparison evidence and remaining work

A local warm-run measurement on the 180-row fixture gave approximately 39 ms for the
existing dotplot's Python `run()` and 55 ms for the D3 experiment. HTML sizes were
10,948 and 470,849 bytes. `tools/compare-cutoff-engines.py` repeats this measurement.
These figures exclude process startup, image rendering and browser work; they are not
an end-to-end speed comparison. D3 supports richer linked exploration at a larger payload.
Both functions use the same Python execution mechanism.

Keyboard handlers and focus affordances are present; exhaustive native keyboard/screen-reader
qualification, GUI performance near the payload limit, additional platforms, and clinical
review remain pending. No Pj service API is assumed. No existing statistical defaults or
analysis implementations were changed.
