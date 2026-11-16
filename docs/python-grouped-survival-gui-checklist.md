# Grouped survival — executed 0.3.78 package and desktop protocol

Executed 2026-11-16 on **macOS arm64 / jamovi 28.17.0**. This is bounded synthetic
qualification of the partial core, not full survival-method or clinical readiness.
See the [package record](python-grouped-survival-package-validation.md) and
[numerical/source contract](python-grouped-survival-core.md). Unexecuted extensions
are listed explicitly below; source tests do not replace desktop acceptance.

## Package gate — passed

- [x] Build standard `ClinicoPathPj_0.3.78.jmo` under the single module identity.
- [x] Validate CRC, safe/unique paths, version, one normal menu entry, exact runtime
      sources/registry/UI and synthetic CSV/curated-example contents; prune bytecode.
- [x] Execute extracted archive runtime: 320,926 grouped checks/540 configurations,
      plus single-cohort and waffle regressions; 638,569 checks/1,428 configurations.
- [x] Built and GUI-installed libraries each pass 2,055 native R assertions across
      60 references, lifecycle and restored-state PNG export. All 1,551 installed /
      1,438 shipped R-library files match the archive/build.

One initial built-native run timed out while build/render jobs overlapped; its
108 passing assertions and one error are retained. The isolated complete rerun
passed with the existing 60-second limit unchanged. Recurring environment stderr
is recorded separately from assertion failures/warnings.

## GUI setup and native outputs — passed

- [x] Install using **Modules → Manage installed → Sideload**. No Finder installation
      or global CLI install. Quit/relaunch before the grouped test; observed fresh
      session endpoint 56921, replacing prior 65134. Installed metadata is 0.3.78.
- [x] Open Data Library → ClinicoPathPj → Grouped Survival Examples; twelve source
      rows and exact Subject/Months/Status/Group fields. One grouped analysis in
      Survival Py → Survival estimates → Grouped survival (core).
- [x] Explicit Months, Status, Group, optional Subject, Event and Censored roles;
      declared months, 12/36/60 horizons, 95% limits and global near-tie normalization.
      Default plot/CI/censor toggles off. Native dropdown values were verified after
      keyboard selection; unsuccessful automation clicks were not counted as success.
- [x] Nine complete subjects, three excluded, three active groups, four events and
      five censored; one missing value per required role. IDs S01–S09 retained.
      B: n=3/events=3/max=18; A: n=3/events=0/max=24; C: n=3/events=1/max=60.
- [x] Independent R reference validates native medians/horizons and log-rank
      chi-square 8.117197847435179, df 2, p 0.01727320324487263. Only C contributes
      at 36/60 months; A/B unsupported horizons are omitted, including B's zero curve.
- [x] Enable native steps/rows/explanations, covariance and pooled-risk audits,
      static plot, log limits and distinct-time censor marks. Visually inspect plot
      group sizes, labelled units, support limits and legend. No interactive SVG claim.

## Saved profiles and exports — passed

- [x] Save `default`, `plotted`, `off`, `incomplete`, `invalid`, `recovered` and
      `reopened` profiles under local ignored validation exports. Turning optional
      outputs off removes those tables/text/images; explicit event removal clears
      previous results; malformed horizons `1,,2` produce a validation error and
      cleared results. Restoring valid values recovers the original tables/image.
- [x] Fully quit/relaunch into a second fresh session (endpoint 57317), reopen the
      recovered workbook, inspect cached results, toggle exact/default tie handling
      to force backend runs and save the reopened profile.
- [x] Export native HTML and PNG. Check all seven profiles against installed R
      `survdiff`/`survfit` and independently counted rows/risks, not analysis status
      alone. Source data/metadata remain unchanged; plotted/recovered/reopened native
      tables and cached pixels are identical. HTML native tables/images agree.
- [x] Match direct PNG at 1400×1000 and cached PNG at 1118×798 with independent
      native R rendering at the same dimensions. Reject four corruptions: cohort,
      log-rank statistic, subject ID and missing image.
- [x] Open prior `python-singlearm-0.3.77-reopened.omv` in the second fresh session,
      force exact/default tie reruns and Save As a separate 0.3.78 compatibility
      copy. Original source data/metadata, native tables and cached PNG remain
      unchanged; the original file is preserved.

## Evidence and open extensions

Checker: `tools/check-grouped-survival-artifacts.py`; independent reference:
`tests/reference/grouped-survival-example.R`; native rendering:
`tools/render-grouped-survival-example.R`. Final report:
`/private/tmp/cpj-grouped-gui-artifacts-final-0.3.78-20261116.json`.
Validation file prefix: `docs/validation-exports/python-grouped-survival-0.3.78-`.
Reports distinguish numerical, compiler, native lifecycle, GUI, compatibility and
platform evidence. No commit, push or library submission is part of this test.

- [x] Curate one configured grouped `.omv` under `data/` and register its manifest
      in 0.3.79 source, preserving original 0.3.78 bytes/provenance.
- [ ] Include that source example in the next package and verify its saved Data
      Library entry. Validation profiles remain ignored; installed 0.3.78 includes
      the synthetic CSV.
- [ ] Extend desktop tests to every required selector/variable removal, duplicate
      IDs, negative times, third outcomes, one-group/all-censored/singular cases,
      labels at bounds and 5,001-step plot omission. These have source/native
      coverage; this GUI run claims only the specific lifecycle paths above.
- [ ] Broader accessibility/clinical review, other jamovi versions/platforms,
      stochastic/model inference, weighted/pairwise methods, Word/LaTeX exports and
      full baseline parity remain separate gates.

Superseded local JMO files are removed at the user's request after replacement
qualification. Historical hashes remain in the records; saved examples are retained.
