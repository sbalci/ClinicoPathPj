# IHC dendrogram inspection — 0.3.14

Implemented 2026-10-27 in the existing Orange-inspired `pyihcheatmap` utility.
No new baseline target or analysis entry point is added. Clustering methods, numerical
defaults, missingness rules and clinical policy are unchanged.

## Behavior

Enable row and/or marker clustering, then **Dendrograms and merge inspection** under
Plots and Interaction. This new display option defaults off. The backend describes the
same average-linkage Euclidean linkage already used to order the heatmap; it does not
perform a second clustering or choose a distance cutoff.

Each axis has a native static Image tree. A shared native merge table records axis, merge
number, left/right child references, merge distance and member count. Leaf children use
source-row/marker identities; internal references use merge numbers scoped to that axis.
Leaf positions follow heatmap order. Labels are thinned above 25 leaves and shortened
above 80 characters in the native plot; full identities remain in tables/local descriptions.
Zero-distance merges remain zero. One retained row has no row-tree merges and an explicit
information notice. There is no imputation, hidden sampling, cluster significance or stability
estimate. Heights are average-linkage distances on displayed raw/z values, not p values.

Local branch click/focus/Enter/Space highlights member source rows or marker columns.
Row branches also highlight matching complete-pair scatter points; a row missing a scatter
coordinate stays highlighted in the heatmap. Marker branches highlight columns and clear
specimen-row selection. Repeated specimen IDs do not merge original row identities.
Clear highlights resets both. Highlighting never changes options, the analysis cohort,
clustering, native outputs, or saved selection columns. It resets on reopening/rerunning.

The new tree plot contract holds at most 199 merges (200 leaves), finite valid branch
geometry and optional leaf labels. Existing plot kinds and saved states are retained.
Generator result visibility now accepts either one Bool or a conjunction of two Bool
options. Tree visibility is bound to both the display and clustering options; there is no
data-driven hiding on failure. Compound forms outside that bounded grammar are rejected.

## Independent numerical and integration checks

- `tools/generate-ihc-tree-oracles.R` uses base-R `hclust(dist(), method='average')` and
  `cophenetic()` to produce six frozen raw/z-score references covering separated/tied/constant
  values and complete-row missingness. Python agrees on row/marker merge heights and every
  pairwise cophenetic distance (tolerance 1e-11), without assuming identical branch orientation.
- Python checks unchanged heatmap output with tree display enabled, preserved source identities
  and member counts, exact native branch coordinates, single-row and zero-distance trees,
  unclustered axes, and the maximum 200 × 20 matrix. The maximum-size HTML remains below
  the runtime's 1.5 MB limit; that is payload evidence, not maximum-size GUI acceptance.
- Full Python suite: **239 passed**. Final focused IHC/tree/generator checks: **42 passed**.
  The initial full run exposed an existing assertion on generator error-message wording;
  compatible wording was restored and the full suite rerun successfully.
- Focused native R: **178 assertions passed** (52 tree, 116 IHC, 10 renderer), with zero
  testthat failures, warnings or skips. Checks cover independent R fixtures, conjunction
  visibility, state restoration/rendering without the analysis dataset, disabled/pending
  clearing and valid recovery against fresh results. Visibility is checked at native
  initialization; direct private reruns check state, not cached visibility fields.
- Both offline jsdom harnesses pass: existing cell/scatter linking and new row/marker branch
  membership, keyboard events, clear, hostile literal annotations, and no backend refit.
  Native option dispatch/fetch throw if inspection calls them. This is not accessibility
  certification or a substitute for complete native keyboard testing.
- The compiler builds the new plot kind and visibility bindings. The final package is checked
  separately for ZIP integrity, source/template identity and 16 extracted runtime cases,
  including both dendrogram kinds and the merge table.

Process cleanup printed macOS `Operation not permitted` diagnostics during focused R runs.
The full R suite/process lifecycle was not rerun or qualified in this batch. Initial and
final logs plus standalone synthetic HTML are under `/private/tmp/cpj-ihc-dendrogram/`.

## Native desktop evidence

On macOS arm64 / jamovi 28.13, the 0.3.14 development package was installed through Sideload.
A separate synthetic validation copy was reopened in a fresh engine. Complete-row mode
retained 9 of 12 supplied rows; both clustering axes and tree inspection were enabled.
The native table showed eight row merges and two marker merges; both native tree images
and local SVG trees rendered in heatmap leaf order.

The row branch at distance 0.31483472295854814 highlighted exactly source rows 1 and 2
(the same S01 specimen annotation, distinct Center/Edge source rows) and their scatter points.
The ER/PR marker branch at distance 0.3358949371253355 highlighted those columns across the
retained rows and cleared specimen-point highlights. Native tree distances/outputs did not
change during local inspection. The native row tree exported through Image → Export → PNG;
the resulting image was decoded and visually inspected.

The saved validation copy was closed and reopened in another fresh engine. Its native merge
table, both tree images, heatmap/scatter and local tree controls restored. Independent
ZIP/protobuf inspection confirms both clustering options, tree display, z scaling,
complete-row handling and four embedded native PNG resources.

Artifacts under `validation-exports/`:

- `python-ihc-dendrogram-0.3.14-validation.omv`
- `python-ihc-dendrogram-0.3.14-native-row-tree.png`
- `python-ihc-dendrogram-0.3.14-saved-file.json`
- `python-ihc-dendrogram-0.3.14-package.json`

The final rebuild includes registry coverage text; GUI-tested calculation/UI/template/renderer
sources are unchanged. The installed candidate may retain earlier coverage metadata until
reinstalled. These checks do not complete full IHC heterogeneity parity or clinical review.

## Remaining gates

Complete native keyboard navigation, theme variants, maximum-size GUI behavior, native
marker-tree export, other architectures/operating systems and broader release qualification
remain pending. Saved row selections and cluster stability/significance are not implemented.
