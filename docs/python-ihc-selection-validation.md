# Applied IHC source-row selection — 0.3.15

Implemented 2026-10-27 in the existing Orange-inspired `pyihcheatmap` utility.
The feature defaults off. Julia remains a deferred backend experiment.

## Behavior

Enable **Saved source-row selection** under Save Row Selection. Heatmap, scatter and
row-tree interactions update a local preview. Individual row toggles are optional;
branches replace the preview. Only **Apply** commits the displayed source-row IDs.
Restore returns to the applied rows; Clear changes the preview, and Apply with an empty
preview clears the saved selection. Marker branches cannot be applied as source rows.

Native tables report requested, applied and unavailable rows with source-row annotations.
The optional native output control creates nominal `IHC_selection`: Selected / Not selected
for retained rows, missing for excluded rows. Disabling the feature or invalidating a saved
snapshot clears existing output flags to missing. Selection never subsets or refits the
heatmap, clustering, marker statistics or scatter results.

A SHA-256 snapshot binds selected marker columns, annotation roles and supplied raw values,
including excluded rows, to original source-row IDs. Input edits, insertions, deletions,
filtering or role changes require review and explicit reapplication. Display scaling,
clustering and scatter choices do not invalidate identity. Unrelated columns and the output
column are excluded from the snapshot. This guards supplied-view consistency; it is not a
patient identity registry. Repeated specimen labels retain distinct source-row identities.

The saved JSON definition is an advanced setting. Native selection summaries are authoritative:
after Apply, an already-open option field can lag until options are closed and the analysis
heading is reselected. Live field synchronization is not qualified.

## Automated evidence

- Full Python suite: **243 tests passed**. Backend selection checks cover sparse source IDs,
  repeated labels, incomplete rows, stale snapshots, filtered input, malformed definitions,
  disabled states and unchanged full-cohort results. Final UI-only revisions were followed
  by the current selection, linked-view and tree DOM harnesses and generator freshness check.
- Focused native R: **219 assertions passed**: 20 selection, 31 single-quality, 52 tree and
  116 IHC assertions, with zero testthat failures, warnings or skips. Selection checks inspect
  original row numbers, nominal output codes/labels, exclusions, disabled/pending clearing,
  recovery and stale-input rejection. Full-cohort marker means remain unchanged.
- Offline jsdom checks cover explicit option dispatch, no automatic writes, row toggles,
  branch replacement, restore/clear, missing native bridge, restored state and stale-state
  review/reapplication. These do not establish complete native keyboard accessibility.
- The compiler built 0.3.15. Its package passed ZIP/source/template checks and **16 packaged
  analysis smoke cases**, including an additional applied-selection rerun with expected flags
  and unchanged plots. See [package evidence](validation-exports/python-ihc-selection-0.3.15-package.json).

The focused R runs printed macOS process-cleanup `Operation not permitted` diagnostics.
The full R suite/process lifecycle was not qualified. Working logs and HTML fixtures are
under `/private/tmp/cpj-ihc-selection/`.

## Native desktop evidence

On macOS arm64 / jamovi 28.13, the exact 0.3.15 package was installed through Sideload.
The synthetic validation document supplies 12 rows, with 9 retained in complete-row mode,
three markers, repeated specimen labels, annotations, both trees and a linked scatterplot.
A row-tree branch previewed source rows 1 and 2 while the applied count stayed zero.
Explicit Apply changed the native summary to Applied / requested 2 / selected 2 /
unavailable 0 / retained 9. Enabling the native output produced `IHC_selection`.

After saving, closing and reopening in a fresh engine, the applied rows and preview were
restored. Changing z scores to raw units forced recalculation without invalidation; restoring
z scores and saving retained both rows and all nine heatmap rows. Independent saved-file
inspection verifies the nominal output metadata, labels, persisted definition, two Selected
codes, seven Not selected codes and three missing codes. ZIP integrity passes.

- [Reopenable synthetic document](validation-exports/python-ihc-selection-0.3.15-validation.omv)
- [Saved-file inspection](validation-exports/python-ihc-selection-0.3.15-saved-file.json)

Broader keyboard/theme acceptance, maximum-size GUI behavior and other platforms remain
open. This is exploratory interaction evidence, not clinical validation or release clearance.
