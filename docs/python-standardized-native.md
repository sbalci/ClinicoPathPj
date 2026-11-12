# Native standardized mean effects — working source (2026-11-12)

The existing `pyjjbetweenstats` and `pyjjwithinstats` partial analyses now optionally
use the [checked standardized-effect core](python-standardized-effects.md).
Their identifiers and menus stay **Stats Plots Py → Group comparisons**. The new
`showStandardized` Boolean defaults to false, preserving the raw default methods
and result contracts. This is an **unpackaged native source increment**; the
installed and desktop-qualified 0.3.67 archive remains unchanged.

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

Compiler preparation and post-compiler generator freshness pass. The source is
installed only into `/private/tmp/cpj-standardized-native-library`, using current
DESCRIPTION metadata; this does not replace the installed desktop module or build
a new JMO. All five Python analysis/shared-engine files in that isolated library
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

## Remaining gates

Counts remain **32 partial targets / 29 planned / 15 utilities**, with zero full
supported-baseline parity releases. Qualified 0.3.67 is preserved in `packages/archive/` with SHA-256
`77dda13ba6530f4808dffcfb178518808a3708a171d4befc5fb55726d15174d1`; all
1,452 installed files still match it. Next build a new
standard `ClinicoPathPj_0.3.68.jmo`, check its actual packaged runtime, then GUI
Sideload and verify fresh-engine option/model transitions, `.omv` save/reopen,
recalculation, and native table/plot exports for these added results. Do not
rebuild this source over the qualified 0.3.67 artifact.

Unequal-variance standardized effects, g-specific interval conventions, rank,
robust/Bayesian/general repeated methods, box/violin/interactive geometry, broader
platforms and clinical review remain separate gates. No new dependency installation
is required; production uses the existing bundled Python libraries.
