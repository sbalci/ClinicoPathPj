# Observable cutoff experiment

`pyobservablecutoff` is a separate analysis under **ClinicoPathPj > Medical Decisions**.
It complements `pydotdecision` (custom SVG) and `pyd3cutoff` (D3). All remain in the
single module. The new entry is a utility experiment; the 61-analysis migration target
and the existing kappa identifiers remain unchanged.

## Use it

Open `data/python_d3_cutoff_examples.csv`. Choose Measurement, Reference, and the
explicit positive level Positive. Enter `2` in the native applied-cutoff option to
compare all three implementations on the same rule. The teaching fixture has 180 rows
and produces TP 47, FP 10, FN 8, TN 115 and AUC 0.962472727272727.

The Observable interface adds:

- A synchronized slider/numeric input, direction and criterion selectors, automatic
  cutoff and reset buttons.
- Observable Plot dotplot tips and ROC crosshairs; clicking a ROC point previews its
  precomputed cutoff. The cutoff line can be dragged or operated with arrow keys,
  Home and End. Shift-arrow takes a larger step.
- Searchable original-row inspection. Checking a row outlines its dot. Search and
  selection change display only, retaining every complete row in ROC/count calculations.
- An explicit **Apply to HTML tables** snapshot. Native jamovi tables and both native
  static images remain tied to the saved analysis options.

Edit the native direction and applied-cutoff options to persist a rule. Select a native
criterion and leave cutoff blank to save an automatic rule. Recalculation or `.omv`
reopening restores saved options and resets browser search, selection and local preview.
Confidence settings and FP/FN weights are native options, shared with the D3 experiment.

## Architecture and methods

Python computes all statistics through `cpj_cutoff.py` and the shared
`cpj_cutoff_analysis.py` workflow. The D3 analysis now calls the same workflow; its
options, defaults and result contracts are preserved. The two frontend analyses receive
identical precomputed states and native result data. JavaScript performs display lookup
and geometry, without fitting models or recalculating inferential statistics.

Exact or Wilson proportion intervals, both test directions, three optimal-cutoff
criteria, endpoint/tie handling and missing-pair exclusions follow the
[D3 statistical contract](python-d3-cutoff.md). Fixed-cutoff intervals omit selection
uncertainty. AUC is empirical with half credit for ties and no inferential interval.
There is no population-prevalence correction or economic modelling.

The module bundles official Plot 0.6.17, Inputs 0.12.0, htl 0.3.1 and the existing
D3 7.9.0. Source URLs and SHA-256 hashes are recorded in
`inst/python/vendor/observable-manifest.json`; ISC licenses accompany the libraries.
The result runs locally, without an account, CDN requests or user package installation.
No Observable notebook runtime, hosted notebook or Pj background-service API is used.
Observable reactivity here consists of input events updating linked displays.

Official APIs: [Plot offline installation](https://observablehq.github.io/plot/getting-started),
[Plot pointer interaction](https://observablehq.github.io/plot/interactions/pointer),
and [Inputs](https://github.com/observablehq/inputs).

## Comparison scope

| Approach | Main benefit | Cost or limitation |
|---|---|---|
| Custom SVG | Smallest result; direct control | More custom interface code; no linked ROC in the existing utility |
| D3 | Detailed linked dotplot/ROC behavior | More manual drawing and event management |
| Observable Plot + Inputs | Declarative marks, tips/crosshairs, reusable controls and row inspection | Additional library payload; plot reconstruction when preview changes |

All use ClinicoPathPj's isolated Python process and export native Python-rendered images.
This compares frontend approaches, not different Python execution mechanisms. Native
option writeback is not supplied by Observable itself. The experimental row cap is
1,000 complete observations and HTML is bounded to 1.5 MB; no display sampling occurs.
No speed or clinical superiority follows from the interface alone.

See [validation evidence](python-observable-cutoff-validation.md). The optional
`tools/compare-cutoff-engines.py` reports warm Python computation/HTML sizes for all
three, excluding process startup, native rendering and browser work.
