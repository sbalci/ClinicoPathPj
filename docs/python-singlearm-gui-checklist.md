# Single-cohort survival package and desktop gate

Source integration is partial and qualified separately in
[the core contract](python-kaplan-meier-core.md). Installed 0.3.76 has not been
replaced. None of the checkboxes below is a completed desktop claim.

- [ ] Choose the next version, build the standard `ClinicoPathPj_<version>.jmo`,
  inspect archive contents and run the actual packaged runtime against the frozen
  references. Check metadata, synthetic data, Python helpers and native renderer.
- [ ] Install through jamovi **Modules → Manage installed → Sideload**. Restart
  jamovi for a fresh engine. Opening the archive in Finder is not an install test.
- [ ] Open **Data Library → ClinicoPathPj → Single-Cohort Survival Examples**.
  Under **Survival Py → Survival estimates**, add the single-cohort core.
- [ ] Select Months, Status and optional Subject. Before explicit event/censor
  choices, confirm clean pending results. Choose Event and Censored respectively.
  Verify 11 source rows, 9 complete pairs, 4 events and 5 censored; declared months
  and supplied elapsed-time origin remain visible.
- [ ] Check event/reverse-KM medians 36/48 months. At 12/36/60 months verify risk
  7/3/1, survival 16/21, 128/315, 128/315, interval events 2/2/0 and interval censors
  2/1/2. Enable person-time: exposure 216 and rate 4/216 per person-month.
- [ ] Defaults keep plot, CI band, censor marks and person-time off. Enable each
  and verify the native step chart, bands, distinct-time censor marks and table
  alignment. Changing declared units changes labels only, not time values.
- [ ] Test valid → incomplete → valid and valid → invalid → valid: unselect each
  required role/level, select identical event/censor levels, enter `1,,2`, a
  negative time, duplicate retained subject ID and an observed third outcome.
  Clear old tables/text/images on failure, then recover to fresh-analysis results.
- [ ] Toggle optional outputs off/on; check no stale person-time, steps, cases,
  explanations or plot state. Verify all-censored, all-event and zero-time cohorts.
- [ ] Save, fully restart, reopen and force recalculation of `.omv` profiles for
  default, plotted, optional-off, incomplete and recovered states. Compare source
  rows, options, native tables and cached images; preserve original saved fixtures.
- [ ] Export native HTML and PNG before/after reopen and inspect curve geometry,
  confidence intervals, origin, axis unit labels and table values. Cached rendering
  and direct export are separate checks; compare at matching pixel dimensions.
- [ ] Verify installed files against the built archive and archive the superseded
  package only after compatibility passes. Record compiler, numerical, desktop,
  compatibility and platform evidence separately; retain initial failures.

Keep exported images/logs/reports outside tracked source. No claim about dates,
landmarking, delayed entry, competing risks, RMST, weights, regression or full
baseline parity follows from this checklist.
