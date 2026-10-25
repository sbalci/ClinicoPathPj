# Observable cutoff validation — 0.3.5

Recorded 2026-10-25 on jamovi 28.13/macOS arm64. This is an experimental frontend
comparison; it is not full migration parity, clinical clearance or all-platform qualification.

## Numerical and integration checks

The new analysis calls the same `cpj_cutoff_analysis.py` workflow and `cpj_cutoff.py`
statistical engine as the D3 experiment. Numerical checks require exact equality of
native tables, plot-ready data, explanatory text and notices across both directions,
exact/Wilson intervals, confidence settings and all three cutoff criteria. Automatic
cutoffs, absent predictions, missing pairs and invalid settings are included. The
existing independent boundary/rank/R interval checks remain applicable to that engine.

All 204 module Python tests pass, including twelve tests across the D3 and Observable
experiments. All 569 installed-package R expectations pass with no failures, warnings
or skips, including 27 D3 and 27 Observable expectations for counts, R intervals and
valid → missing event → valid / invalid cutoff → valid lifecycle transitions. Additional
checks verify the 1,000-row/1.5 MB bounds, script escaping, local-only library embedding,
JavaScript syntax, registered identifiers and generator freshness.

## Offline browser-library checks

`tests/javascript/observable-cutoff.cjs` executes the real pinned D3, Plot, Inputs and
htl distributions in a jsdom 26.1.0 DOM. It checks numeric preview, both rendered SVGs,
HTML snapshot isolation, original-row search, selected-dot outlines, direction change,
reset and keyboard End behavior. The harness enables no external resource loading.

jsdom's form proxy does not implement own accessor setters as Chromium does. A documented
per-form prototype shim supplies those same accessors in the test harness only. The module
ships no such shim. Native GUI evidence is recorded separately below.

Reproduce with jamovi's bundled Python and a temporary development-only jsdom installation:

```sh
npm install --prefix /private/tmp/cpj-observable-dom --ignore-scripts --no-audit --no-fund jsdom@26.1.0
PYTHONHOME=/Applications/jamovi.app/Contents/Resources /Applications/jamovi.app/Contents/MacOS/python -B tests/javascript/make-observable-fixture.py /private/tmp/cpj-observable-fixture.html
NODE_PATH=/private/tmp/cpj-observable-dom/node_modules node tests/javascript/observable-cutoff.cjs /private/tmp/cpj-observable-fixture.html
```

The npm dependency is needed only for development testing. Users install no extra package.

## Local comparison measurement

On the same 180-row fixture, warm Python-run medians were approximately 17 ms (custom
SVG), 33 ms (D3) and 39 ms (Observable). HTML payloads were 10,948, 470,849 and 701,531
bytes. These are local descriptive measurements, not end-to-end speed or usability
evidence. The reproducible script and JSON record explicitly exclude startup, native image
rendering and browser work.

## Native GUI and release scope

All 22 entry points compile; generator/status freshness pass. Twelve packaged analysis
runtimes execute successfully, with local assets and registry/helper bytes inspected.

Installed through Modules → Manage installed → Sideload into the existing module and
restarted jamovi. The 180-row teaching dataset gave matching native counts of
47/10/8/115 at cutoff 2 in SVG, D3 and Observable analyses. Observable numeric preview
3 gave 30/0/25/125; HTML Apply left native results unchanged. Dragging selected
1.61041906121594 and ROC clicking selected 1.79017455846036. Searching original row
180 displayed one of 180 rows; selecting it visibly outlined the dot near 4.206 while
retaining full-cohort statistics.

Saved `validation-exports/python-observable-cutoff-0.3.5-comparison.omv`, containing
all three analyses and five native PNG resources. ZIP integrity passes. Native Image →
Export → PNG wrote `validation-exports/python-observable-cutoff-0.3.5-roc.png`.
The final layout correction removes the fixed maximum height from the small HTML
snapshot tables; jamovi table padding had clipped their last rows. The offline DOM
regression checks the absence of those bounds and all five metric rows. A final GUI
rerun displayed all counts and all five metrics without clipping. Saved the corrected
file, quit/restarted jamovi again, and reopened it: all three native matrices remained
47/10/8/115; Observable reset its preview to 2 and restored all 180 inspection rows.
The final installed analysis, shared workflow, template and manifest match source
byte-for-byte. The final package again passes all twelve runtime smoke checks, and
the five focused Observable Python tests pass after the layout correction. The ROC
PNG was decoded and visually inspected. The function guide documents browser-only Apply, native-option
persistence and experimental limits. Larger GUI payloads, exhaustive assistive-technology
qualification, additional platforms and clinical review remain outside this experiment.
