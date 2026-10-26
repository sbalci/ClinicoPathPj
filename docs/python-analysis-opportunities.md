# Python opportunities for ClinicoPath — web review, 2026-10-26

This is a researched candidate backlog, not an implementation or clinical-validation claim.
Recommendations below are our assessment of clinicopathological usefulness. They do not
expand the frozen 61-analysis migration denominator or register new public identifiers.
Existing registered ports should gain shared engines/views where they fit; genuinely new
analyses need a baseline specification and a stable `py…` registry ID before implementation.

## Assessment of the four requested resources

| Resource | What was verified | How to use it here |
|---|---|---|
| [R Graph Gallery](https://r-graph-gallery.com/) | Reproducible chart examples organized by distribution, association, ranking, composition and flow | Visual reference and comparison with existing R layouts; not a numerical oracle |
| [Python Graph Gallery](https://python-graph-gallery.com/) | Examples primarily using Matplotlib/Seaborn; dedicated distribution, heatmap, flow and interaction pages | Static figure prototypes; recreate required geometry using the existing renderer before adding a plotting dependency |
| [D3 Graph Gallery](https://d3-graph-gallery.com/) | Editable JavaScript examples, including brushing | Interaction patterns only; use current pinned local D3 and native static counterparts |
| [Packt Biostatistics with Python](https://github.com/PacktPublishing/Biostatistics-with-Python) | README describes cleaning, effect sizes, predictive modelling, study design, survival and meta-analysis; chapter notebooks are listed | Teaching/example discovery; inspect and validate individual notebook cells before reuse. Notebook contents were not fully retrievable in this review, so no chapter-to-method or numerical-validity claim is made |

The repository landing page identifies an MIT license; preserve and verify the actual license
and dataset permissions at a pinned commit before copying code or redistributing data. Gallery
code/image licensing must also be checked per source. Link to examples now; do not bundle
notebooks, screenshots, remote datasets or new dependencies in this planning change.

## Ranked candidates and existing-target mapping

“Near” means a good candidate after current lifecycle acceptance, not that implementation
has started. Tier A uses the existing NumPy/SciPy/Matplotlib approach; Tier B requires
separately reviewed/bundled packages; Tier C has substantial method/packaging risk.

| Priority / candidate | ClinicoPath use and mapping | Python engine / dependency tier | Useful local interaction | Essential independent check |
|---|---|---|---|---|
| Near: distribution + estimation plots | Ki-67/H-score or age across diagnoses; `pyjjbetweenstats`, `pyraincloud`, `pyadvancedraincloud`, `pyjjridges`; extend `pysummarydata` views | A: SciPy summaries/KDE + Matplotlib geometry; PtitPrince optional B | Highlight groups/observations; inspect effect-size intervals | Frozen R tests/effect sizes; bandwidth/support; constant or tiny groups; raw n shown |
| Near: paired-change and trajectory views | Biopsy/resection or pre/post treatment; `pyjjwithinstats`, `pylinechart` | A for paired core; B for general repeated/mixed models | Link each subject across times; inspect missing visits | Pair by subject/time, never row order; duplicate visits; patient-level resampling; match paired R fixtures |
| Near: biomarker correlation matrix | IHC panel associations; `pyjjcorrmat`, shared heatmap view | A: SciPy correlations, multiplicity and linkage; optional Seaborn B | Cell inspection with pair-specific n; linked scatter; display reorder | R `cor`/`cor.test`/`p.adjust`; pairwise versus common cohorts; constant columns; clustering settings |
| Near: flows and set membership | Diagnostic reclassification, cohort attrition, marker overlap; `pyalluvial`, `pyvenn`, `pyvartree` | A for exact counts/static views; D3 Sankey needs a separately pinned layout plugin or our own layout | Highlight paths/intersections; expand trees; show contributing row IDs | Exhaustive intersections, weighted conservation, missing categories, denominators; zero paths |
| Near: diagnostic evaluation and calibration | Marker/classifier performance; extend `pydecision`, planned `pyenhancedroc`/`pypsychopdaroc`, link `pydecisioncurve` | A for threshold counts/ROC/PR/Brier core; B for scikit-learn model fitting/calibration | Linked cutoff/ROC/PR and probability-bin inspection; explicit Apply | Hand-count ties and thresholds; define PR/AP convention; independent R curves; out-of-sample calibration |
| Next: continuous-measurement agreement | Manual versus digital Ki-67 or two readers; `pyagreement` continuous component after baseline mapping | A for basic paired bias/limits; Pingouin B as candidate/reference | Link Bland–Altman point to specimen; show predefined tolerance | Bias/LoA and CI fixtures; heteroscedasticity; ICC model definitions; repeated specimens need separate methods |
| Next: patient response displays | Treatment response and follow-up; `pywaterfall`, `pyswimmerplot` | A: validated patient transforms + Matplotlib; local D3/Observable view | Link patient across waterfall/timeline; inspect dates/events | Baseline lesion/date rules, time origin, censoring, missing response; preserve frozen clinical definitions |
| Next: IHC regional heterogeneity | Regional scores, tumor areas and marker patterns; `pyihcheterogeneity` | A for specified summaries/heatmap; B/C for hierarchical inference | Region/patient drill-down and linked heatmap | Separate cells/regions/patients; weighting and cluster inference; no cell-level pseudoreplication |
| Prototype: survival and competing-risk curves | OS/DFS and recurrence with competing death; `pysurvival`, `pysurvivalcont`, `pymultisurvival` | B: lifelines; C: scikit-survival alternative; A independent nonparametric fixtures | Risk-set/time inspection, linked event/censor marks; Apply prediction profiles | R survival/cmprsk fixtures; ties, left truncation, censoring and CI definitions; avoid hidden jitter |
| Prototype: mixed, ordinal and clustered models | Repeated samples/readers; grade/stage; shared engine for relevant registered targets, extensions outside baseline separately scoped | B: statsmodels MixedLM/OrderedModel/GEE | Residual diagnostics and prediction profiles; explicit model Apply | ML/REML, covariance, category order, link/intercept conventions, convergence; compare lme4/nlme/ordinal/geepack as applicable |
| Prototype: evidence synthesis | Prognostic effects or treatment contrasts; new conventional meta-analysis extension; support forest display for oncology meta-analysis | B: statsmodels `combine_effects`; C for bivariate diagnostic models | Select study; inspect weight/CI; explicit leave-one-out recalculation | Match metafor with identical tau², effect scale, CI/HKSJ and zero-cell rules; univariate pooling is not SROC/bivariate parity |
| Later extension: biomarker PCA and clustered heatmaps | Explore multivariate marker patterns; new scope outside the 61 | A: NumPy SVD and SciPy linkage; scikit-learn B optional | Linked scores/loadings; show preprocessing and original rows | R `prcomp`; sign-invariant subspaces; scaling, missingness, rank deficiency; clusters are exploratory |
| Later extension: laboratory QC/run charts | Batch/reader drift, turnaround times, assay monitoring; new scope outside the 61 | A for specified charts; model-dependent extensions B | Inspect batches and predeclared signal rules | Independent chart-limit fixtures; rational subgrouping, denominator changes and serial dependence |

These mappings do not change which features the existing baseline includes. Additions such as
PR/calibration, continuous agreement variants, PCA or laboratory QC require an explicit scope
decision if absent from the relevant frozen baseline. A forest picture alone is not meta-analysis.

## Source-backed implementation findings

1. [Raincloud example](https://python-graph-gallery.com/raincloud-plot-with-matplotlib-and-ptitprince/)
   demonstrates a combined distribution/raw-data display. Recommendation: implement shared
   geometry once; keep inferential engines distinct. Do not add PtitPrince solely for appearance.
2. [Heatmap guide](https://python-graph-gallery.com/heatmap/) and
   [Seaborn clustermap API](https://seaborn.pydata.org/generated/seaborn.clustermap.html)
   support biomarker-panel prototypes. Make scaling, missingness and clustering explicit;
   a reordered or normalized display must not silently change the statistical cohort.
3. [R set diagrams](https://r-graph-gallery.com/venn-diagram.html) illustrate UpSet as a
   readable alternative for larger set collections. Use exact Python membership counts;
   do not present overlapping circle areas as precise counts unless the layout supports it.
4. [D3 gallery brushing](https://d3-graph-gallery.com/graph/interactivity_brush.html)
   contains older v4-style examples. Adapt concepts against the
   [current D3 brush API](https://d3js.org/d3-brush), not legacy `d3.event` code.
   Highlight locally; changing the analysis cohort requires explicit Apply and a rerun.
5. [Python Sankey examples](https://python-graph-gallery.com/sankey-diagram/) use Plotly
   or pySankey. These are alternatives, not required dependencies. Prefer the present
   Matplotlib/local-JavaScript pipeline unless a measured benefit justifies another renderer.
6. [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)
   offers reusable interval machinery. Validate against the bundled version, fixed resample
   indices, and degenerate data; specify whether the resampling unit is patient, pair or study.
7. [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html)
   is a useful route for prediction assessment. Prespecify folds and keep preprocessing,
   feature selection and calibrator fitting inside training data. External evaluation must
   remain separate; a well-shaped reliability plot does not establish clinical utility.
8. [Pingouin agreement APIs](https://pingouin-stats.org/api.html) include ICC and Bland–Altman.
   Treat them as candidates, not universal replacements: lock the version, expose the study
   design, independently verify formula/CI conventions and do not import interpretation bands.
9. [statsmodels MixedLM](https://www.statsmodels.org/stable/mixed_linear.html),
   [GEE](https://www.statsmodels.org/stable/gee.html) and
   [OrderedModel](https://www.statsmodels.org/stable/generated/statsmodels.miscmodels.ordinal_model.OrderedModel.html)
   offer specific model families. MixedLM is not a universal GLMM engine; none by itself
   supplies full robust/Bayesian/repeated-measures jjstatsplot parity.
10. [lifelines Aalen–Johansen](https://lifelines.readthedocs.io/en/latest/fitters/univariate/AalenJohansenFitter.html)
    documents jitter for tied event times. This is material for clinical time data: test tied
    fixtures explicitly and do not silently perturb times to obtain baseline agreement.
    [scikit-survival cumulative incidence](https://scikit-survival.readthedocs.io/en/stable/api/generated/sksurv.nonparametric.cumulative_incidence_competing_risks.html)
    is an alternative to evaluate; its interface also needs checking for truncation/design support.
11. [statsmodels effect pooling](https://www.statsmodels.org/stable/generated/statsmodels.stats.meta_analysis.combine_effects.html)
    supplies conventional fixed/random effect synthesis and notes possible API changes.
    It does not establish a bivariate sensitivity/specificity diagnostic meta-analysis engine.
12. [NumPy SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html)
    makes PCA exploration feasible without a new machine-learning dependency; preprocessing
    and biological interpretation still require their own specification.

## Packaging, interface and data rules

- Tier A is preferred for the first batch. A documented API on the web is not proof that the
  version bundled with jamovi includes it; probe/version-lock before coding against it.
- Tier B/C packages are not claimed installed or qualified. Review licenses, transitive
  dependencies, wheel/ABI availability, package size and cold-start/memory costs on each
  claimed platform. Bundle offline; never require user `pip install` or network services.
- Use existing family menus and topic subgroups. Put distributions/paired/correlation views
  under Stats Plots Py, flows/sets/QC under Descriptives Py, diagnostics/agreement under
  MedDecide Py; activate Survival Py/OncoPath Py only when actual entries are available.
- UI: Data and roles expands first (patient/subject/study ID, time origin, event/reference
  levels, weights); model/method controls remain visible; uncertainty, plots and export use
  the existing organized sections. Show cohort n and exclusions next to each output.
- Interaction is optional. Native tables and Python static images must be useful independently.
  Hover/highlight/reorder does not refit; changing cohorts, models or thresholds commits via Apply.
- Synthetic/local fixtures only in examples. The book README points to external datasets;
  those downloads must not become runtime dependencies or be assumed redistributable.

## Recommended first batch after current acceptance gates

1. Shared distribution/estimation geometry for a narrow classical `pyjjbetweenstats` core,
   with planned feature omissions explicit rather than calling it full jjstatsplot parity.
2. Shared correlation matrix plus linked scatter for `pyjjcorrmat`, with per-cell sample sizes,
   exact missingness policies and multiplicity controls.
3. Exact set/flow engine for `pyvenn`/`pyalluvial`, with exhaustive count fixtures and static output.
4. Extend the already implemented diagnostic engines with selected threshold displays; add
   PR/calibration as separately specified features after independent numerical validation.

This is a proposal for implementation order within the existing waves, not a claim that these
analyses are underway. Current service/renderer acceptance and existing-port gaps still come first.

## Orange BioLab follow-up

The [Orange-inspired workstream](python-migration-plan.md#orange-biolab-inspired-workstream)
adds annotated heatmaps, differential-expression/volcano views, consistent-fold model
assessment, interactive survival and later molecular enrichment/single-sample scoring.
The first [annotated IHC heatmap](python-ihc-heatmap.md), `pyihcheatmap`, is implemented as
an additional utility in 0.3.10; it does not complete the baseline IHC heterogeneity port.
Other Orange-inspired candidates remain proposed. Orange/Qt is not a runtime dependency.
