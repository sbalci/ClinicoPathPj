# IHC heatmap keyboard navigation — 0.3.18

Implemented 2026-10-27 in the existing Orange-inspired IHC utility. This improves bounded
matrix keyboard navigation without changing statistical methods, options, cohorts or
runtime dependencies. It is not complete accessibility certification.

## Behavior

The matrix has one remembered Tab stop, initially the first displayed cell. Focusing or
clicking another cell moves that stop. Arrow keys move one displayed row/marker at a time;
movement clamps at boundaries rather than wrapping. Home/End move to the current row's
first/last marker. Ctrl+Home/End or Command+Home/End move to the matrix endpoints.

Tab/Shift+Tab and native Enter/Space are not intercepted. Standard button activation
continues to inspect/toggle once per activation. Instructions are associated with the
matrix using `aria-describedby`. Original source/marker labels and missing-cell descriptions
remain available. Browser focus scrolls the chosen cell into view.

Existing focus behavior is preserved: ordinary focus previews one source row; individual-row
toggle mode inspects without changing selected rows until activation. Navigation never
writes native options. Apply is still required to persist a selection and update native
selection tables/flags. Clear/Restore keep the remembered stop. Rerun/reopen resets the stop
to the first displayed cell; saved applied rows remain subject to the snapshot guard.

## Automated evidence

- **50 focused Python tests passed**: existing IHC transforms/plots, saved selections,
  independent dendrogram fixtures and generator contracts.
- **159 focused native R assertions passed** (43 selection, 116 IHC), with zero testthat
  failures, warnings or skips. MacOS process cleanup still prints `Operation not permitted`;
  the full R suite/process lifecycle was not qualified in this batch.
- **Five jsdom harnesses passed**, including the new keyboard harness and the linked views,
  dendrograms, explicit Apply and rectangle-preview regressions. Keyboard checks cover all
  arrow directions, row/matrix boundaries, Ctrl/Command modifiers, missing cells, one-row
  and 4,000-cell matrices, one Tab stop, remembered clicks, toggle-mode preview preservation,
  and explicit Apply. Tab/Enter/Space/PageDown retain their default event behavior. jsdom
  does not supply native default button activation or browser Tab movement; those are
  checked separately below.
- The maximum synthetic DOM contains all 200 × 20 cells with exactly one matrix Tab stop.
  This establishes bounded DOM navigation, not maximum-size native GUI acceptance.
- The compiler built 0.3.18. ZIP/source/template checks and **16 packaged analysis smoke
  cases** passed, including an applied-selection rerun and unchanged native plots/flags.
  Generator freshness and hand-source whitespace checks pass. Logs and synthetic HTML
  are under `/private/tmp/cpj-ihc-keyboard/`.

## Native desktop evidence

On macOS arm64 / jamovi 28.13, the exact 0.3.18 package was installed through Sideload.
A separate synthetic validation copy retained raw display, complete rows, clustering on
both axes, the scatter, native selection flag and selected-marker table. Nine of twelve
rows and three markers remained in the heatmap. The initial applied rows were 4 and 9.

In individual-row toggle mode, native Space removed a clicked row from the preview.
Right moved from row 6/Ki67 to row 6/ER; Down moved to row 8/ER. End/Home moved to row 8's
last/first marker. Ctrl and Command endpoint shortcuts moved to row 9/PR and row 6/Ki67.
The applied and preview rows remained unchanged throughout navigation.

Tab left the matrix for the local X-marker control; Shift+Tab returned to the remembered
row 6/ER cell. Shift+Tab from that cell reached Restore; Tab returned to row 6/ER. Enter
added row 6 once, Space removed it once, and Enter added it again. Two Shift+Tab presses
reached **Apply 3 source rows**; Enter committed rows 6, 4 and 9. The selected-marker table
contained nine records and the heatmap still retained all nine usable rows.

The new document was saved and reopened in a fresh engine. Applied rows persisted while
keyboard position reset to the first cell. Independent saved-file inspection verifies
persisted source IDs, nine raw/displayed marker records, nominal flag alignment and
unchanged full-cohort means. The current keyboard instructions are present in saved HTML.

- [Reopenable synthetic document](validation-exports/python-ihc-keyboard-0.3.18-validation.omv)
- [Independent saved-file inspection](validation-exports/python-ihc-keyboard-0.3.18-saved-file.json)
- [Packaged runtime checks](validation-exports/python-ihc-keyboard-0.3.18-package.json)

Screen-reader acceptance, themes, touch, scatter/tree keyboard traversal, maximum-size GUI,
other platforms and separate export acceptance remain open. The known post-Apply live
native option-field refresh limitation remains; native applied summaries are authoritative.
This is exploratory software qualification, not clinical validation or release clearance.
Julia remains deferred.
