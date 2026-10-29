# Outcome organizer — Python status-coding core

`pyoutcomeorganizer` is a partial port in **Survival Py → Data preparation → Outcome
organizer (core)**. It prepares status codes only. It does not estimate survival,
cumulative incidence or state transitions, and it does not establish the number of
unique patients.

## Supported rules

| Route | Code 0 | Code 1 | Code 2 | Code 3 |
|---|---|---|---|---|
| Selected event | Every other observed level | Explicit selected event | — | — |
| Numeric 0/1, no selection | 0 | 1 | — | — |
| Four-category overall survival | Alive with/without disease | Both death categories | — | — |
| Four-category cause-specific | Alive categories and other-cause death | Disease death | — | — |
| Four-category competing risks | Alive categories | Disease death | Other-cause death | — |
| Multistate status snapshot | Alive without disease | Alive with disease | Disease death | Other-cause death |

The default analysis type is `os`, with multiple event levels disabled, matching the
baseline. An arbitrary selected event is described as a selected-event endpoint;
labels alone do not establish overall survival. Cause-specific, competing and
multistate choices in this core require **Multiple event levels** and an explicit
mapping. Unsupported single-level combinations are rejected rather than implying
that a cause of death was inferred.

Factor event selections start empty. Numeric data without a selection must be genuine
0/1, including all-zero or all-one cohorts. Explicit numeric event values are honored;
for other numeric codes, set the measure type to Nominal to select a level in jamovi.
A declared but unused factor event level is valid, with a prominent zero-event warning.
All other observed factor levels become code 0 on the selected-event route, which may
include competing terminal events; review the audit mapping before downstream use.

Every observed level in four-category mode must be assigned exactly once. An absent
category may remain unselected. Unused declared levels remain in the mapping with a
zero count, and an unassigned unused level has no fabricated status code. Missing
outcomes remain missing and do not enter coded-row percentages. Genuine factor missing
levels are normalized; literal `NA` and `Unknown` labels remain data values.

A factor with exactly the three declared levels `Censored`, `Event`, `Competing`
is treated as a competing-risk interchange even when one category is unused. Selecting
`Competing` refocuses it to code 1 and moves `Event` to code 2. `Censored` cannot be
selected as the event. Ordinary `Event`/`No event` factors are not captured by this rule.

## Outputs and controls

Native tables show input/coded/missing rows, the original-to-status mapping, all produced
status categories (including zero counts) and an optional preview of the first 100
source row IDs. The full counts and saved status use every supplied row, up to the
explicit 10,000-row and 20-declared-level bounds; no statistical sampling is performed.
The optional native bar plot displays those full counts. No interactive view is added
because this stage is an auditable deterministic recode rather than a model explorer.

The saved output is nominal: binary codes have labels `0` and `1`, multistate snapshot
codes have labels `0` through `3`, and competing-risk outputs carry the interchange
labels `Censored`, `Event`, `Competing`. The native mapping and status-code table state
the numeric meanings. Original row IDs/order and missing rows are preserved. Output
clears on incomplete selections and Python-reported invalid inputs. Pre-launch/transport
faults still use the existing jamovi error path and are a separate lifecycle boundary.
Factor numeric storage codes are not endpoint
codes: downstream analyses must use the labels and explicit event definition.

All transformations and counts run in bundled Python, with no new dependency. The
existing R bridge presents native tables/columns and renders the static count plot
from Python-produced plot data. The Python filename/registry owns generated YAML and
backend files; the module keeps its single ClinicoPathPj namespace.

## Feature boundary

| Baseline feature | This core |
|---|---|
| Explicit single-event and numeric 0/1 coding | Implemented |
| OS/cause/competing four-category mapping | Implemented |
| Competing-factor handoff/refocusing | Implemented |
| Multistate per-row status snapshot | Implemented; no transitions inferred |
| Frequencies, preview, descriptive report, static plot, saved status | Implemented |
| RFS/PFS/DFS/TTP recurrence composites | Pending |
| Repeated-patient hierarchy and priority event timing | Pending |
| Interval and administrative censoring; truncated follow-up output | Pending |
| Follow-up origins, event-time validity, survival estimation | Outside this status-only core |
| Full baseline parity, other platforms, accessibility and clinical/release review | Open |

The frozen released-source baseline remains jsurvival 1.1.1, commit
`283a8275e3dd6704f6bba2164215442d3d293b8c`. Its shared event coder is retained as an
independent R reference in `tests/reference/outcome-eventindicator.R`, with its full
SHA-256 recorded in the registry. Multistate codes additionally use an independently
constructed four-state truth table. Tests compare raw row codes and counts, not merely
formatted displays.

The PII-free example has 13 source records: 6 alive without disease, 3 alive with disease,
2 disease deaths, 1 other-cause death and 1 missing outcome. Competing-risk counts must
be **9 censored, 2 target events and 1 competing event**, with 1 missing; multistate
snapshot counts must be **6, 3, 2, 1**. Generate it using
`python3 data-raw/generate-outcome-examples.py`.

## Qualification

Numerical, compiler, packaged runtime, native lifecycle, desktop persistence/export,
platform and clinical/release evidence are separate gates. Results will be recorded
after the checks finish; implementation status alone does not imply qualification.


The new native lifecycle fixture exposed a need for an explicit status-transformation
policy: the legacy bridge retains prior native results greyed behind Python errors.
The first broad clearing attempt failed two legacy cutoff lifecycle expectations;
those failures are retained and the policy is now scoped explicitly.
The bridge now replaces previous saved values on successful answers, including
incomplete selections. The new generator-owned `clearOnInputError` boolean is enabled
for this status transformation, clearing its native payload and saved statuses before
reporting a Python input error. The default remains false, preserving the existing
greyed prior-results behavior of the older cutoff demonstrations. No statistical method or default changed.
Full native regressions are required for this shared correction. The initial failed
fixture is retained as evidence.


### Recorded evidence — 2026-10-29 / 0.3.44

- A 344-test Python suite passed. After adding the generator error-policy contract,
  46 focused outcome/generator/service-menu tests passed. The current collection has
  345 tests; the full collection was not repeated after that final policy test.
- The final compiled native package passed **71 outcome assertions** against the frozen
  R coder, independent multistate truth tables, true/literal missingness and sparse
  source IDs. Valid → invalid → valid, successful-but-incomplete and unselected-role
  transitions clear/restore saved statuses and native results.
- A further **143 native assertions** passed across the D3, Observable and SVG cutoff
  demonstrations and outlier saved-output tests. These confirm preserved legacy
  greyed-error behavior and unchanged valid scientific results.
- The earlier full native run had **3,838 passes and two errors** in the legacy D3 and
  Observable greyed-result expectations. Both affected files pass after policy scoping.
  At that milestone the full run had not been repeated against the scoped build.
  The subsequent qualification below closes this gate. Nonfatal OS-permission messages in focused logs
  are recorded separately from assertion results.
- Compiler, generator/status freshness and **24 packaged-runtime cases** pass.
  The installed R database, Python implementation and registry match the final JMO.
- macOS arm64 / jamovi 28.13: install through **Modules → Sideload**, use a fresh engine,
  load the Data Library CSV, assign roles/levels and save output. Reopening preserves
  the selected endpoint and saved status column. The final compiled backend explicitly
  passes `clearOnInputError = TRUE`; duplicate mapping clears every saved status,
  and restoring the mapping repopulates valid counts.
- Native HTML exports, standalone **1600×1000 PNG** and saved `.omv` artifacts pass
  `python3 tools/check-outcome-artifacts.py`: competing counts 9/2/1; multistate counts
  6/3/2/1; one missing outcome; every original source row and label preserved. The final
  invalid-state .omv contains 13 missing saved statuses and unchanged source data.

[Machine-readable evidence](validation-exports/python-outcome-coding-0.3.44-checks.json)
records the gates, initial failures and hashes. These checks qualify this experimental
status-only subset on the tested Mac; they do not establish clinical validity, general
accessibility, other-platform support or full baseline parity. GUI filtering and
pre-launch/transport failure recovery remain separate lifecycle limits.


### Follow-up full native qualification

The frozen 0.3.44 test inventory was subsequently rerun against the scoped 0.3.44
compiled package with process-inspection permission: **3,852 assertions passed**, with
zero failures, errors, warnings or skips. This includes the legacy greyed-result
contracts and the outcome lifecycle. The earlier 3,838-pass/two-error attempt remains
recorded. This closes the clean full-native rerun gate, while broader platforms,
clinical/release review and omitted outcome methods remain open.
