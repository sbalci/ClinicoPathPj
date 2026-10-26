# Pj 1.3.0 service review

Reviewed local upstream commit `f14b072158728ccb3bbdffbd6d643638a90f936e`.
The fork remains unchanged; no upstream process-management modifications or push were made.

The public API (`mzPjServiceInfo`, `mzPjRunPython`, API version 1) permits an R backend
to supply code/data and receive structured items without opening an editor. Bundled and
System Python are supported. Resources and pure-Python helper libraries are available.
The API does not supply NumPy/SciPy for a System interpreter or write the host dataset automatically.

Pj currently uses synchronous `system2()`. Its timeout applies to subprocesses; resource
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
