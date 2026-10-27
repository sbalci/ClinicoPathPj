# Linked IHC scatter keyboard navigation — 0.3.19

Implemented 2026-10-27 in the existing IHC utility. No new analysis, statistical method,
cohort rule, native option or runtime dependency is introduced. The 61-analysis migration
completion counts do not change.

## Behavior

The scatterplot has one remembered Tab stop among complete-pair observations. Right/Down
move to the next point in displayed heatmap row order; Left/Up move to the previous point.
Home/End reach the first/last complete point. Navigation clamps at boundaries and is explicitly
row ordered, not spatial. Overlapping points remain separately reachable by original row ID.
Missing pairs remain omitted and counted. A single-point view retains one stop; empty or
same-marker views have no point stops and retain their existing explanation.

Click/focus updates the remembered source row. Pair changes retain its stop when that row
is still complete, otherwise use the first complete row. Changing a pair from its selector
must not steal focus from that control. Runtime rerun/reopen starts from the first point;
this transient focus state is not a new saved option.

Existing focus/selection behavior is retained: ordinary focus previews a source row;
individual-row toggle mode inspects without changing the preview until activation. Enter/Space
activates once. Tab/Shift+Tab and unrelated keys are not intercepted. Navigation and pair
switching make no backend calls. Only the existing Apply writes the snapshot-bound row selection.
The point group is associated with visible keyboard instructions through `aria-describedby`.

## Evidence and limits

The new DOM harness covers tied points, omitted pairs, clamped boundaries, Home/End,
selector focus retention, redraw, empty/same-marker views, one/200 points, preserved toggle
mode, Enter/Space and explicit Apply. It stubs native option dispatch and rejects network use.
Existing linked-view, tree, selection, rectangle and matrix-keyboard harnesses are rerun
separately. Python/generator, compiler and extracted-package evidence is recorded after checks.

Native GUI keyboard interaction, rerun/save/reopen/export on this build is pending. Prior
0.3.18 native matrix-keyboard qualification is recorded evidence for that version, not proof
of this scatter change. Full screen-reader, theme, touch and additional-platform qualification
remain open. This is not accessibility certification, clinical validation or release clearance.

## Checks run in this session

- 50 focused Python tests passed: IHC transforms/geometry, snapshot-bound selections,
  independent tree fixtures and generator contracts.
- 159 focused native R assertions passed (43 selection and 116 IHC), with no testthat
  failures, warnings or skips. The full R suite was not rerun for this template-only change.
- Six DOM harnesses passed: existing linked views, trees, selection, rectangle preview,
  matrix keyboard navigation and the new scatter navigation harness. The latter includes
  one/200-point bounds, ties, missing pairs, selector focus, redraw and explicit Apply.
- Compiler build passed as `ClinicoPathPj_0.3.19.jmo`; 16 extracted-package runtime cases
  passed, including packaged source/template/registry identity checks. The report is
  `validation-exports/python-ihc-scatter-keyboard-0.3.19-package.json`.
- Generator/status freshness and whitespace checks passed.

No native GUI 0.3.19 acceptance is claimed. Reassessment of earlier-session native evidence
is documented in the main plan; none substitutes for this build's pending desktop check.
