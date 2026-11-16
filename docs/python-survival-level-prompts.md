# Explicit event and censoring prompts — 0.3.79 source increment

This source increment corrects a shared informational prompt and registers one
curated saved grouped-survival workbook. Installed **0.3.78** and its qualified
JMO remain unchanged. No statistical engine, public option/default, result schema,
UI layout, inferential method or analysis identifier is changed.

## Confirmed defect and repair

Both survival specifications marked their censor selector `role: event`, so after
choosing Event the missing Censored selector incorrectly prompted:

> Choose which level of Status is the event: Censored (3 rows), Event (3 rows).

The generator now supports `role: censor` for a required explicit Level choice.
It keeps the existing ordered level gate, blank initial choice and missing-input
clearing. It adds a named `censors` argument only to the two affected generated R
backends. The shared bridge uses that metadata for the notice and console reason:

> Choose which level of Status indicates censoring: Censored (3 rows), Event (3 rows).

Event, positive and abnormal level prompts retain their exact wording. Event-only
callers omit the new argument and use its empty default. The added argument is
last in the bridge signature to preserve existing positional arguments. Optional
levels cannot opt into either required-choice gate. Roles remain generator-only
metadata and are stripped from emitted jamovi options.

`pysinglearm` and `pysurvival` retain byte-equivalent generated option/result/UI
contracts when switching the private censor role back to event. Generation changes
only their backend calls. The public identifiers remain stable and all utility
and demonstration analyses are retained.

## Native and generator evidence

Against the installed pre-repair 0.3.78 module, the new native regression produced
**82 passing assertions and six failures**, all the incorrect censoring notice or
console wording; zero errors/warnings/skips. No numerical failure was observed.
With the repaired source in an isolated library, all 88 survival assertions pass.
Adding an event-only `pyexacttests` compatibility case brings the final focused
native gate to **92 assertions**, all passing, with zero failures/errors/warnings/
skips. It covers both initially unset levels, event-first priority, each missing
level after a valid run, no duplicate notices, clearing all optional native tables/
text/plot, recovery, reused/fresh result equality and original event-only wording.

All **34 generator tests** pass, including censor blank selection, optional-role
rejection, unchanged public contracts and unchanged event-only generation. An
initial new test tried to render an incomplete probe without an explicit UI; that
test-setup error was corrected by comparing the actual survival SPECs. It did not
require changing generator behavior.

Backups and red/green/generator/install logs are under
`/private/tmp/cpj-censor-prompts-20261116/`. Recurring subprocess `Operation not
permitted` stderr remains visible separately from assertion results. Numerical
source/native suites and final freshness checks are recorded at the final
checkpoint below; this source test is not a GUI prompt qualification.

## Curated grouped workbook

`data/python_grouped_survival_examples.omv` is an unmodified byte copy of the
GUI-verified 0.3.78 cold-reopened validation workbook. SHA-256:
`4135759f6a1f597c2f586c971ce857fda201d6d6873cb8eea93b5f8766ee8684`.
It contains one `pysurvival` analysis, twelve synthetic rows, nine complete
subjects, three groups, explicit Event/Censored choices, native tables and a
static KM image. The independently checked native R tables and cached image are
unchanged; the cached pixel SHA-256 remains
`c270ac102d7bf2bf23a737e251e7a74d7b6db5b9373f7c0f58504793b38c847f`.

The saved-example TSV records the original saved module version **0.3.78**, source
snapshot basename, identifiers and full hash. Metadata generation registers one
Saved Analysis: Grouped Survival entry for the next package. The existing CSV
remains available. All **25 curated workbooks / 30 declared analyses** pass ZIP,
manifest checksum and analysis-entry checks through
`tools/check-saved-analysis-examples.py`. These integrity checks are separate from
the grouped workbook's independent R and prior GUI evidence.

Only one reusable grouped workbook is added under `data/`. Incomplete/error/
recovery/export profiles remain local ignored validation outputs. No saved options,
data, cached results or archive internals were rewritten. The original 24 curated
workbooks and existing demonstration/template datasets are preserved.

## Next package gate

Source metadata is 0.3.79 to avoid overwriting the qualified 0.3.78 package.
Packaging, Sideload and fresh-engine GUI verification of the new pending-censor
wording and new saved Data Library entry remain pending. Reopen/recalculate/export
the configured workbook and compare data/native tables/cached pixels, plus event-
only and valid/incomplete/recovery regressions. Keep only the latest qualified
local JMO after replacement acceptance. Full survival methods, older jamovi support,
clinical/accessibility review and other platforms remain separate gates.

## Final source checkpoint

The final full Python suite passes **773 tests in 367.293 seconds**, without
failures, errors or skips. The isolated **0.3.79** R library passes **3,705 native
assertions**: 92 prompt/lifecycle/event-only checks, 1,558 independent single-cohort
checks and 2,055 independent grouped checks. Every suite reports zero failures,
errors, warnings or skips. Existing valid numerical/native results and restored-
state PNG export remain unchanged. Compiler preparation, 34 generator tests,
generator/status freshness and diff checks pass.

Final native logs: `green-final.log`, `singlearm-native.log` and
`grouped-native.log` under `/private/tmp/cpj-censor-prompts-20261116/`. Full Python
log: `full-python.log`; compiler: `prepare.log`; final isolated install:
`install-final.log`; curated integrity report: `curated-examples.json`.
The first six failing wording assertions and the generator test-setup error remain
separate from final passing evidence. Backups of the edited source files are in
that same scratch directory. Nothing was staged, committed or pushed.

Installed metadata remains 0.3.78, and its only local JMO retains SHA-256
`b41371e13128c037512614a3c582285e23239ba4135c264ca6b4e4f85984c440`.
There is **no 0.3.79 JMO or new GUI claim yet**. Next build/inspect/execute it and
verify the new prompt and saved Data Library entry through GUI Sideload and a
fresh engine. This is source qualification, not library submission or clinical
validation.
