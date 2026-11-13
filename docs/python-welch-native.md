# Welch RMS standardized effects — native integration and local qualification

## Scope

The existing `pyjjbetweenstats` entry now has an optional Welch RMS-SD point-only
route. `showStandardized` remains false and `varequal` remains false by default.
No analysis identifier, menu group or module identity changes. The source increment is now built and GUI-Sideloaded as **0.3.69** on macOS arm64 /
jamovi 28.17.0. Qualification below is local and bounded to these estimation routes.

Two compact tables distinguish the denominator/audit quantities from the point:

- **Welch RMS Standardizer:** equal-weight root mean of the two Bessel-corrected
  sample variances, its SD, Welch SE df and the distinct SD moment df.
- **RMS Standardized Difference (Point Only):** explicit first and second levels,
  first-minus-second divided by RMS SD, and point availability status.

The denominator differs from pooled SD. Both tables use the exact same complete
cohort, labels and original-row/subject-ID validation as the raw Welch analysis.
No standardized limits, confidence level column, effect-size significance test,
adjusted point or standardized plot is emitted by this route. Raw mean intervals
remain available and are explicitly distinguished from standardized uncertainty.
Undefined/essentially-constant raw inference produces null standardized values
and a stated availability reason rather than zero or infinity.

Student pooled-SD and paired-difference-SD standardized results retain their
existing tables, estimates, intervals, Hedges points and static delta plots. The
new Welch tables use `(showStandardized && !varequal)`; the original Student
results retain `(showStandardized && varequal)`. The generator now accepts a
negated second Boolean in its bounded two-Boolean visibility grammar. It still
rejects undeclared names, extra terms, repeated negation and executable suffixes;
leading negation is not introduced. Compiler-generated files are regenerated.

## Method evidence

The [source contract](python-welch-standardized-effects.md) freezes independent
R references for 22 datasets/110 confidence configurations. All five focused
adapter tests pass, including all 110 configurations, subprocess execution,
missingness, Unicode/literal-NA labels, one-constant df=1, degenerate inputs,
raw table/plot equality on/off, and point invariance to confidence changes.
Mocked inversion calls fail if invoked; the native adapter explicitly requests
`interval='none'` and emits only the approved point/audit fields.

The [independent replication/sensitivity study](python-welch-standardized-replication.md)
found seven failures and three inconclusive profiles. Its generic approximate
Welch intervals remain source-only. They are not enabled by this native option;
passing adapter/numerical checks does not reverse that method decision.

## Native integration checks

Compiler preparation for jamovi 28.17.0 and post-compiler generator freshness pass.
The source was installed into `/private/tmp/cpj-welch-native-library` and loaded
in fresh R processes with jamovi's bundled Python selected via `PYTHONHOME`.
The focused native suite checks all 22 R datasets, raw-output equality,
Student → Welch → off → incomplete → recovered transitions, confidence changes,
point-only fields, source cohort alignment and fresh-tree visibility.
Final isolated-library results: **446 new Welch assertions**, **531 existing
standardized/paired assertions** and **761 raw-mean assertions** pass separately
(1,738 total), each with zero test failures/errors/warnings/skips. Final process
supervision runs contain no restricted-process permission messages. The final
Python suite passes **627 tests** in 340.020 seconds. Generator/status freshness
and whitespace checks excluding compiler-owned `.h.R` output pass. Six isolated
library engine/adapter sources byte-match the final source tree.

The first native invocations omitted `PYTHONHOME`, so the bridge correctly stopped
with bundled-Python discovery errors. Correcting the test environment enabled the
calculations. Restricted subprocess supervision subsequently emitted `Operation
not permitted` stderr messages; those logs are retained separately from the final
runs with process supervision permitted. No production discovery/cleanup code was
changed to bypass these environmental conditions.

Two initial visibility assertions reused a manually mutated R6 result tree after
its first visibility evaluation. jmvcore `ResultsElement$.update()` caches that
value; its `create()` factory constructs fresh options and analysis objects.
The corrected harness retains reused-object table-clearing assertions and checks
visibility on fresh results under both model settings. This is a harness repair,
not a change to numeric expectations or result visibility rules. Native desktop
transitions still require the separate GUI gate.

The compiler adds trailing spaces to new `.h.R` column definitions. Those generated
lines are preserved; whitespace checks on hand-written/generator-owned files pass.
No compiler-owned header was hand-edited for formatting.

## 0.3.69 packaged and GUI qualification

The standard `ClinicoPathPj_0.3.69.jmo` is **23,231,003 bytes**, SHA-256
`ba611d30509e94356641843597e30bcc2ff9c3971f01321d5a03323f33b8ad6b`.
Archive CRC/path/duplicate/bytecode checks pass. All **1,379 packaged R-library
files** match the compiler output used for native checks. The actual extracted
runtime passes **2,008 checks across 102 configurations**: 51 raw, 32 Student/paired
standardized and 19 Welch point-only configurations. Source bytes, option bindings
and registry implementation contracts match. Generic Welch intervals remain omitted.

Both the compiled library and the exact GUI-installed library separately pass
**446 Welch**, **531 standardized/paired** and **761 raw-mean** assertions,
without failures/errors/warnings/skips. The initial compiled-library invocation
used the nonexistent generic `build/R` path; reruns used the actual architecture
output `build/R4.6.0-arm64-macos`. This was a test invocation issue, not a package
failure. Logs retain both attempts.

Installed using **Modules → Manage installed → Sideload**, then checked all
**1,454 installed files** byte-for-byte against the archive, before and after GUI
qualification. Restarted jamovi to avoid cached namespaces: first fresh session
used port 52654, second 52949 (the prior session used 50827).

The first fresh engine reopened the 0.3.68 Student/paired saved example with its
roles/options intact. Student confidence .95→.90→.95 recalculated both raw and
standardized intervals; the compatibility copy retains all 16 reference-matching
tables/four plots. Switching Student→Welch retained the selected standardized
switch, displayed the two RMS point/audit tables, and cleared Student standardized
limits, Hedges points and the standardized plot. The native layouts were visually
inspected. Welch SD is 4.08 and effect 0.215 at displayed precision.

Verified off/on, required second-level clearing/restoration and saved recovery.
The second fresh engine reopened that recovered file; .95→.90→.95 recalculated
the raw Welch interval while the RMS point stayed fixed. Save As, standalone HTML
export and direct 1300×600 raw PNG export succeeded. Source-native checks cover
both directions of model changes; the recorded GUI model transition is Student→Welch.
Do not infer unrecorded GUI checks from the automated lifecycle suite.

`tools/check-welch-artifacts.py` checks six GUI-saved profiles (compatibility,
valid, off, incomplete, recovered, reopened), the standalone HTML and direct PNG:

- All native numbers agree with independently frozen R references at display precision.
- Equivalent recovered/reopened tables and plot pixels equal the valid state.
- Off and incomplete states clear affected values, notes and cached images while
  preserving paired results.
- Data/metadata bytes equal the 0.3.68 original in every state, including exact subject IDs.
- Standalone HTML preserves the three expected plots; the direct PNG pixels equal
  the same-resolution source-native Welch render. The unchanged raw Welch plot
  also matches the prior qualified cached rendering.
- Four corruption probes (point, denominator, omitted-uncertainty disclosure and
  missing plot) are rejected.

Qualified 0.3.68 is preserved in `packages/archive/ClinicoPathPj_0.3.68.jmo`,
SHA-256 `69f1a62d823a4718d493a6981669cb3fc833b1dd1f8c28eb1cdb57efaeba5088`.
The superseded root copy was removed only after exact rollback verification.
No statistical production code changed during this package qualification. The
frozen-source Python suite remains 627 passing tests; generator/status freshness
passes after metadata updates. Generated-header whitespace remains compiler-owned.

## Remaining delivery gates

This is bounded macOS arm64 package/native GUI qualification, not full baseline
method parity, clinical review, Windows/Linux/Intel qualification or library
submission. No commit, push or submission was performed. Generic Welch standardized
uncertainty stays deferred after the failed sensitivity/coverage profiles. The
next source increment should address a separate frozen baseline method or plotting
feature; it must not silently re-enable the rejected approximate intervals.

Reproduce focused checks from the module root:

```sh
PYTHONHOME=/Applications/jamovi.app/Contents/Resources \
  /Applications/jamovi.app/Contents/MacOS/python -B tests/python/test_welch_adapters.py
PYTHONHOME=/Applications/jamovi.app/Contents/Resources Rscript --vanilla \
  tools/check-standardized-native.R /private/tmp/cpj-welch-native-library \
  tests/testthat/test-welch-python.R
python3 tools/generate.py --check
python3 tools/migration-status.py --check
```
