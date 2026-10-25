# Separate D3 cutoff experiment

`pyd3cutoff` is an additional utility under **ClinicoPathPj > Medical Decisions**.
It does not replace `pydotdecision` or change the 61-analysis migration inventory.
The interface adapts Maurizio Agosti's shared `52_d3_cutoff_explorer.py` demonstration.
Official D3 7.9.0 is bundled locally with its license in `inst/python/vendor/`.
No Pj editor, reticulate, network access, or new user-installed Python package is needed.

## Try the comparison

Import `data/python_d3_cutoff_examples.csv`. Select Measurement and Reference, and
explicitly choose Positive. Enter `2` as the applied cutoff for a Measurement >= 2 rule. Compare with
`pydotdecision` using the same variables and cutoff. Both native results should
report TP 47, FP 10, FN 8 and TN 115 on this synthetic teaching dataset.

The D3 view links a draggable cutoff, numeric input and clickable empirical ROC.
Keyboard users can focus the cutoff line and use arrow keys, Home and End;
the automatic-cutoff button provides an accessible route to the optimum.
Hover/focus identifies observations and the criterion optimum. Hiding correct
classifications only changes the display. No observations are sampled.

**Apply to HTML tables** updates the browser snapshot only. It does not update
jamovi options, native tables, native images, or dataset columns. To retain a rule,
edit **Positive test rule** and **Applied cutoff** in the jamovi options. Recalculation
and saved-file reopening reconstruct the HTML from those saved options. To persist
an automatic criterion, select it in the jamovi options and leave cutoff blank.
Error weights and confidence settings are also native jamovi options.

## Comparison of approaches

| Feature | Existing `pydotdecision` | Separate `pyd3cutoff` |
|---|---|---|
| Python execution | Existing isolated-process bridge | Same bridge, shared statistical state engine |
| Browser graphics | Handwritten SVG | Local D3 7.9.0 |
| Linked ROC | No | Empirical curve, operating point and optimum |
| Native static graphics | Dotplot | Dotplot and ROC |
| Automatic criteria | Errors, Youden | Errors, Youden, weighted errors |
| Proportion intervals | Exact 95% | Exact or Wilson; configurable confidence |
| Browser Apply | Conditional native-option callback; not established by this experiment | Explicit local HTML snapshot |
| Complete-row cap | 5,000 | 1,000; bounded HTML payload |
| Log axis | Available | Omitted |

D3 offers more linked exploration but adds about 280 kB of JavaScript per result.
This experiment compares rendering and interaction; it does not test a Pj background
execution service. Both use ClinicoPathPj's existing isolated Python process. No
performance or clinical superiority is established by adding the D3 interface.

## Statistical contract

One independent observation per row; numeric marker and exactly two declared reference
levels; event level explicit. Rows missing either role are excluded and counted; original
row identities remain in the explorer. Nonfinite measurements and cutoffs are rejected.
At least one complete observation is needed in each reference group.

All threshold statistics, proportion intervals, optima and AUC are computed in Python.
JavaScript looks up the precomputed empirical state; it does not fit a model. Threshold
changes select another stored state; visual geometry and observation coloring remain local.
Ties move together; >= or <= includes exact equality. Candidate boundaries include both
endpoint classifications. Equal optima select the lowest numeric cutoff. Weighted error
cost is FP weight times FP plus FN weight times FN, with no economic modelling.

Empirical AUC equals the pairwise ranking probability, assigning half credit to marker
ties. No AUC interval or model comparison is supplied. Sensitivity, specificity, PPV, NPV
and accuracy receive fixed-cutoff binomial intervals. Undefined proportions are blank.
These intervals do not account for cutoff selection; PPV/NPV/accuracy depend on the sample's
group proportions. Predictive values from a case-control sample need not describe a population.

## Evidence and limits

The focused Python tests independently enumerate classifications at every boundary and
additional interior/exterior thresholds in both directions. They compare AUC with pairwise
rankings, independently minimize all three objectives, compare exact/Wilson intervals with
R `binom.test()`/uncorrected `prop.test()`, and check agreement with the existing dotplot.
Missing pairs, zero prediction denominators, invalid settings, payload size, script escaping,
JavaScript syntax and the 1,000-row limit are covered.

See [validation evidence](python-d3-cutoff-validation.md) for package and GUI results.
This is an experimental utility, not full baseline parity or clinical release clearance.
