# Two ways to run the same Python analysis

Pj's public service API lets an installed host module submit Python code and data,
without opening a Pj editor. The host keeps its R6 backend, options, UI and native
results. Pj handles interpreter discovery, subprocess execution and its bundled
helpers. It executes Python supplied by the host; it does not translate R analyses.

References: [tagged Pj 1.5.0 API guide](https://github.com/MAgojam/Pj/blob/v1.5.0/docs/mzPj_service_api.md),
[host connector](https://github.com/MAgojam/Pj/blob/v1.5.0/docs/examples/mzPj_connect.R),
[complete example backend](https://github.com/MAgojam/Pj/blob/v1.5.0/docs/examples/serviceDemo.b.R).

## Try the matched examples

Build/install ClinicoPathPj 0.3.62 through jamovi's Modules → Sideload menu.
Install Pj 1.5.0 separately for the Pj example. Under Data Library → ClinicoPathPj,
open **Python Execution Service Examples**. Add these from **Python Lab → Execution services**
and select **Measurement** in each:

| Analysis | Stable identifier | Python execution |
|---|---|---|
| Own Python Summary Example | `pyservicedirect` | ClinicoPathPj's own processx bridge |
| Pj Service Summary Example | `pyservicepj` | Public Pj service; jamovi bundled Python |

Both use [one calculation](../inst/python/cpj_service_examples.py), based on Python's
standard library. Expected table: input rows 6, N 5, missing 1, mean 4,
sample SD 3.535533905932738, median 3, minimum 1, maximum 10.
Missing cells are excluded explicitly. Empty/all-missing input produces counts and
blank summaries; a singleton has a blank sample SD. Infinite values and nonnumeric
input are rejected. The teaching examples allow at most 100,000 rows.

These descriptive summaries make no inferential independence assumption. They
include no tests, clinical classifications or plots. The existing **Python Bridge
Comparison** remains available for matched diagnostic tables and graphical experiments.

## What changes in the backend?

The generator reads a literal fixed execution route from each Python SPEC:

```python
# pyservicedirect.py
'executionBackend': 'processx'
# pyservicepj.py
'executionBackend': 'pj'
```

It generates the following calls in the host R6 `.run()` method (abbreviated):

```r
# Host launches its own interpreter and passes a JSON request.
.cpjRun(self, "pyservicedirect", backend = "processx", ...)
# Host calls the installed Pj public service, using the same result contract.
.cpjRun(self, "pyservicepj", backend = "pj", ...)
```

See [direct backend](../R/pyservicedirect.b.R), [Pj backend](../R/pyservicepj.b.R),
[own executor and native mapping](../R/utils-python.R), and
[Pj service adapter](../R/utils-pj-service.R). Generated backends should be regenerated,
not edited. The Pj adapter passes code importing the host's installed Python runtime,
then validates its named, versioned envelope before updating native results.

## Minimal public API call for another module

A host can use Pj's helpers directly instead of our envelope. After discovering and
loading Pj through the official `mzPjConnect()` connector, this is the essential call
inside an R6 backend with a declared native `summary` table containing `n` and `mean`:

```r
service <- mzPjConnect()  # Copy/adapt the official connector linked above.
response <- service$run(
    code = paste(
        'import statistics',
        'x = [v for v in data["x"] if v is not None]',
        'mzpjShowTable([{"N": len(x), "Mean": statistics.mean(x) if x else None}],',
        '              columns=["N", "Mean"], name="summary")', sep = "\n"),
    data = data.frame(x = jmvcore::toNumeric(self$data[[self$options$measurement]])),
    python = "jamovi", timeout = 60L,
    checkpoint = function() private$.checkpoint(flush = FALSE))
tables <- Filter(function(item)
    identical(item$name, "summary") && identical(item$type, "Table"), response$items)
if (length(tables) != 1L || length(tables[[1]]$rows) != 1L ||
    length(tables[[1]]$rows[[1]]) != 2L) stop("Unexpected Pj table shape")
cells <- tables[[1]]$rows[[1]]
cells <- lapply(cells, function(x) if (is.null(x)) NA_real_ else x)
self$results$summary$deleteRows()
self$results$summary$addRow(rowKey = "summary", values = setNames(cells, c("n", "mean")))
```

This short excerpt illustrates transport and mapping; production code also needs
input validation, incomplete-state handling, result type validation, error clearing
and recovery. When catching errors, rethrow jamovi's `error$code == "restart"`
condition so cancellation works. Use the complete official backend or our adapter
for these lifecycle details. Ordinary `library(Pj)` may not find a sibling module;
the connector resolves its R library without requiring Pj to be a hard dependency.

The exported entry points are `Pj::mzPjServiceInfo()` and `Pj::mzPjRunPython()`;
the connector's `service$run` resolves the latter. Require API 1 and Pj 1.5.0 for
checkpoint-aware cooperative cancellation. The call is **synchronous**: background
means no editor is opened, not an asynchronous job handle. A timeout and checkpoints
allow the host to interrupt work. Both current execution routes use processx;
whole-route elapsed times do not isolate process-launch overhead.

Use jamovi Python for these examples. System Python support depends on a separately
configured external interpreter; see [local discovery limitations](python-system-bridge.md).
Bundled Pj libraries are version-specific. Users do not need network access or
additional Python packages for these examples once both modules are installed.

## Historical preparation evidence (2026-11-09)

Focused Python tests cover literal expected values, sample SD, missing/empty/singleton
input, invalid values, runtime serialization, fixed-route generation and rejected
route configurations. The 47 focused Python tests passed with local startup hooks disabled; see
`validation-exports/python-0.3.62-focused.json` for the harness adjustment. Native
comparisons against base R and real Pj execution are prepared in
[check-service-examples.R](../tools/check-service-examples.R) and remain pending
until the package builds. GUI installation/save/reopen/export also remain pending. These utility examples do not change the
61-analysis migration denominator. Passing these checks does not qualify other
platforms, all migration analyses, or the interactive SVG save/export lifecycle.

Local build attempts on 2026-11-09 were cancelled after prolonged stalls (system
load above 450). Logs are retained as `python-0.3.62-build.log` and
`python-0.3.62-build-clean.log`. No 0.3.62 installation or GUI qualification is claimed;
the installed 0.3.61 module was left in place.

## Verified follow-up — 2026-11-10

ClinicoPathPj 0.3.62 is built and installed on the current macOS arm64 setup with Pj 1.5.0.
The 58 focused Python checks passed, including these summary examples. Fresh native R
processes ran both entries on four fixtures (ordinary missingness, singleton, all missing,
and varied signed/extreme values), matched base R mean/SD/median/range/counts, and recovered
following invalid infinite input. See
[native results](validation-exports/python-service-examples-native-20261110.log).
The 33 packaged-runtime smoke cases include both examples and verify their shared helper
and typed Data Library `.omv` assets in the archive.

Their normal location is **Python Lab → Execution services**. The separate
[age-pyramid pair](python-age-pyramid-service.md) and these summary entries have
current-macOS GUI evidence; see the subsequent summary desktop qualification below.
Additional platforms remain pending.
A standalone service caller must initialize `jmvcore:::initProtoBuf()` before requesting
results; the host jamovi engine performs that initialization for ordinary R6 analyses.
The [dated qualification record](validation-exports/python-0.3.62-qualification-20261110.json)
keeps numerical, compiler, native, desktop and platform evidence separate.

### Regression follow-up — 2026-11-10

The full bundled-Python suite passed **473 tests** in 179.036 seconds, and the
generator freshness check passed. See
[full Python log](validation-exports/python-0.3.62-full-python-20261110.log).
This extends the focused checks above; it does not establish desktop acceptance.

An earlier summary-example GUI attempt stalled before loading the Data Library
(superseded by the successful restart and qualification below).
The accessibility tree changed to File/Open/Data Library while the displayed window
remained on the saved age-pyramid comparison. Refocusing and keyboard navigation
did not recover a usable library listing. No summary analysis was opened or saved
in that attempt, so it did not establish summary save/reopen/export. This observation
does not establish a defect in Pj or either summary calculation.

The full R run exposed a runner mismatch: `tools/check.sh` used system R, and Pj's
macOS discovery searches upward from `R.home()` to find the jamovi application.
That run failed before calculating the age-pyramid service result and was stopped;
its [log](validation-exports/python-0.3.62-full-r-system-runner-20261110.log) is retained.
The runner now launches bundled R and initializes protobuf results, matching the
host's service-discovery context. The previously failing lifecycle test passes
all 11 assertions with the corrected runner; see the
[focused log](validation-exports/python-0.3.62-r-runner-focused-20261110.log).
Use `CPJ_TEST_FILTER=age-pyramid-service bash tools/check.sh --r-only` to reproduce.
The optional `CPJ_TEST_LIBRARY` fallback is for already-installed local test/oracle
dependencies and does not qualify a clean installation.

The full suite with the corrected runner passed **4,498 R assertions**, with zero
failures, warnings or skips (499.2 seconds); see the
[full R log](validation-exports/python-0.3.62-full-r-20261110.log).

The summary harness now also reuses each R6 instance across valid → incomplete →
changed-variable → over-limit → valid transitions. It checks table and route-text
clearing, independently computed summaries for the replacement column, rejection
above the documented 100,000-row limit, and restoration of the initial table.
Both the own bridge and real Pj service pass; see the
[lifecycle log](validation-exports/python-service-examples-lifecycle-20261110.log).
The harness explicitly refreshes selected data when roles change, as the engine
does. Its initial missing-refresh attempt is retained in the
[harness log](validation-exports/python-service-examples-lifecycle-harness-20261110.log);
that failure was in the test setup. These are native backend checks, separate from
the separately observed desktop save/reopen/export test below.

### Summary desktop qualification — 2026-11-10

The stalled session recovered after **native jamovi menu → Quit jamovi**, followed
by reopening the application. Neither backend nor module source needed a change.
In the fresh session, Data Library → ClinicoPathPj → Python Execution Service
Examples loaded successfully. Both entries ran with **Measurement** and displayed
the expected row: input 6, N 5, missing 1, mean 4, sample SD 3.54, median 3,
minimum 1 and maximum 10. SD is rounded for display; numerical checks above use
the unrounded value. The Pj service ran without an editor opening.

Both analyses were saved together, exported as a native Web Page, and reopened
after quitting and relaunching the full application. Each saved selection remained
Measurement. Removing it cleared the table, route explanation and timing; restoring
it produced the same summary with a new backend timing in the fresh engine.
Save As then wrote a separate reopened file, followed by another native HTML export.

- [Initial comparison](validation-exports/python-summary-service-0.3.62-comparison.omv)
  and [HTML](validation-exports/python-summary-service-0.3.62-comparison.html).
- [Reopened and recalculated comparison](validation-exports/python-summary-service-0.3.62-reopened.omv)
  and [HTML](validation-exports/python-summary-service-0.3.62-reopened.html).
- [Artifact evidence](validation-exports/python-summary-service-artifacts-20261110.json)
  and [read-only checker](../tools/check-summary-service-artifacts.py).

The checker verifies archive CRCs, two literal native table displays, host/variable
records, both execution-route explanations, matching HTML exports and unchanged
source bytes/metadata. For this numeric-only fixture, jmvReadWrite emits empty
label metadata as `[]` and jamovi emits `{}`; that exact empty-label change alone
is allowed. Four corrupted-HTML probes (mean, SD, removed table and missing service
identity) are rejected. These checks inspect persisted displays and do not decode
all protobuf options or replace the numerical or GUI evidence.

Qualification is limited to **ClinicoPathPj 0.3.62 / Pj 1.5.0 / jamovi 28.17 on the
current macOS arm64 setup**. No plot is defined in these summary examples, so
there is no summary plot-export claim. Other platforms, clean-machine dependencies,
System GUI/renderer integration and GUI long-job cancellation remain separate gates.
The subsequent [office-export checks](python-service-office-exports.md) verify Word
tables and LibreOffice page rendering, plus LaTeX tables/figure assets. Full LaTeX
compilation remains blocked by missing local `apa7.cls`, with duplicate labels also
requiring cross-reference review. Observed elapsed times are whole-route observations, not a speed
benchmark. No new package build was needed for this qualification follow-up.

### Bundled and external source/API calculations

The [shared source/API harness](python-service-source-api.md) now includes
`--summaries --all`. All four summary fixtures match base R through both the own
subprocess and Pj under bundled Python 3.11.9/NumPy 2.4.6 and existing external
Python 3.9.12/NumPy 1.24.3. Every pair verifies matching executable, Python version,
NumPy version and dependency location. No packages or persistent settings changed.
These are developer source/API calculations; the installed summary entries remain
fixed to bundled Python. System GUI execution and persistence are not qualified.
