# ClinicoPathPj implementation plan — revised 2026-10-28

This is the current delivery plan. It supersedes the implementation recommendations in
`python-roadmap.md` (2026-10-18) and the initial `interactive-analysis-plan.md`.
The original 61-analysis inventory remains the target; a menu entry does not establish parity.
Detailed per-analysis evidence remains in the [generated status matrix](python-migration-status.md).

## Reassessment after parallel-session changes — 2026-10-27

Reviewed clean starting HEAD `5b46301` (0.3.18), source/registry, TODO and dated IHC
validation records. Work from the other session is retained. The entries below distinguish
recorded earlier evidence from checks newly run for 0.3.19; no earlier GUI result is silently
credited to a new build. At that reviewed HEAD the baseline had 16 partial ports, 45 planned and
zero full-parity releases, with 26 implementation entries including utilities. The 0.3.20
correlation core below now advances one planned baseline target to partial implementation.

| Area | Current implementation | Remaining work |
|---|---|---|
| Annotated IHC core | Raw/z scales, missingness, original rows, annotations, clustering, static export | Larger native GUI payloads, themes and additional platforms |
| Linked marker scatter | Native pair roles, complete-pair tables/static plot, local pair switching and row linking (0.3.12–0.3.13) | Broader assistive-technology/platform checks |
| Dendrograms | Independent R fixtures, native merge/static trees and local member inspection (0.3.14) | Full tree keyboard workflow and marker-tree export qualification |
| Applied selections | Snapshot guard, explicit Apply, native summaries and row-aligned dataset flag (0.3.15) | Broader lifecycle/platform/assistive-technology evidence |
| Selected data | Native raw/displayed marker table retaining full-cohort scaling (0.3.16) | Large-output native GUI qualification |
| Rectangle previews | Inclusive numeric/pointer preview, ties/missing pairs and explicit Apply (0.3.17) | Broader touch/theme/platform checks |
| Matrix keyboard focus | One remembered Tab stop, directional/endpoints, preserved activation (0.3.18) | Screen-reader certification is not established |
| Scatter keyboard focus | 0.3.19 adds one remembered complete-pair Tab stop, row-order arrows and endpoints | New-build native keyboard/save/reopen/export qualification remains separate |

The original “start heatmap” milestone is complete as an exploratory utility. Repeating
linked scatter, dendrogram or saved-selection implementation would duplicate work already
present. The next numerical Orange-inspired analysis is now implemented as the partial
`pyjjcorrmat` core in 0.3.20: explicit pairwise/common-cohort rules, pair-specific n,
multiplicity controls and independent R references, with macOS desktop lifecycle evidence.
Raw-row linking remains a proposed extension, not an implemented correlation feature.
Continue with the remaining IHC/scatter accessibility gates and correlation baseline gaps
listed below; broader platform and clinical qualification remain separate.

Keep the Pj comparison available as an optional experiment; retain processx as default.
The known host cutoff-field refresh limitation and planned future jamovi/Julia backends
are not reasons to block these independent IHC presentation improvements. Deferred molecular
scoring/enrichment and model-evaluation pipelines remain outside this keyboard milestone.

## What changes after the jamovi discussion

| Feedback | Decision | Current position |
|---|---|---|
| Jonathon: dragging and linked plots run in client JavaScript; Python is not required for interaction | Evaluate statistical engines separately from presentation. Use JavaScript for display interaction; justify Python by numerical capability, reuse or teaching | Shared Python cutoff engine already feeds separate HTML/D3, Observable and native Svg experiments |
| Jonathon: consider the native Svg result element | Prefer testing native export/snapshot behavior before choosing a production interactive renderer | `pysvgcutoff` interaction and current-view SVG/PNG export verified; saved-analysis `.omv` lifecycle remains unresolved on jamovi 28.13 |
| Maurizio: Pj 1.3.0 provides a public service without an editor | Add an optional adapter behind the existing result contract and compare identical computation workloads | `pybridgecompare` implemented; default processx retained; optional public Pj API v1 routes |
| Maurizio: processx gives finer lifecycle control than current Pj `system2()` | Retain checkpoints, cancellation and cleanup as acceptance requirements; document route differences | Processx regression checks pass; Pj call is synchronous with no checkpoint callback while running |
| Jonathon: a Python engine calling R through rpy2 is planned | Isolate transport behind adapters, preserving registry identities and numerical oracles | Future integration is a watch item based on the supplied discussion, not an available API, release promise or implemented dependency |

The original all-Python statistical migration remains the research target. It does not
require rewriting already reliable R calculations just to obtain interactive graphics.
A hybrid R/Python/JavaScript experiment can inform the design, but must be labelled separately
and does not count as a completed Python port. Existing production R modules remain intact.
Do not add rpy2 or replace the current bridge based on an announced future engine.

## Verified current inventory

There are **30 registered implementation entry points**: **20 partial baseline ports** and
**10 utility/demonstration analyses**. Of the 61 baseline targets, **41 are planned**,
**0 have complete supported-feature parity and all release gates**.

| Family | Baseline targets | Partial ports | Planned |
|---|---:|---:|---:|
| ClinicoPathDescriptives | 14 | 11 | 3 |
| jjstatsplot | 19 | 1 | 18 |
| meddecide | 15 | 8 | 7 |
| jsurvival | 9 | 0 | 9 |
| OncoPath | 4 | 0 | 4 |

Partial descriptives: `pyagepyramid`, `pybenford`, `pycategorize`, `pycheckdata`,
`pychisqposttest`, `pydataquality`, `pyreportcat`, `pysummarydata`, `pyvenn` (exact-count core),
`pyoutlierdetection` (univariate screening core), and `pyvartree` (categorical count-tree core).

Partial statistical plots: `pyjjcorrmat` (Pearson/Spearman core only).

Partial medical decisions: `pycotest`, `pydecision`, `pydecisioncalculator`,
`pydecisioncurve`, `pykappaci`, `pykappafixedn`, `pykappapower`, `pysequentialtests`.

Utilities/demonstrations: `pydescriptives`, `pywelch`, `pyexacttests`, `pyruntime`,
`pydotdecision`, `pyd3cutoff`, `pyobservablecutoff`, `pysvgcutoff`, `pybridgecompare`, `pyihcheatmap`.
For example, `pywelch` does not establish full `pyjjbetweenstats` parity.

## Implemented foundation

- One ClinicoPathPj namespace and standard versioned JMO filename; stable `py…` identifiers,
  including existing kappa identifiers. Source paths are independent of public IDs.
- Authoritative registry with frozen-source provenance, supported feature/omission records,
  dependency and validation fields; five family source folders and shared engines.
- Literal SPEC options/results/UI generation; organized tame interfaces; binding checks,
  Terms/Output/Action schema support. Analysis-specific Action delivery is not universally qualified.
- Versioned result mapping, native tables/notices, original-row and factor metadata transport,
  row-aligned saved outputs, and Python static rendering through the native Image bridge.
- Default isolated processx execution, checkpoints and cleanup. Reviewed bundled resources
  are local; the qualified scientific environment is currently macOS arm64 CPython 3.11.
- Compact registry-driven groups: **Descriptives Py**, **Stats Plots Py**, **MedDecide Py**,
  **Python Lab**, with topic subgroups. Survival Py/OncoPath Py remain reserved until ports exist.
- Separate local D3, Observable and Svg experiments, each clearly distinguishing preview
  from persisted analysis options. No silent refit from hover, highlighting or initial render.

## Work currently under way

### 1. Finish the execution-service comparison acceptance

Implemented in 0.3.8: public Pj adapter; processx/bundled-Pj/System-Pj route selector;
identical cutoff calculations; native results and elapsed time; explicit native cutoff Apply.
Pj is optional; existing analyses retain the default bridge. JSON transport preserves the host
factor/row contract. Native static images use the existing renderer on either computation route.

Evidence already obtained:

- 220 Python tests and 633 R assertions pass; zero R warnings/skips.
- Twelve matched bundled-interpreter configurations agree on counts, estimates, intervals
  and ROC summaries; independent R counts and exact `binom.test()` intervals agree.
- Ties, missing pairs, row IDs, malformed result envelopes and recovery checks pass.
- Packaged runtime smoke checks pass for 15 cases. DOM checks verify preview isolation,
  explicit cutoff dispatch and no backend call on render/reset.
- Both modules installed through the GUI, followed by a fresh jamovi session. Family menus,
  comparison controls, processx/Pj runs and preview-to-native Apply were exercised.
- A new `.omv` contains `pybridgecompare`, saved `execution="pj"`, `cutoff="3"`, results
  and native PNG resources. Saved-file existence is not fresh-engine reopening evidence.

Fresh-engine `.omv` reopen/recalculation and native ROC PNG export subsequently passed
on the installed 0.3.8 build; see [lifecycle evidence](python-bridge-comparison-validation.md).
The 0.3.9 summary explicitly reports the applied rule and cohort counts. A screenshot-based check confirms that closing the options panel
and reselecting the analysis heading refreshes its cutoff field.

Remaining: live native-field synchronization,
long-running cancellation/error lifecycle comparison, repeatable latency measurements at
matched payload sizes and optional-System qualification. The native options panel displayed
its prior cutoff immediately after HTML Apply although saved/backend state was 3; qualify
panel synchronization before calling the complete Apply workflow ready for release.

The upstream macOS Python-location tests passed. The full upstream API script encountered
`ModuleNotFoundError: colorsys`; keep that failure visible and localize the affected route.
Do not report it as a Pj-wide failure: the CPJ bundled-service comparison passed separately.
Do not infer a processx-versus-system2 speed advantage from whole-route timings.

### 2. Choose renderers after lifecycle testing

| Renderer | Implemented | Next gate |
|---|---|---|
| HTML diagnostic dotplot | Native option Apply and shared Python results | Preserve existing behavior and exported static counterpart |
| D3 explorer | Linked dotplot/ROC, local numeric/drag interaction, HTML-only Apply | Larger payload/accessibility/platform checks |
| Observable Plot/Inputs | Local linked exploration and teaching comparison | Gather user feedback and larger-payload/platform checks |
| Native Svg | Numeric/drag/keyboard/ROC and current-view SVG/PNG export | Resolve saved-analysis lifecycle before promoting it |
| New service comparison | Same engine via either route, explicit native Apply; 0.3.8 fresh-engine reopen/recalculation and native ROC PNG export verified | Live option-panel synchronization, long-running lifecycle and additional platforms |

Use local pinned assets, keyboard controls, accessible colors and bounded payloads.
Display filtering must disclose aggregation/sampling and must not alter inference silently.
HTML graphics need a native static counterpart; browser-only exports do not replace native
saved-analysis/export qualification. No renderer is selected universally for all families yet.

### 3. Close gaps in existing ports before enlarging the catalog

Prioritize GUI/saved-output/export gaps for the 20 partial ports, then remaining frozen-baseline
features and independent numerical agreement. Record implemented, independently validated,
GUI-verified and release-ready status separately. Core accuracy or Benford calculations do not
establish full umbrella feature parity. Keep statistical defaults and clinical rules unchanged.

## Web-informed candidates and revised implementation priorities

Reviewed the four requested galleries/book repository and primary Python-library documentation.
See [the researched candidate matrix](python-analysis-opportunities.md) for clinicopathological
use cases, source links, engine choices, target mappings, interaction and validation gates.
These are proposed additions/views, not newly implemented analyses; the 61-target denominator
and current completion counts are unchanged.

After existing acceptance gaps, prioritize shared **distribution/estimation plots**, **biomarker
correlation/heatmap views**, **exact set/flow calculations**, and selected **diagnostic threshold
and calibration features**. Reuse the existing NumPy/SciPy/Matplotlib pipeline first.
Paired trajectories, continuous agreement and linked patient response views follow their
subject/design specifications. Statsmodels, Pingouin, lifelines and scikit-survival are
candidate dependencies requiring offline packaging and independent validation, not approved
or already qualified runtime requirements.

Add explicit feasibility gates: tied-time behavior in competing risks (lifelines documents
jitter), model/CI conventions in ICC and mixed/ordinal/GEE analyses, leakage-free calibration,
and conventional versus bivariate diagnostic meta-analysis. Do not choose engines from chart
appearance or assume gallery/book code supplies baseline feature parity. Older D3 gallery
examples need adaptation to the pinned modern API.

PCA/cluster exploration, laboratory QC and conventional evidence synthesis are useful optional
extensions outside the frozen inventory. Keep them in a separate backlog; assign stable `py…`
identifiers through the registry only when their scope is specified for implementation.

## Orange BioLab-inspired workstream

The [Orange widget catalog](https://orangedatamining.com/widget-catalog/) provides useful
workflow/interface references. These are our ClinicoPath adaptations, not copied widgets
or evidence of numerical equivalence. Orange desktop/Qt is not a module dependency.

| Idea | ClinicoPath adaptation | Current status |
|---|---|---|
| [Annotated heatmap](https://orangedatamining.com/widget-catalog/visualize/heatmap/) | IHC marker panel with original-row IDs, patient/specimen, group and region annotations; scaling, missingness and optional clustering | `pyihcheatmap` core plus linked scatter, trees, selections, selected-data and previews through 0.3.18; 0.3.19 scatter keyboard extension under qualification; evidence/limits recorded separately |
| [Differential expression / volcano](https://orangedatamining.com/widget-catalog/bioinformatics/volcano_plot/) | Effect magnitude versus multiplicity-adjusted evidence for specified marker designs | Proposed; distinguish gene expression, bounded IHC scores and repeated specimens |
| Set-overlap inspection | Exact marker-panel intersections with native aligned bars/dot matrix and local source-row inspection | `pyvenn` exact 2–4-set core and compact preview verified through 0.3.28; optional bounded matrix added in 0.3.29 with macOS GUI/export/fresh-engine reopen verified; full UpSet/Venn parity remains omitted |
| Categorical hierarchy inspection | Ordered category partitions with native counts and local branch expansion | `pyvartree` partial categorical core in 0.3.35; no learned classifier or row-selection pipeline |
| [Test and Score](https://orangedatamining.com/widget-catalog/evaluate/testandscore/) | Consistent folds and saved predictions feeding linked ROC, confusion matrix and calibration | Proposed; existing diagnostic engines are a starting point, not a model-validation pipeline |
| [Interactive survival](https://orangedatamining.com/widget-catalog/survival-analysis/kaplan-meier-plot/) | Risk-set and patient inspection with explicit time/event roles | Proposed within survival wave; selected cohorts require Apply and rerun |
| [Gene-set enrichment](https://orangedatamining.com/widget-catalog/bioinformatics/gene_set_enrichment/) | Offline, versioned gene-set over-representation testing with stated background universe | Later molecular extension outside the 61; hypergeometric over-representation remains distinct from ranked-list GSEA |
| [Single-sample scoring](https://orangedatamining.com/widget-catalog/bioinformatics/single_sample_scoring/) | Per-sample pathway scores linked to morphology/outcomes | Later molecular extension outside the 61; specify normalization, gene mapping and reference versions |

Use shared, versioned result contracts and row-aligned outputs to connect views. Highlighting
remains local; inferential cohort changes commit explicitly. Prevent preprocessing/feature-selection
leakage across validation folds. Database licensing, offline gene-set versions and method-specific
validation are prerequisites for molecular extensions.

Versions 0.3.12–0.3.13 extend the existing IHC utility with optional linked heatmap/scatter row
inspection, saved native X/Y marker roles, complete-pair counts/source rows and a native
static scatterplot. Browser marker switching and highlighting remain local and transient;
no cohort changes or inferential refitting are introduced. Version 0.3.13 fixes marker reuse
in the shared supplier. Native mouse linking, custom pair controls, fresh-engine save/reopen
and PNG export are checked on macOS arm64 / jamovi 28.13; broader gates remain open. See
[linked-view checks and open acceptance gates](python-ihc-linked-validation.md).

The first IHC heatmap is a separate utility extension, not completion of `pyihcheterogeneity`.
It displays every retained row (maximum 200 × 20 markers), excludes/counts all-marker-missing
rows, exposes partial-versus-complete-row handling and performs no imputation. Z scaling uses
sample SD; constant/one-observation columns display observed z values as zero with a warning.
Optional average-linkage Euclidean clustering requires complete marker data. Repeated IDs
remain annotations; no tests, molecular subtype claims or clinical response thresholds are added.
See [IHC methods, examples and omissions](python-ihc-heatmap.md).

Version 0.3.14 adds optional native dendrogram/merge outputs and local member highlighting
to the same IHC utility. It reuses the existing row/marker linkage and does not count as a
new baseline port. Numerical and desktop scopes are recorded in
[the dendrogram validation record](python-ihc-dendrogram-validation.md).

Version 0.3.15 adds explicitly applied source-row selections to the IHC utility, with
native selected-row summaries and an optional dataset flag. Preview inspection remains
local; Apply changes saved options without changing the analysis cohort. Input snapshots
prevent silent reuse after supplied marker/annotation data or role changes. See
[selection qualification](python-ihc-selection-validation.md). This is a utility extension,
not another baseline port or a model-validation pipeline.

Version 0.3.16 adds an optional native selected-data table to the same IHC utility.
Applied retained rows expose raw and full-cohort displayed marker measurements, source
identities, annotations and missingness in heatmap order. It introduces no new inference,
selection refit or baseline port. See [selected-data checks](python-ihc-selected-values-validation.md).

Version 0.3.17 adds local rectangle row previews to the linked IHC scatterplot, using
inclusive numeric displayed-value bounds or optional pointer dragging. Complete pairs
retain original source identities and ties remain separate rows. Only the existing Apply
action persists a row selection; it changes no statistical calculation. See
[rectangle interaction checks](python-ihc-brush-validation.md).

Version 0.3.18 adds a single remembered Tab stop and directional/endpoint keyboard focus
navigation to the IHC matrix. Native cell activation and local preview semantics remain
unchanged. This is a bounded keyboard improvement, not full accessibility certification.
See [keyboard qualification](python-ihc-keyboard-validation.md).

## Deferred backend experiment: Julia

Retain Julia as a future optional analysis backend, following the 2026-10-26 discussion.
It is not part of the current implementation batch. Prototype a direct isolated Julia
process behind the existing versioned result contract before considering Python-to-Julia
embedding. Keep native jamovi outputs and stable analysis identities; qualify runtime
availability, offline dependencies, platform packaging, startup/compilation latency,
cancellation/cleanup, row/factor/missingness transport and independent numerical agreement.
A small numerical comparison is the first feasibility gate. Do not install Julia, replace
the current Python backend or promise a speed advantage under this planning entry.

## Correlation-matrix core — 0.3.20

`pyjjcorrmat` is now a partial implementation of the already registered baseline target,
under Stats Plots Py / Associations. Supported defaults retain Pearson, listwise deletion,
Holm adjustment and 0.95 confidence. The core includes Spearman asymptotic p values,
pairwise complete-pair n/exclusions, four adjustment choices, Pearson Fisher-z intervals,
native unique-pair results/static matrix and local cell inspection. All planned unique
pairs define the multiplicity family, including unavailable tests. Intervals are pointwise,
not multiplicity-adjusted. Undefined estimates remain missing with explicit reasons.

Independent base-R cor.test/p.adjust comparisons and native lifecycle/render checks passed
(406 assertions over 16 configurations); the stable full Python suite passes 253 tests,
and all 17 extracted packaged-runtime cases pass. Six hand/edge Python tests and a DOM inspector
harness passed. macOS arm64 jamovi 28.13 also passed native installation, fresh-engine
reruns, keyboard inspection, OMV save/fresh-engine reopen/recalculation and native PNG
export; additional platforms remain pending. See the [desktop record](python-correlation-desktop-validation.md).
Robust, Bayesian, partial/grouped correlations, Spearman CIs, additional p-adjust methods
and full plot styling remain omitted. This is not full baseline parity or clinical validation.
See [correlation methods and qualification](python-correlation-matrix.md).

Current inventory: 61 baseline targets, **17 partial**, **44 planned**, **0 full-parity**;
27 implementation entries including the 10 retained utilities. Existing IHC and diagnostic
identifiers, defaults and production R analyses are unchanged.

## Next delivery sequence — planned, not currently implemented

| Stage | Deliverables | Exit condition |
|---|---|---|
| Foundation completion | Service/renderer decisions, UI synchronization, dependencies and lifecycle checks; high-risk engine prototypes | Documented route/renderer decision and numerical feasibility evidence |
| Wave 1 | Finish 14 descriptives plus `pydatetimeconverter`, `pyoutcomeorganizer`, `pytimeinterval` | Complete retained features, denominators, calendar/missingness rules and row-aligned outputs |
| Wave 2 | Twelve meddecide targets excluding agreement, penalized logistic and latent-class analysis | Validated uncertainty, paired comparisons, ROC/calibration and decision features |
| Wave 3 | Nineteen statistical-plot targets | Classical, robust, Bayesian, paired/repeated-measures calculations validated separately from geometry |
| Wave 4 | Remaining six survival targets plus `pyagreement`, `pylassologistic`, `pynogoldstandard` | Censoring, ties, convergence, prediction and selection/cluster assumptions validated |
| Wave 5 | Four oncology targets | Patient-level transformations, response rules, heterogeneity and diagnostic meta-analysis validated |
| Platform qualification | Additional macOS architecture, Windows and Linux | Each claimed interpreter/dependency/GUI combination passes its applicable gates |

Retain `pyagepyramid`, `pysurvivalcont` and `pytimeinterval` in the inventory. Do not replace
these waves with a count of utility demonstrations. Robust/Bayesian, mixed/ordinal, penalized,
competing-risk and bivariate diagnostic meta-analysis engines still need feasibility prototypes;
SPEC generation or availability of a Python function does not establish numerical equivalence.
Do these prototypes before promising dates for the advanced waves.

## Acceptance and reporting policy

Each analysis needs frozen baseline methods/defaults/outputs; independent numerical references;
edge cases; generator/UI validation; valid→incomplete→valid clearing; cancellation and recovery;
packaged fresh-engine run; save/reopen and native export; and platform qualification.
For stochastic work, share folds/resampling indices where possible; equal seeds alone are insufficient.
Clinical review remains distinct from software/numerical checks. Never mark the 61-analysis
migration complete until retained feature and applicable acceptance gates are satisfied.

Version 0.3.11 retains the host cutoff-panel refresh limitation and adds the missing optional
`pycategorize` histogram with exact break-point lines. Numerical/native-state checks and
desktop acceptance for this addition are tracked in
[the histogram validation record](python-categorize-histogram-validation.md). Inventory counts
remain unchanged.

Next implementation actions: qualify the 0.3.19 scatter keyboard extension, complete remaining
IHC keyboard/theme/platform gates, then extend correlation accessibility/platform qualification and decide its next baseline
features from the explicit omission list. Keep the already documented host cutoff-panel limitation visible without treating it
as a blocker for independent work. Preserve the existing migration waves and statistical defaults.

## Correlation keyboard extension — 0.3.21

The existing `pyjjcorrmat` inspector now uses one remembered Tab stop with bounded
row/column arrow navigation, row Home/End and Ctrl/Command matrix endpoints. Native
Enter/Space activation and local-only detail inspection are preserved. DOM checks cover
2, 3 and 20 variables, boundaries, unavailable estimates, focus re-entry and unhandled
modifier/activation keys. Six focused Python tests, compiler/freshness checks and 17
extracted packaged-runtime cases pass. Statistical methods, saved options and the 61-target inventory
are unchanged. Native keyboard qualification of 0.3.21 remains open; 0.3.20 installation,
save/reopen, rerun and export evidence is retained at its tested scope.

## Native keyboard follow-up — 0.3.22

Native 0.3.21 installation and fresh-engine rerun succeeded, and Tab exit/re-entry
worked. First-cell Left Arrow incorrectly moved to the last column: handled navigation
events still bubbled to the host. The template now stops propagation only for handled
navigation keys, with a failing-before/passing-after DOM host-listener regression.
Tab, native Enter/Space and unhandled modifiers retain normal propagation. Requalify
the packaged repair in the native application before closing the keyboard gate.

That retest passed on macOS arm64 / jamovi 28.13: boundaries, directional/endpoints,
Tab re-entry and native activation, followed by separate OMV save and second fresh-engine
reopen with the boundary repair retained. Six focused Python tests, 2/3/20-variable DOM
fixtures, compiler/freshness and 17 packaged runtime cases pass. See the
[keyboard finding and retest](python-correlation-keyboard-validation.md). Broader
accessibility/theme/platform gates and omitted numerical methods remain open.

## Correlation adjustment expansion — 0.3.23

Hochberg, Hommel and BY extend the existing registered core to all seven adjustment
choices in its frozen baseline; Holm remains the default. Unavailable pairs remain in
the planned family and produce no invented p-values. All seven methods match 1,533
independent base-R fixtures, including sparse/empty families, ties, extremes and up to
190 comparisons. Native integration passes 706 assertions over 28 configurations; compiler/freshness
and 17 packaged runtime cases pass, including the added adjustment paths. The new controls pass macOS arm64 desktop checks: Hochberg/Hommel/BY values match
R, BY settings/results survive separate OMV save and second fresh-engine reopen, and
Hochberg recalculates afterward. Native export and keyboard evidence retain their
0.3.20/0.3.22 scopes; broader platform/accessibility/theme checks remain open. Remaining numerical gaps are robust/Bayesian, partial/grouped methods
and Spearman uncertainty; the 61-target inventory remains 17 partial and 44 planned.

## Partial Pearson extension — 0.3.24

The existing baseline partial option now supports Pearson with three or more variables
and a common complete-case cohort. It controls all other selected variables and reports
controls, residual df, adjusted-df t inference and Fisher-z intervals. Singular/constant
systems remain unavailable, without a pseudoinverse. Unsupported method/missingness
combinations are rejected. Zero-order defaults and inventory counts remain unchanged.
Eight focused Python tests and 1,007 native R assertions pass, including independent
residual-regression estimates/t tests/Fisher-z intervals across all seven adjustments.
Final compiler/freshness and all 17 packaged runtime cases also pass, including an
analytical partial-correlation fixture. Native desktop checks also pass on macOS arm64 / jamovi 28.13 (2026-10-28):
unsupported/constant-system recovery, second-engine save/reopen/rerun and native PNG
export. Additional platforms and broader accessibility/theme checks remain open. Partial
Spearman and robust/Bayesian/grouped features remain open.

## Partial Spearman extension — 0.3.25

The existing partial option now supports common-cohort average-ranked Spearman, with
linear adjustment for all other selected ranked variables, explicit controls/residual df
and approximate two-sided t p-values. No Spearman CI or exact/permutation inference is
added. Pairwise partial settings and singular ranked systems remain explicitly unsupported
or unavailable. Nine focused Python tests and 1,308 native R assertions pass, including independent
ranked-residual coefficients, approximate p-values, controls/df and unavailable intervals
over seven adjustment choices. Final compiler/freshness and all 17 packaged runtime cases also pass, including an
independent tied-rank fixture. Native tied-data controls, R agreement, second-engine save/reopen/rerun and native
PNG export also pass on macOS arm64 / jamovi 28.13 (2026-10-28). Broader
accessibility/theme and cross-platform qualification remain open. Inventory remains 17 partial,
44 planned and zero full parity. Grouped, robust and Bayesian correlations remain open.

## Grouped correlation extension — 0.3.26

The frozen baseline `grvar` role is now implemented for up to six observed factor groups.
Each group has separate missingness/cohorts, ranks, partial systems and adjustment family;
missing grouping rows and unused levels are counted. Native cohort/grouped pair tables
and a stacked static matrix accompany local group inspection with remembered per-group
keyboard focus. Browser switching clears stale details without refitting or changing
native options/results. No pooled/across-group inference or correlation-difference test
is added. Ungrouped defaults and the 61-target inventory are unchanged. Eleven focused
Python tests and ungrouped/grouped DOM checks pass. The native suite passes 1,886
assertions, including twelve grouped configurations compared with independent within-group
R estimates/inference and adjustment families, cohort counts, factor order and raster
rendering. Final compiler/freshness and all 17 packaged runtime cases also pass. macOS arm64 / jamovi 28.13 also passes previous saved-file recalculation, grouped
cohorts, local switching/remembered focus, constant-system recovery, fresh-engine
save/reopen/rerun and stacked PNG export (2026-10-28). Broader maximum-size/theme/
accessibility and cross-platform gates remain open. Robust/Bayesian methods,
Spearman CI, more than six groups and full plot styling remain open.

## Exact set-intersection core — 0.3.27

The planned `pyvenn` baseline target now has a partial exact-count implementation:
two to four factor variables, explicit positive levels, complete-case exclusive patterns
(including none), marginal sizes/union/all-set intersection, native count/membership
tables and intersection-size plot, bounded local inspection and saved nominal membership
with original row alignment. Missing rows never become negative/none membership.
A four-marker synthetic Data Library example covers all sixteen patterns and missingness.
No geometric Venn/Euler, full UpSet, larger-set, weighted or inferential/enrichment features
are claimed. Seven focused Python tests, 86 native R assertions and the DOM harness pass;
the full Python suite passes 265 tests. Final compiler/freshness and all 18 packaged
runtime cases pass. macOS arm64 desktop positive-level controls, exact counts/local
inspection, nominal saved membership, second-engine OMV reopen/rerun and native PNG
export pass. Version 0.3.28 hides redundant long labels in the optional row preview while retaining
its result contract. Native compact-layout and 0.3.27 saved-file reopen/rerun checks pass;
broader accessibility/platform gates remain open. At 0.3.27 the inventory advanced to **18 partial**, **43 planned**, zero
full parity and 28 implementation entries including 10 retained utilities. See
[set-intersection methods and limits](python-set-intersections.md).


## Bounded intersection matrix — 0.3.29

Extend the existing partial `pyvenn` baseline port with an optional native count-bar and
membership-dot figure, reusing the exact common-cohort signatures. The organized tame UI
places the default-off option under Plots and Interaction; native static export and the
existing local inspector cover presentation and exploration separately. Counts, positive
levels, missingness, pattern order and saved membership are unchanged. This is a feature
extension within the same 61-target inventory (18 partial, 43 planned), not a new utility
or full UpSet completion. Independently check bar/dot geometry, native state clearing,
packaged raster rendering and new desktop/export lifecycle evidence separately.


0.3.29 evidence: 270 Python tests (12 focused set/matrix tests), 97 native R assertions,
and 18 packaged runtime cases pass, including bar/dot geometry, native raster and
option/incomplete/recovery clearing. macOS arm64 desktop matrix controls, saved-image reopening/export, second-engine rerun
and missing-level recovery pass. Accessibility, broader long-label/theme cases and other
platforms remain open.


## Unequal-frequency demonstration — 0.3.30

The all-patterns-once validation fixture correctly produces equal bars. Retain it for
coverage and add a separate reproducible Data Library example with 60 complete marker
panels, two missing rows and unequal exact counts 0–12. This improves demonstration
without altering the analysis, cohort policy or plot scale. Independent CSV/runtime/saved
column checks and native varied-bar rendering/export are recorded separately. The new
example is not another analysis or a full feature-parity claim.


## Stable display ordering — 0.3.31

Add optional largest-first exact-pattern display to the existing pyvenn core, preserving
membership order as default. Native table, both static plots and local inspector share
stable frequency ordering; equal counts use original membership codes. Saved membership
and row previews remain canonical and row-aligned. Validate ties, zero patterns, source
identities, order reversal and saved-code invariance separately from new-control desktop
qualification. Inventory remains 18 partial targets and 43 planned.

0.3.31 validation passes 273 Python tests, two DOM harnesses, 106 native assertions and
18 packaged runtime cases. The new ordering control remains desktop-pending because
native automation cannot start its pipe; prior desktop evidence is retained separately.


## Univariate screening core — 0.3.32

Advance the planned pyoutlierdetection target to a partial core: robust/standard Z and
IQR methods, baseline univariate thresholds (3.29/1.7), one finite complete-case cohort,
explicit undefined/flagged states, original-row nominal flags and native summaries/count
plot. The core defaults to robust univariate screening; it does not implement the baseline
composite default. Reject more than 10,000 rows instead of implicitly sampling; cap the
preview at 1,000 source rows while retaining full saved output. Advanced multivariate,
interval and exclusion features remain omitted. Validate against base R and performance
and track the new desktop/lifecycle gate separately. Inventory becomes 19 partial, 42
planned, zero full parity, and 29 implementation entries including 10 retained utilities.

0.3.32 evidence: 278 Python tests, 45 independent/native assertions and 19 packaged
runtime cases pass. Source infinities are excluded by the Python engine but rejected
by the native option validator before dispatch; this host distinction is documented.
New-analysis desktop qualification remains pending because native automation is unavailable.


## Native flagged-measurement inspection — 0.3.33

Extend pyoutlierdetection with optional original-row measurement/limit details. Report
flagged measurement counts separately from flagged rows; cap the native detail view at
500 matches while screening all retained rows and saving all row flags. Preserve every
method, threshold and default. Check late-row visibility, multiple drivers, zero-spread
labels, empty states and output invariance. Track new native desktop rendering/lifecycle
separately; the inventory remains 19 partial targets and 42 planned.

0.3.33 evidence: 281 Python tests, 59 native assertions and 19 packaged runtime cases
pass; the numerical engine remains unchanged from 0.3.32. New details-table desktop
rendering/save/export qualification remains pending.


## Empirical screening distributions — 0.3.34

Continue Orange-inspired distribution inspection with an optional static native view in
`pyoutlierdetection`: 101 empirical percentiles per variable (linear interpolation),
method-specific screening limits and independent measurement axes. This is aggregation
for display; the full common complete cohort supplies every percentile and all flags.
It does not add individual-row selection, deletion or new inferential methods.
The default is off. Maximum payload is 2,020 percentile records across 20 variables.
Native tables remain authoritative for observed values, original row IDs and classifications.
Desktop installation/export/OMV evidence remains a separate pending gate while computer
use fails at native-pipe startup. Inventory and full-parity counts do not change.

0.3.34 implementation evidence: 285 full Python tests, 12 focused tests, 69 native
assertions and 19 packaged runtime cases pass. Compiler/generator checks pass; the
packaged renderer produces the expected 1,000×800 PNG. The screening engine remains
byte-identical to 0.3.33. Desktop and clinical/release gates remain open.


## Categorical variable tree — 0.3.35

Advance planned `pyvartree` to a partial categorical count-tree core, using the existing
registry identity and frozen baseline. Shared Python prefix counting supplies native node
counts, parent/cohort percentages and declared factor order. A local native-disclosure
view provides expansion without changing cohorts; a native top-30 leaf count plot gives
a static export counterpart. Cohort is complete across all 1–4 selected variables.
Bounded at 10,000 rows and 200 non-root nodes, with rejection instead of silent sampling.
Advanced pruning/follow rules, missing-category branches, continuous/percentage-variable
summaries, DiagrammeR geometry and styling remain omitted. Full baseline oracle parity
is not claimed. See [feature/omission and validation guide](python-variable-tree.md).

Inventory now contains 20 partial targets, 41 planned targets and 10 retained utilities
(30 installed implementation entries), with zero fully qualified baseline ports. Desktop,
accessibility, platform and clinical/release evidence remain separate acceptance gates.

0.3.35 evidence: 291 full Python tests (six focused tree tests), 78 independent
base-R/native assertions and 20 packaged runtime cases pass. Compiler/freshness passes;
packaged CSV counts and raster dimensions agree. Native interaction/save/export gates
remain pending because computer use still fails at native-pipe startup. This does not
establish full vtree equivalence or clinical/release readiness.


## Native qualification and synthetic CSV repair — 0.3.36

Native control recovered. GUI installation and fresh-engine testing exposed the tree
example's NA-token ambiguity (34 complete rather than 36). Use Type C in the synthetic
CSV and regenerate its Data Library description; genuine/literal NA engine handling
remains unchanged. Independent blank/NA import fixtures now retain 36 of 38 rows.

macOS arm64 / jamovi 28.13 tree and default robust-Z outlier examples now pass native
installation, rendering, OMV save/fresh-engine reopen/recalculation and native PNG
export. Tree mouse and focused Enter/Space disclosures work. Saved outlier flags remain
row-aligned (30 nonflags, one flag, two missing). Record numerical, GUI and archive
evidence separately; this does not qualify broader keyboard, table export, long labels,
themes, other platforms, full baseline parity or clinical/release readiness.

292 Python tests (seven focused tree tests), 83 native tree assertions and 20 packaged
runtime cases pass. No numerical engine or existing analysis defaults change. Inventory
remains 20 partial targets, 41 planned and 10 retained utilities.


## Compact native tree table — 0.3.37

Address the observed table-width gap without dropping stored paths or changing tree
counts: hide the full JSON path column by default and provide a native Results and
Interpretation checkbox for display/copy/export. Preserve column identity and every
value; `asDF` follows native visibility, while `nodes$columns$path` retains hidden data.
Validate earlier OMV reopening and true/false toggling separately from numerical
invariance. Inventory and numerical scope remain unchanged.

0.3.37 bounded gate passes: 293 Python tests, 95 native assertions, 20 packaged
runtime cases, earlier-file compatibility, compact/expanded fresh-engine option
persistence, and native HTML table exports with independent path/count checks.
The count engine is unchanged; broader layout/accessibility/platform gates remain open.


## Qualification reconciliation — 2026-10-29 / 0.3.38

Close the previously blocked pyvenn pattern-order desktop gate using unchanged 0.3.37
calculation/presentation assets: native frequency/membership reversal, stable ties, local
inspection, both static views, HTML/PNG exports, saved-option reopening and forced
recalculation pass on macOS arm64 / jamovi 28.13. Independent artifact checks verify all
16 CSV pattern counts, marginal/missing counts and original row-aligned nominal codes
and labels. No source observations are reordered or recoded.

Reconcile the pyvartree registry entry with the completed 0.3.37 compact/full-path saved
states and native HTML table exports. Earlier pending checklist items remain historical
where the original version is stated; the current registry and dated evidence govern
the current bounded gate. Other themes, accessibility, broader platforms and full
feature parity stay open. The next core-delivery targets remain the three unimplemented
descriptives (pyalluvial, pycrosstable, pytableone) and the three Wave-1 survival
transformations; select scope against their frozen baseline before adding methods.

This qualification/metadata update retains all numerical defaults and dependencies.
Inventory remains 20 partial baseline targets, 41 planned, 10 utilities and zero full
parity/release-ready claims. Do not credit it as an additional analysis port.

Current 0.3.38 checks: 15 focused Python tests, 106 native assertions, compiler and
20 packaged cases pass. Archive comparison checks 1,272 Python-area files: registry
evidence is the only difference. The prior 293-test suite remains historical
unchanged-code evidence. GUI install of 0.3.38, full restart, saved frequency restore
and forced recalculation pass. The dated artifact checker confirms raw saved-code and
label identity with the original 0.3.30 fixture.


## Continuous within-node summaries — 0.3.39

Extend the retained pyvartree baseline with optional summaryvar and summarylocation
(leafonly default / allnodes). Python computes mean, sample SD and explicit node/valid/
missing n without changing the categorical complete cohort or node percentages. Native
tables are authoritative; local disclosures append the same statistics with display
rounding. Preserve old scientific R argument positions by allowing appended variable
roles only when the SPEC supplies an explicit tame UI.

Require independent base-R node masks/moments, all-missing and singleton cases, numeric
limits, stale annotation clearing, original categorical-result invariance, packaged
fixtures and new-feature GUI/save/reopen/export qualification. Full baseline missing-
category/pruning/percentage-variable/styling features remain outside this increment.
Inventory stays 20 partial targets, 41 planned and 10 utilities.

0.3.39 bounded acceptance passes: compiler/freshness, 299 Python tests, 43 focused
tree/generator tests, 188 native assertions and 20 packaged runtime cases. Native GUI
roles, both summary locations, missing/singleton annotations, on/off clearing, native
HTML export, saved settings and fresh-engine recalculation pass on macOS arm64/jamovi
28.13. Earlier categorical-only saved-file behavior and original data/labels are retained.
Independent artifact checks derive every exported node summary from the synthetic CSV.
Full vtree parity and broader platform/accessibility/clinical gates remain open.


## Reference-level node summaries — 0.3.40

Extend pyvartree with explicit percvar/percvarLevel and the optional pct toggle. Public
vtree 5.7.0 checks establish that reference percentages use valid reference n, not all
node rows or the categorical parent's count. Report matches and missing n explicitly;
keep all-missing percentages undefined. Preserve the complete categorical cohort and
independent numeric summaries, including when reference configuration is pending.

Add generator-owned optional-Level public-wrapper defaults after compiler headers so
existing R calls retain their prior argument behavior. Preserve literal labels without
vtree parser restrictions, and allow a categorical tree variable to be its own reference.
Require independent base-R masks, public-vtree percentage fixtures, literal/true-NA
cases, combined annotations, lifecycle and packaged/new-GUI checks. Inventory remains
20 partial targets, 41 planned and 10 utilities; no full-parity claim.


0.3.40 bounded acceptance passes: 303 Python tests (47 focused), 251 native R assertions,
compiler/freshness and 20 packaged cases. Installed GUI roles, waiting-level state,
reference-only clearing/recovery, combined labels, native HTML export and full-restart
OMV reopening/forced rerun pass on macOS arm64 / jamovi 28.13. An independent artifact
checker derives every native reference count/percentage and mean/SD from source CSV.
Old R call positions/default behavior pass native checks. Full vtree parity and remaining
platform/accessibility/clinical gates stay open; the 61-target inventory is unchanged.


## Next descriptive port: categorical flow core — 0.3.41

Implement `pyalluvial` from the frozen alluvial baseline, with two to four categorical
axes and count-based paths. Preserve excl=false: show genuine missing categories with
a distinct collision-free label, or explicitly exclude all incomplete profiles. Preserve
recorded factor order and omit unused categories. Weights, condensation, numeric binning,
marginal plot panels, other fill rules, orientations and full styling remain omitted.

A shared Python geometry keeps complete-path identity and row-count thickness across
every axis; independent tests verify marginal conservation, node tiling and unequal
widths. Native flow/category tables remain authoritative. JavaScript hover and a native
keyboard-operated select highlight existing geometry locally; they never alter cohorts
or trigger fits. The same counts have a Python static counterpart for native export.
Enforce 10,000 input rows, 60 paths and 20 categories/axis without hidden sampling.

The inventory becomes 21 partial and 40 planned baseline targets, plus 10 utilities;
zero full-parity claims. Acceptance still requires full-suite, independent base-R, native
lifecycle, packaged runtime and installed desktop save/reopen/export evidence.


0.3.41 bounded acceptance passes: 311 Python tests, eight focused alluvial tests,
71 native alluvial assertions, compiler and 21 packaged-runtime cases. Installed GUI
inclusion/exclusion, keyboard highlighting/Clear, native HTML/PNG export, saved roles
and full-restart forced rerun pass on macOS arm64 / jamovi 28.13. Independent exported
artifact checks agree with CSV counts/proportions and unchanged saved inputs. The
registry now counts 21 partial targets and 40 planned, with ten utilities retained.
Next Wave-1 core candidates remain pycrosstable, pytableone and survival transformations;
advanced alluvial options remain explicit omissions rather than completed parity.


## Next descriptive port: grouped cross tables — 0.3.42

Deliver pycrosstable's supported default gtsummary subset: grouped/overall native
summaries, valid/missing denominators, baseline low-distinct numeric typing with an
explicit continuous override, R 4.6 exact Wilcoxon (including conditional ties)/normal approximation, Kruskal–Wallis and categorical
Pearson/sparse-Fisher selection. Larger exact tables remain explicitly unavailable;
no substitute p-value is supplied. Retain means/sample SD versus median/type-7 quartiles
as display choices without changing rank inference. Apply selected multiplicity over
available variable-level tests, matching base R's default NA handling.

Extend generator-owned column visibility only to declared List choices, so the numeric
columns switch natively. Validate source labels, actual-NA levels, zero marginals,
incomplete roles, missingness reversal, independent R/gtsummary outputs, package/runtime
and installed export/save/reopen. Alternate styles, SMDs, weights and full parity remain
omitted. Inventory becomes 22 partial and 39 planned targets, plus ten utilities.


0.3.42 bounded acceptance passes: 323 Python tests (43 focused), 275 native R assertions,
compiler/freshness and 22 packaged cases. Independent R 4.6 comparison detected and
resolved the small-sample tied-Wilcoxon default difference; conditional exact counts
now agree with brute-force label assignments and extreme-tail boundary fixtures.

Native GUI mean/median visibility, available/complete-case cohort reversal, typed Data
Library loading, Holm results, HTML exports and fresh-engine saved-state reopening/
forced rerun pass on macOS arm64 / jamovi 28.13. The typed .omv avoids CSV integer
measure-type guessing; source CSV remains the independent oracle input. Full crosstable
parity and broader qualification remain open. Wave-1 core candidates now include
pytableone and the three survival transformations; the inventory is 22 partial targets,
39 planned, ten utilities and zero full-parity releases.


## Standard overall-cohort Table One — 0.3.43

Implement the frozen t1 subset as pytableone: mean/sample SD or median/type-7 quartiles,
valid-value categorical percentages, explicit binary second-level counting and an
optional all-levels view. Preserve low-distinct numeric columns as measurements. Omit
all-missing and unsupported scalar classes before listwise exclusion; reject structured
columns. Optional storage/shape/row-count/units/label metadata extends transport without
changing old decoded numeric/factor/text values. Independent old-route regressions and
full native testing are required because the R bridge is shared.

Use native tables and optional explanation/report text; no plots or inference are
introduced in this overall-cohort function. Other table engines/styles and full parity
remain omitted. A typed synthetic example with an uncollected variable must retain
25 rows by default and 21 after listwise exclusion. Inventory becomes 23 partial
baseline ports, 38 planned, ten utilities and zero full-parity releases.


Qualification: the 0.3.43 standard core passed 335 Python tests, 267 focused native R
assertions and 23 packaged-runtime cases. Native GUI sideload, option reversal,
HTML export and fresh-engine persistence were checked on macOS arm64 / jamovi 28.13.
The full native suite retains five sandbox process-inspection errors alongside 3,775
passes. A separate permitted process-inspection run passed all 25 bridge assertions;
the full suite was not repeated outside the sandbox. The next
Wave-1 candidates remain the three survival transformations. Advanced Table One engines
and styles remain planned; this core does not count as full baseline parity.


## Outcome status preparation — 0.3.44

Implement `pyoutcomeorganizer` first in Survival Py → Data preparation. The released
R coder supplies a frozen independent reference for selected-event/numeric 0/1,
four-category overall/cause/competing coding and labelled competing-factor handoff.
Add explicit multistate status snapshots with independent truth tables. Require
complete observed-level mapping, preserved missingness and original row identities in
saved output. Expose native mapping/counts, optional bounded source preview/report and
static count plot in organized generator-owned UI. Keep event definitions visible.

This wave deliberately does not expose recurrence composites, patient hierarchy,
interval/administrative censoring or transition estimation before their time-variable
contracts are implemented and validated. A status snapshot is not an event history.
The inventory is 24 partial baseline targets, 37 planned, ten retained utilities and
zero full-parity releases. Next transformation candidates remain datetimeconverter
and timeinterval, followed by completion of the time-aware outcome methods.


The 0.3.44 core now has frozen-R/independent row-code evidence, native saved-output
lifecycle tests, a Data Library CSV, fresh-engine desktop persistence and HTML/PNG
export evidence. Qualification comprises a 344-test Python run, 46 final focused
checks, 71 outcome native assertions, 143 targeted native regressions and 24 packaged
cases. The first broad error-clearing policy failed two legacy greyed-result contracts;
scoping it through a generator-owned boolean restored both. The earlier full R run
(3838 passes, two now-corrected compatibility errors) remains visible; a clean final
full-native rerun, broader platforms/accessibility and clinical/release gates stay open.
See docs/python-outcome-organizer.md and its machine-readable evidence. Next: calendar
conversion and time intervals, then time-aware outcome methods; the inventory remains
24 partial, 37 planned, ten utilities and zero full-parity releases.


## Follow-up qualification and UTC datetime core — 0.3.45

The scoped 0.3.44 package has now passed a full frozen native inventory rerun:
3852 assertions, zero failures/errors/warnings/skips. This closes the previously open
full-R gate without erasing the earlier compatibility-failure evidence.

Continue Wave 1 with `pydatetimeconverter` in Survival Py → Data preparation. The first
core uses strict explicit calendar formats in UTC, Excel 1900/1904 origins and Unix
seconds, with native quality/preview tables and original-row-aligned saved components.
It preserves Excel whole-second ties-to-even rounding and Jan-1-block week semantics.
Reject invalid calendars and keep invalid vs missing accounting explicit. Expose UTC
visibly; do not infer a system timezone, an epoch, day/month order or a century.

The bundled Python lacks zoneinfo/tzdata. Auto-detection, two-digit-year policies,
named/system timezones/DST, permissive parsing and native Date/POSIX inputs remain
pending; this core uses explicit YMD/UTC instead of pretending to implement the R
analysis's auto/system defaults. No new package installation is required.

Inventory: 25 partial baseline targets, 36 planned, ten utilities and zero full-parity
releases. Next: timeinterval, then complete time-aware outcome methods. Qualification
and omissions are tracked in docs/python-datetime-converter.md.


The UTC converter core now has independent conversion/component fixtures, native
row-aligned output/lifecycle evidence and desktop save/reopen/HTML checks. A GUI-detected
blank-column-title defect was corrected by supplying explicit output metadata; its
initial .omv remains failure evidence. The 354-test Python run, 41 final focused checks,
163 converter native assertions and 25 packaged cases pass. The separate 0.3.44 full
native qualification remains 3852/3852; no full-0.3.45 native-run claim is made. See
python-datetime-converter.md for default differences, exact scope and remaining gates.

## Standardized UTC interval core — 0.3.46

Activate `pytimeinterval` under Survival Py → Data preparation using the frozen
umbrella 1.0.81.01 baseline (`9fae7c5c7af84e65dfff9262d3bb2a031618753e`).
The first core supports fixed-length elapsed units, explicit negative/extreme
exclusions, follow-up landmarks, arithmetic-mean t intervals and aligned saved
values. It reuses the strict UTC date parser without changing its calculations.
Calendar-aware months/years, auto parsing, packed numeric dates/epochs and the
baseline's clinical plausibility bands remain omitted. No JavaScript interaction
is needed for these controls: changing an option reruns the Python calculation.

Inventory: 26 partial baseline targets, 35 planned, ten utilities, 36 executable
entry points and zero full-parity releases. See [interval qualification](python-time-intervals.md)
for current numerical, native, compiler, package and desktop evidence separately.
Next: complete the applicable interval/date qualification and time-aware outcome
methods before describing Wave 1 as complete.

0.3.46 qualification: 362 Python tests, 45 focused native R assertions, generator/status
freshness, compiler and 26 packaged-runtime cases pass. On macOS arm64 jamovi 28.13,
sideload/restart, baseline/landmark/error/exclusion states, named saved output, HTML
and fresh-engine reopen/rerun pass. The native artifacts independently retain source
rows and expected intervals. Full native inventory qualification is not newly claimed;
calendar-aware methods, broader platforms and full parity remain open.
