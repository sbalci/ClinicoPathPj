"""Exact tests for a 2x2 table: Fisher's, Barnard's and Boschloo's tests for two independent groups,
or the exact McNemar test for paired data, with the odds ratio and (independent groups) the risk
difference.

Methods (each checked against R in tests/python/test_pyexacttests.py):
- Fisher's exact test, the conditional maximum-likelihood odds ratio and its exact (Cornfield)
  interval, computed as R's stats::fisher.test computes them, except that the roots are found to near
  machine precision: fisher.test's uniroot() keeps its default tolerance (about 1.2e-4 on the 1/OR
  scale), which leaves errors of several per cent in large upper limits.
  Fisher RA. Statistical Methods for Research Workers, 1935; Cornfield J. Proc 3rd Berkeley Symp 1956.
- Barnard's test with the pooled z (score) statistic, and Boschloo's test, which orders the tables by
  Fisher's p-value (two-sided: R's minimum-likelihood p-value, so it is never larger than Fisher's).
  Both fix only the group sizes; the p-value is the largest over the common event probability.
  As Exact::exact.test(method = "z-pooled" / "boschloo", tsmethod = "square").
  Barnard GA. Biometrika 1947;34:123-38. Boschloo RD. Stat Neerl 1970;24:19-35.
  Suissa S, Shuster JJ. J R Stat Soc A 1985;148:317-27.
- Exact McNemar test: exact binomial test of the discordant pairs (as binom.test), with the paired
  odds ratio b/c and its Clopper-Pearson-based interval (as exact2x2::mcnemar.exact).
  McNemar Q. Psychometrika 1947;12:153-7.
- Risk difference with Newcombe's hybrid score interval (method 10), from Wilson intervals as
  prop.test(correct = FALSE) computes them. Newcombe RG. Stat Med 1998;17:873-90.
scipy is not used for Barnard/Boschloo: barnard_exact compares statistics without a tie tolerance,
boschloo_exact defines two-sided as twice the smaller one-sided p, and both search the nuisance
parameter from 32 points. scipy's fisher_exact on a table larger than 2x2 is a Monte Carlo estimate
(unseeded by default), so larger tables are refused.
The exact odds-ratio interval inverts two one-sided tests while the two-sided p-value is R's minimum-likelihood
one, so the two can disagree about an odds ratio of 1 (36 of 865 tables with groups of 8 to 25); a note says so.
"""

from cpj_runtime import Factor, InputError, fmt_num, md_escape

SPEC = {'name': 'pyexacttests',
 'title': 'Exact Tests for 2x2 Tables (Python)',
 'menuGroup': 'MedDecide Py',
 'menuSubgroup': 'Exact tests',
 'version': '0.1.0',
 'options': [{'name': 'group',
              'type': 'Variable',
              'title': 'Group (paired: first measurement)',
              'permitted': ['factor'],
              'suggested': ['nominal', 'ordinal'],
              'required': True},
             {'name': 'outcome',
              'type': 'Variable',
              'title': 'Outcome (paired: second measurement)',
              'permitted': ['factor'],
              'suggested': ['nominal', 'ordinal'],
              'required': True},
             {'name': 'counts',
              'type': 'Variable',
              'title': 'Counts (optional)',
              'permitted': ['numeric'],
              'suggested': ['continuous']},
             {'name': 'event',
              'type': 'Level',
              'title': 'Event level',
              'variable': '(outcome)',
              'role': 'event'},
             {'name': 'refLevel',
              'type': 'Level',
              'title': 'Reference group (default: first level)',
              'variable': '(group)',
              'allowNone': True},
             {'name': 'design',
              'type': 'List',
              'title': 'Design',
              'default': 'independent',
              'options': [{'name': 'independent', 'title': 'Independent groups'},
                          {'name': 'paired', 'title': 'Paired: the same subjects measured twice'}]},
             {'name': 'alternative',
              'type': 'List',
              'title': 'Alternative hypothesis',
              'default': 'twoSided',
              'options': [{'name': 'twoSided', 'title': 'Two-sided: odds ratio not 1'},
                          {'name': 'greater', 'title': 'One-sided: odds ratio greater than 1'},
                          {'name': 'less', 'title': 'One-sided: odds ratio less than 1'}]},
             {'name': 'ciWidth',
              'type': 'Number',
              'title': 'Confidence level (%)',
              'default': 95,
              'min': 50,
              'max': 99.9}],
 'results': [{'name': 'summary', 'type': 'Text', 'title': 'Interpretation'},
             {'name': 'crosstab',
              'type': 'Table',
              'title': 'Contingency Table',
              'columns': [{'name': 'label', 'title': '', 'type': 'text'},
                          {'name': 'event', 'title': 'Event', 'type': 'integer'},
                          {'name': 'nonevent', 'title': 'No event', 'type': 'integer'},
                          {'name': 'total', 'title': 'Total', 'type': 'integer'}]},
             {'name': 'tests',
              'type': 'Table',
              'title': 'Exact Tests',
              'columns': [{'name': 'test', 'title': 'Test', 'type': 'text'},
                          {'name': 'p', 'title': 'p', 'type': 'number', 'format': 'zto,pvalue'}]},
             {'name': 'effects',
              'type': 'Table',
              'title': 'Effect Sizes',
              'columns': [{'name': 'measure', 'title': 'Measure', 'type': 'text'},
                          {'name': 'estimate', 'title': 'Estimate', 'type': 'number'},
                          {'name': 'lower',
                           'title': 'Lower',
                           'type': 'number',
                           'superTitle': 'Confidence interval'},
                          {'name': 'upper',
                           'title': 'Upper',
                           'type': 'number',
                           'superTitle': 'Confidence interval'}]}],
 'ui': {'children': [{'type': 'VariableSupplier',
                      'persistentItems': False,
                      'stretchFactor': 1,
                      'children': [{'type': 'TargetLayoutBox',
                                    'label': 'Group (paired: first measurement)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'group',
                                                  'isTarget': True,
                                                  'maxItemCount': 1},
                                                 {'type': 'LevelSelector',
                                                  'name': 'refLevel',
                                                  'enable': '(group)'}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Outcome (paired: second measurement)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'outcome',
                                                  'isTarget': True,
                                                  'maxItemCount': 1},
                                                 {'type': 'LevelSelector',
                                                  'name': 'event',
                                                  'enable': '(outcome)'}]},
                                   {'type': 'TargetLayoutBox',
                                    'label': 'Counts (optional)',
                                    'children': [{'type': 'VariablesListBox',
                                                  'name': 'counts',
                                                  'isTarget': True,
                                                  'maxItemCount': 1}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Analysis and Model',
                      'collapsed': False,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'design', 'type': 'ComboBox'},
                                                 {'name': 'alternative', 'type': 'ComboBox'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Uncertainty and Validation',
                      'collapsed': True,
                      'children': [{'type': 'LayoutBox',
                                    'margin': 'large',
                                    'children': [{'name': 'ciWidth',
                                                  'type': 'TextBox',
                                                  'format': 'number'}]}]},
                     {'type': 'CollapseBox',
                      'label': 'Advanced Settings',
                      'collapsed': True,
                      'children': [{'type': 'CheckBox', 'name': 'showConsole'}]}]}}

MAX_N = 1_000_000      # exact tests are for small samples; larger totals are refused
MAX_GROUP = 1000       # Barnard/Boschloo enumerate (n1 + 1) * (n2 + 1) tables: about 4 s at 1000 each
FISHER_TIES = 1 + 1e-7  # R's fisher.test: probabilities within this ratio count as equal
TIES = 1e-12           # relative: statistics of different tables this close count as equal
ALTERNATIVES = {"twoSided": "two-sided", "greater": "greater", "less": "less"}


def _num(x):
    return "infinity" if x == float("inf") else fmt_num(x)


def _points(x):
    return f"{100 * x:.1f}"


def _p(p):
    return "p < .001" if p < 0.001 else "p = " + f"{p:.3f}".lstrip("0")


def _pct(k, n):
    return f"{k} of {n} ({100 * k / n:.1f}%)"


def _interval(lower, upper, alternative, level_text, fmt=_num):
    """Narrative for an interval; a one-sided interval is reported by its informative bound."""
    if alternative == "greater":
        return f"{level_text} lower confidence bound {fmt(lower)}"
    if alternative == "less":
        return f"{level_text} upper confidence bound {fmt(upper)}"
    return f"{level_text} CI {fmt(lower)} to {fmt(upper)}"


def _root(f):
    """Root of f, increasing in u (a log odds ratio), found to near machine precision."""
    from scipy.optimize import brentq
    lo, hi = -1.0, 1.0
    while f(lo) > 0:
        lo *= 2
    while f(hi) < 0:
        hi *= 2
    return brentq(f, lo, hi, xtol=1e-14, maxiter=1000)


def fisher(a, b, c, d, alternative, level):
    """R's fisher.test on [[a, b], [c, d]]: p, conditional MLE odds ratio and exact interval.

    Returns (p, estimate, lower, upper); estimate and limits are None when the table has an empty
    margin (the odds ratio is then undefined), and may be 0 or infinity.
    """
    import math

    import numpy as np
    from scipy import stats

    m, n, k, x = a + c, b + d, a + b, a
    lo, hi = max(0, k - n), min(k, m)
    support = np.arange(lo, hi + 1)
    logdc = stats.hypergeom.logpmf(support, m + n, m, k)

    def density(u):  # distribution of a given the margins, odds ratio exp(u)
        z = logdc + u * support
        z = np.exp(z - z.max())
        return z / z.sum()

    if alternative == "less":
        p = stats.hypergeom.cdf(x, m + n, m, k)
    elif alternative == "greater":
        p = stats.hypergeom.sf(x - 1, m + n, m, k)
    else:
        dens = density(0.0)
        p = dens[dens <= dens[x - lo] * FISHER_TIES].sum()
    p = min(float(p), 1.0)
    if lo == hi:
        return p, None, None, None

    def upper(alpha):  # P(A <= x) = alpha
        return math.inf if x == hi else math.exp(_root(lambda u: alpha - density(u)[: x - lo + 1].sum()))

    def lower(alpha):  # P(A >= x) = alpha
        return 0.0 if x == lo else math.exp(_root(lambda u: density(u)[x - lo:].sum() - alpha))

    estimate = 0.0 if x == lo else math.inf if x == hi else math.exp(_root(lambda u: density(u) @ support - x))
    if alternative == "less":
        limits = (0.0, upper(1 - level))
    elif alternative == "greater":
        limits = (lower(1 - level), math.inf)
    else:
        limits = (lower((1 - level) / 2), upper((1 - level) / 2))
    return p, estimate, *limits


def _fisher_p_all(n1, n2, alternative):
    """Fisher's p-value (as R's fisher.test, for this alternative) of every table: [x1, x2]."""
    import numpy as np
    from scipy import stats

    x1 = np.arange(n1 + 1)[:, None]
    x2 = np.arange(n2 + 1)[None, :]
    s = x1 + x2
    if alternative == "less":
        return stats.hypergeom.cdf(x1, n1 + n2, s, n1)
    if alternative == "greater":
        return stats.hypergeom.sf(x1 - 1, n1 + n2, s, n1)
    pmf = stats.hypergeom.pmf(x1, n1 + n2, s, n1)
    pvalues = np.empty_like(pmf)
    for total in range(n1 + n2 + 1):  # tables with the same margins lie on one anti-diagonal
        i = np.arange(max(0, total - n2), min(total, n1) + 1)
        d = pmf[i, total - i]
        d = d / d.max()
        d = d / d.sum()
        order = np.sort(d)
        cumulative = np.cumsum(order)
        pvalues[i, total - i] = cumulative[np.searchsorted(order, d * FISHER_TIES, side="right") - 1]
    return np.minimum(pvalues, pvalues[::-1, ::-1])  # a table and its mirror image tie exactly


def _sup_p(reject, n1, n2):
    """max over pi of P(table in reject) when x1 ~ Bin(n1, pi) and x2 ~ Bin(n2, pi), independently."""
    import numpy as np
    from scipy import stats
    from scipy.optimize import minimize_scalar

    weights = reject.astype(float)
    i1, i2 = np.arange(n1 + 1)[:, None], np.arange(n2 + 1)[:, None]

    def p_at(theta):  # pi = sin(theta)^2: equal binomial standard errors along theta
        pi = np.sin(np.atleast_1d(theta)) ** 2
        return np.einsum("ig,ig->g", stats.binom.pmf(i1, n1, pi), weights @ stats.binom.pmf(i2, n2, pi))

    # about 13 grid points per standard error of pi; p(0) and p(1) are 0 or 1 (one possible table)
    grid = np.linspace(0, np.pi / 2, int(min(4000, max(400, 40 * np.sqrt(n1 + n2)))))
    values = p_at(grid)
    best = values.max()
    if best >= 1:
        return 1.0
    peaks = [k for k in range(1, grid.size - 1) if values[k] > values[k - 1] and values[k] >= values[k + 1]]
    for k in sorted(peaks, key=lambda k: -values[k])[:20]:  # ponytail: only the 20 highest grid peaks refined
        found = minimize_scalar(lambda t: -p_at(t)[0], bounds=(grid[k - 1], grid[k + 1]), method="bounded",
                                options={"xatol": 1e-12, "maxiter": 1000})
        best = max(best, -found.fun)
    return min(float(best), 1.0)


def unconditional(method, x1, n1, x2, n2, alternative):
    """Barnard's (pooled z) or Boschloo's exact unconditional p-value for p1 versus p2."""
    import numpy as np

    if method == "barnard":
        i, j = np.arange(n1 + 1)[:, None], np.arange(n2 + 1)[None, :]
        total, events = n1 + n2, i + j
        # z = (p1 - p2) / sqrt(p (1 - p) (1/n1 + 1/n2)) with the integer numerator (p1 - p2) n1 n2, so that a
        # table and its mirror image (events and non-events swapped) get exactly opposite z
        difference = i * n2 - j * n1
        with np.errstate(divide="ignore", invalid="ignore"):
            stat = difference * np.sqrt(total / (n1 * n2 * (events * (total - events))))
        stat[difference == 0] = 0.0  # equal proportions, including the 0/0 tables
        observed = stat[x1, x2]
        slack = TIES * abs(observed)
        if alternative == "two-sided":
            reject = np.abs(stat) >= abs(observed) - slack
        elif alternative == "greater":
            reject = stat >= observed - slack
        else:
            reject = stat <= observed + slack
    else:
        pvalues = _fisher_p_all(n1, n2, alternative)
        reject = pvalues <= pvalues[x1, x2] * (1 + TIES)
    return _sup_p(reject, n1, n2)


def mcnemar(b, c, alternative, level):
    """Exact McNemar test (binom.test on b of b + c) and the paired odds ratio b/c with exact limits.

    Returns (p, estimate, lower, upper), all None without discordant pairs.
    """
    import math

    from scipy import stats

    n = b + c
    if n == 0:
        return None, None, None, None
    p = stats.binomtest(b, n, 0.5, alternative=alternative).pvalue

    def lower(alpha):
        return 0.0 if b == 0 else stats.beta.ppf(alpha, b, n - b + 1)

    def upper(alpha):
        return 1.0 if b == n else stats.beta.ppf(1 - alpha, b + 1, n - b)

    if alternative == "less":
        limits = (0.0, upper(1 - level))
    elif alternative == "greater":
        limits = (lower(1 - level), 1.0)
    else:
        limits = (lower((1 - level) / 2), upper((1 - level) / 2))
    odds = [math.inf if q == 1 else q / (1 - q) for q in (b / n,) + limits]
    return float(p), *odds


def _wilson(x, n, z):
    """Wilson score interval, as prop.test(x, n, correct = FALSE) computes it."""
    import math
    p = x / n
    z22n = z * z / (2 * n)
    root = z * math.sqrt(p * (1 - p) / n + z22n / (2 * n))
    lower = 0.0 if p <= 0 else (p + z22n - root) / (1 + 2 * z22n)
    upper = 1.0 if p >= 1 else (p + z22n + root) / (1 + 2 * z22n)
    return max(lower, 0.0), min(upper, 1.0)


def newcombe(x1, n1, x2, n2, alternative, level):
    """Risk difference x1/n1 - x2/n2 with Newcombe's hybrid score interval (method 10).

    A one-sided bound is the bound of the two-sided 1 - 2 * alpha interval; the other limit is -1 or 1.
    """
    import math

    from scipy import stats

    z = stats.norm.ppf(level if alternative != "two-sided" else (1 + level) / 2)
    p1, p2 = x1 / n1, x2 / n2
    (l1, u1), (l2, u2) = _wilson(x1, n1, z), _wilson(x2, n2, z)
    lower = p1 - p2 - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = p1 - p2 + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    if alternative == "greater":
        upper = 1.0
    elif alternative == "less":
        lower = -1.0
    return p1 - p2, lower, upper


def _with_data(levels, totals):
    return [levels[i] for i, total in enumerate(totals) if total > 0]


def _not_2x2(name, labels):
    return InputError(
        f"This analysis needs a 2x2 table, but '{name}' gives {len(labels)} categories here "
        f"({', '.join(labels)}). For larger tables use jamovi's Contingency Tables, whose Fisher's exact test uses "
        f"R's fisher.test.")


def _cells(data, options, g, y):
    """Counts by (group level, outcome level) and the number of excluded rows."""
    import numpy as np

    counts = options.get("counts")
    usable = (g.codes >= 0) & (y.codes >= 0)
    if counts:
        w = data[counts]
        if isinstance(w, Factor) or not isinstance(w, np.ndarray):
            raise InputError(f"'{counts}' must be a numeric variable of counts.")
        usable &= ~np.isnan(w)
        if np.any(w[usable] < 0) or np.any(w[usable] != np.floor(w[usable])):
            raise InputError(f"'{counts}' must hold whole numbers of zero or more: exact tests need counts.")
        weights = w[usable]
    else:
        weights = np.ones(int(usable.sum()))
    if weights.sum() > MAX_N:
        raise InputError(f"There are more than {MAX_N:,} observations; exact tests are meant for small samples.")
    cells = np.zeros((len(g.levels), len(y.levels)), dtype=np.int64)
    np.add.at(cells, (g.codes[usable], y.codes[usable]), weights.astype(np.int64))
    return cells, int(g.codes.size - usable.sum())


def _independent(cells, g, y, options, out, alternative, level):
    import math

    first, second, event = options["group"], options["outcome"], options["event"]
    level_text = f"{options['ciWidth']:g}%"
    sided = "two-sided" if alternative == "two-sided" else "one-sided"
    present = _with_data(g.levels, cells.sum(axis=1))
    if len(present) > 2:
        raise _not_2x2(first, present)
    if len(present) < 2:
        raise InputError(f"'{first}' needs two groups with data; it has {len(present)}.")
    other = [label for label in _with_data(y.levels, cells.sum(axis=0)) if label != event]
    if len(other) > 1:
        raise _not_2x2(second, [event] + other)
    # Unset means the first level is the reference: with the event as the outcome's second level (No/Yes,
    # Negative/Positive) the odds ratio then has the orientation of jamovi's Contingency Tables and of
    # R's fisher.test(table(group, outcome)), and a one-sided 'greater' tests the usual hypothesis.
    reference = options.get("refLevel") or present[0]
    if reference not in present:
        raise InputError(f"The reference group '{reference}' has no observations; choose one of: "
                         f"{', '.join(present)}.")
    comparison = present[0] if reference == present[1] else present[1]
    e, ci, ri = y.levels.index(event), g.levels.index(comparison), g.levels.index(reference)
    a, c = int(cells[ci, e]), int(cells[ri, e])
    b, d = int(cells[ci].sum()) - a, int(cells[ri].sum()) - c
    n1, n2 = a + b, c + d
    out.row("crosstab", label=comparison, event=a, nonevent=b, total=n1)
    out.row("crosstab", label=reference, event=c, nonevent=d, total=n2)
    out.row("crosstab", label="Total", event=a + c, nonevent=b + d, total=n1 + n2)
    out.note("crosstab", f"Rows: {first}. Columns: {second}, event = {event}"
                         + (f", no event = {other[0]}." if other else "."))

    p_fisher, estimate, lower, upper = fisher(a, b, c, d, alternative, level)
    out.row("tests", test="Fisher's exact test", p=p_fisher)
    unconditional_p = {}
    for method, title in (("barnard", "Barnard's exact test"), ("boschloo", "Boschloo's exact test")):
        if max(n1, n2) <= MAX_GROUP:
            unconditional_p[method] = unconditional(method, a, n1, c, n2, alternative)
        out.row("tests", test=title, p=unconditional_p.get(method))
    out.note("tests", f"{sided.capitalize()} p-values" + (
        "." if alternative == "two-sided" else
        f"; the alternative is that {event} is {'more' if alternative == 'greater' else 'less'} likely in "
        f"{comparison} than in {reference}."))
    out.note("tests", "Fisher's test conditions on both margins. Barnard's (pooled z statistic) and Boschloo's "
                      "(Fisher's p-value as the statistic) tests fix only the group sizes and report the largest "
                      "p-value over the unknown common event probability; Boschloo's p-value is never larger than "
                      "Fisher's, but Barnard's can be. Report the test that fits the design, chosen before seeing "
                      "the results (Boschloo's when the group sizes are fixed, Fisher's to condition on both "
                      "margins); the other rows are for comparison.")
    if len(unconditional_p) < 2:
        out.note("tests", f"Barnard's and Boschloo's tests were not computed: they enumerate every possible table, "
                          f"which is limited to groups of at most {MAX_GROUP:,}.")

    rd, rd_lower, rd_upper = newcombe(a, n1, c, n2, alternative, level)
    out.row("effects", measure=f"Odds ratio, {comparison} vs {reference} (conditional MLE)",
            estimate=estimate, lower=lower, upper=upper)
    out.row("effects", measure=f"Risk difference, {comparison} minus {reference}",
            estimate=rd, lower=rd_lower, upper=rd_upper)
    out.note("effects", f"Odds ratio = odds of {event} in {comparison} divided by the odds in {reference}; "
                        f"risk difference = proportion with {event} in {comparison} minus that in {reference}.")
    out.note("effects", f"{sided.capitalize()} {level_text} intervals: exact (Fisher) for the odds ratio, "
                        f"Newcombe's hybrid score interval for the risk difference.")
    if estimate is None:
        out.note("effects", f"The odds ratio is undefined because {'no subject' if a + c == 0 else 'every subject'} "
                            f"has {event}.")
    elif estimate == math.inf:
        out.note("effects", "A zero cell makes the odds ratio and its upper limit infinite (shown as '.').")
    else:
        if estimate > 0:  # a zero cell makes both estimates 0 (or infinite)
            out.note("effects", f"Conditional maximum-likelihood odds ratio, as R's fisher.test reports; the "
                                f"sample odds ratio ad/bc is {_num(a * d / (b * c))}.")
        if upper == math.inf:
            out.note("effects", "The upper limit of the one-sided odds-ratio interval is infinite (shown as '.').")
    # one-sided limits invert the one-sided test, so only the two-sided pair can disagree
    disagree = alternative == "two-sided" and estimate is not None and (p_fisher < 1 - level) != (lower > 1 or upper < 1)
    if disagree:
        out.note("effects", f"Fisher's two-sided p-value and the {level_text} odds-ratio interval disagree about an "
                            f"odds ratio of 1. As in R's fisher.test, the p-value sums the probabilities of all tables "
                            f"no more likely than the observed one, while the interval combines two one-sided tests at "
                            f"{(100 - options['ciWidth']) / 2:g}% each, so the two can differ near the "
                            f"{100 - options['ciWidth']:g}% boundary.")

    effects = [f"risk difference {_points(rd)} percentage points "
               f"({_interval(rd_lower, rd_upper, alternative, level_text, _points)})"]
    if estimate is not None:
        effects.insert(0, f"odds ratio {_num(estimate)} ({_interval(lower, upper, alternative, level_text)})")
    effects = "; ".join(effects)
    text = (f"**{md_escape(event)}** in **{md_escape(comparison)}**: {_pct(a, n1)}; in **{md_escape(reference)}**: "
            f"{_pct(c, n2)}. {effects[0].upper()}{effects[1:]}. "
            f"{sided.capitalize()} p-values: Fisher's exact test {_p(p_fisher)}")
    for method, title in (("barnard", "Barnard's"), ("boschloo", "Boschloo's")):
        if method in unconditional_p:
            text += f", {title} {_p(unconditional_p[method])}"
    if disagree:
        text += ". Fisher's p-value and the odds-ratio interval disagree about an odds ratio of 1 (see the note under " \
                "Effect Sizes)"
    out.markdown("summary", text + ".")


def _paired(cells, g, y, options, out, alternative, level):
    import math

    first, second, event = options["group"], options["outcome"], options["event"]
    level_text = f"{options['ciWidth']:g}%"
    sided = "two-sided" if alternative == "two-sided" else "one-sided"
    if options.get("refLevel") is not None:
        out.info("The reference group applies to independent groups only; it is ignored in the paired design.")
    if event not in g.levels:
        raise InputError(f"In the paired design both variables must use the same levels, but the event level "
                         f"'{event}' is not a level of '{first}'.")
    first_other = [label for label in _with_data(g.levels, cells.sum(axis=1)) if label != event]
    second_other = [label for label in _with_data(y.levels, cells.sum(axis=0)) if label != event]
    for name, labels in ((first, first_other), (second, second_other)):
        if len(labels) > 1:
            raise _not_2x2(name, [event] + labels)
    if first_other and second_other and first_other != second_other:
        raise InputError(f"In the paired design both variables must use the same two levels, but '{first}' has "
                         f"'{first_other[0]}' where '{second}' has '{second_other[0]}'.")
    n = int(cells.sum())
    if n == 0:
        raise InputError("There are no complete pairs.")
    fe, se = g.levels.index(event), y.levels.index(event)
    a = int(cells[fe, se])
    b = int(cells[fe].sum()) - a
    c = int(cells[:, se].sum()) - a
    d = n - a - b - c
    other = (first_other or second_other or [f"not {event}"])[0]
    out.row("crosstab", label=event, event=a, nonevent=b, total=a + b)
    out.row("crosstab", label=other, event=c, nonevent=d, total=c + d)
    out.row("crosstab", label="Total", event=a + c, nonevent=b + d, total=n)
    out.note("crosstab", f"Rows: {first}. Columns: {second}, event = {event}. Each count is a number of pairs.")

    p, estimate, lower, upper = mcnemar(b, c, alternative, level)
    out.row("tests", test="Exact McNemar test", p=p)
    out.row("effects", measure="Odds ratio, paired (b/c)", estimate=estimate, lower=lower, upper=upper)
    if b + c == 0:
        out.note("tests", "There are no discordant pairs, so the test and the odds ratio are undefined.")
    else:
        out.note("tests", f"Exact binomial test of the {b} pair(s) with {event} only at {first} among the {b + c} "
                          f"discordant pair(s), probability 1/2; concordant pairs do not enter. {sided.capitalize()} p"
                          + ("." if alternative == "two-sided" else
                             f"; the alternative is that {event} is {'more' if alternative == 'greater' else 'less'} "
                             f"frequent at {first} than at {second}."))
    out.note("effects", f"Odds ratio b/c = pairs with {event} only at {first} divided by pairs with {event} only at "
                        f"{second}; above 1 means {event} is more frequent at {first}. Exact {sided} {level_text} "
                        f"interval (Clopper-Pearson, on the discordant pairs).")
    if b + c and c == 0:
        out.note("effects", f"No pair has {event} only at {second}, so the odds ratio and its upper limit are "
                            f"infinite (shown as '.').")
    elif upper == math.inf:
        out.note("effects", "The upper limit of the one-sided odds-ratio interval is infinite (shown as '.').")

    names = {"first": md_escape(first), "second": md_escape(second), "event": md_escape(event)}
    text = (f"**{names['event']}** at **{names['first']}**: {_pct(a + b, n)} pairs; at **{names['second']}**: "
            f"{_pct(a + c, n)}. ")
    if b + c == 0:
        text += "No pair is discordant, so the exact McNemar test is undefined."
    else:
        text += (f"Of the {b + c} discordant pairs, {b} had **{names['event']}** only at **{names['first']}** and "
                 f"{c} only at **{names['second']}**: exact McNemar test {_p(p)} ({sided}); paired odds ratio "
                 f"{_num(estimate)} ({_interval(lower, upper, alternative, level_text)}).")
    out.markdown("summary", text)


def run(data, options, out):
    first, second = options["group"], options["outcome"]
    if first == second:
        raise InputError("Choose two different variables.")
    g, y = data[first], data[second]
    for name, column in ((first, g), (second, y)):
        if not isinstance(column, Factor):
            raise InputError(f"'{name}' must be a nominal or ordinal variable.")
    if options.get("event") not in y.levels:
        raise InputError(f"Choose the event level of '{second}'.")
    cells, excluded = _cells(data, options, g, y)
    design = _paired if options["design"] == "paired" else _independent
    design(cells, g, y, options, out, ALTERNATIVES[options["alternative"]], options["ciWidth"] / 100)
    if excluded:
        out.note("crosstab", f"{excluded} row(s) with a missing value were excluded.")
