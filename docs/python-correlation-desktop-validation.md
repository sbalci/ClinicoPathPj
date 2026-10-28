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
