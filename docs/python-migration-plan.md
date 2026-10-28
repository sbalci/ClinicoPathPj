# ClinicoPathPj implementation plan — revised 2026-10-27

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

There are **27 registered implementation entry points**: **17 partial baseline ports** and
**10 utility/demonstration analyses**. Of the 61 baseline targets, **44 are planned**,
**0 have complete supported-feature parity and all release gates**.

| Family | Baseline targets | Partial ports | Planned |
|---|---:|---:|---:|
| ClinicoPathDescriptives | 14 | 8 | 6 |
| jjstatsplot | 19 | 1 | 18 |
| meddecide | 15 | 8 | 7 |
| jsurvival | 9 | 0 | 9 |
| OncoPath | 4 | 0 | 4 |

Partial descriptives: `pyagepyramid`, `pybenford`, `pycategorize`, `pycheckdata`,
`pychisqposttest`, `pydataquality`, `pyreportcat`, `pysummarydata`.

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

Prioritize GUI/saved-output/export gaps for the 17 partial ports, then remaining frozen-baseline
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
