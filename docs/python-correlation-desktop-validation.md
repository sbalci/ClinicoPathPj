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
