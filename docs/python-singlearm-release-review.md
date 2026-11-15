# pysinglearm 0.3.77 bounded release review

## 1. Overall verdict

Qualified for the documented experimental right-censored single-cohort subset on
macOS arm64/jamovi 28.17.0. This is not full-baseline parity, clinical approval,
whole-module library clearance or submission. Keep status partial. The metadata
retains minApp 28.3.0; compatibility below the tested jamovi 28.17.0 is unqualified.

## 2. Findings

No confirmed mathematical defect was found in the supported subset. Packaging
initially omitted unregistered curated workbooks; metadata generation now registers
all 24 and the actual archive verifies their bytes. The pending-level bridge notice
calls censor selection an event selection; visible distinct event/censor fields are
correct and prevent ambiguity in calculations, but notice wording remains a minor
usability follow-up. Additional desktop cases are explicitly unchecked in the
[executed checklist](python-singlearm-gui-checklist.md).

## 3. Changes made

Prepare 0.3.77 without changing statistical engines/defaults. Register curated data
examples, add actual-archive and saved-artifact validation tools, an independent R
example reference and native plotting reference. GUI-Sideload, verify lifecycle/
export and prior-waffle compatibility; archive verified 0.3.76.

## 4. Statistical verification

Frozen survival 3.8.12/R 4.6.0 core references cover 26 datasets/156 configurations
and 58,635 source comparisons. Actual archive checks cover core results, native
payloads and plot steps over 468 configurations. Independent GUI example references
use `survfit`, `summary.survfit` and exact `poisson.test` intervals; 9 complete
subjects/4 events/216 person-months give medians 36/48 and rate 4/216.

## 5. Data-flow audit

| Controls | Python computation | Native outputs |
|---|---|---|
| elapsedtime, outcome, subject | explicit role validation, complete pairs, retained IDs | cohort, mapping, missingness, cases |
| outcomeLevel, censorLevel | distinct labelled mapping; observed third category refused | event/censor definition, all summaries |
| timetypeoutput, cutp | declared units; sorted/deduplicated supported horizons | unit labels, selectedTimes |
| ciWidth, timefix | Greenwood log-log limits; near-tie normalization | medians, horizons, steps and drawing state |
| showFollowup, person_time | reverse KM; raw exposure/conditional Poisson rate | optional median/rate |
| showSteps, showCases, showExplanations | bounded presentation, explanations | optional tables/text |
| sc, ci95, censored | bounded saved drawing state; no renderer refit | native Image, pointwise band, distinct-time marks |
| showConsole | shared bridge diagnostics | console output |

Generator-owned UI/YAML/R bridge preserve bindings. CI/marks intentionally retain
choices while disabled by plot-off. No transformation/date origin is inferred.
Subject IDs must be unique among retained rows; that audit does not establish
independent patients. Unsupported methods are disclosed in visible scope text.

## 6. Test results

Actual final archive: 347,807 checks/1,409 configurations across survival and three
existing plotting analyses. Built and installed native survival suites each pass
1,558 assertions. The unchanged statistical source retains 757 tests; current
33 generator tests pass. Seven GUI profiles, two fresh engines, R-matched native
HTML/PNG, four rejected corruptions and prior-waffle compatibility pass. All 1,544
installed and 1,433 shipped R-library files match the archive/build. Preserve
sandbox process stderr and initial checker/environment diagnostics separately.

## 7. Remaining limitations

The unchecked desktop cases, clinical/accessibility review and other platforms
remain open. Full baseline survival methods and interaction are omitted. Figures
are static; near-equal times follow the documented unit-sensitive R convention.
Pointwise uncertainty and Poisson assumptions do not establish model validity.

## 8. Release recommendation

Use as a bounded experimental local build with its disclosed methods. Do not
claim full supported parity or clinical/library readiness. Next freeze grouped
KM/log-rank R references for `pysurvival` before implementation.
