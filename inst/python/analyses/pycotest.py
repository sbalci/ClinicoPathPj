"""Co-testing: post-test probabilities after two diagnostic tests run in parallel.

Port of the ClinicoPath umbrella analysis cotest (R/cotest.b.R). Both tests are done on the same
subject before either result is known; each result combination, and the parallel rule (positive
if either test is positive), gets a combined likelihood ratio and a post-test probability.
Dependence is a correlation (phi) between the two results within each disease group: the joint
positive probability is m1 m2 + phi sqrt(m1 (1 - m1) m2 (1 - m2)), i.e. the conditional
covariance of Gardner et al. (Prev Vet Med 2000;45:107-122). A phi the entered values cannot
attain is truncated to the Frechet bound of that probability, with a warning, as the umbrella does.

New in this port: uncertainty intervals. Each value with a sample size n > 0 is drawn from its
Jeffreys posterior Beta(x + 0.5, n - x + 0.5), x = value * n; for one value alone the percentile
interval is the Jeffreys interval (Brown, Cai and DasGupta, Stat Sci 2001;16:101-133). The
correlations stay fixed, and a draw at which they are not attainable is discarded and counted.
"""
import math

from cpj_runtime import InputError, fmt_num, md_escape

SPEC = {
    "name": "pycotest",
    "title": "Co-Testing Analysis (Python)",
    "menuGroup": "ClinicoPathPj",
    "menuSubgroup": "Diagnostic tests",
    "version": "0.1.0",
    "options": [
        {"name": "name1", "type": "String", "title": "Name of test 1 (optional)", "default": ""},
        {"name": "sens1", "type": "Number", "title": "Test 1 sensitivity (0-1)", "default": 0.80, "min": 0.01, "max": 0.999},
        {"name": "spec1", "type": "Number", "title": "Test 1 specificity (0-1)", "default": 0.90, "min": 0.01, "max": 0.999},
        {"name": "name2", "type": "String", "title": "Name of test 2 (optional)", "default": ""},
        {"name": "sens2", "type": "Number", "title": "Test 2 sensitivity (0-1)", "default": 0.75, "min": 0.01, "max": 0.999},
        {"name": "spec2", "type": "Number", "title": "Test 2 specificity (0-1)", "default": 0.95, "min": 0.01, "max": 0.999},
        {"name": "prevalence", "type": "Number", "title": "Prevalence, the pre-test probability (0-1)",
         "default": 0.10, "min": 0.001, "max": 0.999},
        {"name": "indep", "type": "Bool", "title": "Assume the two tests are conditionally independent", "default": False},
        {"name": "depPos", "type": "Number", "title": "Correlation (phi) among subjects with disease",
         "default": 0.05, "min": -1, "max": 1},
        {"name": "depNeg", "type": "Number", "title": "Correlation (phi) among subjects without disease",
         "default": 0.05, "min": -1, "max": 1},
        {"name": "ci", "type": "Bool", "title": "Uncertainty intervals (Monte Carlo)", "default": False},
        {"name": "nSens1", "type": "Integer", "title": "Sample size of test 1 sensitivity (diseased; 0 = known)",
         "default": 0, "min": 0, "max": 10000000},
        {"name": "nSpec1", "type": "Integer", "title": "Sample size of test 1 specificity (non-diseased; 0 = known)",
         "default": 0, "min": 0, "max": 10000000},
        {"name": "nSens2", "type": "Integer", "title": "Sample size of test 2 sensitivity (diseased; 0 = known)",
         "default": 0, "min": 0, "max": 10000000},
        {"name": "nSpec2", "type": "Integer", "title": "Sample size of test 2 specificity (non-diseased; 0 = known)",
         "default": 0, "min": 0, "max": 10000000},
        {"name": "nPrev", "type": "Integer", "title": "Sample size of the prevalence (0 = known)",
         "default": 0, "min": 0, "max": 10000000},
        {"name": "ciWidth", "type": "Number", "title": "Interval level (%)", "default": 95, "min": 50, "max": 99},
        {"name": "draws", "type": "Integer", "title": "Monte Carlo draws", "default": 20000, "min": 1000, "max": 200000},
        {"name": "seed", "type": "Integer", "title": "Random seed", "default": 1, "min": 0, "max": 2147483647},
        {"name": "showPlot", "type": "Bool", "title": "Plot of post-test probabilities", "default": False},
    ],
    "results": [
        {"name": "summary", "type": "Text", "title": "Interpretation"},
        {"name": "params", "type": "Table", "title": "Test Parameters", "columns": [
            {"name": "test", "title": "Test", "type": "text"},
            {"name": "sens", "title": "Sensitivity", "type": "number", "format": "pc"},
            {"name": "spec", "title": "Specificity", "type": "number", "format": "pc"},
            {"name": "plr", "title": "Positive LR", "type": "number"},
            {"name": "nlr", "title": "Negative LR", "type": "number"},
        ]},
        {"name": "posttest", "type": "Table", "title": "Co-Testing Results", "columns": [
            {"name": "scenario", "title": "Result", "type": "text"},
            {"name": "probText", "title": "Post-test probability", "type": "text"},
            {"name": "prob", "title": "Post-test probability (exact)", "type": "number", "visible": False},
            {"name": "relative", "title": "Relative to prevalence", "type": "number"},
            {"name": "odds", "title": "Post-test odds", "type": "number"},
            {"name": "lr", "title": "Combined LR", "type": "number"},
        ]},
        {"name": "intervals", "type": "Table", "title": "Uncertainty Intervals", "visible": "(ci)", "columns": [
            {"name": "scenario", "title": "Result", "type": "text"},
            {"name": "probText", "title": "Post-test probability", "type": "text"},
            {"name": "lowerText", "title": "Lower", "type": "text", "superTitle": "Percentile interval"},
            {"name": "upperText", "title": "Upper", "type": "text", "superTitle": "Percentile interval"},
            {"name": "prob", "title": "Post-test probability (exact)", "type": "number", "visible": False},
            {"name": "lower", "title": "Lower (exact)", "type": "number", "visible": False},
            {"name": "upper", "title": "Upper (exact)", "type": "number", "visible": False},
        ]},
        {"name": "probPlot", "type": "Image", "title": "Post-Test Probabilities", "plot": "interval",
         "width": 600, "height": 300, "visible": "(showPlot)"},
        {"name": "joint", "type": "Table", "title": "Joint Probabilities of the Two Results", "columns": [
            {"name": "pattern", "title": "Result", "type": "text"},
            {"name": "pDText", "title": "With disease", "type": "text"},
            {"name": "pNText", "title": "Without disease", "type": "text"},
            {"name": "pD", "title": "With disease (exact)", "type": "number", "visible": False},
            {"name": "pN", "title": "Without disease (exact)", "type": "number", "visible": False},
        ]},
        {"name": "dependence", "type": "Table", "title": "Conditional Dependence", "columns": [
            {"name": "group", "title": "Subjects", "type": "text"},
            {"name": "entered", "title": "Entered phi", "type": "number"},
            {"name": "fitted", "title": "Fitted phi", "type": "number"},
            {"name": "low", "title": "Lowest", "type": "number", "superTitle": "Attainable phi"},
            {"name": "high", "title": "Highest", "type": "number", "superTitle": "Attainable phi"},
            {"name": "cov", "title": "Covariance", "type": "number"},
        ]},
    ],
}

TOL = 1e-10  # cotest.b.R's NUMERICAL_TOLERANCE: a joint probability this close to 0 is a structural zero
INPUTS = (("sens1", "nSens1"), ("spec1", "nSpec1"), ("sens2", "nSens2"), ("spec2", "nSpec2"), ("prevalence", "nPrev"))
TITLES = {option["name"]: option["title"] for option in SPEC["options"]}
DEFAULTS = {option["name"]: option["default"] for option in SPEC["options"]}
TAIL_DRAWS = 10  # an interval needs at least this many draws expected beyond each of its limits


def _cells(np, m1, m2, phi):
    """Joint probabilities (++, +-, -+, --; test 1 first) of two results with positive rates m1, m2
    (sensitivities with disease, 1 - specificities without) and correlation phi, plus the ++
    probability before truncation to its Frechet bounds max(0, m1 + m2 - 1) .. min(m1, m2).
    Scalars give the point estimate, arrays one column per Monte Carlo draw."""
    raw = m1 * m2 + phi * np.sqrt(m1 * (1 - m1) * m2 * (1 - m2))
    p11 = np.clip(raw, np.maximum(0.0, m1 + m2 - 1), np.minimum(m1, m2))
    p10, p01 = m1 - p11, m2 - p11
    return np.array([p11, p10, p01, 1 - (p11 + p10 + p01)]), raw


def _patterns(cells):
    """P(result | group) in table order: either positive, test 1 only, test 2 only, both, neither."""
    return [1 - cells[3], cells[1], cells[2], cells[0], cells[3]]


def _posterior(p_d, p_n, prior_odds):
    """Combined LR, post-test odds and probability of one result, None when undefined. A result that
    cannot occur without disease has an infinite LR and probability 1, as in cotest.b.R."""
    if abs(p_n) < TOL:
        return (None, None, None) if abs(p_d) < TOL else (math.inf, math.inf, 1.0)
    lr = 0.0 if abs(p_d) < TOL else p_d / p_n
    odds = prior_odds * lr
    return lr, odds, odds / (1 + odds)


_sig = fmt_num  # significant digits without exponent (R's formatC 'fg'), shared with the other analyses


def _pct(p):
    """A probability as cotest.b.R's .fmtPct prints it: never 0.0% or 100.0% unless exactly so."""
    if p is None:
        return "not estimable"
    if p <= 0 or p >= 1:
        return "0%" if p <= 0 else "100%"
    if p < 1e-5 or p > 1 - 1e-5:
        return "<0.001%" if p < 1e-5 else ">99.999%"
    tail = min(p, 1 - p)
    decimals = 1 if tail >= 0.01 else math.ceil(-math.log10(100 * tail)) + 1
    return f"{100 * p:.{decimals}f}%"


def _pct_cell(p):
    """A table cell in the interpretation's format; undefined stays None (shown as '.')."""
    return None if p is None else _pct(p)


def _change(ratio):
    if ratio is None:
        return "not estimable"
    if _sig(ratio) == "1":
        return "about the same as the prevalence"
    return f"{_sig(ratio)}x increase" if ratio > 1 else f"{_sig(ratio)}x of prevalence, a decrease"


def _shift(lr):
    """Reading aid from the combined LR (Jaeschke et al. 1994 bands, mirrored below 1)."""
    if lr is None:
        return "not estimable"
    if math.isinf(lr) or lr == 0:
        return (f"{'certain' if lr else 'excluded'} by construction under the dependence entered, "
                f"not an estimate (see the table notes)")
    bands = ((lr > 10, "a large shift towards disease"), (lr > 5, "a moderate shift towards disease"),
             (lr > 2, "a small shift towards disease"), (lr >= 0.5, "little shift either way"),
             (lr >= 0.2, "a small shift away from disease"), (lr >= 0.1, "a moderate shift away from disease"),
             (True, "a large shift away from disease"))
    return f"combined likelihood ratio {_sig(lr)}; by the usual rule of thumb, " + next(t for hit, t in bands if hit)


def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _simulate(np, values, sizes, phi, draws, seed):
    """Monte Carlo post-test probabilities (5 x accepted draws) and the number of draws discarded."""
    # one stream per input, so one input's sample size never changes another input's draws
    streams = [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(len(INPUTS))]
    x = {}
    for (key, size), rng in zip(INPUTS, streams):
        p, n = values[key], sizes[size]
        x[key] = rng.beta(p * n + 0.5, (1 - p) * n + 0.5, draws) if n > 0 else np.full(draws, p)
    cells_d, raw_d = _cells(np, x["sens1"], x["sens2"], phi[0])
    cells_n, raw_n = _cells(np, 1 - x["spec1"], 1 - x["spec2"], phi[1])
    ok = (np.abs(raw_d - cells_d[0]) <= TOL) & (np.abs(raw_n - cells_n[0]) <= TOL)  # phi attainable here
    prev = x["prevalence"][ok]
    p_d = np.maximum(np.array(_patterns(cells_d))[:, ok], 0.0)
    p_n = np.maximum(np.array(_patterns(cells_n))[:, ok], 0.0)
    return prev * p_d / (prev * p_d + (1 - prev) * p_n), draws - int(ok.sum())


def _intervals(np, out, rows, values, sizes, phi, indep, fits, options, labels):
    """Fill the Uncertainty Intervals table; return what the summary needs, or None if not computed."""
    level, draws, seed = float(options["ciWidth"]), int(options["draws"]), int(options["seed"])
    if not 0 < level < 100 or draws < 1 or seed < 0:
        raise InputError("The interval level must lie between 0 and 100, the number of draws must be at least 1 "
                         "and the seed must be 0 or more.")
    drawn = [f"{labels[key]} (n = {sizes[size]})" for key, size in INPUTS if sizes[size] > 0]
    fixed = [labels[key] for key, size in INPUTS if sizes[size] == 0]
    why, mc = None, None
    if not drawn:
        why = ("No interval was computed: every sample size is 0, so all values are treated as known and there is no "
               "sampling uncertainty to propagate. Enter the number of subjects behind at least one value.")
    elif any(fit["truncated"] or 0.0 in fit["cells"] for fit in fits):
        why = ("No interval was computed: a correlation is at, or was truncated to, the limit the entered values allow, "
               "so the point estimates come from a boundary model in which some combination of results is impossible. "
               "Move the correlation into the attainable range shown in Conditional Dependence.")
    else:
        post, discarded = _simulate(np, values, sizes, phi, draws, seed)
        accepted, tail = post.shape[1], (1 - level / 100) / 2
        need = math.ceil(TAIL_DRAWS / tail)
        if accepted < need:
            kept = (f"{accepted} of {draws} draws remained after discarding those at which the fixed correlations are "
                    f"not attainable, which is" if discarded else f"{draws} draws are")
            why = (f"No interval was computed: {kept} fewer than the {need} needed for a {level:g}% interval (at least "
                   f"{TAIL_DRAWS} draws expected beyond each limit). Increase the number of draws"
                   + (" or move the correlations toward 0." if discarded else "."))
        else:
            limits = np.percentile(post, [100 * tail, 100 * (1 - tail)], axis=1)
            finite = np.isfinite(post).all(axis=1)
            for row, low, high, ok in zip(rows, limits[0], limits[1], finite):
                if ok:
                    row["lower"], row["upper"] = float(low), float(high)
            # "accepted of draws": the draws option and the seed are what reproduce the result
            used = f"{accepted} of {draws}" if discarded else f"{draws}"
            mc = {"level": level, "seed": seed, "used": used, "discarded": discarded, "drawn": drawn, "fixed": fixed}
    for row in rows:
        out.row("intervals", scenario=row["label"], prob=row["prob"], lower=row.get("lower"), upper=row.get("upper"),
                probText=_pct_cell(row["prob"]), lowerText=_pct_cell(row.get("lower")),
                upperText=_pct_cell(row.get("upper")))
    if why:
        out.note("intervals", why)
        return None
    out.note("intervals", f"{level:g}% percentile intervals over {used} Monte Carlo draws (seed {seed}; numpy "
                          f"{np.__version__}, PCG64). Re-run with another seed to check that the limits are stable.")
    out.note("intervals", "Each value with a sample size n > 0 was drawn from its Jeffreys posterior "
                          "Beta(x + 0.5, n - x + 0.5), with x = value times n (not rounded), independently of the other "
                          f"values: {_join(drawn)}." + (f" Held at the entered value (n = 0): {_join(fixed)}." if fixed else "")
                          + (" The tests were assumed conditionally independent in every draw." if indep else
                             " The correlations (phi) were held fixed at the entered values."))
    if not indep:
        out.note("intervals", f"{discarded} of {draws} draws ({100 * discarded / draws:.1f}%) were discarded because the "
                              f"fixed correlations are not attainable at the drawn sensitivities or specificities; the "
                              f"intervals use the remaining {accepted}"
                              + (", so they are conditional on values at which those correlations can occur."
                                 if discarded else "."))
    if not finite.all():
        out.note("intervals", "A row without limits had an undefined post-test probability in some draws.")
    out.note("intervals", "The intervals reflect only the sampling uncertainty of the values with a sample size. They do "
                          "not cover bias in those values (for example spectrum or verification bias) or uncertainty in "
                          "the correlations, and when both tests were evaluated in the same subjects they ignore the "
                          "correlation between the two estimates.")
    return mc


def run(data, options, out):
    import numpy as np

    names = [str(options[key]).strip() or default for key, default in (("name1", "Test 1"), ("name2", "Test 2"))]
    values, sizes = {}, {}
    for key, size in INPUTS:
        values[key], sizes[size] = float(options[key]), int(options[size])
        if not 0 < values[key] < 1:
            raise InputError(f"{TITLES[key]} must lie strictly between 0 and 1; it is {options[key]}.")
        if sizes[size] < 0:
            raise InputError(f"{TITLES[size]} must be 0 or more; it is {options[size]}.")
    entered = (float(options["depPos"]), float(options["depNeg"]))
    if not all(-1 <= r <= 1 for r in entered):
        raise InputError("The correlations (phi) must lie between -1 and 1.")
    se1, sp1, se2, sp2, prev = (values[key] for key, _ in INPUTS)
    indep = bool(options["indep"])
    phi = (0.0, 0.0) if indep else entered
    labels = {"sens1": f"{names[0]} sensitivity", "spec1": f"{names[0]} specificity",
              "sens2": f"{names[1]} sensitivity", "spec2": f"{names[1]} specificity", "prevalence": "the prevalence"}

    # ---- checks on the entered values (cotest.b.R's validation notices) ----
    for name, se, sp in ((names[0], se1, sp1), (names[1], se2, sp2)):
        if se + sp < 1:
            out.warn(f"{name} is below the chance diagonal (sensitivity plus specificity below 1): a positive result "
                     f"makes disease less likely, not more. Check whether its sensitivity and specificity, or its "
                     f"positive and negative categories, have been entered the wrong way round.")
        elif se + sp < 1.1:
            out.warn(f"{name} has low discriminatory power (sensitivity plus specificity below 1.1, i.e. a Youden "
                     f"index below 0.1). Check its likelihood ratios in the Test Parameters table: an operating point "
                     f"close to the chance diagonal can still give an informative LR+ or LR- when sensitivity and "
                     f"specificity are very unequal.")
    if prev < 0.05 or prev > 0.95:
        low = prev < 0.05
        out.warn(f"{'Low' if low else 'Very high'} prevalence ({'below 5%' if low else 'above 95%'}): check that this "
                 f"is the pre-test probability in the population you are actually testing. At a prevalence this "
                 f"{'low' if low else 'high'} a small absolute change (for example from "
                 f"{'1% to 2%' if low else '98% to 99%'}) about doubles the pre-test odds and moves every post-test "
                 f"probability with it, so re-run with a plausible range, or enter the sample size behind the "
                 f"prevalence, before acting on the numbers.")
    elif prev > 0.5:
        out.info("High prevalence (above 50%) detected. Ensure this reflects your actual clinical population.")

    # ---- joint probabilities in each disease group (point estimate, as cotest.b.R) ----
    fits = []
    for (m1, m2), r, word, what in zip(((se1, se2), (1 - sp1, 1 - sp2)), phi, ("with", "without"),
                                       ("sensitivities", "specificities")):
        cells, raw = _cells(np, m1, m2, r)
        sd = math.sqrt(m1 * (1 - m1) * m2 * (1 - m2))
        fit = {"cells": [0.0 if abs(c) < TOL else float(c) for c in cells], "truncated": bool(abs(raw - cells[0]) > TOL),
               "fitted": float(cells[0] - m1 * m2) / sd, "cov": float(cells[0] - m1 * m2),
               "low": (max(0.0, m1 + m2 - 1) - m1 * m2) / sd, "high": (min(m1, m2) - m1 * m2) / sd}
        fits.append(fit)
        if fit["truncated"]:
            out.warn(f"The correlation (phi) entered for subjects {word} disease, {_sig(r)}, is not attainable with these "
                     f"{what} (attainable range {_sig(fit['low'])} to {_sig(fit['high'])}), so the probability that both "
                     f"tests are positive in that group was truncated from {raw:.4f} to its limit {cells[0]:.4f}. The "
                     f"model fitted is therefore not the one you specified, and at least one combination of results "
                     f"becomes impossible in that group. Move the value toward 0, into the attainable range.")

    out.row("params", test=names[0], sens=se1, spec=sp1, plr=se1 / (1 - sp1), nlr=(1 - se1) / sp1)
    out.row("params", test=names[1], sens=se2, spec=sp2, plr=se2 / (1 - sp2), nlr=(1 - se2) / sp2)
    out.note("params", "LR+ is how many times more likely a positive result is in someone with the disease than in "
                       "someone without it; LR- is the same ratio for a negative result. A common rule of thumb "
                       "(Jaeschke et al. 1994) reads values above 10 or below 0.1 as large shifts in the probability of "
                       "disease, 5 to 10 or 0.1 to 0.2 as moderate, 2 to 5 or 0.2 to 0.5 as small, and 0.5 to 2 as "
                       "little change; it is a convention to help reading, not a threshold.")
    if not indep:
        out.note("params", "These likelihood ratios describe each test on its own. Because the two tests are modelled "
                           "as conditionally dependent, the combined likelihood ratio is not their product; use the "
                           "Combined LR column of the Co-Testing Results table instead.")
    out.note("params", "Worth checking: if a test's sensitivity plus specificity is below 1, a positive result makes "
                       "disease less likely, which usually means its sensitivity and specificity (or its positive and "
                       "negative categories) have been entered the wrong way round. Prevalence should be the pre-test "
                       "probability in the population you are testing, not the figure from the study that validated "
                       "the test.")

    # ---- post-test probabilities ----
    scenario = ["Either Test Positive (Parallel Rule)", f"{names[0]} Positive Only", f"{names[1]} Positive Only",
                "Both Tests Positive", "Both Tests Negative"]
    rows = []
    for label, p_d, p_n in zip(scenario, _patterns(fits[0]["cells"]), _patterns(fits[1]["cells"])):
        lr, odds, prob = _posterior(p_d, p_n, prev / (1 - prev))
        rows.append({"label": label, "lr": lr, "prob": prob, "relative": None if prob is None else prob / prev})
        out.row("posttest", scenario=label, prob=prob, probText=_pct_cell(prob), relative=rows[-1]["relative"],
                odds=odds, lr=lr)
    out.note("posttest", "Combined LR = probability of the row's result among subjects with disease divided by its "
                         "probability among subjects without disease; post-test odds = pre-test odds x combined LR; "
                         "relative to prevalence = post-test probability / prevalence.")
    out.note("posttest", "Model: the two tests are conditionally independent." if indep else
             f"Model: conditional dependence, fitted correlation (phi) {_sig(fits[0]['fitted'])} among subjects with "
             f"disease and {_sig(fits[1]['fitted'])} among subjects without disease (see Conditional Dependence).")
    for row in rows:
        if row["lr"] is None:
            out.note("posttest", f"{row['label']}: under the dependence entered this combination of results cannot "
                                 f"occur in either group, so no post-test probability exists. Move the correlation "
                                 f"toward 0.")
        elif math.isinf(row["lr"]) or row["lr"] == 0:
            certain = math.isinf(row["lr"])
            out.note("posttest", f"{row['label']}: under the dependence entered this combination of results cannot "
                                 f"occur in subjects {'without' if certain else 'with'} disease, so its probability is "
                                 f"{1 if certain else 0} by construction, not an estimate"
                                 f"{' (its LR and odds are infinite)' if certain else ''}. Move the correlation "
                                 f"toward 0.")

    mc = _intervals(np, out, rows, values, sizes, phi, indep, fits, options, labels) if options["ci"] else None
    if mc:
        out.note("posttest", "Point estimates from the values entered; their uncertainty intervals are in the "
                             "Uncertainty Intervals table.")
    else:
        out.note("posttest", "Sensitivity, specificity and prevalence are treated as exact, so these post-test "
                             "probabilities carry no uncertainty interval. "
                             + ("Uncertainty Intervals says why none was computed." if options["ci"] else
                                "Tick Uncertainty intervals and enter the sample sizes behind the values to propagate "
                                "their sampling uncertainty."))

    if options["showPlot"]:
        bars = f"bars: {mc['level']:g}% uncertainty interval; " if mc else ""
        out.plot("probPlot", [{"label": row["label"], "estimate": 100 * row["prob"],
                               "lower": 100 * row["lower"] if "lower" in row else None,
                               "upper": 100 * row["upper"] if "upper" in row else None}
                              for row in rows if row["prob"] is not None],
                 xlab=f"Post-test probability of disease, % ({bars}dashed line: prevalence)", ylab="",
                 reference=100 * prev)

    # ---- the fitted joint distribution (cotest.b.R's Test Dependence panel) ----
    for label, p_d, p_n in zip(scenario[1:], _patterns(fits[0]["cells"])[1:], _patterns(fits[1]["cells"])[1:]):
        out.row("joint", pattern=label, pD=p_d, pN=p_n, pDText=_pct_cell(p_d), pNText=_pct_cell(p_n))
    out.note("joint", "Probability of each combination of the two results within each group; each column sums to "
                      "100%. Under conditional independence each one is the product of the two single-test "
                      "probabilities.")
    for fit, group, r in zip(fits, ("With disease", "Without disease"), entered):
        out.row("dependence", group=group, entered=None if indep else r, fitted=fit["fitted"], low=fit["low"],
                high=fit["high"], cov=fit["cov"])
    if indep:
        out.note("dependence", "Conditional independence is assumed, so the correlation boxes are not used and phi = 0 "
                               "in both groups.")
    out.note("dependence", "phi is the correlation between the two test results within a disease group; 0 is "
                           "conditional independence. The attainable range follows from the sensitivities (with "
                           "disease) or specificities (without disease) entered; a value outside it is truncated to the "
                           "nearest limit.")
    out.note("dependence", "Covariance = phi x sqrt(Se1 (1 - Se1) Se2 (1 - Se2)) with disease, and the same with the "
                           "specificities without disease: the conditional covariance of Gardner et al. (2000). Convert "
                           "a published covariance to phi before entering it.")

    out.markdown("summary", _summary(names, values, rows, indep, fits, entered, mc))


def _summary(names, values, rows, indep, fits, entered, mc):
    """Reading guide and copy-ready sentence (cotest.b.R's Explanation panel), written as plain text
    and escaped whole, so no test name or number can turn into Markdown."""
    prev = values["prevalence"]

    def interval(row):
        if mc and "lower" in row:
            return f"{mc['level']:g}% uncertainty interval {_pct(row['lower'])} to {_pct(row['upper'])}"
        return ""

    def quoted(row):
        return _pct(row["prob"]) + (f" ({interval(row)})" if interval(row) else "")

    lines = ["**Reading the results (a rough guide).** " + md_escape(f"Prevalence (pre-test probability): {_pct(prev)}."), ""]
    for row in rows:
        detail = "; ".join(part for part in (interval(row), _change(row["relative"])) if part)
        lines.append(f"- **{md_escape(row['label'])}:** "
                     + md_escape(f"{_pct(row['prob'])} ({detail}); {_shift(row['lr'])}."))
    lines += ["", md_escape("These descriptions apply a conventional rule of thumb for likelihood ratios (Jaeschke et "
                            "al. 1994) to help read the tables. They are a guide, not a clinical judgement."), ""]

    either, both, neither = rows[0], rows[3], rows[4]
    ratio = neither["relative"]
    if ratio is None or _sig(ratio) == "1":
        towards = "not estimable" if ratio is None else "about the same as the prevalence"
    else:
        towards = f"{'reduced' if ratio < 1 else 'raised'} to {_sig(ratio)}x of prevalence"
    entered_pct = [f"{_sig(100 * values[key], 4)}%" for key in ("sens1", "spec1", "sens2", "spec2")]
    text = (f"Co-testing with {names[0]} (sensitivity {entered_pct[0]}, specificity {entered_pct[1]}) and {names[1]} "
            f"(sensitivity {entered_pct[2]}, specificity {entered_pct[3]}) at a pre-test probability of {_pct(prev)} "
            f"gave calculated post-test probabilities of disease of {quoted(either)} after a positive result on either "
            f"test (the parallel rule; {_change(either['relative'])}), {quoted(both)} when both tests were positive "
            f"({_change(both['relative'])}) and {quoted(neither)} when both were negative ({towards}).")
    if indep:
        text += " The calculation assumes both tests are performed in parallel and are conditionally independent."
    else:
        truncated = "".join(f" (requested {_sig(r)} among {group}, truncated to the nearest value the entered {what} allow)"
                            for fit, r, group, what in zip(fits, entered, ("diseased", "non-diseased"),
                                                           ("sensitivities", "specificities")) if fit["truncated"])
        text += (f" The calculation assumes both tests are performed in parallel and allows conditional dependence "
                 f"(correlation {_sig(fits[0]['fitted'])} among diseased and {_sig(fits[1]['fitted'])} among "
                 f"non-diseased subjects){truncated}.")
        if entered == (DEFAULTS["depPos"], DEFAULTS["depNeg"]):
            text += " These dependence values are the analysis defaults, not estimates from data."
    if any(row["prob"] in (0.0, 1.0) for row in (either, both, neither)):
        text += (" A probability of exactly 0% or 100% here is set by the dependence being at the limit the entered "
                 "values allow; it is not an estimate.")
    if mc:
        text += (f" Uncertainty intervals are {mc['level']:g}% percentile intervals over {mc['used']} Monte Carlo "
                 f"draws (seed {mc['seed']}) from Jeffreys Beta posteriors for {_join(mc['drawn'])}"
                 + (f"; {_join(mc['fixed'])} {'was' if len(mc['fixed']) == 1 else 'were'} treated as exact"
                    if mc["fixed"] else "")
                 + ("" if indep else "; the correlations were held fixed"
                    + (", and draws at which they are not attainable were discarded" if mc["discarded"] else ""))
                 + ".")
    else:
        text += (" Sensitivity, specificity and prevalence were treated as exact, so these probabilities carry no "
                 "uncertainty interval.")
    lines.append("**Copy-ready summary.** " + md_escape(text))
    return "\n".join(lines)
