# Single-cohort survival package and desktop gate

Executed bounded qualification: **ClinicoPathPj 0.3.77**, macOS arm64,
jamovi 28.17.0, 2026-11-16. This is partial-method experimental qualification;
clinical, broader accessibility and other-platform approval remain open.
Numerical scope is in [the core contract](python-kaplan-meier-core.md).

- [x] Build standard `ClinicoPathPj_0.3.77.jmo`, inspect CRC/paths/runtime/UI/data,
  and execute the actual archive: 101,443 survival checks/468 configurations plus
  246,364 waffle/lollipop/pie checks/941 configurations. All 24 curated saved
  workbooks are generator-registered and bundled byte-for-byte.
- [x] Install through **Modules → Manage installed → Sideload**, then fully quit
  and restart. Two fresh engines (64812 and 65134) were used. Finder was not used
  to install. All 1,544 installed files match the archive, and 1,433 shipped
  R-library files match the tested build. Built/installed native suites each pass
  1,558 assertions. Verified 0.3.76 is archived.
- [x] Open **Data Library → ClinicoPathPj → Single-Cohort Survival Examples**.
  Add **Survival Py → Survival estimates → Single-cohort survival (core)**.
  Select Months, Status and Subject. Missing event/censor selections produce
  clean pending results. Explicitly choose Event and Censored.
- [x] Verify 11 source rows, 9 complete pairs, 4 events, 5 censored and visible
  declared months/supplied elapsed-time origin. Event/reverse-KM medians are
  36/48 months. At 12/36/60, risks are 7/3/1, survival is 16/21, 128/315, 128/315,
  interval event counts are 2/2/0 and censor counts 2/1/2. Person-time is 216,
  rate 4/216 per person-month. Saved native tables match independent R at display
  precision, including limits, missingness, source rows and effective times.
- [x] Confirm plot, CI band, censor marks and person-time are off by default.
  Enable detailed tables, explanation, plot/band/marks and visually inspect.
  Toggle optional outputs off/on, including reverse follow-up; confirm clearing,
  single-median output and retained-but-disabled CI/mark choices when plot is off.
- [x] Test valid → missing event → valid and valid → malformed `1,,2` → valid.
  Save incomplete/invalid profiles and confirm no stale computed tables, narrative
  or cached plot. Preserve source data and recover original results.
- [x] Save seven profiles: default, plotted, off, incomplete, invalid, recovered,
  reopened. Fully quit/restart, reopen recovered, verify restored roles/levels/
  options/cached results, force backend rerun and save reopened separately.
  Equivalent-input native tables and cached PNG bytes agree; dataset/metadata
  bytes are unchanged across all seven profiles.
- [x] Export native HTML and PNG after reopen/rerun. HTML tables agree after
  normalizing only numeric percentage spacing; cached/HTML/native R pixels agree
  at 1038×718. Direct 1300×900 PNG is byte-identical to native R. Four artifact
  corruptions (cohort, exposure, median and image removal) are rejected.
- [x] Open **Saved Analysis: Waffle** (saved 0.3.76) through the new Data Library,
  force rerun, restore original settings and save a separate compatibility file.
  Original data, native tables and cached PNG bytes remain unchanged.

Additional desktop coverage remains open (these cases have native R/Python
coverage but were not all repeated through the GUI in this bounded pass):

- [ ] Unselect each other role/level; test identical event/censor levels, negative
  time, duplicate retained ID and an observed third outcome in the GUI.
- [ ] Change declared units in the GUI; confirm labels only change. Exercise
  all-censored, all-event and all-zero-time GUI cohorts.
- [ ] Individually reopen default/off/incomplete/invalid profiles across fresh
  engines and export before/after each. Only recovered → reopened was tested
  across a full application restart here.
- [ ] Broader keyboard/theme/accessibility, long-job cancellation and other
  platforms. Dates, landmarking, delayed entry, competing risks, RMST, weights,
  regression, hazards and full baseline parity remain separate method gates.

Generated `.omv`, PNG, JSON and log evidence stays ignored; the HTML export
remains a local untracked artifact. Initial missing Data Library
registration and checker-only percentage whitespace/PNG encoding/image-tag probe
failures are retained separately. The generic pending-level message still calls
both selectors an event selector; visible field labels and distinct-level checks
prevent guessing, but wording refinement is a usability follow-up.
