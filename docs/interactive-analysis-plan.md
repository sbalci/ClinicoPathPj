# Interactive diagnostic dotplot and next analyses

> Historical planning snapshot. For current architecture, implemented scope and next steps,
> see [the revised migration plan](python-migration-plan.md), updated 2026-10-26.


Prepared 2026-10-25. Experimental implementation, separate from the umbrella's production analyses.

## Diagnostic dotplot

`pydotdecision` adds **ClinicoPathPj > Diagnostic tests > Interactive Diagnostic Dotplot (Python)**.
Open `interactive-dotplot-example.csv` for a six-row synthetic test (positive level `P`).
Its source is `inst/python/analyses/pydotdecision.py`; its SVG/JavaScript view is
`inst/python/templates/dotdecision.html`. Python computes the applied result; JavaScript previews changes.
The generator and R bridge now support module-authored `Html` results through `out.html()`.
User labels are embedded as escaped JSON and inserted into the DOM as text.

The design follows the behaviour described in the
[MedCalc interactive dot diagram manual](https://www.medcalc.org/en/manual/interactive-dot-diagram.php):
two reference groups, a horizontal cutoff and changing diagnostic accuracy summaries.
The implementation uses original code and no copied graphics or MedCalc code.

1. Select a numeric measurement and a binary reference column.
2. Explicitly select the positive reference level and the test direction (`>=` or `<=`).
3. Leave the applied cutoff blank to choose an empirical automatic cutoff: fewest errors
   (`FP + FN`) or maximum Youden index (`sensitivity + specificity - 1`). These objectives differ
   in imbalanced samples. Equal optima use the lowest numerical evaluated cutoff.
4. Drag/click in the chart or edit its numeric field to preview a cutoff. All equal measured
   values move together under the stated inclusive comparison rule.
5. **Apply cutoff** calls jamovi's `window.setOption('cutoff', ...)`, which reruns Python and
   updates native count/accuracy tables. This committed cutoff is part of the saved analysis.
   An uncommitted drag preview is transient. Blank the applied cutoff option to return to automatic mode.

The live display reports TP, FP, FN, TN, sensitivity, specificity, PPV and NPV.
Native tables also include accuracy and exact 95% Clopper-Pearson intervals. Zero-denominator
metrics stay undefined. The log option changes only the plotting scale, preserving the raw-unit
cutoff and calculations, and requires positive measurements. Missing measurement/reference pairs
are excluded and counted. Infinite measurements, nonbinary references and single observed groups
are rejected. This first version accepts at most 5,000 complete rows, without hidden subsampling.

One row must represent one independent observation. This version has no repeated-patient or
cluster-aware uncertainty engine. Automatically selected cutoffs are exploratory; the intervals
condition on a fixed cutoff and ignore selection. PPV/NPV and accuracy use the observed sample
composition, which may not represent population prevalence in a case-control study.

`interactive-dotplot-preview.html` is a standalone synthetic six-observation example; open it
in a browser. Its Apply button explains how to copy the cutoff when outside jamovi.
The interactive HTML chart has no native Image fallback in this version: Word/ODT export of the
interactive graphic is not supported. Native tables remain the reportable numerical outputs.
Measurements are embedded in the HTML saved with the analysis; no network service is used.

## Recommended sequence for other umbrella analyses

This ranking concerns **benefit from interaction**, a different criterion from the existing
`python-roadmap.md` ranking of numerical porting benefit. A plot-first analysis can be a very
good interactive candidate while gaining little from rewriting its statistical engine.
Menu states below were checked against the umbrella's current `.a.yaml` files on 2026-10-25.
These are proposals, not implemented or validated ports.

| Priority | Umbrella source | Interaction worth adding | Numerical approach / main work |
|---|---|---|---|
| 1 | `enhancedROC`, `psychopdaROC`, `decision` | Link this dotplot to an ROC point, threshold table and Se/Sp-versus-cutoff curve; click any view to move the others | Share the threshold engine. Independently validate AUC, direction/ties and any DeLong/bootstrap procedures before adding inference. |
| 2 | `decisioncurve` | Move a probability threshold to compare net benefit, treat-all/none and interventions avoided; toggle models | Vectorized threshold counts; match existing R outputs. A risk probability threshold differs from a biomarker measurement cutoff. |
| 3 | `cotest`, `sequentialtests` | Prevalence and test-property controls linked to PPV/NPV, patient-flow diagrams and uncertainty | Extend existing `pycotest`, preserving its conditional-dependence assumptions and uncertainty definition. Simple option changes need no persistent worker. |
| 4 | `waterfall`, `swimmerplot` | Select a patient across waterfall, longitudinal/spider and treatment/event lanes; hover for measurements | Preserve validated patient grouping, time origins and response rules; presentation can be Python/JS without replacing the clinical engine. |
| 5 | `pathagreement` (test menu) | Click a disagreement cell to inspect contributing observations; link ratings, confusion matrix and cutoff disagreement | Reuse a verified agreement engine first. Respect patient/reader clustering; row selection must not silently refit inferential summaries. |
| 6 | `parallelplot`, `jggheatmap`, `jcomplexupset` (draft menus) | Brush axes, inspect heatmap cells/clusters, click set intersections to inspect records | High interaction benefit with modest new statistics. Preserve row identity; validate normalization, clustering and intersection counts separately. |
| 7 | `kappaSizeCI`, `kappaSizeFixedN`, `kappaSizePower` | Explore sample size, marginal prevalence and agreement scenarios on linked power/coverage curves | Build on existing Python kappa ports; describe simulation uncertainty and retain the currently validated design limits. |
| Later | `survival`, `decisiongraph` | Inspect KM risk sets or decision-tree sensitivity scenarios | Prefer retained R numerical engines initially. Full Cox/competing-risk/Markov/PSA ports require substantially more validation than an interactive view. |

Suggested first product: a diagnostic explorer sharing **dotplot + ROC + threshold table**, then
decision curves and co-testing. Python handles the calculations; SVG/JavaScript handles immediate
interaction; explicit Apply actions commit changes to jamovi options and reproducible native results.

## Verification and remaining acceptance checks

- Compiler preparation succeeded with `--assume-app-version 28.13.0`, matching the installed app's
  `CFBundleShortVersionString` (28.13.0.0). The normal `jmvtools::prepare()` app probe cannot access
  jamovi here; bypassing that probe is compiler evidence only, not desktop evidence.
- Focused native R tests: 12 assertions passed, including count fixtures and all five intervals
  against base R `binom.test()`.
- Python tests include 160 brute-force comparisons of the optimized threshold search, both
  directions, tied values, differing automatic objectives, missing pairs, undefined predictive
  values, invalid inputs and hostile HTML labels.
- Full Python suite: **138 tests passed**. Full R suite: **313 assertions passed, 5 errors**;
  all five errors are in existing bridge process-lifecycle tests where macOS denies
  `ps::ps_pids()` / child-process enumeration with `Operation not permitted`. That suite is
  not a full pass in this environment.
- The ClinicoPathPj `.jmo` built successfully and passed ZIP integrity checking. JavaScript
  syntax checking passed. The standard package was installed through jamovi's GUI into the existing ClinicoPathPj module.
- A DOM unit harness (`node tests/js/test_dotdecision.cjs`) checks preview counts, decimal
  editing, Apply's option binding, pointer-event calculations and reset. This is not a real
  browser rendering or desktop integration test.
- A smoke run extracted the final `.jmo` and executed its packaged Python runtime: the current
  template was present, counts were correct, and interactive HTML was generated successfully.
- GUI follow-up on 2026-10-25: sideload succeeded. Initially the active R engine retained the
  older namespace: Rj `get0("pydotdecisionOptions", envir=asNamespace("ClinicoPathPj"))` returned
  NULL, causing `optionsClass$new(): attempt to apply non-function`. Reloading the namespace
  in the synthetic test session resolved initialization. Restart jamovi after replacing an
  already loaded development build; its module menu can update before the R namespace does.
- Native GUI verification passed: measurement/reference selection, explicit positive level,
  automatic cutoff 5, numeric preview at cutoff 2, and Apply updating the native counts to
  TP=3, FP=2, FN=0, TN=1, sensitivity=100%, specificity=33.3%.
- The repository root now contains the single standard `ClinicoPathPj_0.2.0.jmo`; previous
  artifacts are preserved as ZIP backups under `build/previous-artifacts/`.
- Desktop `.omv` save/reopen, dark mode and export acceptance remain separate open checks.

Build the single ClinicoPathPj module without installation (standard package filename):

```sh
node /Library/Frameworks/R.framework/Versions/4.6/Resources/library/jmvtools/node_modules/jamovi-compiler/index.js \
  --build . --assume-app-version 28.13.0 --skip-deps \
  --jmo ClinicoPathPj_0.2.0.jmo
```

Use `tools/generate.py` for generated analysis files; do not edit generated R/YAML directly.
