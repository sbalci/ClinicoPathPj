# Migration foundation validation — 2026-10-25

This report concerns the 0.3.0 experimental foundation and the `py` naming correction.
It does not certify full parity for the 61 migration targets.

## Completed checks

- 166 Python tests passed using jamovi's bundled CPython, including frozen-baseline hashes,
  preservation of existing option/result contracts, registry routing, ordered factors,
  categorical summaries, plot geometry and PNG dimensions.
- The compiler built the organized tame interfaces and the standard
  `ClinicoPathPj_0.3.0.jmo` archive.
- Packaged-runtime smoke checks passed for all six existing core analyses.
- All 66 registry identities (61 targets and five utilities/examples) start with `py`.
  Planned targets do not become placeholder menu entries.
- The package was installed through jamovi's Sideload GUI into ClinicoPathPj. The installed
  manifest reports version 0.3.0 and contains 16 implemented, uniquely named analyses.
- jamovi was restarted; the server address and engine session changed. The pre-migration
  synthetic `.omv` reopened with the existing Python identifiers, including all three kappa
  analyses. The kappa power setting 0.8 -> 0.9 -> 0.8 recalculated N 241 -> 322 -> 241.
- `pyreportcat` ran through native variable controls in that fresh session and produced
  native summary/frequency tables and a Python plot. Native GUI PNG export succeeded:
  `validation-exports/pyreportcat-0.3.0-native-export.png`.
- The separate `validation-exports/python-migration-0.3.0-validation.omv` saved and reopened
  in another document session, retaining pyreportcat native tables and its plot resource.
- The final rebuilt archive passed its packaged-runtime checks and registry byte comparison.
  Its Python helper sources match the GUI-tested installation; registry status/documentation
  were refreshed after the GUI run.

## R suite and environment

The restricted-shell source-package run produced 419 passing expectations, zero warnings,
zero skips, and five errors from macOS denying `ps` process enumeration in cancellation/
child-process tests. Those failures are environmental and are not counted as passing.
The unrestricted installed-package rerun passed **425 expectations**, with zero failures,
warnings or skips (611.7 seconds). This includes the cancellation/child-process checks and
independent base R categorical fixtures.

## Remaining acceptance

Full advanced-method parity; all-analysis native lifecycle/export checks; saved-column and
Action workflow qualification; broader interactive views; additional macOS architectures;
and Windows/Linux support remain pending. See the generated status matrix.
