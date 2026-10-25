"""Welch two-sample t-test (unequal variances), computed with scipy."""

from cpj_runtime import Factor, InputError, fmt_num, md_escape

SPEC = {
    "name": "pywelch",
    "title": "Welch Two-Sample t-Test (Python)",
    "menuGroup": "ClinicoPathPj",
    "menuSubgroup": "Comparisons",
    "version": "0.2.0",
    "options": [
        {"name": "dep", "type": "Variable", "title": "Outcome", "permitted": ["numeric"],
         "suggested": ["continuous"], "required": True},
        {"name": "group", "type": "Variable", "title": "Group", "permitted": ["factor"],
         "suggested": ["nominal", "ordinal"], "required": True},
        {"name": "refLevel", "type": "Level", "title": "Reference group (default: second level)",
         "variable": "(group)", "allowNone": True},
        {"name": "ciWidth", "type": "Number", "title": "Confidence level (%)", "default": 95, "min": 50, "max": 99.9},
        {"name": "showPlot", "type": "Bool", "title": "Plot of group means", "default": True},
    ],
    "results": [
        {"name": "summary", "type": "Text", "title": "Interpretation"},
        {"name": "groups", "type": "Table", "title": "Group Descriptives", "columns": [
            {"name": "group", "title": "Group", "type": "text"},
            {"name": "n", "title": "N", "type": "integer"},
            {"name": "mean", "title": "Mean", "type": "number"},
            {"name": "sd", "title": "SD", "type": "number"},
        ]},
        {"name": "test", "type": "Table", "title": "Welch t-Test", "columns": [
            {"name": "diff", "title": "Mean difference", "type": "number"},
            {"name": "lower", "title": "Lower", "type": "number", "superTitle": "Confidence interval"},
            {"name": "upper", "title": "Upper", "type": "number", "superTitle": "Confidence interval"},
            {"name": "t", "title": "t", "type": "number"},
            {"name": "df", "title": "df", "type": "number"},
            {"name": "p", "title": "p", "type": "number", "format": "zto,pvalue"},
        ]},
        {"name": "means", "type": "Image", "title": "Group Means", "plot": "interval",
         "width": 500, "height": 300, "visible": "(showPlot)"},
    ],
}


def _num(x):
    return fmt_num(x)


def _p(p):
    return "p < .001" if p < 0.001 else "p = " + f"{p:.3f}".lstrip("0")


def run(data, options, out):
    import warnings

    import numpy as np
    from scipy import stats

    y, g = data[options["dep"]], data[options["group"]]
    if not isinstance(g, Factor):
        raise InputError("The group variable must be nominal or ordinal.")
    usable = ~np.isnan(y) & (g.codes >= 0)
    present = [g.levels[i] for i in range(len(g.levels)) if np.any(usable & (g.codes == i))]
    if len(present) != 2:
        raise InputError(f"The group variable needs exactly two groups with data; it has {len(present)}.")

    # Unset (the default) means the second level is the reference, so the difference is
    # level 1 minus level 2, the same sign as jamovi's Independent Samples T-Test.
    reference = options.get("refLevel") or present[1]
    if reference not in present:
        raise InputError(f"The reference group '{reference}' has no observations; choose one of: "
                         f"{', '.join(present)}.")
    comparison = present[1] if reference == present[0] else present[0]
    sample = {level: y[usable & (g.codes == g.levels.index(level))] for level in present}
    for level in present:
        if sample[level].size < 2:
            raise InputError(f"Group '{level}' needs at least two observations; it has {sample[level].size}.")

    level_ci = options["ciWidth"] / 100
    means = []
    for level in present:  # level order, like jamovi's tables
        x = sample[level]
        mean, sd = x.mean(), x.std(ddof=1)
        half = stats.t.ppf((1 + level_ci) / 2, x.size - 1) * sd / np.sqrt(x.size)
        out.row("groups", group=level, n=x.size, mean=mean, sd=sd)
        means.append({"label": level, "estimate": mean, "lower": mean - half, "upper": mean + half})
    out.plot("means", means, xlab=f"{options['dep']} (mean, {options['ciWidth']:g}% CI)", ylab=options["group"])

    a, b = sample[comparison], sample[reference]
    diff = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)
    names = {"dep": md_escape(options["dep"]), "a": md_escape(comparison), "b": md_escape(reference)}
    # stats::t.test's guard. Below it scipy reports df = 1 instead of NaN, which must not be shown.
    if not np.isfinite(se) or se <= 10 * np.finfo(float).eps * max(abs(a.mean()), abs(b.mean())):
        out.row("test", diff=diff)
        out.note("test", "t, df, p and the confidence interval are undefined: the outcome is constant "
                         "(or too extreme to compute) within both groups.")
        out.markdown("summary", f"Mean {names['dep']} differs by {_num(diff)} between {names['a']} and "
                                f"{names['b']}; the t-test is undefined because the outcome does not vary "
                                f"within either group.")
    else:
        with warnings.catch_warnings():  # a constant group alone is exact here, not "unreliable"
            warnings.filterwarnings("ignore", "Precision loss occurred", RuntimeWarning)
            result = stats.ttest_ind(a, b, equal_var=False)
            interval = result.confidence_interval(confidence_level=level_ci)
        out.row("test", diff=diff, lower=interval.low, upper=interval.high,
                t=result.statistic, df=result.df, p=result.pvalue)
        if diff == 0:
            head = f"Mean {names['dep']} was the same in {names['a']} and {names['b']}"
        else:
            head = (f"Mean {names['dep']} was {_num(abs(diff))} {'higher' if diff > 0 else 'lower'} "
                    f"in {names['a']} than in {names['b']}")
        out.markdown("summary",
                     f"{head} (difference {_num(diff)}, {options['ciWidth']:g}% CI {_num(interval.low)} to "
                     f"{_num(interval.high)}; Welch t({result.df:.1f}) = {result.statistic:.2f}, {_p(result.pvalue)}).")
    out.note("test", f"Mean difference = {comparison} minus {reference}; "
                     f"{options['ciWidth']:g}% confidence interval; two-sided p; variances are not assumed equal.")
    excluded = int(y.size - usable.sum())
    if excluded:
        out.note("test", f"{excluded} row(s) with a missing outcome or group were excluded.")
