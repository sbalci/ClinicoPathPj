# Composite and progression-only status — 0.3.49

The existing **Survival Py → Data preparation → Outcome organizer (core)** gains
four explicit status choices. The original OS/cause/competing/multistate routes,
defaults, saved output name and option order are retained. New recurrence options
are appended; their controls appear with the other data roles.

| Choice | Status rule |
|---|---|
| RFS/PFS/DFS status | Explicit selected outcome event OR selected recurrence/progression event |
| TTP status | Selected progression indicator alone; outcome values/event level are unused |

These labels identify an intended endpoint, not a complete survival analysis.
Choose the appropriate death/event level yourself; other observed levels in that
component are coded 0. Recurrence/progression requires a nominal/ordinal variable
and an explicit event level. Four-state multievent composites are rejected. Labelled Censored/Event/Competing
interchange cannot be an active binary component; first prepare the appropriate
binary indicator rather than silently collapsing competing events. TTP does not
interpret its unused outcome variable.

For OR status, a known event determines 1 even if the other component is unknown.
Both components must be known and coded 0 to produce 0. Otherwise final status is
missing. Component source counts and unknown counts are displayed separately from
final frequencies, whose denominator is known final status. Unknown status is never
automatically censoring. All-unknown final status has unavailable percentages.

TTP ignores the outcome event level and values, including all-missing outcome;
the outcome variable is retained only for supplied-row alignment in this interface.
Its outcome-component audit count is unavailable, indicating that component was not
used. Progression unknown remains unknown. Output codes are labelled 0/1, with the
existing name **Recoded survival outcome**; descriptions state the rule and that no
first-event time was calculated.

No recurrence/progression date is available. Pair composite status with time to
FIRST component event and TTP status with appropriate progression/censoring time.
Death or last-contact time alone is not automatically first-event/progression time.
These transformations do not establish independent censoring, deduplicate patients,
construct event histories or estimate survival/cumulative incidence.

The frozen reference is jsurvival commit
`283a8275e3dd6704f6bba2164215442d3d293b8c`, with the R component formula in
`tests/reference/outcome-composite-status.R`. Its known-event-over-unknown behavior
is checked against an independently enumerated nine-pair truth table. TTP bypasses
unused outcome validation, matching the current R route; its status formula is the
same as the frozen baseline on supported input. Original baseline hashes remain
in the registry; this is a partial feature port.

The **Composite Outcome Status Examples** dataset enumerates all nine combinations
of 0, 1 and unknown for both components. With Outcome event Death and Progression
event Yes, RFS/PFS/DFS gives five events, one code-0 and three unknowns. TTP gives
three events, three code-0 and three unknowns. No real patients or event times are
included.

## Qualification

- **48 focused Python checks** pass, including outcome regressions and generator contracts.
- **376 full Python tests** pass in 674.421 seconds.
- **116 focused native R assertions** pass: 45 composite and 71 existing outcome
  checks, with zero failures/errors/warnings/skips. The initial all-missing fixture
  used logical NA instead of numeric NA; correcting that test type required no
  backend change. Sandbox subprocess `Operation not permitted` diagnostics are
  separate from assertion results.
- Compiler, generator/status freshness and **26 packaged-runtime cases** pass,
  including an additional composite saved-row request. One early package check
  started before the archive existed; the completed archive then passed.
- macOS arm64 jamovi 28.13: Sideload/full restart and installed manifest/R database/
  registry/outcome-engine archive-byte comparisons pass. RFS and TTP show the
  expected native counts/audits; the TTP outcome event selector is disabled.
- Incomplete recurrence level clears all saved statuses; restoring it recovers.
  The TTP file reopens after a full restart. Switching to RFS forces recalculation
  of the tables, saved status and plot, restoring five events and one code-0.
- Native HTML exports preserve the tables and embedded plots. Standalone 1277×798
  PNGs were extracted byte-for-byte from these exports and visually inspected:
  TTP bars are 3/3; RFS bars are 1/5. These are HTML/embedded-plot export checks,
  not a separate direct Save Image dialog test.
- `tools/check-composite-artifacts.py` independently checks all four OMV source/
  saved-status states, both native HTML exports, denominators, component audit,
  nine preview rows and embedded PNG bytes without importing the outcome engine.

First-event time construction, patient hierarchy, interval/administrative censoring,
full parity, additional platforms, accessibility certification and clinical review
remain outside this extension's claims.

Result/column visibility now permits a bounded OR (at most 16 terms) of declared
List choices, for example `(analysistype:rfs || analysistype:ttp)`. Unknown options,
unknown choices and executable syntax are rejected. Existing Bool visibility rules
remain unchanged; this does not enable arbitrary expressions.

Reproduce with the bundled-Python discovery command in `tools/check.sh`, focused
`test-composite-outcomes-python.R` / `test-outcomes-python.R` against the built
library, `tools/check-core-package.py`, `tools/check-composite-artifacts.py`,
`tools/generate.py --check` and `tools/migration-status.py --check`. Evidence and
hashes are in `docs/validation-exports/python-composite-0.3.49-checks.json`.
