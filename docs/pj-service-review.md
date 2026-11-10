# Pj service review — updated 2026-11-09

## 0.3.61 System-route correction

[System Python isolation](python-system-bridge.md) documents a confirmed inherited-environment
startup failure, its repair and 54 passing restoration/alias assertions. The final build,
30 packaged cases, genuine external-interpreter API comparison and native alias-message/
bundled-recovery checks pass. Native positive System calculations remain unqualified in
this GUI environment, which discovers the bundled executable. Separate-session bundled-child
cleanup also passes, without establishing double-fork or cross-platform behavior. The full
suite numbers below belong to 0.3.60; no analysis identifier or statistical method changed.

## Pj 1.5.0 reassessment

Reviewed the tagged [public API guide](https://github.com/MAgojam/Pj/blob/v1.5.0/docs/mzPj_service_api.md),
[connector](https://github.com/MAgojam/Pj/blob/v1.5.0/docs/examples/mzPj_connect.R)
and [release](https://github.com/MAgojam/Pj/releases/tag/v1.5.0).
API version 1 remains compatible. Since 1.5.0, Pj uses processx, accepts a cooperative
caller checkpoint and applies one execution budget across preparation and computation.
The call remains synchronous; cancellation depends on the host supplying a checkpoint
and propagating jamovi's restart condition unchanged. This supersedes the older runner
limitations below; it does not establish a speed improvement.

The source adapter now passes the analysis checkpoint only when the runner explicitly
declares that argument and does not advertise `checkpoint=FALSE`. Older 1.3/1.4 API v1
signatures remain usable without the new argument. The host rethrows `code='restart'`
conditions intact instead of displaying cancellation as an analysis error. Timing text
uses returned module/runner/checkpoint/timeout metadata rather than assuming all API v1
implementations behave like 1.3. Missing optional Pj still cannot prevent module loading.

Pj's Plotly, Chart.js and D3 resources offer optional presentation experiments. Its
data-preparation, effect-size and uncertainty helpers are candidates for independently
validated engines, not automatic substitutes for our frozen statistical baselines.
Keep explicit Apply, local resources, row-aligned host Outputs and native static plots.
Pj's `Svg` item support does not resolve the separately documented host save/LaTeX issues.

The original source increment was followed by a 0.3.60 compiler build and Sideload
installation of ClinicoPathPj 0.3.60 and Pj 1.5.0. A separate legacy comparison window
recalculated and reported the new runner/checkpoint/timeout metadata. Scoped native
save/reopen, recalculation and HTML export also passed, as recorded below.

### Packaged and native 0.3.60 qualification

- The final compiler build passes. The installed `.rdb`/`.rdx` and Python comparison
  source match the archive; the analysis source also matches the repository. The prior
  0.3.59 package is preserved under `packages/archive/`.
- 17 R lifecycle assertions pass, with compiled bridge function bodies matching source.
  The compiled adapter also passes the isolated Pj 1.5.0 counts, main-process cancellation,
  timeout and recovery probes. Sandbox process-inspection diagnostics remain visible.
- The final 44-test focused Python run passes, including generator/registry/menu checks,
  route equivalence and the previously errored composite-outcome case. All 30 packaged
  runtime cases pass against the final archive, including the six ICC model subcases.
- Native jamovi 28.17 on macOS arm64 installed both modules through **Modules → Manage
  installed → Sideload**. The unrelated OncoPath window was neither closed nor edited.
- The 0.3.8 legacy comparison fixture opened in a separate window. Changing its cutoff
  recalculated using Pj 1.5.0, processx, an enabled checkpoint and a shared call timeout.
  A separate cutoff-4 copy was saved and closed. Reopening it created a new document/engine
  window; recalculating cutoff 3 succeeded, and a new reopened copy and native HTML were saved.
- [Artifact checks](../tools/check-pj-comparison-artifacts.py) verify unchanged six-row,
  three-column input bytes/labels, persisted native TP=2/FP=1/FN=1/TN=2, service metadata,
  corrected cancellation wording and two native PNG resources in each saved file and export.

Artifacts: `validation-exports/python-pj-service-0.3.60-{cutoff4,reopened}.omv` and
`validation-exports/python-pj-service-0.3.60-reopened.html`; checks and logs use the
`python-0.3.60-` prefix. The cutoff-4 copy intentionally preserves the pre-correction cached
summary; fresh recalculation in the reopened copy contains the corrected wording.

**Earlier attempts:** the broad Python suite was interrupted under extreme host load after
66 passes and one error without a traceback. A subsequent 44-test run had two runtime alarm
exits (`-14`); a retry then exposed a new assertion that had not unescaped Markdown punctuation.
The assertion was corrected and the final 44 tests pass. Raw failed/interrupted logs are
retained. These earlier attempts did not establish a full-suite pass or unrestricted cleanup.

### Full-suite and cleanup follow-up — 2026-11-09

The complete Python suite now passes **465 tests in 166.448 seconds**, with
`OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1`. No runtime alarm or assertion limit was
relaxed. This completes the Python-suite gate for the current source; the earlier logs
remain as historical evidence.

The full R retry against installed 0.3.60 also passes **4,450 assertions in 720.0
seconds**, with zero failures, warnings or skips. It ran outside the sandbox to permit
the suite's own-process inspection. The first R attempt ended during the user interruption
and is preserved as incomplete, not counted as a suite pass. Raw Python/R logs and
`validation-exports/python-0.3.60-follow-up-20261109.json` record the separate outcomes.

The installed CPJ 0.3.60/Pj 1.5.0 matched-route check also passes all **12 configurations**
(two directions, exact/Wilson intervals, three cutoff criteria). Native counts, estimates,
intervals and ROC summaries agree across routes. Independently constructed R threshold
counts and exact `binom.test()` intervals agree; the Wilson comparison in this script is
between routes. Ties, missing pairs, original row identities, invalid-input recovery and
unchanged library paths pass. `tools/check-pj-routes.R` now accepts an optional output CSV
and jamovi's direct R launch, preserving the original timing evidence. The new CSV is
`validation-exports/pj-1.5.0-matched-route-timings-20261109.csv`. These are whole-analysis
timings, not an isolated process-launcher benchmark.

`tools/check-pj-process-cleanup.R` ran against installed Pj 1.5.0 and CPJ 0.3.60 outside
the sandbox, which blocks `ps` inspection. Each case launches a Python parent that starts
a child sleeping for 30 seconds and records their exact PIDs in a temporary marker.
The child first writes its own readiness marker, and the parent verifies that it is
still running; a child that fails to start cannot pass as successful cleanup.
The normal-success, caller-cancellation and 10-second timeout cases all found both PIDs
absent after the service returned. The timeout marker proves main Python was reached,
so a timeout confined to library preparation cannot pass. Cancellation preserved the exact
restart condition; a subsequent service call succeeded. The probe's failure fallback may
terminate only a child whose command line contains its own unique marker and is not counted
as passing cleanup evidence.

The first probe attempt used a `ps` function unavailable in jamovi's bundled version.
It was corrected to the supported `ps_pids()` interface and rerun; both logs are retained.
This checks direct bundled Python on macOS arm64, not detached descendants, Flatpak,
System Python, desktop cancellation or other platforms. Detailed shared-deadline accounting
and other document export formats remain pending.

To reproduce the cleanup probe from the repository root in an ordinary Mac terminal:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
R_HOME=/Applications/jamovi.app/Contents/Frameworks/R.framework/Resources \
DYLD_LIBRARY_PATH=/Applications/jamovi.app/Contents/Frameworks/R.framework/Resources/lib \
/Applications/jamovi.app/Contents/Frameworks/R.framework/Resources/bin/exec/R \
  --vanilla --slave -f tools/check-pj-process-cleanup.R
```

It uses the installed modules, creates temporary synthetic probe files and starts only
short-lived test processes. No Pj editor or existing dataset is modified. Raw follow-up
logs and the machine-readable evidence summary are in `validation-exports/` under
`python-0.3.60-*-20261109`.

### Initial source-increment evidence (historical)

- 17 R assertions pass for argument forwarding, legacy signatures, explicit capability
  opt-out, exact restart preservation, ordinary-error diagnostics and timing descriptions.
- Four existing Python service/menu/generator tests pass (27.453 seconds).
- The published Apple Silicon JMO was downloaded to a temporary directory and unpacked;
  SHA256 `aaf0f7be4229984663edcf37e0d4fcdc98d5d51f7526c5cb3c413afa0162cc0a`
  matches the release asset digest. Neither installed module nor the local Pj fork changed.
- `tools/check-pj-service-lifecycle.R` executes the new source adapter against that packaged
  Pj and the unchanged CPJ statistical runtime. Counts are TP=14, FP=0, FN=41, TN=125;
  response metadata reports processx, an enabled checkpoint and a shared call timeout.
- Cancellation after the main Python script creates its start marker returns the exact
  caller restart condition. A one-second service budget returns `kind='timeout'`;
  a following valid request succeeds without changing library paths.

The [runtime log](validation-exports/pj-1.5.0-service-lifecycle-2026-11-08.log)
retains `Operation not permitted` process-inspection diagnostics from the sandbox. Passing
assertions do not establish descendant cleanup, a clean unrestricted run, System Python,
desktop integration or other platforms. The timeout probe does not independently prove
deadline accounting across every preparation phase.

The initial terminal harness could not discover bundled Python because `Rscript` resolved
to system R. Running jamovi's `bin/exec/R` directly with its own `R_HOME` and library path,
and initializing jmvcore's protocol definitions, enabled the isolated calls:

```sh
R_HOME=/Applications/jamovi.app/Contents/Frameworks/R.framework/Resources \
DYLD_LIBRARY_PATH=/Applications/jamovi.app/Contents/Frameworks/R.framework/Resources/lib \
/Applications/jamovi.app/Contents/Frameworks/R.framework/Resources/bin/exec/R \
  --vanilla --slave -f tools/check-pj-service-lifecycle.R \
  --args /private/tmp/cpj-pj150-review/Pj/R
```

This is a developer test command for this Mac, not a change to installed jamovi startup.

## Historical Pj 1.3.0 review

Reviewed local upstream commit `f14b072158728ccb3bbdffbd6d643638a90f936e`.
The fork remains unchanged; no upstream process-management modifications or push were made.

The public API (`mzPjServiceInfo`, `mzPjRunPython`, API version 1) permits an R backend
to supply code/data and receive structured items without opening an editor. Bundled and
System Python are supported. Resources and pure-Python helper libraries are available.
The API does not supply NumPy/SciPy for a System interpreter or write the host dataset automatically.

Pj 1.3.0 used synchronous `system2()`. Its timeout applies to subprocesses; resource
preparation can involve more than one subprocess. There is no public running-job handle
or host checkpoint callback. ClinicoPathPj can checkpoint before/after the call, but cannot
interrupt it through the existing processx cancellation loop while it is running.
This is a functional review, not a full security audit or cross-platform qualification.

## Integration

`R/utils-pj-service.R` discovers a loaded or sibling Pj module without changing global
library paths. It requires Pj >=1.3.0 and API 1. The optional service executes the same
installed `cpj_runtime.execute()` as the default route. A JSON request envelope preserves
factor levels, original row IDs and explicit missingness rather than relying on a second
factor encoding. Exactly one named Text response must contain the versioned CPJ result.
Malformed, duplicate and unsupported envelopes are rejected.

Pj remains optional. Existing analyses retain their processx implementation. Native
static images use the existing renderer regardless of the chosen computation transport.
The comparison therefore does not isolate raw `system2` versus `processx` speed.

## Evidence

On macOS arm64, jamovi 28.13 / Python 3.11, 12 matched configurations agreed on native
counts, estimates, confidence intervals and ROC summaries. Counts and exact intervals
also agreed with independent R threshold counts and `binom.test()`. Ties, missing pairs,
original row IDs, recovery after invalid input and unchanged library paths passed.
See `tools/check-pj-routes.R` and `validation-exports/pj-matched-route-timings.csv`.
Those timings measure whole R analysis calls, including setup, rather than isolated transport.
The new native timer excludes plot rendering and reports that scope separately.

Upstream macOS interpreter-location tests passed. The full upstream service test script
encountered `ModuleNotFoundError: colorsys` in its interpreter/resource workflow and is
not recorded as passed. The CPJ bundled-interpreter matched-route test passed separately.
System Python and Windows/Linux service routes are not qualified by these checks.

Regression evidence: 220 Python tests and 633 R assertions passed (zero R warnings/skips).
The jsdom interaction harness passed preview-only updates, native Apply dispatch, restore
and render-without-rerun checks. The built archive passed 15 packaged runtime cases.
