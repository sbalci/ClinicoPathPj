# Correlation matrix desktop qualification — 0.3.20

Date: 2026-10-27. Platform: macOS arm64, jamovi 28.13.

The local `ClinicoPathPj_0.3.20.jmo` was installed through Modules → Manage installed →
Sideload. Jamovi reported successful installation. The application was quit and restarted
before creating the analysis, so its Python/R namespace was fresh. The older synthetic IHC
window's unsaved changes were discarded under the user's prior authorization; its saved
fixture was preserved.

## Observations

1. Imported `data/python_correlation_examples.csv` (eight synthetic rows) and selected all
   four numeric columns under Stats Plots Py → Associations → Correlation matrix (core).
2. Default Pearson/listwise mode reported six common complete rows, six planned tests and
   three unavailable pairs involving the constant column. Native estimates and the local
   matrix rendered. Keyboard Return on Marker_A versus Marker_B displayed r=0.6085023853,
   n=6, excluded=2, CI −0.4011729082 to 0.9506148855, p=0.1999030790 and
   Holm-adjusted p=0.9995153949.
3. Pairwise missingness recalculated the per-pair sample sizes (including seven and eight
   observed rows where appropriate). Switching to Spearman produced the asymptotic-inference
   warning and disabled the Pearson interval control.
4. Saved a new OMV with Spearman/pairwise/Holm options. Exported the native Image result as
   PNG through its context menu. The exported image was visually inspected: valid diagonal
   cells, symmetric matrix, bounded legend and gray constant-variable cells were present.
   The native image follows the current global palette; the local inspector has its own
   documented fixed diverging palette.
5. Quit and relaunched jamovi, reopened the saved OMV in a second fresh engine, confirmed
   the restored options/results/inspector, and switched to Pearson. New Pearson estimates
   appeared after recalculation. That temporary rerun was not saved over the fixture.

## Artifacts

- [Saved Spearman/pairwise fixture](validation-exports/python-correlation-0.3.20-validation.omv)
- [Native PNG export](validation-exports/python-correlation-0.3.20-native.png)
- [Checks and artifact SHA-256 hashes](validation-exports/python-correlation-0.3.20-desktop.json)
- [Methods and separate numerical/package evidence](python-correlation-matrix.md)

The package was subsequently rebuilt to include the updated registry evidence; the
statistical and rendering source was unchanged. Archive/runtime integrity is checked again
for that rebuild. This desktop record covers one macOS configuration and these specific
interactions. It does not establish all-option accessibility, theme, cancellation, other
platform, full-baseline-parity or clinical qualification.

## Adjustment controls — 0.3.23 follow-up

The 0.3.23 module was installed through the GUI, jamovi restarted and the synthetic
0.3.22 fixture reopened. The native dropdown exposed all seven adjustment choices.
Hochberg, Hommel and BY each triggered a successful recalculation; native table values
and full-precision local details agreed with independent base-R `p.adjust()` values.
For Marker_C versus Marker_A (n=7, six planned tests), Hochberg/Hommel yielded
0.020157263008230647 and BY yielded 0.04938529437016508.

A new fixture saved Pearson/pairwise/BY options, preserving the older fixture. After a
second fresh-engine restart the new OMV restored BY and its matching result. Switching
to Hochberg then recalculated the expected value. That temporary rerun was not saved
over the BY fixture. This extends macOS control/lifecycle evidence; it does not extend
prior native export, full accessibility, other-platform or clinical evidence.

- [BY saved example](validation-exports/python-correlation-adjustments-0.3.23-validation.omv)
- [Desktop checks and file hash](validation-exports/python-correlation-adjustments-0.3.23-desktop.json)

The package is rebuilt with updated registry evidence and its extracted runtime checked
again; statistical, UI-control and rendering implementation sources are unchanged by
that evidence-only rebuild.

## Partial Pearson — 0.3.24 follow-up (2026-10-28)

Installed 0.3.24 through the GUI and restarted jamovi. The prior adjustment fixture
opened with its saved values. Enabling partial while pairwise missingness was selected
produced the stated requirement notice. Switching to a common cohort with Constant
retained produced unavailable estimates and the explicit constant-system reason.
Removing Constant recovered valid partial estimates without restarting the analysis.

Marker_C versus Marker_B, controlling Marker_A, reported n=6, two exclusions, one
control, df=3, r=0.6836774085481553, p=0.203125888572847 and BY-adjusted p=
0.3723974623835528. An independent base-R residual-regression check agreed. Native
columns and local inspection showed the same control/df context.

Saved a separate partial/listwise/BY OMV and exported the native matrix as PNG, then
visually inspected the image. A second fresh-engine restart/reopen restored settings
and estimates. Switching to zero-order and back recalculated the same partial result.
The original fixture was preserved. This evidence covers one macOS arm64 configuration,
not full method parity, all accessibility/theme combinations, other platforms or clinical use.

- [Saved partial example](validation-exports/python-correlation-partial-0.3.24-validation.omv)
- [Native PNG](validation-exports/python-correlation-partial-0.3.24-native.png)
- [Checks and hashes](validation-exports/python-correlation-partial-0.3.24-desktop.json)

The evidence-only registry update is rebuilt and its extracted runtime rechecked;
statistical, interface and rendering implementation sources are unchanged.

## Partial Spearman — 0.3.25 follow-up (2026-10-28)

Loaded 0.3.25 through the GUI in a fresh jamovi engine. Imported the new synthetic
`data/python_partial_spearman_examples.csv`, which contains ties in both marker columns.
A new analysis retained Pearson/nonpartial/Holm defaults. With partial correlations and
Spearman selected, the native table and local inspector showed r=0.1601592641029555,
n=6, no exclusions, one control, df=3, approximate p=0.7969540733546534 and Holm
adjusted p=1 for Marker_A versus Marker_B controlling Control_Z. The independent R
ranked-residual fixture agrees. The Pearson interval control was disabled and interval
cells remained unavailable.

Saved a new partial/Spearman/listwise/Holm OMV and exported its native image as PNG.
The PNG was visually inspected. A second fresh-engine restart/reopen restored settings
and results. Toggling to zero-order and back reproduced the partial result. The original
0.3.24 fixture and PNG hashes remained unchanged. One export attempt opened the whole
results export panel; it was cancelled and the image-specific PNG route completed.

- [Saved tied example](validation-exports/python-correlation-partial-spearman-0.3.25-validation.omv)
- [Native PNG](validation-exports/python-correlation-partial-spearman-0.3.25-native.png)
- [Checks and hashes](validation-exports/python-correlation-partial-spearman-0.3.25-desktop.json)

This is one macOS arm64 / jamovi 28.13 configuration, not broad accessibility, theme,
other-platform, full-baseline-parity or clinical qualification. The evidence-only registry
update is rebuilt and the packaged runtime rechecked; the statistical implementation
is unchanged by this follow-up.

## Grouped correlations — 0.3.26 follow-up (2026-10-28)

Installed 0.3.26 through the GUI and restarted jamovi. Reopened the 0.3.25 saved
partial Spearman example and recalculated: the new All rows cohort appeared and the
same r=0.1601592641029555, p=0.7969540733546534, one control and df=3 were preserved.
That original fixture was not overwritten; its OMV and PNG hashes remained unchanged.

In another clean engine, imported `data/python_grouped_correlation_examples.csv`,
selected Marker_A/B/C and Group as Split By. Native results counted thirteen input rows,
one missing group and two observed groups. Group_A had 6 input/6 common rows; Group_B
had 6 input/5 common rows. Group_A partial Spearman matched the earlier R reference;
Group_B's constant adjustment system remained unavailable. Unchecking partial recovered
Group_B's valid zero-order Marker_A/B result (n=5, excluded=1, df=3, r approximately −1).
Constant-marker pairs remained unavailable with their explicit reason.

Local switching cleared prior details and left the native summary unchanged. Keyboard
navigation remembered a different position per group; returning to Group_B and pressing
Tab restored its previously inspected Marker_B/C cell. The saved example retains
Spearman, listwise, Holm and partial=False. Local group choice/focus is transient.

Saved the new grouped OMV and exported the native image as PNG. Visual inspection
confirmed both matrices, group-prefixed row labels and unavailable gray cells. A fresh
engine reopened the grouped roles/settings/results, and partial then zero-order reruns
reproduced Group_B's result. The tests cover one two-group macOS arm64 / jamovi 28.13
configuration, not exhaustive maximum-size/theme/accessibility/other-platform or clinical
qualification. No between-group difference inference is supplied.

- [Saved grouped example](validation-exports/python-correlation-groups-0.3.26-validation.omv)
- [Native stacked PNG](validation-exports/python-correlation-groups-0.3.26-native.png)
- [Desktop checks and hashes](validation-exports/python-correlation-groups-0.3.26-desktop.json)

The registry evidence update is rebuilt and its extracted runtime rechecked; statistical
and interface implementation sources are unchanged in this follow-up.
