# Python migration status

Generated from `inst/python/registry.json`; never infer full parity from a menu entry.
See the [revised migration plan](python-migration-plan.md) for current priorities and architecture.
The frozen baseline contains 61 analyses across five families. Existing utility and
example analyses are retained separately. Every public identifier starts with `py`;
the original R identifier is provenance, not a second menu entry.

`partial` means an executable implementation exists with incomplete feature or acceptance
coverage. `planned` entries are not installed as placeholder analyses. Full supported
parity and GUI/platform acceptance remain separate gates.

| Python identifier | Original R analysis | Family | Wave | Implementation | Full parity | GUI |
|---|---|---|---:|---|---|---|
| pyagepyramid | agepyramid | descriptives | 1 | partial | pending | fresh-engine run, custom-boundary/denominator rerun, .omv reopen and native PNG export verified |
| pyalluvial | alluvial | descriptives | 1 | planned | pending | pending |
| pybenford | benford | descriptives | 1 | partial | pending | pending |
| pycategorize | categorize | descriptives | 1 | partial | pending | fresh-engine run, ordinal saved column and .omv reopen verified; category plot export pending |
| pycheckdata | checkdata | descriptives | 1 | partial | pending | macOS arm64: installed 0.3.6; valid-incomplete-valid saved flags; local filter; fresh-engine OMV reopen; native PNG export |
| pychisqposttest | chisqposttest | descriptives | 1 | partial | pending | pending |
| pycrosstable | crosstable | descriptives | 1 | planned | pending | pending |
| pydataquality | dataquality | descriptives | 1 | partial | pending | fresh-engine native tables/maps, local paging/filter/focus events, .omv reopen and native PNG export verified |
| pyoutlierdetection | outlierdetection | descriptives | 1 | planned | pending | pending |
| pyreportcat | reportcat | descriptives | 1 | partial | pending | fresh-engine native tables and plot verified |
| pysummarydata | summarydata | descriptives | 1 | partial | pending | fresh-engine run, .omv reopen and native histogram PNG export verified |
| pytableone | tableone | descriptives | 1 | planned | pending | pending |
| pyvartree | vartree | descriptives | 1 | planned | pending | pending |
| pyvenn | venn | descriptives | 1 | planned | pending | pending |
| pydatetimeconverter | datetimeconverter | jsurvival | 1 | planned | pending | pending |
| pyoutcomeorganizer | outcomeorganizer | jsurvival | 1 | planned | pending | pending |
| pytimeinterval | timeinterval | jsurvival | 1 | planned | pending | pending |
| pycotest | cotest | meddecide | 2 | partial | pending | pending |
| pydecision | decision | meddecide | 2 | partial | pending | pending |
| pydecisioncalculator | decisioncalculator | meddecide | 2 | partial | pending | pending |
| pydecisioncombine | decisioncombine | meddecide | 2 | planned | pending | pending |
| pydecisioncompare | decisioncompare | meddecide | 2 | planned | pending | pending |
| pydecisioncurve | decisioncurve | meddecide | 2 | partial | pending | pending |
| pyenhancedroc | enhancedROC | meddecide | 2 | planned | pending | pending |
| pykappaci | kappaSizeCI | meddecide | 2 | partial | pending | pending |
| pykappafixedn | kappaSizeFixedN | meddecide | 2 | partial | pending | pending |
| pykappapower | kappaSizePower | meddecide | 2 | partial | pending | legacy .omv reopen and power 0.8 -> 0.9 -> 0.8 rerun verified |
| pypsychopdaroc | psychopdaROC | meddecide | 2 | planned | pending | pending |
| pysequentialtests | sequentialtests | meddecide | 2 | partial | pending | pending |
| pyadvancedraincloud | advancedraincloud | jjstatsplot | 3 | planned | pending | pending |
| pyhullplot | hullplot | jjstatsplot | 3 | planned | pending | pending |
| pyjjarcdiagram | jjarcdiagram | jjstatsplot | 3 | planned | pending | pending |
| pyjjbarstats | jjbarstats | jjstatsplot | 3 | planned | pending | pending |
| pyjjbetweenstats | jjbetweenstats | jjstatsplot | 3 | planned | pending | pending |
| pyjjcorrmat | jjcorrmat | jjstatsplot | 3 | partial | pending | macOS arm64 jamovi 28.13: 0.3.23 GUI install, fresh-engine Hochberg/Hommel/BY native/local reruns match R, BY OMV save/second-engine reopen and Hochberg recalculation; keyboard repair qualified 0.3.22; native PNG export qualified 0.3.20; 0.3.24 partial Pearson invalid/constant/valid recovery, second-engine save/reopen/rerun and native PNG export verified on macOS arm64; 0.3.25 partial Spearman tied-data controls, R agreement, second-engine save/reopen/rerun and native PNG export verified on macOS arm64 |
| pyjjdotchart | jjdotchart | jjstatsplot | 3 | planned | pending | pending |
| pyjjdotplotstats | jjdotplotstats | jjstatsplot | 3 | planned | pending | pending |
| pyjjhistostats | jjhistostats | jjstatsplot | 3 | planned | pending | pending |
| pyjjpiestats | jjpiestats | jjstatsplot | 3 | planned | pending | pending |
| pyjjridges | jjridges | jjstatsplot | 3 | planned | pending | pending |
| pyjjscatterstats | jjscatterstats | jjstatsplot | 3 | planned | pending | pending |
| pyjjsegmentedtotalbar | jjsegmentedtotalbar | jjstatsplot | 3 | planned | pending | pending |
| pyjjwithinstats | jjwithinstats | jjstatsplot | 3 | planned | pending | pending |
| pyjwaffle | jwaffle | jjstatsplot | 3 | planned | pending | pending |
| pylinechart | linechart | jjstatsplot | 3 | planned | pending | pending |
| pylollipop | lollipop | jjstatsplot | 3 | planned | pending | pending |
| pyraincloud | raincloud | jjstatsplot | 3 | planned | pending | pending |
| pystatsplot2 | statsplot2 | jjstatsplot | 3 | planned | pending | pending |
| pylassocox | lassocox | jsurvival | 4 | planned | pending | pending |
| pymultisurvival | multisurvival | jsurvival | 4 | planned | pending | pending |
| pyoddsratio | oddsratio | jsurvival | 4 | planned | pending | pending |
| pysinglearm | singlearm | jsurvival | 4 | planned | pending | pending |
| pysurvival | survival | jsurvival | 4 | planned | pending | pending |
| pysurvivalcont | survivalcont | jsurvival | 4 | planned | pending | pending |
| pyagreement | agreement | meddecide | 4 | planned | pending | pending |
| pylassologistic | lassologistic | meddecide | 4 | planned | pending | pending |
| pynogoldstandard | nogoldstandard | meddecide | 4 | planned | pending | pending |
| pydiagnosticmeta | diagnosticmeta | oncopath | 5 | planned | pending | pending |
| pyihcheterogeneity | ihcheterogeneity | oncopath | 5 | planned | pending | pending |
| pyswimmerplot | swimmerplot | oncopath | 5 | planned | pending | pending |
| pywaterfall | waterfall | oncopath | 5 | planned | pending | pending |

## Additional utilities and experiments

These entries do not increase the 61-analysis baseline denominator.

| Identifier | Menu | Numerical evidence | GUI evidence |
|---|---|---|---|
| pydescriptives | Descriptives Py / Summaries | See analysis documentation | See analysis documentation |
| pydotdecision | Python Lab / Cutoff explorers | See analysis documentation | See analysis documentation |
| pyexacttests | MedDecide Py / Exact tests | See analysis documentation | See analysis documentation |
| pyruntime | Python Lab / Runtime | See analysis documentation | See analysis documentation |
| pywelch | Stats Plots Py / Group comparisons | See analysis documentation | See analysis documentation |
| pyd3cutoff | Python Lab / Cutoff explorers | See analysis documentation | See analysis documentation |
| pyobservablecutoff | Python Lab / Cutoff explorers | See analysis documentation | See analysis documentation |
| pysvgcutoff | Python Lab / Cutoff explorers | Shared cutoff engine; 217-test Python and 619-expectation R suites passed; final focused 6 Python/20 R checks passed | macOS arm64 jamovi 28.13: numeric, drag, keyboard, ROC, local snapshot and current SVG/PNG export verified; native OMV save/reopen unresolved |
| pybridgecompare | Python Lab / Execution services | 12 processx/Pj bundled-route configurations matched; independent R counts/exact intervals, ties/missingness/row-ID transport and recovery passed on 0.3.8 | macOS arm64 jamovi 28.13 / 0.3.8: installed, fresh-engine OMV reopen, Pj recalculation and native ROC PNG export verified; live native-field refresh unresolved; 0.3.9 summary pending GUI verification |
| pyihcheatmap | Descriptives Py / Biomarker panels | 24 independent base-R raw/z-score and missingness fixtures; 104 native assertions; seven Python fixtures including identity, missing cells, clustering grouping and geometry passed | macOS arm64 jamovi 28.13 / 0.3.10: installed fresh engine; raw/z-score tables/heatmap and annotations; missing-cell inspection; OMV save/fresh-engine reopen; complete-row clustering recalculation; native PNG export verified. Other platforms and large-payload GUI pending. |

## Menus and optional execution service

Installed analyses use Descriptives Py, Stats Plots Py, MedDecide Py and Python Lab,
with registry-owned topic subgroups and compact experiment titles. Planned Survival Py
and OncoPath Py groups do not install placeholder entries. Existing identifiers remain stable.

`pybridgecompare` is a retained utility experiment, not another baseline port. It uses
the same cutoff engine through processx (default) or optional Pj >=1.3.0 service API 1.
Twelve bundled-interpreter route configurations passed matched native results and
independent R count/exact-interval checks. See [service review](pj-service-review.md).

## Foundation and next gates

Implemented: registry-based family routing, frozen baselines with file hashes,
generator-owned organized `u.yaml`, mixed-case-capable internal schema, stable existing
Python identifiers, Python static plotting through bundled Matplotlib Agg, categorical
factor ordering and original-row transport, and native saved-column payload validation.

The bridge supports Terms transport and Output payloads. Action options/UI are accepted;
analysis-specific Action result/file delivery and GUI tests are still required before
claiming those workflows complete.

Existing static interval, line, box, bar and diagnostic scatter plots are constructed in
Python. The diagnostic interactive dotplot also has an applied-cutoff static export.
The R bridge displays PNGs and supplies jamovi palette/theme settings. Existing saved
R plot-data states are translated into the same Python drawing input without model refits.

Pending: remaining method parity across all waves; advanced engines and independent
validation; broader interactive views; native saved-column/action GUI qualification;
SVG/PDF asset delivery; remaining save/reopen/export acceptance; and Windows/Linux support.

The current dependency lock targets CPython 3.11 on macOS arm64. Users install nothing.
Never label the entire 61-analysis migration complete from the foundation build.
