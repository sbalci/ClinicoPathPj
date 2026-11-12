# Clinical ROC analysis: native partial integration — 2026-11-11

`pyenhancedroc` now has a literal Python SPEC and `run()` adapter, generated native
options/results/UI/R bridge, native tables and an exportable static ROC plot. It
uses the independently checked [ROC/paired DeLong engine](python-roc-core.md).
The **0.3.65 local package is now installed through jamovi's Sideload menu** and
has passed bounded native GUI checks on macOS arm64 / jamovi 28.17.0. The 0.3.63
and 0.3.64 rollback archives remain under `packages/archive`. This remains an experimental
partial implementation, without full baseline parity, other-platform or clinical
acceptance. See [package qualification](validation-exports/python-roc-0.3.65-ui-qualification-20261111.json).

The existing stable identifier is retained under **MedDecide Py → ROC and
comparison → Clinical ROC Analysis**. The registry now has 29 partial targets,
32 planned targets, 15 utilities and zero full-parity releases. No alias or second
module/menu identity was introduced. The analysis remains far short of the frozen
enhancedROC feature inventory.

## Organized interface

| Section | Controls and purpose |
|---|---|
| Data roles | Binary reference, explicit positive level, one required score and two optional scores; all roles use the first variable supplier. |
| Analysis and Model | Higher/lower direction for each score. Directions remain visible and are never inferred; source bindings now disable unused directions (desktop follow-up below). |
| Uncertainty and Validation | Confidence level .80–.99, default .95; the displayed method is the approximate normal DeLong method. |
| Results and Interpretation | Paired unadjusted comparisons, observed-threshold classifications and retained source rows. Secondary details default off. |
| Plots and Interaction | Native static empirical ROC plot, enabled by default. Interactive exploration is deferred. |
| Advanced Settings | Optional Python console diagnostics. |

The generator owns `.a.yaml`, `.r.yaml`, `.u.yaml` and `.b.R`. The UI uses
`compilerMode: tame`; compiler headers and function documentation are regenerated.
Essential directions and confidence controls are expanded. Optional results and
advanced controls are collapsed. This core offers no unused bootstrap/model
controls or implied option for an unimplemented method.

## Outputs and numerical behavior

- **Cohort:** source rows, common complete cases, excluded rows and both class counts.
- **AUC:** one row per score, its positive inequality, AUC, approximate SE/interval
  and a textual uncertainty status. Limits are bounded at [0,1].
- **Comparisons:** first-minus-second AUC, SE, raw normal difference limits, signed
  z, two-sided **unadjusted** p and status. With one score, the table has no rows
  and explains that comparisons need at least two scores.
- **Thresholds:** optional counts, sensitivity and specificity at every observed
  cutoff, plus the explicit none-positive endpoint with an empty cutoff cell.
- **Source rows:** optional original row identifiers, reference labels and score
  slots aligned to the selected input roles. Score 3 can be used with Score 2 empty.
- **ROC plot:** the same computed FPR/TPR points, grouped by score, plus a chance
  reference. Rendering uses the existing Python plotting backend and jamovi theme
  palette; R displays the completed image. No model is recomputed by the renderer.

All selected scores share one complete-case cohort. Input errors clear prior
results through the existing opt-in bridge policy before rejection. Incomplete
selection clears prior outputs and returns through the bridge's normal setup
path. Duplicate score roles are rejected. Optional output suppression clears
inactive tables/plot state; it does not change the underlying cohort or estimates.

The method text and table notes explicitly disclose independence, fixed direction,
approximate uncertainty, inadequate small-class coverage, unavailable zero-variance
inference and unadjusted multiple testing. The engine's two-per-class variance
requirement is not presented as a reliable clinical minimum. No clinical
acceptance categories or automatically optimized cutoff are produced.

## Synthetic example

Import `data/python_roc_examples.csv`, set `Reference` to nominal and both
measurement columns to continuous. Select positive level `Positive`, Score 1
`Measurement_A`, Score 2 `Measurement_B`, both directions higher.

There are 12 source rows and eight common complete cases (four in each reference
class). Four source rows are excluded for reference/score missingness. Expected
AUCs are **21/32 = .65625** and **23/32 = .71875**; their paired difference is
−.0625. For Score 1 at cutoff 3 with `>=`, TP=3, FP=2, FN=1 and TN=2. These are
synthetic numerical examples, not clinical cutoffs or validation data. The CSV is
not yet a Data Library `.omv` demonstration.

## Validation and delivery boundary

The runtime adapter is checked against all 17 independent R/pROC/literal-kernel
fixtures, including undefined inference. A real subprocess request checks row-ID
and plot/threshold alignment. Focused tests cover optional outputs, empty/invalid
roles and use of Score 3 without Score 2. Existing numerical-engine checks and
known-truth simulation remain recorded separately.

The jamovi compiler prepares the generated interface using the installed app's
28.17.0 version. The source package is installed into an isolated temporary R
library for native tests; this does not replace the user's installed module.
Native checks compare frozen fixtures, same-instance valid→incomplete/error→valid
transitions, optional-output removal, event/direction changes, filtered source
positions, confidence changes, and PNG rendering from serialized plot state with
analysis data cleared. This is automated native integration evidence, not native
GUI save/reopen acceptance.

Retained initial harness failures are separate from target behavior: a subprocess
fixture supplied integer row IDs where the runtime requires positive integer
strings, and an R test tried assigning through a method-call return expression.
The fixtures/tests were repaired without changing estimates or reference values.
The initial R compiler invocation also used an unsupported `app` argument;
direct compiler preparation with explicit installed app version succeeded.

The final source suite passes **531 Python tests** (223.673 seconds). The host
native suite passes **320 assertions** (40.6 seconds), with zero failures,
warnings or skips. Generator/status freshness checks pass. The earlier restricted
native run's process-monitoring permission errors remain logged separately; the
host reruns contain no such errors. Genuine missing factor levels and literal
`"NA"` event labels both pass their native checks.

The synthetic example's [native PNG](validation-exports/python-roc-native-example-20261111.png)
and [native table values](validation-exports/python-roc-native-example-20261111.json)
are retained. The PNG was visually inspected for labels, empirical geometry and
chance reference. These are automated native exports, not GUI exports.

See the [integration qualification record](validation-exports/python-roc-native-qualification-20261111.json)
for exact assertion/test counts, hashes and logs. The earlier
[source numerical qualification](validation-exports/python-roc-qualification-20261111.json)
does not include these native checks.

## Completed local package and GUI checks

- Build and CRC/runtime-check 0.3.64, remove regenerable bytecode, and preserve the
  qualified 0.3.63 rollback archive.
- Install via **Modules → Manage installed → Sideload**, retaining the single module
  identity. Verify all 1,438 installed files match the archive with zero extras.
- Native Quit/relaunch after installation; run the synthetic example. Save a
  comparison `.omv` and native HTML export with all optional details enabled.
- Native Quit/relaunch again; reopen the saved file. Reverse Score 2 to lower
  (AUC .28125), restore higher (.71875), remove required Score 1, verify clearing,
  save an incomplete snapshot, restore the role and Save As a recovered snapshot.
- Inspect the restored native plot; export PNG and recovered HTML. The GUI-installed
  module independently passes 320 native R assertions with no failures/warnings/skips.
- Validate all saved/exported tables and threshold counts against literal source
  calculations; verify unchanged data/metadata and cleared incomplete outputs.
  Reject four deliberate artifact corruptions.

Saved artifacts: [initial comparison](validation-exports/python-roc-0.3.64-comparison.omv),
[incomplete snapshot](validation-exports/python-roc-0.3.64-incomplete.omv),
[fresh-engine recovered analysis](validation-exports/python-roc-0.3.64-reopened.omv),
[HTML export](validation-exports/python-roc-0.3.64-reopened.html) and
[native PNG export](validation-exports/python-roc-0.3.64-reopened.png).
[Artifact checks](validation-exports/python-roc-0.3.64-artifacts-20261111.json)
record hashes and validation limits.

The saved/HTML cached plot is 1038×718 and remains pixel-identical across equivalent
saved states. Standalone PNG export is 1300×900 and is pixel-identical to the earlier
independent native render at that same size. These different resolutions are not
claimed to be pixel-identical to one another. The post-GUI literal-kernel R check
for the CSV example confirms paired SE .2338535867 and p .7892680261; it is separate
from the preimplementation blinded R/pROC fixtures.

Earlier desktop timeouts, a nonresponsive old jamovi session and unsuccessful native
GoToFolder attempts remain history. Normal native Quit/relaunch restored module
navigation; choosing the file through native folder navigation completed Sideload.
The current blockers are full baseline scope, other platforms, additional export
formats and clinical review, not local HTML/PNG saved-file acceptance.

Bootstrap, partial/smoothed/multiclass ROC, calibration, model validation, interactive
threshold views and complete baseline parity remain omitted. `pydecisioncompare`
still requires its separate binary paired-test implementation.

## Direction-control follow-up — 0.3.65

The installed 0.3.64 panel showed an enabled direction for empty Score 3. The
jamovi 28.17.0 client explains this: `(marker3)` propagates `null` for an empty
role, while ComboBox disables its input only for strict `false`. The literal
SPEC now uses `(!(!marker1))` through `(!(!marker3))` to return booleans. The outer
parentheses ensure the client recognizes a dynamic binding. Only the
generated UI changes; option identities, defaults and calculations are preserved.

Run `node tools/check-roc-ui-bindings.js` to exercise the actual installed
client's binding and ComboBox methods in an isolated VM. It checks all three
roles through empty → selected → empty → reselected → empty transitions,
including binding recognition, dependency registration and 45 state checks. The
original UI fails on its first empty dropdown; the repaired UI passes. The tool
records the client bundle hash and fails if its extraction assumptions no longer
match the installed client. This is a focused client-method check, not a full
browser or native GUI test.

All 533 Python regressions and 33 separately rerun generator tests pass, as do
generator/status freshness checks. An AST comparison confirms executable code
and option/result contracts are unchanged; the only SPEC differences are the
three enable expressions. Compiler preparation passes with jamovi 28.17.0
without warnings. The 0.3.65 archive passes all 17 frozen ROC fixtures, contains
the compiled boolean bindings and matches all 1,438 installed files. The
installed native suite passes 320 assertions without failures, warnings or skips
in the host run. An earlier restricted-shell run also passed its assertions but
emitted two teardown permission errors; it is retained separately.

On macOS arm64 / jamovi 28.17.0, GUI Sideload and native Quit/relaunch pass.
Removing Score 2 disables its dropdown; moving that variable into Score 3
enables Score 3, and removing it disables Score 3 again. Restoring Score 2
re-enables its dropdown. Clearing required Score 1 disables its direction and
clears computed native results; restoring it re-enables the control and recovers
the original two-model results. Save As to a separate fixture, another native
Quit/relaunch, reopening and HTML export pass. The reopened empty Score 3
control is visibly grey and disabled.

Run `tools/check-roc-artifacts.py --ui-followup 0.3.65` in bundled Python to check
the [saved fixture](validation-exports/python-roc-0.3.65-ui-recovered.omv) and
[HTML export](validation-exports/python-roc-0.3.65-ui-recovered.html). Their tables,
threshold counts and source rows pass independent checks; dataset bytes and
metadata equal the qualified 0.3.64 fixture, and cached/exported plot pixels
match that baseline. Four artifact corruption probes are rejected. Generated
JSON reports and logs remain local and ignored. Native standalone PNG export
was not repeated for 0.3.65; the 0.3.64 result remains separate evidence.

The standard archive is `ClinicoPathPj_0.3.65.jmo`, SHA-256
`d5f10ffc0614cb69739fcac2e2e31470542b02b95290d30a3b4f2e373c9c4283`.
Other platforms, full baseline parity and clinical review remain open. Inactive
scores remain excluded from results.
