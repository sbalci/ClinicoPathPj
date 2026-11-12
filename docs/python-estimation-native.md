# Native independent and paired raw-mean estimation — 2026-11-12

The stable identifiers `pyjjbetweenstats` and `pyjjwithinstats` now have literal
Python SPECs, generator-owned R/YAML integration, organized controls, native tables
and a static raw-difference plot. They share the
[independently checked estimation engine](python-estimation-core.md).

These are **bounded native partial analyses in ClinicoPathPj 0.3.67**, locally
GUI-qualified on macOS arm64/jamovi 28.17.0. The registry has 32 partial baseline
targets, 29 planned targets and 15 retained utilities (47 implementation entry
points); none has full supported-baseline parity plus every release gate.
The qualified 0.3.66 archive is preserved in `packages/archive/` for rollback.

## Interface and contracts

Both entries are under **Stats Plots Py → Group comparisons**, with compact menu
titles **Independent Mean Comparison** and **Paired Mean Comparison**. Existing
`pywelch`, the R baseline and utility/demonstration entries remain unchanged.
The titles describe the implemented raw-mean scope; these are not complete
box/violin or standardized-effect ports.

| Section | Independent analysis | Paired analysis |
|---|---|---|
| Data roles | One outcome, group and explicit distinct first/second levels; optional subject ID. | First and second numeric measurements; optional subject ID. |
| Analysis and Model | Visible first-minus-second contrast and independent-case assumption; equal-variance checkbox off by default (Welch). | Visible within-row pairing, first-minus-second contrast and one-row-per-independent-subject assumption. |
| Uncertainty and Validation | Confidence level 0.95, range 0.50–0.999. | Same. |
| Results and Interpretation | Optional retained source-row table, off by default. | Same, including both measurements and each within-row difference. |
| Plots and Interaction | Optional static raw-difference/CI plot, on by default. | Same; limits belong to the paired difference. |
| Advanced Settings | Optional console diagnostics. | Same. |

All roles are in the first variable supplier. Independent level selectors use
explicit boolean enablement and start unset. The baseline `dep` Variables option
is retained but this core accepts exactly one outcome. Paired `dep1`/`dep2` remain
scalar roles; third/fourth measurements are not offered. Confidence and variance
defaults preserve the supported frozen choices. The static difference plot and
always-available native tables are new partial-core presentation choices; they do
not reproduce the R baseline's box/violin geometry or default subtitle behavior.

The adapter rejects extra requests for rank, robust or Bayesian statistics,
standardized effects, splitting and additional measurements/comparison families.
It never substitutes a classical method for one of those requests. Scalar storage
checks reject dates, dimensions and unsupported classes; jamovi may reject these
before the Python adapter. Optional subject IDs use exact factor/text labels,
preserving leading zeros. Known/unique IDs are required only among retained cases;
ID checks do not establish independence or handle clustering.

## Results and safeguards

Five native tables show the cohort, missingness per role, two descriptive rows,
a raw contrast row, and optional original source rows. The contrast names both
sides and the test, SE, t, df, raw confidence limits, confidence level and status.
The p-value is two-sided. Missing-role counts may overlap; exclusions count their
union. Retained counts and statistical sample sizes describe all retained data.
The optional source table shows at most the first 1,000 retained rows and states
that limit explicitly. It does not sample or change the inferential cohort.

The static Python-rendered plot displays one raw contrast and its interval, with
a zero-reference line. It reuses the existing Image/interval rendering contract,
jamovi palette and serialized plot state; there is no model refit during rendering.
A degenerate result retains a descriptive point with no inferential limits, SE,
t, df or p; its warning rules out a zero-width interval or infinite significance.
Small samples receive an assumption/uncertainty warning, without method switching.
A null-compatible interval or large p does not establish equivalence or clinical
unimportance. Raw difference intervals are not standardized-effect intervals.

## Synthetic example

**Independent and Paired Mean Examples** (`data/python_estimation_examples.csv`)
contains 13 synthetic subjects with distinct text IDs, including `001`, `01` and
`1`. It is generated from independent frozen fixtures by
`data-raw/generate-python-estimation-examples.py`, without calling the target engine.

- Independent: choose Outcome, IndependentGroup, first `First`, second `Second`,
  and optional Subject. There are five first-group and eight second-group cases;
  all 13 are retained. Welch is the default.
- Paired: choose FirstMeasurement and SecondMeasurement, with optional Subject.
  Five complete pairs remain; eight rows are excluded for missing measurement(s).
  Original retained source rows are 2, 3, 5, 7 and 8.

Native source renders: [independent](validation-exports/python-estimation-independent-native-20261112.png)
and [paired](validation-exports/python-estimation-paired-native-20261112.png).
These images were visually inspected for contrast labels, zero-reference lines
and limits. They are isolated-source renders, not GUI exports.

## Evidence and remaining gates

The shared engine's 20,380 R-reference checks, 17 focused tests and reference
correction/replay evidence remain separate from adapter and native validation.
Six adapter tests cover all 255 independent R configurations, both analyses through the subprocess
module runtime, disabled outputs, exact subject/source IDs,
unsupported methods, storage metadata, bounded display and preserved defaults.
Compiler preparation and isolated-source installation pass.

Native tests compare the 95% configurations of every frozen dataset and both
independent variance methods. They exercise same-instance required-role/level
clearing and restoration, invalid distinct-role and repeated-ID errors, optional
output clearing, confidence changes, genuine missing factor levels and Date
rejection. Plots survive RDS serialization and render after analysis data is
cleared. The final isolated native run passes **761 assertions with zero failures, errors,
warnings or skips**. The initial Date-rejection expectation was corrected to
accept the upstream numeric-type rejection as well as the Python guard.

The first full Python run exposed a compiler rewrite: a `maxItemCount: 1` cap
on the baseline `Variables` outcome caused its control to move into a second
variable supplier. The literal SPEC now leaves that multi-variable widget uncapped
and the adapter enforces exactly one outcome with an explicit error. Compiler
preparation now preserves the generator-owned panel with every role in the first
supplier, and immediate generator freshness passes. The final full regression run passes **588 Python tests** after this correction;
generator/status freshness and whitespace checks pass. Earlier failure evidence
remains local.

The 0.3.67 build passes archive CRC/namespace/bytecode checks. Its actual extracted
Python runtime passes **1,071 checks across 32 independent R datasets and 51
95% method configurations**, maximum relative difference 2.05e-14 (tolerance
1e-11). Build-library and GUI-installed-library native runs each pass **761
assertions with zero failures/errors/warnings/skips**. Every one of the **1,452
installed files** matches the immutable archive, checked before and after runtime
qualification. Generator freshness still passes after compilation.

GUI installation used **Modules → Manage installed → Sideload**. A fresh engine
opened the synthetic example and both adjacent Group comparisons entries. Explicit
First/Second levels, optional Subject IDs and source-row tables were selected.
The independent example retained 13 rows and reported difference 0.875; switching
to Student updated the method and df=11 before restoring Welch. The paired example
retained five subjects (source rows 2, 3, 5, 7, 8) and reported difference 2.4.
Both input lifecycles were saved: missing first paired measurement; missing second
independent group level. Each cleared all affected computed rows and its cached
plot while preserving the other analysis. Restoration recovered the results.

A second fresh engine reopened the recovered file with both cached plots. Both
analyses recalculated at confidence 0.90, then restored 0.95, and were saved again.
Native HTML and separate independent/paired PNG exports succeeded. The saved
`.omv` tables agree with the independent R fixtures at their displayed precision;
valid/recovered/reopened tables and same-resolution plot pixels are identical.
Dataset bytes, metadata and exact subject labels are unchanged throughout all
five saved lifecycle states. HTML changes PNG encoding/file hashes but preserves
all rendered pixels; the checker explicitly compares dimensions/pixel hashes for
this format. Both direct PNG exports are byte-identical to the 1300×600 source
renders. Four deliberate corruptions (cohort, difference, p-value, missing plot)
are rejected. The initial artifact-check failure was an overly strict HTML PNG
byte comparison; its evidence is retained locally and the pixel comparison is
recorded separately from compressed-file hashes.

Archive: `ClinicoPathPj_0.3.67.jmo`, **23,218,953 bytes**,
SHA-256 `77dda13ba6530f4808dffcfb178518808a3708a171d4befc5fb55726d15174d1`.
Rollback: `packages/archive/ClinicoPathPj_0.3.66.jmo`,
SHA-256 `82a4f42b10a26dbd76d3427258e1b2ca4c18c9effd556b49dcc12ef891c74fc8`.
The source registry records post-install numerical/GUI/platform evidence; only
those coverage fields may differ from the immutable archive. Source code,
contracts, baseline hashes and full-parity status must still match.

Reproducible checks:

- `tools/check-estimation-package.py`: actual archive/source contract, fixture runtime.
- `tools/check-estimation-native.R <library>`: source/built/installed native tests.
- `tools/check-estimation-artifacts.py`: five saved states, ten tables, HTML/two PNGs,
  independent numerical targets, image pixels, source identity and corruption probes.

Saved artifacts: [valid](validation-exports/python-estimation-0.3.67-valid.omv),
[paired incomplete](validation-exports/python-estimation-0.3.67-incomplete.omv),
[independent incomplete](validation-exports/python-estimation-0.3.67-independent-incomplete.omv),
[recovered](validation-exports/python-estimation-0.3.67-recovered.omv),
[reopened and recalculated](validation-exports/python-estimation-0.3.67-reopened.omv),
[HTML](validation-exports/python-estimation-0.3.67-recovered.html),
[independent PNG](validation-exports/python-estimation-0.3.67-independent-plot.png),
[paired PNG](validation-exports/python-estimation-0.3.67-paired-plot.png).
Generated JSON evidence and logs remain local and ignored.

| Baseline feature | Current boundary |
|---|---|
| One-endpoint two-group Welch/Student; two-column paired t | Native partial implementation. |
| Raw mean limits and source-row audit | Implemented. |
| Standardized effects/intervals | Omitted; separate method specification needed. |
| More groups/measurements, ANOVA/repeated-measures corrections | Omitted. |
| Rank/robust/Bayesian, splitting, multiple endpoints/multiplicity | Omitted. |
| Box/violin geometry, subject paths, annotations, interactive inspection | Omitted. |
| Clinical review, broader platforms and full parity | Pending. |

No full-parity, clinical-validation or library-submission claim is made. Next
freeze standardized-effect estimands and independent interval references before
extending the analysis controls; validate plot geometry and interactions separately.
Other platforms, architectures and the omitted statistical branches remain open.


## Working-source follow-up — standardized results

The [optional standardized native extension](python-standardized-native.md) now
adds compact model/Cohen/Hedges tables and a static delta plot to these same
identifiers. It is off by default, requires the supported Student/paired models,
and preserves the raw calculations. Its 605 Python tests, 531 standardized and
761 raw native assertions and source-native plot checks are separate from the
0.3.67 desktop qualification above. Build/GUI-qualify a new 0.3.68 package before
claiming installed acceptance of these new results. Qualified 0.3.67 is archived.
