"""Exploratory diagnostic cutoff diagram; one independent observation per row."""
import json
import math
import uuid
from pathlib import Path

from cpj_runtime import Factor, InputError, md_escape

SPEC = {'name': 'pydotdecision',
 'title': 'Interactive Diagnostic Dotplot (Python)',
 'menuGroup': 'Python Lab',
 'menuSubgroup': 'Cutoff explorers',
 'version': '0.1.0',
 'options': [{'name': 'marker',
              'title': 'Numeric test measurement',
              'type': 'Variable',
              'permitted': ['numeric'],
              'suggested': ['continuous'],
              'required': True},
             {'name': 'reference',
              'title': 'Binary reference classification',
              'type': 'Variable',
              'permitted': ['factor'],
              'suggested': ['nominal'],
              'required': True},
             {'name': 'positive',
              'title': 'Reference positive level',
              'type': 'Level',
              'variable': '(reference)',
              'role': 'event'},
             {'name': 'direction',
              'title': 'Positive test rule',
              'type': 'List',
              'options': [{'name': 'high', 'title': 'Measurement >= cutoff'},
                          {'name': 'low', 'title': 'Measurement <= cutoff'}],
              'default': 'high'},
             {'name': 'criterion',
              'title': 'Automatic cutoff criterion',
              'type': 'List',
              'options': [{'name': 'errors', 'title': 'Fewest errors (FP + FN)'},
                          {'name': 'youden', 'title': 'Maximum Youden index'}],
              'default': 'errors'},
             {'name': 'cutoff',
              'title': 'Applied cutoff (blank = automatic)',
              'type': 'String',
              'default': ''},
             {'name': 'logScale',
              'title': 'Logarithmic measurement axis',
              'type': 'Bool',
              'default': False}],
 'results': [{'name': 'summary', 'title': 'Applied Cutoff', 'type': 'Text'},
             {'name': 'explorer', 'title': 'Cutoff Explorer', 'type': 'Html'},
             {'name': 'counts',
              'title': 'Applied Cutoff Classification',
              'type': 'Table',
              'columns': [{'name': 'cell', 'title': 'Classification', 'type': 'text'},
                          {'name': 'n', 'title': 'Count', 'type': 'integer'}]},
             {'name': 'metrics',
              'title': 'Applied Cutoff Accuracy',
              'type': 'Table',
              'columns': [{'name': 'metric', 'title': 'Metric', 'type': 'text'},
                          {'name': 'estimate',
                           'title': 'Estimate',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'lower',
                           'title': '95% CI Lower',
                           'type': 'number',
                           'format': 'pc'},
                          {'name': 'upper',
                           'title': '95% CI Upper',
                           'type': 'number',
                           'format': 'pc'}]},
             {'name': 'staticDotplot',
              'title': 'Applied Cutoff Dotplot',
              'type': 'Image',
              'plot': 'scatter',
              'width': 600,
              'height': 400}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Numeric test measurement',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'marker',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Binary reference classification',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'reference',
                                                  'isTarget': True,
                                                  'maxItemCount': 1},
                                                 {'type': 'LevelSelector',
                                                  'name': 'positive',
                                                  'enable': '(reference)'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Analysis and Model',
                      'collapsed': False,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'direction', 'type': 'ComboBox'},
                                                 {'name': 'criterion', 'type': 'ComboBox'},
                                                 {'name': 'cutoff',
                                                  'type': 'TextBox',
                                                  'format': 'string'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Plots and Interaction',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'logScale', 'type': 'CheckBox'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}


def confusion(values, truth, cutoff, direction):
    import numpy as np
    predicted = values >= cutoff if direction == "high" else values <= cutoff
    return [int(np.sum(predicted & truth)), int(np.sum(predicted & ~truth)),
            int(np.sum(~predicted & truth)), int(np.sum(~predicted & ~truth))]


def automatic_cutoff(values, truth, direction, criterion):
    """O(n log n), tied measurements move together; equal optima choose lowest cutoff."""
    import numpy as np
    unique, indices = np.unique(values, return_inverse=True)
    pos = np.bincount(indices, weights=truth.astype(int), minlength=len(unique))
    neg = np.bincount(indices, weights=(~truth).astype(int), minlength=len(unique))
    if direction == "high":
        cuts = np.append(unique, np.nextafter(unique[-1], np.inf))
        tp = np.append(pos.sum() - np.r_[0, np.cumsum(pos)[:-1]], 0)
        fp = np.append(neg.sum() - np.r_[0, np.cumsum(neg)[:-1]], 0)
    else:
        cuts = np.insert(unique, 0, np.nextafter(unique[0], -np.inf))
        tp, fp = np.r_[0, np.cumsum(pos)], np.r_[0, np.cumsum(neg)]
    objective = fp + pos.sum() - tp if criterion == "errors" else -(tp / pos.sum() - fp / neg.sum())
    usable = np.isfinite(cuts)
    best = np.min(objective[usable])
    tied = usable & np.isclose(objective, best, rtol=0, atol=1e-12)
    return float(cuts[np.flatnonzero(tied)[0]]), int(tied.sum())


def html_document(payload):
    encoded = json.dumps(payload, allow_nan=False, ensure_ascii=True)
    for char, safe in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026")):
        encoded = encoded.replace(char, safe)
    template = (Path(__file__).resolve().parents[2] / "templates" / "dotdecision.html").read_text()
    return template.replace("__ROOT__", "cpjdot" + uuid.uuid4().hex).replace("__PAYLOAD__", encoded)


def run(data, options, out):
    import numpy as np
    from scipy.stats import binomtest
    marker, reference = options.get("marker"), options.get("reference")
    if not marker or not reference:
        raise InputError("Choose a measurement and a binary reference classification.")
    values, group = np.asarray(data[marker], dtype=float), data[reference]
    if not isinstance(group, Factor) or len(group.levels) != 2:
        raise InputError("The reference must have exactly two defined levels.")
    if options.get("positive") not in group.levels:
        raise InputError("Choose the reference positive level explicitly.")
    if np.any(np.isinf(values)):
        raise InputError("Infinite measurements are not supported; check the source data.")
    keep = np.isfinite(values) & (group.codes >= 0)
    row_ids = np.asarray(out.row_ids)[keep] if out.row_ids is not None else np.flatnonzero(keep) + 1
    values = values[keep]
    truth = group.codes[keep] == group.levels.index(options["positive"])
    if len(values) == 0 or not truth.any() or truth.all():
        raise InputError("Both reference groups need complete observations.")
    if len(values) > 5000:
        raise InputError("This experimental dotplot accepts at most 5,000 complete rows. Filter the data first.")
    if options.get("logScale") and np.any(values <= 0):
        raise InputError("A logarithmic axis requires every complete measurement to be positive.")
    direction, criterion = options.get("direction", "high"), options.get("criterion", "errors")
    if direction not in ("high", "low") or criterion not in ("errors", "youden"):
        raise InputError("Unknown direction or automatic cutoff criterion.")
    auto, ties = automatic_cutoff(values, truth, direction, criterion)
    entered = str(options.get("cutoff", "")).strip()
    try:
        cutoff = float(entered) if entered else auto
    except ValueError:
        raise InputError("The applied cutoff must be a finite number, or blank for automatic.") from None
    if not math.isfinite(cutoff):
        raise InputError("The applied cutoff must be finite.")
    tp, fp, fn, tn = confusion(values, truth, cutoff, direction)
    for label, n in zip(("True positive", "False positive", "False negative", "True negative"),
                        (tp, fp, fn, tn)):
        out.row("counts", cell=label, n=n)
    for label, numerator, denominator in (("Sensitivity", tp, tp + fn),
            ("Specificity", tn, tn + fp), ("Positive predictive value", tp, tp + fp),
            ("Negative predictive value", tn, tn + fn), ("Accuracy", tp + tn, len(values))):
        ci = binomtest(numerator, denominator).proportion_ci() if denominator else None
        out.row("metrics", metric=label, estimate=numerator / denominator if denominator else None,
                lower=ci.low if ci else None, upper=ci.high if ci else None)
    excluded = len(keep) - len(values)
    mode = "manual" if entered else ("fewest errors" if criterion == "errors" else "maximum Youden index")
    rule = ">=" if direction == "high" else "<="
    out.markdown("summary", md_escape(
        f"Applied rule: {marker} {rule} {cutoff!r}; cutoff mode: {mode}. "
        f"Reference positive: {options['positive']}. Complete rows: {len(values)}; excluded: {excluded}. "
        f"The automatic criterion has {ties} tied optimum cutoffs among the evaluated boundaries; "
        "the lowest numeric cutoff is selected. Dragging previews a cutoff; Apply cutoff updates the native tables."))
    out.note("metrics", "Exact Clopper-Pearson intervals assume independent rows and a fixed cutoff. "
             "Intervals do not account for selecting the cutoff on these data. PPV, NPV and accuracy reflect "
             "this sample's group proportions; a case-control sample does not estimate population predictive values.")
    out.info("Exploratory diagnostic cutoff analysis: use one independent observation per row. "
             "A cutoff selected on these data requires separate validation.")
    payload = {"marker": marker, "reference": reference, "positive": options["positive"],
               "negative": group.levels[1 - group.levels.index(options["positive"])] ,
               "values": values.tolist(), "truth": truth.astype(int).tolist(),
               "rows": row_ids.tolist(), "cutoff": cutoff, "automatic": auto,
               "direction": direction, "log": bool(options.get("logScale"))}
    out.html("explorer", html_document(payload))

    shown = np.log10(values) if options.get("logScale") else values
    shown_cutoff = (math.log10(cutoff) if cutoff > 0 else None) if options.get("logScale") else cutoff
    out.plot("staticDotplot", [dict(x=float(x), y=int(y), group=options["positive"] if y else payload["negative"])
             for x,y in zip(shown,truth)], reference=shown_cutoff,
             xlab=("log10 " if options.get("logScale") else "")+marker, ylab=reference)
