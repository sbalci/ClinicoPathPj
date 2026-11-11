# Lin CCC in continuous measurement agreement

The 0.3.63 build adds **Lin concordance (CCC, point estimates only)** to the
existing `pyagreement` method selector under **MedDecide Py → Agreement**.
Bland–Altman remains the default; existing options and result identifiers are retained.
This increment follows the independently checked [CCC numerical engine](python-concordance-prototype.md).
It is included in the GUI-sideloaded `ClinicoPathPj_0.3.63.jmo`. The previous
0.3.62 archive is retained in `packages/archive/`.

## Data and interface

Select exactly two scalar numeric measurement columns **in the same units**.
Each row represents one independent case. At least **10 complete pairs** are
required, preserving the frozen meddecide 1.1.2 public CCC minimum. Up to 5,000
source rows are supported without display sampling. Missing measurements exclude
whole pairs; infinities, dates, categorical codes and ambiguous storage are refused.
The array engine's three-pair minimum remains limited to numerical fixtures.

An optional independent case-ID role accepts text or factor labels. Retained pairs
must have known, unique labels. IDs on excluded rows do not define the retained
cohort. Literal `NA`, leading zeros, factor ordering and original source-row IDs
are preserved. ID checks cannot prove independence; units are a user responsibility.

The UI groups method/model, uncertainty, results, plots and advanced controls.
For CCC, Bland–Altman coverage, CI confidence and ICC-model controls are disabled.
CCC has separate pair-table and plot checkboxes, both off by default; existing
Bland–Altman and ICC switches have no effect on CCC estimates.

## Native results

- **CCC Paired Observation Audit:** supplied rows, complete/excluded pairs, first-only,
  second-only and both-missing counts.
- **Concordance Point Estimates:** Lin CCC, Pearson precision and directly computed
  bias correction. Population moments use divisor **n**.
- **Complete Independent CCC Pairs:** optional original row ID, case label and both
  raw measurements. No generated data columns or automatic exclusions are written.
- **CCC Complete Measurement Pairs:** optional native Image rendered by the existing
  Python `points` renderer. Coordinates are the retained raw measurements without
  jitter, regression fitting or subsampling. Axis labels use the selected column names.

Identical constants yield undefined coefficients, shown as blank cells with explicit
notices. Unequal constants yield CCC = 0 and Cb = 0 with undefined Pearson precision.
Negative CCC is retained. **No CCC confidence intervals, p-values, clinical bands or
interchangeability verdict are available.** Pearson correlation alone does not measure
concordance. CCC depends on case mix and should accompany an assessment of differences.
Repeated cases, multirater pooling and inference remain omitted.

## Acceptance evidence

The original source numerical engine passed 436 independent base-R/DescTools
coefficient/audit comparisons. New integration tests use its frozen fixtures through
the real JSON runtime and native R bridge; test code also checks a hand-computed
10-pair example with CCC = 16.5 / 17.5. The native lifecycle test uses the same R6
instance for CCC → Bland–Altman → ICC → CCC, incomplete roles, a nine-pair refusal,
duplicate retained IDs, restoration and optional-output disabling.

The full source Python suite passes **489 tests** (211.081 seconds), including
seven new CCC integration tests; a final registry/UI freshness follow-up passes six
tests. Compiler preparation, documentation generation and isolated R installation
pass. The final consolidated native run passes **166 assertions** with no failures,
warnings or skips (57.6 seconds), including frozen references, lifecycle checks,
positional compatibility and a nonempty 800 × 600 raster rendered from serialized
plot state after removing the source dataset. A compatibility wrapper
preserves all original positional R arguments, including `showConsole`; new CCC
display arguments follow them.

See the [integration qualification record](validation-exports/python-concordance-integration-20261111.json)
for actual executed counts and logs. Native compiler/temporary-library evidence is
separate from GUI acceptance. The subsequent [0.3.63 package qualification](validation-exports/python-0.3.63-qualification-20261111.json)
records the build, GUI Sideload, installed-byte matching, fresh-engine rendering,
`.omv` save/reopen/Save As and native HTML export on macOS arm64. A subsequent
fresh-session single-click test passes live method switching, incomplete-role
clearing and recovery after reopen; the earlier unsuccessful interaction attempt
remains recorded. See the [live GUI follow-up](validation-exports/python-concordance-live-qualification-20261111.json). Other export formats,
platform qualification, CCC inference and clinical review remain open. The 61-analysis inventory
and partial/planned totals are unchanged.

## Synthetic example

Open [python_concordance_examples.csv](../data/python_concordance_examples.csv) in
jamovi with the 0.3.63 build. Choose `Method_A` and
`Method_B`, optional `Case`, and the CCC method. Enable source pairs and the CCC
measurement plot. The audit should show **15 supplied rows, 12 complete pairs,
three excluded rows, and one row in each missingness category**. These are
synthetic arbitrary-unit values, not clinical acceptance limits. Regenerate with
`python3 data-raw/create-python-concordance-examples.py`. The CSV is available now;
no Data Library entry is added before packaged GUI qualification.

## Editing a saved analysis

Single-click its result to open the existing analysis controls. In the tested fresh
session, changing CCC to Bland–Altman replaced the method-specific outputs; returning
to CCC restored all three coefficients and its plot. Removing `Method_B` from the
measurement role cleared every computed row, coefficient note and image while
showing the two-column requirement. Restoring it recovered the original 12 pairs
and coefficients. The regenerated result was saved and exported as
`python-concordance-0.3.63-live-recalculated.omv` and `.html`.

The earlier repeated/double-click session did not respond reliably. Jamovi's local
client source toggles analysis selection on a cover click, which supports using a
single click; it does not establish the cause of the earlier stall. No backend,
statistical, bridge or system-setting change was required for the successful retest.

The [uncertainty increment plan](python-concordance-uncertainty-plan.md) records
the frozen interval contract and required independent validation. Intervals remain
unavailable in 0.3.63.

The final 0.3.63 follow-up passes the full **489-test Python suite** (269.014 s)
and **4,573 installed-module R assertions** (571.1 s; no failures, warnings or
skips). Artifact checks cover all three saved fixtures and both HTML exports,
including matching retained rows, unchanged source bytes/metadata and identical
plot pixels. Four corrupted-artifact probes are rejected. After runtime imports,
all 1,431 non-cache installed files still match the archive; 15 bytecode-cache
members are excluded from this post-runtime comparison, five of which changed.
The original exact 1,446-file comparison immediately after installation remains
separate evidence.
