# Native SVG experiment validation — 0.3.7

Recorded 2026-10-26. This is an experiment, with native GUI acceptance incomplete.

## Passing evidence

- Full bundled-Python suite: **217 tests passed**.
- Full installed-package R suite: **619 expectations passed**, zero failures, warnings or skips.
- Final targeted checks after layout/initialization changes: **6 Python tests and
  20 installed-package R expectations passed**, including early script registration.
- All **24 entry points** compile; generator/status freshness checks pass.
- All **14 packaged runtime cases** pass, including the new Svg result payload and local script integrity.
- New Python comparisons cover both inequality directions, both interval methods and all
  three optimization criteria. Native tables and static plots agree exactly with the
  existing D3 entry point; it uses the same independently tested Python engine.
- Tests cover tied cutoffs, automatic and endpoint rules, missing pairs, undefined
  proportions, the 1,000-row payload, invalid settings and markup-bearing variable names.
- R checks compare five exact proportion intervals against independent `binom.test()`
  references, serialize the Svg result, clear incomplete results and recover after errors.
- The local DOM harness verifies linked numeric/keyboard/ROC controls, lookup boundaries,
  local snapshot labels, reset, invalid input and serialized visible SVG content. It now
  loads the script before inserting the result, matching native jamovi's ordering.

The first full run found two test-harness errors: the expected utility count needed to
increase from seven to eight, and a nested R6 assignment in the new lifecycle test was
invalid for that assignment target in R. These were corrected before the passing full run.

## Native GUI observations and open gate

Installed the standard `ClinicoPathPj_0.3.7.jmo` into the existing module using jamovi's
GUI. Opened the existing 180-row synthetic frontend comparison in a fresh engine and
added the new analysis. The native cutoff 2 gives TP 47, FP 10, FN 8 and TN 115,
matching the other frontends. Native tables and both static images render.

The initial GUI run caught inline SVG layout and script insertion-order issues; the
renderer now uses block layout, scoped styles and one bounded observer with cleanup.
The corrected layout and numeric controls are visibly present in jamovi. A later check
showed that the numeric field changed while the plotted preview did not. The generated
bridge now registers script assets in `.init()` as well as `.run()` so they are available
when the native view is first constructed. Final fresh-engine confirmation of this
change remains pending.

Save As did not produce the intended separate comparison file during this session.
Automatic approval review rejected discarding the unsaved synthetic window for a
restart. The quit was cancelled; the original saved comparison fixture is unchanged.
A user approval question is pending before discarding that temporary window.

**Not yet qualified:** final native dragging/keyboard/ROC behavior, current-view SVG/PNG
export, save/reopen, missing-module snapshot viewing, other architectures/platforms
and clinical use. No native GUI export or reopening claim is made for this experiment.
The native static Image counterparts remain available from the shared engine.

See [methods, interaction semantics and comparison](python-svg-cutoff.md).
