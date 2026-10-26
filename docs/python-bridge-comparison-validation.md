# Bridge comparison lifecycle follow-up — 2026-10-26

## Native GUI evidence (installed 0.3.8; macOS arm64 / jamovi 28.13)

- Opened the saved `python-bridge-comparison-0.3.8-validation.omv` in a fresh jamovi
  session. The Pj execution choice and native cutoff 3 were restored. The native count
  table and local applied result agreed: TP=2, FP=1, FN=1, TN=2.
- Opened native options: cutoff 3 and Pj service / jamovi Python were visible.
- Changed native cutoff to 2: Pj recalculated TP=3, FP=2, FN=0, TN=1. Restored 3.
- Exported the native ROC Image through jamovi's image Export menu to
  `validation-exports/python-bridge-comparison-0.3.8-roc.png` (41,504 bytes).
  Visually inspected the PNG: ROC, chance line, applied point and axes are present.
- The saved fixture remains unchanged; subsequent synthetic exploration is not a new
  saved-file acceptance claim. Native Svg saved-analysis problems are a separate issue.

## Panel synchronization diagnosis

HTML `window.setOption` updates backend/native results and saved options, but the already
open options panel can retain its previous field value. The accessibility tree also retained stale values: an initial accessibility-only
check incorrectly suggested that panel reopening failed. A subsequent screenshot-based
check confirmed that closing options and clicking the analysis heading again refreshed
the visible native cutoff from 3 to 4 after Apply. Fresh file reopening also restored
the correct field value.

Read-only inspection of the installed jamovi client (`main-RVur5Zlb.js`) found the result
message handler calling analysis `setOptions(values)` while the options-resource listener
refreshes its frame only for an external-change flag. This supports a host synchronization
cause. We have not modified jamovi or claimed an upstream fix.

## 0.3.9 implementation

The comparison's native summary now reports the actual Python-applied rule without
rounding the cutoff to six significant digits, positive
reference level, complete-row count and exclusions. It also gives the verified close-panel/reselect-heading
workaround; the shared D3 and Observable analyses retain their existing behavior.
No statistical methods/defaults or calculation engine changed.

A focused Python regression failed against the former generic summary and passes with
these explicit fields. Menu/routing equivalence tests, native bridge lifecycle tests (15 assertions),
DOM preview/Apply isolation and packaged-runtime checks are tracked separately in this
turn's logs. The earlier 220-Python/633-R full-suite pass belongs to 0.3.8 and is not claimed
as a newly rerun full suite for this presentation-only change.

Remaining: host-side live panel synchronization, long-running Pj cancellation evaluation,
System interpreter and additional platforms. No release or clinical-validation clearance.

Final 0.3.9 checks: compiler build passed; four focused Python tests (including exact
cutoff text precision) passed; 15 focused R assertions passed without warnings/skips;
DOM Apply/preview checks passed; 15 extracted-package runtime cases passed. Generator,
status freshness and whitespace checks passed. Packaged source/template/registry bytes
matched the working source. The 0.3.9 package has not replaced the installed 0.3.8 GUI
build in this follow-up; new-summary GUI acceptance remains pending.
