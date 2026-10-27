# IHC scatter rectangle preview — 0.3.17

Implemented 2026-10-27 in the existing Orange-inspired IHC utility. No new baseline port,
statistical method, runtime dependency or native analysis option is introduced. The new
controls live inside the local linked scatter inspector.

## Behavior

Expand **Rectangle row preview** below the local X/Y marker controls. Numeric bounds use
inclusive comparisons on displayed raw/z values. Activate **Preview rectangle rows** or
press Enter in a bounds field. Alternatively enable **Drag a rectangle to preview rows**
(default off) and drag inside the plot. Reversed drags are normalized; pointer positions
are transformed through the SVG screen matrix and clamped to the plot. Pointer capture
retains the gesture outside the plot; without capture, leaving cancels it. Escape, pointer
cancellation and capture loss abandon an unfinished drag without changing the prior rows.
A tiny drag leaves the preview unchanged; exact point ranges remain possible numerically.

Rectangles replace the row preview, regardless of individual-row toggle mode. Each complete
pair contributes its original source identity, including coincident points. Missing pairs
are omitted rather than imputed. A valid empty rectangle clears the preview; invalid or
nonfinite/reversed numeric bounds leave it unchanged with an explanatory status message.
Constant axes retain the existing padded plotting extent.

Point clicks are suppressed while drag mode is enabled; keyboard point inspection and
numeric bounds remain available. Cell/branch inspection, Clear and Restore remove the
rectangle. Local marker changes reset rectangle bounds and geometry while retaining selected
source identities. Rectangle controls, bounds and geometry are transient and reset on rerun
or reopening. Only the existing explicit Apply action persists row IDs via the snapshot-bound
selection definition. Native tables, optional output flags and the selected-marker table
update after recalculation; all statistical results still use the full retained cohort.

## Automated evidence

- **50 focused Python tests passed**: IHC transforms/plots, saved selections, independent
  tree fixtures and generator contracts. This includes existing maximum 200 × 20 payload
  checks. The first run overlapped vendored-library regeneration and failed importing `six`;
  the completed build was followed by a clean successful rerun. No dependency was added.
- **242 focused native R assertions passed**, with zero testthat failures, warnings or skips:
  43 selection, 31 single-quality, 52 tree and 116 IHC. The calculations and native selection
  contract are unchanged. macOS process cleanup still prints `Operation not permitted`;
  the full R suite/process lifecycle is not qualified.
- **Four jsdom harnesses pass**: new rectangle tests plus existing linked cell/scatter,
  dendrogram and explicit Apply regressions. Rectangle checks cover inclusive bounds,
  individual tied identities, missing/empty pairs, constant axes, raw/z coordinates,
  scaled SVG/client coordinates, screen-matrix transformation, reverse/outside drags,
  capture/cancel/Escape/leave fallbacks, foreign pointers, invalid bounds, Enter, clear/
  restore/branch interactions and explicit Apply. No native option is dispatched during
  numeric or pointer preview, marker changes, cancellation or restoration.
- The compiler built 0.3.17. ZIP/source/template checks and **16 packaged analysis smoke
  cases** pass, including the applied-selection rerun and unchanged native plots/flags.
  Generator freshness and hand-source whitespace checks pass.

Focused logs and synthetic HTML are under `/private/tmp/cpj-ihc-brush/`. These checks do
not establish full browser accessibility or maximum-size GUI behavior.

## Native desktop evidence

On macOS arm64 / jamovi 28.13, the exact 0.3.17 development package was installed through
Sideload. A new synthetic document retained the earlier annotations, clustering, linked
scatter, optional output flag and selected-marker table. Complete-row mode retained nine
of twelve supplied rows, with three markers. Raw display mode was used for the interaction.

Numeric bounds X 40–80 and Y 0–5 previewed rows 6, 8, 5 and 7 in heatmap order while the
applied selection remained rows 1 and 2. A pointer drag around the midrange points then
previewed rows 4 and 9. Explicit Apply changed the native selected-source table to S03/row 4
and S07/row 9, with six corresponding marker measurements. The full heatmap still retained
nine rows. Saving, closing and reopening in a fresh engine restored applied rows 4 and 9.
Drag mode reset off, the rectangle disclosure reset closed and default bounds returned to
X 8–75 / Y 0–80. A fresh-engine disable/re-enable of the selected-marker table also reran
Python without invalidating the applied identities.

Independent ZIP/protobuf inspection checks persisted row IDs, selection flags, selected raw
marker records and unchanged full-cohort marker means against the saved synthetic inputs.
The saved document contains native results and the current rectangle-enabled HTML template.

- [Reopenable synthetic document](validation-exports/python-ihc-brush-0.3.17-validation.omv)
- [Saved-file inspection](validation-exports/python-ihc-brush-0.3.17-saved-file.json)
- [Packaged runtime checks](validation-exports/python-ihc-brush-0.3.17-package.json)

Broader native keyboard/theme/touch/maximum-size/other-platform checks and separate export
acceptance remain open. The known live native option-field refresh limitation remains;
applied native summaries are authoritative. This is exploratory interaction qualification,
not clinical validation or release clearance. Julia remains deferred.
