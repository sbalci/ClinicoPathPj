# Pj service review — updated 2026-11-08

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

This is a source integration increment. The installed ClinicoPathPj 0.3.59 and Pj 1.3.0
modules have not been replaced. A new JMO and desktop lifecycle checks remain separate gates.

### Evidence for this source increment

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
