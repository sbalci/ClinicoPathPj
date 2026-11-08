# Native SVG experiment validation — 0.3.7

Recorded 2026-10-26 with jamovi 28.13 on macOS arm64. The prototype's interaction and
current-view exports pass the checks below. **Native OMV saving with the Svg result
remains unresolved, so save/reopen and release acceptance are not complete.**

## Word page rendering and LaTeX follow-up — 2026-11-07

**Later session-close observation:** during the 0.3.59 ICC tests, the disposable
SVG session was closed normally and its unsaved synthetic changes discarded.
Closing finalized the stalled export as a 22-byte ZIP with no members. The
original zero-byte/Saving observations below remain valid for the open session;
the finalized empty archive still contains no TeX source or figures and does not
qualify as successful export. The regression now rejects both states. See the
post-session-close field in the follow-up evidence JSON.

Opened the recorded `python-svg-28.17-confirmed-preview3.docx` in Microsoft Word
**16.114.4** on macOS arm64. All three pages were visually inspected in whole-page
view: the explorer image, preview/native labels, classification and accuracy
tables, static dotplot, static ROC and references are present. No JavaScript
source or clipped figures were observed. The file was not edited or saved, and
its bytes still pass the recorded artifact check. This closes the previously
untested Word page-rendering gate for this synthetic example and this local
Word build only. It is not a cross-platform Word qualification.

Native jamovi **28.17** File → Export → LaTeX bundle was attempted with the same
open analysis. The UI continued to display `Saving` across repeated observations
over several minutes; `python-svg-28.17-latex.zip` remained zero bytes. Escape
dismissed the file panel but the Saving indicator remained. No successful export
notification was observed. The pending export and unsaved synthetic analysis
were left in jamovi; the application was not force-quit.

The [LaTeX check result](validation-exports/python-svg-28.17-latex-artifacts.json)
correctly rejects this empty destination. There are no bundle members, TeX source
or figures to compile; `pdflatex` is installed, but compilation was not attempted
against an invalid bundle. The cause of the stalled export was not established.
This is separate from the already reproduced native `.omv` Save As exception.

For future three-figure exports, run:

```sh
python3 tools/check-svg-artifacts.py --latex /path/export.zip
```

The tool checks ordinary, active `includegraphics` references and at least three
distinct nonempty figure files (the explorer plus two static counterparts). It
rejects empty ZIPs, missing figures, duplicate references to one image, commented
references and unsupported dynamic/external paths. It does not evaluate TeX
macros, compile the document or establish figure identity/visual correctness.
Five additional regression tests cover these cases; all twenty focused artifact
and host-preflight tests pass in bundled Python.

See the [follow-up evidence](validation-exports/python-svg-28.17-export-followup.json).
PDF/ODT, native SVG save/reopen, LaTeX completion/compilation and additional
platforms remain open gates. Keep native Svg experimental.

## Native macOS follow-up — jamovi 28.17, 2026-11-07

The application changed between sessions: the new GUI run and bundle metadata
both identify **28.17.0.0** on macOS arm64. The earlier 28.13 record below remains
historical evidence. ClinicoPathPj's existing `pysvgcutoff` was tested with the
six-row data-only control, Measurement/Reference, event level Positive,
rule ≥ and native cutoff 2. Native counts were TP 3, FP 2, FN 0, TN 1.

**Save As failed**, displaying the exact message
`'DataSetModel' object has no attribute 'instance_path'`.
The separate destination `python-svg-28.17-preview3.omv` was not created.
No existing OMV was overwritten. The read-only
[28.17 preflight](validation-exports/python-svg-host-28.17-2026-11-07.json)
also identifies the same installed snapshot-path signature at line 428.
This is now a direct local reproduction of the reported exception, rather than
only an observation that saving did not update a file. The synthetic analysis is
left open and unsaved; neither fresh-engine reopening nor snapshot persistence
can pass from this run.

**Native Word export completed.** After explicitly confirming numeric preview 3
in the rendered SVG, File → Export → Word Document produced
[the DOCX](validation-exports/python-svg-28.17-confirmed-preview3.docx).
Its three image relationships resolve to embedded PNGs. The
[extracted explorer image](validation-exports/python-svg-28.17-preview3-embedded.png)
was decoded and visually inspected: dotplot, linked ROC, axes, numeric field and
count labels are present, with native rule 2, preview 3 and local snapshot 2.
The preview counts are TP 2, FP 1, FN 1, TN 2. The DOCX's native classification
table retains TP 3, FP 2, FN 0, TN 1, and its applied-rule text remains cutoff 2.
This confirms that the transient preview and native calculation are distinct.

`python3 tools/check-svg-artifacts.py --word-example` checks that table and rule
text, resolves the inspected PNG by its recorded hash, and compares its bytes
with the extracted image. A limited scan found none of the listed JavaScript
markers in document text; it is not a general detector for arbitrary code.
The initial export before explicit preview confirmation is retained separately
as `python-svg-28.17-initial.docx` and is not used for preview-3 qualification.

At this stage the run verified native DOCX export and the embedded plot's appearance,
but had not yet opened the document in Word; see the later page-rendering follow-up above. PDF/ODT and
LaTeX exports were not tested in this run. See the
[separate evidence record](validation-exports/python-svg-28.17-desktop-checks.json)
and [reproducible artifact checks](validation-exports/python-svg-28.17-word-artifacts.json).

Continue to retain HTML interaction and native Image alternatives while the
host's Svg save path fails; native SVG remains experimental.

## Follow-up — 2026-11-07: host source preflight

In the earlier source-preflight check, the installed application was jamovi
**28.13.0.0**. The read-only
`python3 tools/check-svg-host.py` preflight identifies the known snapshot-path
mismatch at `Analysis.set_svg()` line 428: `self.dataset.instance_path`.
The installed `Analysis.dataset` returns `project.get_dataset()`, and the
installed `DataSetModel` declares neither `instance_path` nor a dynamic accessor;
`Project` provides that property. The app was not modified.
The evidence is [machine-readable](validation-exports/python-svg-host-2026-11-07.json).
Exit 2 means this known source signature is present; exit 0 only means the
signature is absent, **not** that saving or export has passed. Four focused
preflight tests cover the mismatch, changed path, compatible accessor/inheritance
and unrecognized source. This is a source check, not a fresh desktop reproduction
or an execution of jamovi's full save path.

Upstream was checked through GitHub on 2026-11-07:

- [#1907](https://github.com/jamovi/jamovi/issues/1907) is closed as completed.
  Its [timeline](https://api.github.com/repos/jamovi/jamovi/issues/1907/timeline)
  records closure by the reporter without a linked commit. The
  [main analysis source](https://github.com/jamovi/jamovi/blob/main/server/jamovi/server/analyses/analysis.py)
  retrieved during this check still uses `self.dataset.instance_path`. No fix
  commit or released build containing a correction was identified. Closure alone
  must not be interpreted as a verified fix. This qualifies the earlier reply's
  suggestion of testing a build containing the fix: such a build is not yet established.
- [#1902](https://github.com/jamovi/jamovi/issues/1902) remains open. Its reporter
  describes successful DOCX/PDF/ODT export and failing LaTeX export on their
  Windows/Linux installations. These are external observations, not our macOS
  qualification evidence.

Keep `pysvgcutoff` experimental and retain the HTML alternatives plus native
static Images. Those alternatives do not repair saving an existing document
that still contains an affected Svg result. There is no verified workaround for
that document here. No host monkey patch or automatic renderer conversion is shipped.

When a candidate corrected host is available, record its version/build and source
preflight, then use disposable synthetic data to qualify these gates separately:

1. Data-only Save, then populated Svg Save and Save As to distinct paths; verify
   ZIP integrity, analysis presence and nonempty SVG snapshot resources.
2. Quit/restart, reopen both files in a fresh engine, recalculate and verify
   native results, interactive reconstruction and option changes.
3. Distinguish saved native cutoff, transient preview and displayed snapshot in
   all persistence assertions; `Apply to SVG snapshot` remains local.
4. Export current-view SVG/PNG and verify dimensions, visible labels and contents.
5. Export DOCX/PDF/ODT; inspect embedded media and rendered documents for a plot
   rather than JavaScript source. Verify source counts remain unchanged.
6. Export LaTeX bundle separately; check nonempty figure files, active references,
   compilation and rendered figures, with bounded completion/failure reporting.
7. Qualify missing-module snapshot viewing separately on an isolated profile;
   record each OS/architecture rather than extrapolating across platforms.

The previous 0.3.7 GUI evidence below is preserved as historical evidence.

## Executable artifact checks — 2026-11-07

`tools/check-svg-artifacts.py` now implements read-only structural checks for
saved OMV snapshots and DOCX media. It neither launches jamovi/Word nor executes
JavaScript, LaTeX or archive content. It reads bounded archive members without
extracting them. Run the existing evidence check:

```sh
python3 tools/check-svg-artifacts.py --historical
```

The [recorded result](validation-exports/python-svg-artifacts-2026-11-07.json)
confirms the historical SVG/PNG dimensions and the distinct native rule 2,
preview 3 and local snapshot 3 labels. Both historical data-only OMVs are rejected
as saved SVG analyses, including the misleadingly named `validation.omv`.
No new desktop save success is asserted.

For a future GUI session, save the data-only baseline before adding the analysis,
then Save/Save As and fresh-engine-reopen copies of exactly that synthetic data:

```sh
python3 tools/check-svg-artifacts.py --baseline /path/data-only.omv \
  --omv /path/saved.omv --omv /path/save-as.omv --omv /path/reopened.omv
python3 tools/check-svg-artifacts.py --docx /path/export.docx
```

OMV checks require unchanged data bytes, field metadata and labels, exactly one
`pysvgcutoff` analysis, and a nonempty SVG snapshot referenced by its saved record.
They do not decode analysis options/statistics or establish a fresh engine rerun.
DOCX checks resolve embedded drawing relationships to nonempty PNG/SVG media;
they reject external/missing media. They do not establish which plot was embedded,
whether JavaScript text leaked elsewhere, or how Word rendered the document.
PNG checks cover its header/dimensions, not pixel decoding. These remaining checks
must be recorded independently, alongside native results and visual inspection.
PDF/ODT and LaTeX qualification remain pending; no structural tool result closes
those gates. Ten focused artifact tests use explicitly synthetic archives for
positive and malformed cases; those archives are not native GUI evidence.

## Numerical, compiler and integration evidence

- Full bundled-Python suite: **217 tests passed**.
- Full installed-package R suite: **619 expectations passed**, zero failures/warnings/skips.
- Final focused checks after layout/initialization changes: **6 Python tests and
  20 installed-package R expectations passed**, including early script registration.
- All **24 entry points** compile; generator and migration-status freshness checks pass.
- All **14 packaged runtime cases** pass, including Svg transport and local-script integrity.
- Python comparisons cover both inequality directions, both interval methods and all
  three optimization criteria. Native tables/static plots equal the existing D3 entry
  point, through the same independently tested Python engine.
- Checks include ties, automatic/endpoint rules, missing pairs, undefined proportions,
  the 1,000-row payload, invalid settings and markup-bearing variable names.
- R compares five exact proportion intervals with independent `binom.test()` references,
  serializes Svg results, clears incomplete input and recovers after invalid settings.

The DOM harness loads the asset before inserting content, matching native jamovi's
ordering. It verifies linked numeric, window-captured drag and keyboard/ROC controls,
lookup boundaries, local snapshot labels, reset, invalid input and serialized drawing
content. Pointer geometry is stubbed only in that harness; native dragging was also
checked directly. The runtime payload is removed from the displayed SVG after parsing,
so image exports omit the full threshold lookup.

The first full run exposed two test-harness mistakes: the expected utility count needed
to increase from seven to eight, and a nested R6 assignment was invalid for that target.
Both were corrected before the passing full run. A focused runner also needed the
engine-like Python environment and explicit protobuf initialization; its final run passes.

## Native GUI interaction and export

Installed the standard `ClinicoPathPj_0.3.7.jmo` into the existing module using the GUI.
Fresh engines were used after bridge/asset changes; installed helper and JavaScript
bytes match the final source. Previous entry points and original saved comparisons are
retained.

The larger 180-row shared fixture gives TP 47, FP 10, FN 8, TN 115 at native cutoff 2.
Its numeric preview at 3 gives TP 30, FP 0, FN 25, TN 125 without changing native tables.

Final qualification uses `data/python_svg_cutoff_examples.csv` with six rows and a tie at 2:

- Native cutoff 2: TP 3, FP 2, FN 0, TN 1.
- Numeric preview 3: TP 2, FP 1, FN 1, TN 2; native rule remains 2.
- Dragging to about 4.055 changes the line, number and ROC point together:
  TP 2, FP 0, FN 1, TN 3.
- With the line focused, End selects the upper display endpoint 6.4:
  TP 0, FP 0, FN 3, TN 3.
- Clicking a ROC point selects its precomputed cutoff. Apply at preview 3 updates only
  the local snapshot label to TP 2, FP 1, FN 1, TN 2.

The final exports were made through the native Image → Export menu:

- [SVG preview](validation-exports/python-svg-cutoff-0.3.7-preview.svg): valid XML,
  980 × 720, saved native rule 2 and current preview/local snapshot 3; no runtime payload.
- [PNG preview](validation-exports/python-svg-cutoff-0.3.7-preview.png): 3136 × 2342,
  decoded and visually inspected with full axes, white background, controls and labels.

Earlier GUI attempts exposed inline layout, script timing, result-selection drag
interference and export styles depending on an HTML ancestor. These are corrected by
registering assets in `.init()`, initializing inserted roots once, handling dragging at
the window capture phase and emitting one self-contained SVG with scoped styles and
embedded controls. The earlier clipped/black PNG attempt is not the linked final export.

## Save/reopen gate remains open

A clean six-row dataset with no analysis saves successfully. The explicit
`python-svg-cutoff-0.3.7-data-only-control.omv` control is 2039 bytes and contains no
analysis; **it is not a saved-analysis example**. The similarly named validation OMV
is the same data-only control and must not be presented as evidence of Svg persistence.

After adding Svg, native Save/Save As (including the macOS Save dialog) did not update
the OMV with the analysis in the tested sessions. This occurred in the larger comparison
and the isolated six-row document. The cause is not established; numerical/R serialization
and current-view SVG/PNG export passing do not establish ordinary file-save compatibility.
Final analysis save/reopen and missing-module snapshot viewing therefore remain unverified.

An automatic approval review initially blocked discarding the unsaved synthetic window.
The user explicitly authorized discarding it, and testing continued in fresh engines.
That approval is resolved and is not the remaining save/reopen limitation.

The final evidence-only rebuild changes registry metadata, not the GUI-tested statistical,
bridge, renderer or JavaScript implementation. Additional architectures/platforms,
large native previews, exhaustive cancellation and clinical review remain outside this
qualification. See [methods and comparison](python-svg-cutoff.md).
