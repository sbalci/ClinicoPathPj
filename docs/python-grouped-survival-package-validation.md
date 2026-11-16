# Grouped survival 0.3.78 — bounded package and desktop qualification

The source/native increment is described in the [grouped contract](python-grouped-survival-core.md).
This record adds actual archive evidence. The [executed GUI protocol](python-grouped-survival-gui-checklist.md) adds bounded
macOS desktop evidence. Source, archive and desktop checks do not establish
clinical readiness or full parity.

## Archive

- Standard single-module package: `ClinicoPathPj_0.3.78.jmo`, 27,622,288 bytes.
- SHA-256: `b41371e13128c037512614a3c582285e23239ba4135c264ca6b4e4f85984c440`.
- Build via `Rscript --vanilla tools/build.R --build-only`; no global CLI install.
- Archive checks validate CRC, unique/safe paths, module version, one normal
  grouped-survival menu entry, exact registry/source files, generated UI bindings,
  the grouped CSV and existing curated example contents. Bytecode is pruned.
- The new checker launches a fresh subprocess importing only the extracted archive
  runtime; imported `cpj_` module locations are asserted. No source runtime is used
  as a substitute for executing the archived implementation.

## Packaged numerical and drawing checks

| Actual archived runtime | Configurations | Comparisons |
|---|---:|---:|
| Grouped survival, 30 frozen R datasets | 540 | 320,926 |
| Existing single-cohort survival, 26 datasets | 468 | 101,443 |
| Existing waffle allocation/geometry, 14 datasets | 420 | 216,200 |
| Total | 1,428 | 638,569 |

Grouped checks compare full KM/log-rank core outputs, native counts, group order,
medians, horizon support, row identities, observed/expected/score/covariance and
pooled risk audits against the independent R fixture. Actual saved-payload plot
steps, log bands and censor marks agree with that fixture, with model fitting
explicitly disabled during drawing. Output-off and invalid-mapping configurations
are included. Final PNG rendering passes. Numerical tolerance is the grouped
source contract's scaled 2e-10; integer/label/missing-value checks are exact.

Before the archive existed, the checker had a separate source trial. Its matching
counts are not counted twice or substituted for the actual archived runtime.
Reports/logs are in `/private/tmp/cpj-{grouped,singlearm,waffle}-0.3.78-package-20261116.json`
and their `.log` siblings. Build log:
`/private/tmp/cpj-grouped-build-0.3.78-20261116.log`.

## Native library and example

The built library is `build/R4.6.0-arm64-macos`. A first native run encountered the
bridge's existing 60-second subprocess timeout while build/render checks overlapped:
108 assertions passed, zero failed, one test errored. That is retained as failed
qualification evidence, not ignored. No timeout or statistical implementation was
changed; the isolated rerun passes all **2,055 assertions** with zero failures,
errors, warnings or skips. The GUI-installed library also passes the same 2,055
assertions. Its log is `/private/tmp/cpj-grouped-installed-native-0.3.78-20261116.log`.

The synthetic example passes independent installed-R `survdiff` and `survfit`
checks of cohort, log-rank, horizons and subject identity plus native PNG export.
It has nine complete subjects in three groups; chi-square 8.117197847435179,
df 2 and p 0.01727320324487263. Reference code:
`tests/reference/grouped-survival-example.R`; native rendering/checking code:
`tools/render-grouped-survival-example.R`. Preview/reference PNG:
`/private/tmp/cpj-grouped-0.3.78-native-reference.png`.

Logs: `/private/tmp/cpj-grouped-built-native-0.3.78-20261116.log`,
`/private/tmp/cpj-grouped-built-native-retry-0.3.78-20261116.log`,
`/private/tmp/cpj-grouped-built-example-0.3.78-20261116.log`.
Recurring subprocess `Operation not permitted` stderr remains visible separately
from test-framework failures/warnings.

## Executed bounded desktop and compatibility gate

GUI Sideload updates the existing ClinicoPathPj installation to 0.3.78. Fresh
sessions at endpoints 56921 and 57317 replace the old 65134 session; the second
follows a full quit/relaunch and cold saved-file reopen. Explicit roles, levels,
units and defaults, optional-output off, event removal, malformed horizons,
recovery, forced rerun and native export are observed and saved. All seven profiles
pass independent R table, data identity and image checks. Native dropdown
interaction required keyboard selection after unsuccessful automation clicks;
actual stored values and numerical output were verified before saving.

The direct PNG is **1400×1000**, byte SHA-256
`77606662cc5cbb5c24da5bd8c5df29e9b69e8c79ecc4c892bd3ad061a4fc656f`;
its pixels match native R export at the same size. Cached images are **1118×798**,
pixel SHA-256 `c270ac102d7bf2bf23a737e251e7a74d7b6db5b9373f7c0f58504793b38c847f`.
The native R renderer at that viewport size agrees. Plotted/recovered/reopened
profiles have identical source data/metadata, tables and cached pixels. The
native HTML export agrees with saved tables and images. Four corruptions are
rejected: cohort count, log-rank statistic, subject ID and missing image.

Prior `python-singlearm-0.3.77-reopened.omv` is cold-reopened, forced to rerun and
saved as a separate `python-singlearm-0.3.78-compatibility.omv`. Source data/metadata,
native tables and cached PNG are unchanged; the original is preserved.

All **1,551 installed files** match the actual JMO. All **1,438 shipped R-library
files** match the tested build and installation. Hash comparison is separate from
native tests and desktop acceptance. Full native/GUI artifact checker:
`tools/check-grouped-survival-artifacts.py`; final report:
`/private/tmp/cpj-grouped-gui-artifacts-final-0.3.78-20261116.json` and its `.log`.
Local validation outputs remain under `docs/validation-exports/` and the tested
OMV/PNG/JSON/log ignore rules apply. Native HTML remains an untracked local export.

## Remaining gates

The configured grouped workbook is now curated under `data/` and manifest-
registered in 0.3.79 source; inclusion and GUI Data Library checks remain pending
for that subsequent package. Broader desktop edge-case
interaction, accessibility/clinical review, older jamovi support, other platforms
and full survival baseline methods remain unqualified. Declared `minApp: 28.3.0`
is unchanged; this qualification covers only 28.17.0 on macOS arm64. No commit,
push or library submission is included. Superseded local JMO files are deleted
after replacement qualification per the user's cleanup preference; historical
hashes remain documented. Inventory: 39 partial / 22 planned / 15 utilities /
54 entries; zero full supported parity.

## Final checkpoint

All 54 focused generator/migration/grouped-core/adapter tests pass in 14.599
seconds, with no failures/errors/skips. The unchanged statistical source retains
its prior complete 772-test pass. All ten hash-locked wheels, generator/status
freshness and diff checks pass. Final focused log:
`/private/tmp/cpj-grouped-final-focused-0.3.78-20261116.log`.
The superseded 0.3.77 JMO was hash-verified and removed after replacement
qualification; only `ClinicoPathPj_0.3.78.jmo` remains. Its SHA-256 is unchanged.
The installed module remains 0.3.78. Work is left uncommitted and unpushed.
