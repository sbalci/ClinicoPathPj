# Native standardized mean effects — 0.3.68 qualification (2026-11-12)

The existing `pyjjbetweenstats` and `pyjjwithinstats` partial analyses now optionally
use the [checked standardized-effect core](python-standardized-effects.md).
Their identifiers and menus stay **Stats Plots Py → Group comparisons**. The new
`showStandardized` Boolean defaults to false, preserving the raw default methods
and result contracts. These results are included in **ClinicoPathPj 0.3.68**, GUI-qualified locally on
macOS arm64/jamovi 28.17.0. Qualified 0.3.67 is archived for rollback.

## Controls and presentation

A single **Standardized results and plot** switch sits in **Results and
Interpretation**, with adjacent denominator/interval explanations. In independent
comparisons it is enabled only by the existing Student equal-variance option;
Welch remains the raw default. Paired comparisons explicitly use the SD of
within-row differences. No legacy `effsizetype` aliases or unvalidated methods
are accepted. Required roles and inferential units remain visible in the existing
organized controls; generator-owned YAML uses `compilerMode: tame`.

The optional output is split into compact native tables:

1. **Standardizing SD and Model:** denominator, its sample SD and degrees of freedom.
2. **Cohen Standardized Difference and Population-Delta Interval:** d/d_z point,
   population-delta limits, confidence and availability status. Notes identify
   the target, normal-model assumptions and any reason limits are unavailable.
3. **Hedges-Corrected Point Estimate:** g/g_z point, exact J(df), and point status.
   This table has no CI columns; it does not attach Cohen limits to a g label.

A static native Image plots the Cohen point and population-delta interval with a
zero reference line. It is controlled by the standardized-results switch; the
existing raw-plot switch still controls only the raw plot. It reuses the interval
renderer and global palette. Rendering consumes serialized drawing data and does
not refit a model. A degenerate standardized estimate emits no plot. A finite
point with unavailable limits is shown without a fabricated interval.

Changing Student to Welch clears every standardized table and the standardized
plot, retains raw Welch calculations and warns that the requested standardized
branch is unsupported. The switch remains stored; returning to Student restores
the requested standardized output. This neither switches the model silently nor
rejects the valid raw analysis. Turning standardized output off does not call its
engine and preserves the five raw tables and raw plot. Missing/invalid roles clear
the dependent outputs through the existing bridge lifecycle.

## Independent and native evidence

Six adapter tests cover all **160 independently generated R dataset/confidence
configurations**, both designs through the subprocess bridge, raw on/off equality,
Welch preservation, strict Boolean validation, explicit unavailable intervals,
degeneracy, plot coordinates and UI/default/model bindings. The underlying source
core retains its separate **2,060 numerical checks**, mixture-CDF/MBESS/effectsize
references, reference replay and five mutation probes.

The first adapter run exposed an invalid all-null plot request for degenerate
data. The adapter now leaves that plot absent while retaining status/reason tables;
its regression cases cover all five confidence levels for those datasets. Test
notice expectations were corrected to use the runtime's `text` field and escaped
Markdown. The first full-suite run began before the compact table contract was
frozen and failed because its cached adapter used the prior columns with the new
schema. That log is retained; final qualification requires a separate frozen-source
suite, not that failed run. The final frozen-source suite passes **605 Python
tests**, including the six adapter tests and all 11 standardized-core tests.

Compiler preparation and post-compiler generator freshness pass. The initial source gate installed into
`/private/tmp/cpj-standardized-native-library`; the packaged/installed qualification
below subsequently verified the 0.3.68 artifact and actual desktop installation. All five Python analysis/shared-engine files in that isolated library
match the frozen workspace bytes.

**531 native assertions pass with zero failures, errors, warnings or skips.** They
compare all 32 R datasets at 95%, exact source rows, denominator/target labels and
point-only g columns. Same-instance checks cover standardized on/off, Student/Welch,
required-input clearing/recovery, repeated-ID rejection/recovery, valid → degenerate
→ valid, raw-plot independence, confidence changes and reuse-versus-fresh results.
Standardized plot state survives RDS serialization and exports after private analysis
data is cleared. Out-of-range inversion retains finite points and null limits;
degenerate estimates clear the plot. All **761 existing raw-mean assertions also pass**, with zero failures, errors,
warnings or skips; they run separately against the same isolated library.

Synthetic source-native figures, rendered from the existing 13-subject example and
compared with independent R points/limits:

- [Independent pooled effect](validation-exports/python-standardized-independent-native-20261112.png):
  d=0.20374649, population-delta 95% CI [-0.92131364, 1.31971381], g=0.18947604.
- [Paired difference-SD effect](validation-exports/python-standardized-paired-native-20261112.png):
  d_z=2.10493925, population-delta_z 95% CI [0.42967065, 3.73243266], g_z=1.67949853.

Both 1300×600 images were visually inspected for labels, zero references, points
and interval geometry. These are source-native exports, not desktop acceptance.
The independent illustration explicitly uses Student; the raw default stays Welch.
Exact subject labels and retained source rows remain unchanged.

Reproduce with `tests/python/test_standardized_adapters.py`,
`tools/check-standardized-native.R`, `tools/check-estimation-native.R <isolated-library>`,
and `tools/render-standardized-example.R`. Generated JSON and logs remain ignored.

## Packaged and native GUI qualification — 0.3.68

Build and post-compiler freshness pass. The immutable archive passes CRC,
single-namespace, source-byte, registry-contract and bytecode checks. Its extracted
runtime passes **1,875 checks across 102 configurations**: 51 raw, 32 standardized
and 19 requested-standardized/Welch cases across the 32 independent R datasets.
Both the built and GUI-installed libraries separately pass **531 standardized and
761 raw native assertions**, with no failures, errors, warnings or skips.

Installed through **Modules → Manage installed → Sideload**, then verified all
**1,453 installed files** against the archive. A fresh engine reopened the existing
0.3.67 saved example. It retained the prior roles/subject labels, selected Welch,
and kept the new standardized controls off; the independent control was disabled
until Student was explicitly selected. Both analyses then produced the expected
Cohen/population-delta and Hedges point-only tables and plots.

Saved states verify Student → Welch → Student, paired standardized off/on,
required paired measurement clearing/restoration, and independent-result
preservation. Unsupported independent standardized tables/plot disappear under
Welch, with raw Welch results retained and explained. The incomplete paired file
contains no computed paired rows, stale notes or cached paired images. Restoration
recovers all results. A second fresh engine reopens the recovered file; changing
both confidence levels to 0.90 then back to 0.95 recalculates the raw and standardized
intervals. Save As, HTML export and both direct standardized PNG exports pass.
The initial desktop-control timeout was resolved by reconnecting; final acceptance
uses observed successful interactions and inspected saved/exported files.

`tools/check-standardized-artifacts.py` validates all **16 native tables** against
independent R fixtures at display precision. Valid/recovered/reopened tables and
plot pixels are identical. Welch raw results match the default-off state; model,
off and incomplete transitions preserve unaffected outputs. Dataset bytes,
metadata and exact source/subject IDs match the original 0.3.67 example in all
seven saved states. HTML re-encoding changes PNG file bytes but preserves pixels;
both direct 1300×600 PNG exports match the source renders. Four deliberately
corrupted artifacts (cohort, Cohen estimate, Hedges estimate, missing plot) fail.

Artifact: `ClinicoPathPj_0.3.68.jmo`, **23,226,839 bytes**,
SHA-256 `69f1a62d823a4718d493a6981669cb3fc833b1dd1f8c28eb1cdb57efaeba5088`.
Rollback: `packages/archive/ClinicoPathPj_0.3.67.jmo`,
SHA-256 `77dda13ba6530f4808dffcfb178518808a3708a171d4befc5fb55726d15174d1`.
Only post-build numerical/GUI/platform coverage evidence may advance in the source
registry; the packaged implementation, defaults, baselines and contracts stay fixed.

Saved artifacts: [defaults/compatibility](validation-exports/python-standardized-0.3.68-defaults.omv),
[valid](validation-exports/python-standardized-0.3.68-valid.omv),
[Welch](validation-exports/python-standardized-0.3.68-welch.omv),
[paired standardized off](validation-exports/python-standardized-0.3.68-off.omv),
[incomplete](validation-exports/python-standardized-0.3.68-incomplete.omv),
[recovered](validation-exports/python-standardized-0.3.68-recovered.omv),
[reopened/recalculated](validation-exports/python-standardized-0.3.68-reopened.omv),
[HTML](validation-exports/python-standardized-0.3.68-reopened.html),
[independent PNG](validation-exports/python-standardized-0.3.68-independent-plot.png),
[paired PNG](validation-exports/python-standardized-0.3.68-paired-plot.png).

## Remaining gates

Counts remain **32 partial targets / 29 planned / 15 utilities**, with zero full
supported-baseline parity releases. Unequal-variance standardized effects,
g-specific interval conventions, rank, robust/Bayesian/general repeated methods,
box/violin/interactive geometry, broader platforms and clinical review remain
separate gates. A separate [unequal-variance source prototype](python-welch-standardized-effects.md)
now has frozen independent references and a coverage screen (11 pass, one
inconclusive). Review its approximate methods and further coverage evidence before
extending the current Welch controls; it is not part of the qualified archive.
No new dependency installation is required; production uses bundled libraries.
