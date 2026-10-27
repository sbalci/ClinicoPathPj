# Applied selected IHC marker data — 0.3.16

Implemented 2026-10-27 in the existing Orange-inspired `pyihcheatmap` utility.
This extends the applied-selection workflow with a native selected-data table. It adds
no analysis entry point, baseline port, inference method or runtime dependency.

## Behavior

Enable **Saved source-row selection**, then **Applied selected marker values** under
Save Row Selection. The new option defaults off. After Apply, the native table lists one
record per applied retained source row and marker, in heatmap row/marker order. It includes
heatmap row position, original source-row ID, patient/specimen, group, region, marker,
raw measurement, displayed measurement and Observed/Missing status.

Displayed values reuse the heatmap's raw or within-marker sample-SD z values, calculated
on the entire retained cohort. They are never restandardized within selected rows.
Missing measurements remain missing. Unavailable/excluded source rows contribute no
records. Repeated specimen labels retain separate source IDs and annotations. There is
no aggregation, imputation, selected-group statistical summary or change to other outputs.

The existing snapshot guard applies. Empty/stale selections, disabled options and missing
required inputs clear the table. Inspection changes only the preview until Apply. Existing
200-retained-row and 20-marker limits bound this table to 4,000 records without sampling.
Native table copying/export is available through jamovi; a separate export-file workflow
was not qualified in this batch. The saved document's native HTML table was checked.

## Automated evidence

- **247 Python tests passed**, including four new selected-data checks. Independent fixed
  arithmetic verifies full-cohort z values. Coverage includes raw/z values, both cluster
  orders, partial/complete rows, repeated IDs, sparse source positions, constant markers,
  literal punctuation/annotation labels, missing cells, stale/empty/disabled/pending states
  and all 4,000 distinct source-row/marker pairs at the existing maximum size.
- **242 focused native R assertions passed**, with zero testthat failures, warnings or skips:
  43 selection (23 new), 31 single-quality, 52 trees and 116 IHC. Independent base-R `scale()`
  checks verify full-cohort values before and after complete-row exclusion. New checks also
  cover protobuf serialization, conjunction visibility, clearing/recovery and annotations.
- All three existing jsdom harnesses passed on current generated fixtures: linked cells/scatter,
  dendrogram inspection and explicit selection Apply. The HTML template was unchanged.
- Compiler build succeeded. ZIP/source/template checks and **16 packaged analysis smoke cases**
  passed, including an applied-selection rerun checking both raw/displayed table values,
  nominal flags and unchanged plots. Generator freshness and hand-source whitespace checks pass.

The first R invocation lacked jamovi's required `PYTHONHOME`; it was corrected and the
focused suite rerun successfully. Process cleanup still prints macOS `Operation not permitted`
diagnostics. The full R suite/process lifecycle is not qualified. Logs and standalone HTML
fixtures are under `/private/tmp/cpj-ihc-selected-values/`.

## Native desktop and saved-file evidence

On macOS arm64 / jamovi 28.13, the exact 0.3.16 package was installed through Sideload.
A separate synthetic validation copy retained the earlier applied rows 1 and 2 (both S01,
Center versus Edge), three markers, z scaling, complete rows, both trees and a linked scatter.
Enabling the new option produced six measurement records while the heatmap retained all
nine usable rows from twelve supplied rows.

Previewing branch rows 6 and 8 left the native table at rows 1 and 2. Explicit Apply changed
it to rows 6 and 8. Applying the original branch restored rows 1 and 2. After saving, closing
and reopening in a fresh engine, the table and option were restored. Disabling the new
option removed the table; re-enabling it reran Python and reconstructed all six measurements.
The final document was saved with the table enabled.

Independent ZIP/protobuf inspection verifies the six raw values against decoded integer
input columns and all displayed z values against Python `statistics.mean/stdev` on the nine
complete input rows (tolerance 1e-12). The two-selected/seven-unselected/three-missing nominal
flag is unchanged. ZIP integrity and the saved native HTML table pass.

- [Reopenable synthetic document](validation-exports/python-ihc-selected-values-0.3.16-validation.omv)
- [Independent saved-file checks](validation-exports/python-ihc-selected-values-0.3.16-saved-file.json)
- [Package smoke evidence](validation-exports/python-ihc-selected-values-0.3.16-package.json)

Maximum-size tests establish complete backend output, not maximum-size GUI acceptance.
Broader keyboard/theme/platform and separate export-file checks remain open. The known
post-Apply live option-field refresh limitation persists; native applied summaries remain
authoritative. This evidence is exploratory software qualification, not clinical validation
or release clearance. Julia remains deferred.
