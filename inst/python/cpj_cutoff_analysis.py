"""Shared cutoff workflow: statistical results independent of browser renderer."""
import math
import numpy as np
from cpj_runtime import Factor, InputError, md_escape
from cpj_cutoff import states, select, METRICS

def run_cutoff(data, options, out, render_html, *, result_type="html"):
    marker, reference = options.get("marker"), options.get("reference")
    if not marker or not reference:
        raise InputError("Choose a measurement and a binary reference classification.")
    values, group = np.asarray(data[marker], dtype=float), data[reference]
    if not isinstance(group, Factor) or len(group.levels) != 2:
        raise InputError("The reference must have exactly two defined levels.")
    if options.get("positive") not in group.levels:
        raise InputError("Choose the reference positive level explicitly.")
    if np.any(np.isinf(values)):
        raise InputError("Infinite measurements are not supported.")
    keep = np.isfinite(values) & (group.codes >= 0)
    row_ids = np.asarray(out.row_ids)[keep] if out.row_ids is not None else np.flatnonzero(keep) + 1
    values = values[keep]
    truth = group.codes[keep] == group.levels.index(options["positive"])
    if not len(values) or truth.all() or not truth.any():
        raise InputError("Both reference groups need complete observations.")
    if len(values) > 1000:
        raise InputError("This experiment accepts at most 1,000 complete rows. Filter the data first.")
    direction, criterion = options.get("direction", "ge"), options.get("criterion", "errors")
    if direction not in ("ge", "le") or criterion not in ("errors", "youden", "cost"):
        raise InputError("Unknown direction or cutoff criterion.")
    method = options.get("ciMethod", "exact")
    try:
        confidence = float(options.get("ciWidth", 95))
        fp_cost, fn_cost = float(options.get("fpCost", 1)), float(options.get("fnCost", 4))
    except (ValueError, TypeError):
        raise InputError("Confidence and error weights must be numbers.") from None
    if not 50 <= confidence <= 99.9 or method not in ("exact", "wilson"):
        raise InputError("Choose an interval method and confidence level between 50 and 99.9%.")
    if not all(math.isfinite(c) and 0 <= c <= 1000 for c in (fp_cost, fn_cost)):
        raise InputError("Error weights must be finite numbers between 0 and 1,000.")
    curves = {d: states(values, truth, d, method, confidence / 100, fp_cost, fn_cost) for d in ("ge", "le")}
    curve = curves[direction]
    optimum = curve["optima"][criterion]
    auto = curve["points"][optimum["point"]]["cutoff"]
    entered = str(options.get("cutoff", "")).strip()
    try:
        cutoff = float(entered) if entered else auto
    except ValueError:
        raise InputError("The applied cutoff must be a finite number or blank for automatic.") from None
    if not math.isfinite(cutoff):
        raise InputError("The applied cutoff must be finite.")
    point = select(curve["points"], cutoff, direction)
    for key, label in zip(("tp", "fp", "fn", "tn"), ("True positive", "False positive", "False negative", "True negative")):
        out.row("counts", cell=label, n=point[key])
    for label, (estimate, lower, upper) in zip(METRICS, point["metrics"]):
        out.row("metrics", metric=label, estimate=estimate, lower=lower, upper=upper)
    for label, value in [("Empirical AUC", curve["auc"]), ("Youden index", point["youden"]), ("Applied cutoff", cutoff), ("Weighted error cost", point["cost"]), ("Complete rows", len(values)), ("Excluded rows", len(keep)-len(values)), ("Tied optimal boundaries", optimum["ties"])]:
        out.row("rocSummary", metric=label, value=value)
    negative = group.levels[1-group.levels.index(options["positive"])]
    rule = ">=" if direction == "ge" else "<="
    out.markdown("summary", md_escape(f"Saved jamovi rule: {marker} {rule} {cutoff!r}; reference positive: {options['positive']}. Complete rows: {len(values)}; excluded: {len(keep)-len(values)}. Native tables and images use this rule. Browser controls preview precomputed results; Apply to HTML tables changes only the local snapshot. To persist a rule, edit the jamovi direction and applied-cutoff options. Reopening restores those saved options."))
    out.note("metrics", f"{confidence:g}% {method} intervals assume independent observations and a fixed cutoff; selection uncertainty is excluded. PPV, NPV and accuracy reflect this sample's group proportions. Undefined proportions are blank.")
    out.note("rocSummary", "Empirical AUC uses tied observations together; no AUC inference. Optimal boundaries include both endpoint classifications; ties select the lowest numeric cutoff. Error weights are simple FP/FN weights, not an economic model.")
    out.info("Experimental comparison with the existing dotplot. Use independent rows and validate selected cutoffs in separate data. Browser snapshots are not saved analysis options.")
    payload = dict(rows=[dict(row=str(r), value=float(v), positive=bool(t)) for r,v,t in zip(row_ids,values,truth)], initial=cutoff, automatic=auto, curves=curves, expected={k:point[k] for k in ("tp","fp","fn","tn")}, measurement=marker, positive=options["positive"], negative=negative, source="Python threshold-state lookup", excluded=len(keep)-len(values), direction=direction, criterion=criterion, fpCost=fp_cost, fnCost=fn_cost, method=method, confidence=confidence, prevalence=float(truth.mean()), metricNames=METRICS)
    if result_type == "svg":
        out.svg("explorer", render_html(payload))
        out.markdown("summary", md_escape(f"Native applied rule: {marker} {rule} {cutoff!r}; reference positive: {options['positive']}. Complete rows: {len(values)}; excluded: {len(keep)-len(values)}. Native tables and static images use saved jamovi options. The SVG previews Python-computed threshold states locally. Apply updates only its local snapshot label. Export captures the displayed SVG. Edit native options to persist an analysis rule; reopening interactive content starts from saved options."))
    else:
        out.html("explorer", render_html(payload))
    out.plot("staticDotplot", [dict(x=float(v), y=int(t), group=options["positive"] if t else negative) for v,t in zip(values,truth)], reference=cutoff, xlab=marker, ylab=reference)
    plot = [dict(x=p["fpr"], y=p["tpr"], group="Empirical ROC") for p in sorted(curve["points"], key=lambda p:(p["fpr"],p["tpr"]))]
    plot += [dict(x=0,y=0,group="Chance"),dict(x=1,y=1,group="Chance"),dict(x=point["fpr"],y=point["tpr"],group="Applied rule")]
    out.plot("staticROC", plot, xlab="False positive rate", ylab="Sensitivity")
