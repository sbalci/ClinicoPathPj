# System Python isolation — 0.3.61

The optional **Python Lab → Execution services → Python bridge comparison** analysis
retains its existing identifiers and default execution route. This increment repairs the
environment used when the Pj System Python route selects an external interpreter.

## Confirmed failures and correction

The inherited jamovi `PYTHONHOME` and `PYTHONPATH` caused an external Python 3.9.12 to
look for its standard library in jamovi's folders and fail with `No module named encodings`.
A diagnostic control clearing these variables only during System calls succeeded. Clearing
them for bundled calls failed, establishing why isolation must be specific to the route.

`R/utils-pj-service.R` now removes both variables during a System call and restores their
original populated, empty or unset state when the call exits, including errors and restart
conditions. This affects the calling R process for the duration of that synchronous call;
it does not change persistent settings, install packages, replace the selected interpreter
or change a statistical calculation. Custom `PYTHONPATH` locations are not used by this route;
required dependencies must be importable by the selected interpreter itself.

Native GUI discovery exposed another case: the System choice resolved to jamovi's own
bundled executable. Clearing its Python home then caused a bundled-interpreter startup
failure. On macOS the adapter now rejects this alias before launching Python, with guidance
to choose jamovi Python or configure an external interpreter on PATH before starting jamovi.
It does not silently select a different interpreter or edit PATH.

## Evidence and limits

- The pre-repair source fails the new environment assertions; the repaired source passes
  54 focused R assertions. These include exact restoration after success, failure and restart
  for populated/empty/unset values, unchanged bundled calls, and rejection of a symlinked
  bundled executable on System PATH.
- The final compiler build and 30 packaged runtime cases pass. The compiled bridge body
  matches the repaired source and passes all 54 focused assertions. Installed R bytecode
  is checked against the final archive.
- The compiled 0.3.61 adapter passes diagnostic-table agreement with bundled Python,
  checkpoint forwarding and recovery from a Python exception, without the diagnostic wrapper.
  The detected external setup is arm64 Python 3.9.12, NumPy 1.24.3 and SciPy 1.8.1. This
  qualifies that calculator probe only, not every analysis under those dependency versions.
- An empty-PATH probe reports an unavailable interpreter and preserves the environment.
- The native GUI initially reproduced the bundled-executable alias. Positive GUI System
  calculation, saved-file reopening and export remain unqualified unless a genuine external
  interpreter is discovered in that app session. API success is not GUI acceptance.
- The final package was installed through Sideload and jamovi restarted. In that fresh
  session, the System choice reports the actionable alias message; returning to Pj's bundled
  Python recalculates successfully. Separate error/recovery OMVs and a native HTML export
  preserve the six original rows. The two error snapshots contain no native PNGs; recovery
  restores TP=2/FP=1/FN=1/TN=2 at cutoff 4 and both native images. These snapshots do not
  qualify positive System calculations or reopening of a System-computed analysis.
- Bundled-Python children launched with `start_new_session=True` pass success, cancellation
  and timeout cleanup checks. The child confirms readiness; session IDs confirm separation;
  parent and child PIDs are absent after the service returns. A subsequent call succeeds.
  This covers one new-session design, not double-fork daemons, other interpreters, Flatpak
  or other platforms.

Developer probes: `tools/check-pj-system.R --adapter-only` tests the compiled CPJ adapter;
`--empty-path` checks unavailable discovery. The default probe deliberately tests the raw Pj
API with the inherited environment; `--clean-environment` is a diagnostic control, not a
required user action after this repair. `tools/check-pj-process-cleanup.R --new-session`
checks the separate-session design. Run these through jamovi's R executable as described
in [the service review](pj-service-review.md), with process inspection permitted for cleanup.

Earlier full-suite evidence (465 Python tests, 4,450 R assertions) belongs to 0.3.60.
The 0.3.61 focused, packaged and native evidence is recorded separately under
`docs/validation-exports/python-0.3.61-*` and `python-system-0.3.61-*`; the artifact checker
is `tools/check-pj-comparison-artifacts.py`. Full-suite 0.3.61 qualification remains pending.
The full 61-analysis
migration, other platforms, detailed deadline accounting and clinical qualification remain open.

## 0.3.62 source/API follow-up — 2026-11-10

The [source/API comparison](python-service-source-api.md) checks both execution
examples with bundled and existing external interpreters. Sixteen matched pairs
pass independent R summaries/counts/percentages and executable/dependency identity.
The external environment is Python 3.9.12/NumPy 1.24.3. Its existing dependency path
is explicitly supplied to this developer probe; no package is installed.
The fixed teaching entries still select bundled Python. This follow-up does not
qualify a System GUI route, external rendering or saved System-computed analyses,
and does not supersede the GUI discovery limitations recorded above.
