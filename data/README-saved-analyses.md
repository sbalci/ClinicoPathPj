# Saved jamovi analysis examples

Keep reusable `.omv` examples in `data/`. Generated validation snapshots belong
in `docs/validation-exports/`, which is ignored for `.omv`, PNG, JSON and log files.
Use one curated workbook per analysis topic; a comparison workbook can contain
related analyses together. Keep incomplete, error, recovery and export-only
profiles local rather than adding each profile as another example.

Open a workbook from jamovi's file menu with ClinicoPathPj installed. The version
below identifies the saved implementation: use that version or a later compatible
one to recalculate. Examples from unreleased source increments may require a
locally built module. Pj service comparisons also require the compatible Pj module.
Cached results are examples, not a substitute for rerunning or clinical validation.

These 25 saved-analysis workbooks were copied byte-for-byte from existing synthetic
validation examples; ZIP integrity, analysis presence and SHA-256 equality were
checked. No saved options, data or results were edited, and no workbook merger
was attempted. Earlier `.omv` example/data templates already in this folder remain
unchanged. The TSV manifest records full hashes and the original local snapshot.

| Workbook | Related analysis identifiers | Saved module version |
|---|---|---|
| [python_age_pyramid_comparison_examples.omv](python_age_pyramid_comparison_examples.omv) | `pyagepyramid,pyagepyramidpj` | 0.3.62 |
| [python_alluvial_examples.omv](python_alluvial_examples.omv) | `pyalluvial` | 0.3.41 |
| [python_barstats_examples.omv](python_barstats_examples.omv) | `pyjjbarstats` | 0.3.71 |
| [python_bridge_comparison_examples.omv](python_bridge_comparison_examples.omv) | `pybridgecompare` | 0.3.60 |
| [python_calendar_intervals_examples.omv](python_calendar_intervals_examples.omv) | `pytimeinterval` | 0.3.47 |
| [python_checkdata_examples.omv](python_checkdata_examples.omv) | `pycheckdata` | 0.3.6 |
| [python_composite_outcome_examples.omv](python_composite_outcome_examples.omv) | `pyoutcomeorganizer` | 0.3.49 |
| [python_concordance_examples.omv](python_concordance_examples.omv) | `pyagreement` | 0.3.63 |
| [python_correlation_examples.omv](python_correlation_examples.omv) | `pyjjcorrmat` | 0.3.26 |
| [python_cutoff_explorers_examples.omv](python_cutoff_explorers_examples.omv) | `pyd3cutoff,pydotdecision,pyobservablecutoff` | 0.3.5 |
| [python_dataquality_examples.omv](python_dataquality_examples.omv) | `pydataquality` | 0.3.3 |
| [python_diagnostic_meta_examples.omv](python_diagnostic_meta_examples.omv) | `pydiagnosticmeta` | 0.3.57 |
| [python_estimation_examples.omv](python_estimation_examples.omv) | `pyjjbetweenstats,pyjjwithinstats` | 0.3.69 |
| [python_grouped_survival_examples.omv](python_grouped_survival_examples.omv) | `pysurvival` | 0.3.78 |
| [python_histogram_examples.omv](python_histogram_examples.omv) | `pyjjhistostats` | 0.3.70 |
| [python_ihc_heatmap_examples.omv](python_ihc_heatmap_examples.omv) | `pyihcheatmap` | 0.3.18 |
| [python_lollipop_examples.omv](python_lollipop_examples.omv) | `pylollipop` | 0.3.75 |
| [python_outlier_screening_examples.omv](python_outlier_screening_examples.omv) | `pyoutlierdetection` | 0.3.36 |
| [python_paired_decision_examples.omv](python_paired_decision_examples.omv) | `pydecisioncompare` | 0.3.66 |
| [python_pie_examples.omv](python_pie_examples.omv) | `pyjjpiestats` | 0.3.74 |
| [python_roc_examples.omv](python_roc_examples.omv) | `pyenhancedroc` | 0.3.64 |
| [python_set_intersections_examples.omv](python_set_intersections_examples.omv) | `pyvenn` | 0.3.30 |
| [python_summary_service_comparison_examples.omv](python_summary_service_comparison_examples.omv) | `pyservicedirect,pyservicepj` | 0.3.62 |
| [python_variable_tree_examples.omv](python_variable_tree_examples.omv) | `pyvartree` | 0.3.40 |
| [python_waffle_examples.omv](python_waffle_examples.omv) | `pyjwaffle` | 0.3.76 |

The grouped-survival workbook was added from the GUI-verified 0.3.78 cold-reopened
profile. It contains twelve synthetic rows, nine complete subjects, three groups,
explicit Event/Censored levels, native log-rank/KM/risk tables and a static plot.
Its original saved options, source data, tables and cached PNG are retained.
The 0.3.79 source manifest registers it for the next package; installed 0.3.78
continues to expose the corresponding CSV until updated. Run
`python3 tools/check-saved-analysis-examples.py` to verify all curated hashes,
ZIP integrity and declared analysis entries independently of numerical/GUI checks.
