"""kappaSize sample-size engines for interobserver agreement, ported from the R package kappaSize 1.2.

Used by pykappaci, pykappafixedn and pykappapower only. The three engines reproduce kappaSize's
stopping rules (CIBinary/CI3-5Cats, FixedNBinary/FixedN3-5Cats, PowerBinary/Power3-5Cats), so
their answers equal the package's; the cell probabilities use stable closed forms instead of the
package's expanded polynomials, which lose digits for a common category typed first.

Goodness-of-fit (GOF) cells, as in kappaSize:
- binary rating, R raters: Altaye, Donner & Klar (2001) eq. 4 -- with probability kappa all raters
  give one shared call, otherwise each rates independently -- over j = 0..R ratings in the first
  category (two raters: Donner & Eliasziw 1992);
- 3-5 categories: Dirichlet-multinomial (Altaye, Donner & Eliasziw 2001) -- the cells are "all
  raters choose category i" plus one pooled cell for any disagreement.

The Monte Carlo check (binary rating, two raters) simulates whole studies under the same model and analyses
each with the published GOF interval/test of Donner & Eliasziw (1992): the cells both raters agree on either
category / they disagree, the prevalence estimated by the study's share of ratings. With more raters or 3-5
categories the same plug-in (shares from all ratings, cells pooled into all-agree / any disagreement) rejects a
true kappa too often even in large studies -- the shares use information the pooled cells do not hold
(Chernoff-Lehmann): 8.75% instead of 5% for 6 raters, a 20% finding, kappa0 = 0.4, n = 2000 (200,000 draws);
23.8% for 5 categories and 6 raters. The check is therefore offered only where mc_available() is true.
"""
import math
import re

from cpj_runtime import InputError

MAX_SUBJECTS = 10 ** 9  # beyond this the package's own n search is dominated by rounding


def parse_props(text, categories):
    """'0.20, 0.80' -> (proportions, rescaled). A binary outcome also takes one prevalence."""
    raw = str(text or "").strip()
    tokens = [t for t in re.split(r"[,;|\s]+", raw) if t]
    if not tokens:
        raise InputError("Enter the expected proportion of each category, for example 0.20, 0.80.")
    if "%" in raw:
        raise InputError("Enter the proportions as fractions, not percentages: 0.20, 0.80 rather than 20%, 80%.")
    try:
        values = [float(t) for t in tokens]
    except ValueError:
        values = None
    if values is None or not all(math.isfinite(v) and 0 < v < 1 for v in values):
        if re.search(r"\d,\d", raw) and _valid_fractions(re.sub(r"(\d),(\d)", r"\1.\2", raw)):
            raise InputError("Use a decimal point, not a decimal comma: 0.20, 0.80 rather than 0,20 0,80.")
        if values is not None and all(math.isfinite(v) and v > 0 for v in values) and abs(sum(values) - 100) <= 0.1:
            raise InputError("Enter the proportions as fractions, not percentages: 0.20, 0.80 rather than 20, 80.")
        if values is None or not all(math.isfinite(v) for v in values):
            raise InputError("The proportions could not be read as numbers. Separate them with commas, "
                             "semicolons or spaces, for example 0.20, 0.80.")
        raise InputError("Each proportion must lie strictly between 0 and 1.")
    if categories == 2 and len(values) == 1:
        values.append(1 - values[0])
        if values[1] == 1:  # 1 - p rounds to 1 below about 1e-16; model_floor would then divide by zero
            raise InputError("The agreement-pattern probabilities cannot be computed for these proportions "
                             "(a proportion is too close to 0).")
    if len(values) != categories:
        hint = " (or one prevalence)" if categories == 2 else ""
        raise InputError(f"Enter {categories} proportions{hint}, one per outcome category; got {len(values)}.")
    total = sum(values)
    if abs(total - 1) > 0.001:
        raise InputError(f"The proportions must sum to 1; they sum to {total:.4g}.")
    if abs(total - 1) <= 1e-9:  # kept as typed, so the engines see exactly what kappaSize sees
        return values, False
    return [v / total for v in values], True


def _valid_fractions(text):
    try:
        values = [float(t) for t in re.split(r"[,;|\s]+", text) if t]
    except ValueError:
        return False
    return bool(values) and all(math.isfinite(v) and 0 < v < 1 for v in values)


def _binary_cells(raters, p, rho):
    """P(j ratings in the first category), j = 0..raters, under the Altaye-Donner-Klar mixture."""
    q = 1.0 - p
    cells = [(1.0 - rho) * math.comb(raters, j) * p ** j * q ** (raters - j) for j in range(raters + 1)]
    cells[0] += rho * q
    cells[raters] += rho * p
    return cells


def _agree(raters, p, rho):
    """Dirichlet-multinomial probability that all raters choose a category of share p."""
    x = 1.0
    for r in range(raters):
        x *= (p * (1.0 - rho) + r * rho) / ((1.0 - rho) + r * rho)
    return x


def cells(categories, raters, props, rho):
    """kappaSize's GOF cell probabilities at agreement rho (same cells, same order)."""
    if categories == 2:
        return _binary_cells(raters, props[0], rho)
    agree = [_agree(raters, p, rho) for p in props]
    return [1.0 - sum(agree)] + agree


def pooled_cells(categories, raters, props, rho):
    """Cells of the 1-df test: [any disagreement, all raters choose category 1, ..., category K]."""
    if categories == 2:
        c = _binary_cells(raters, props[0], rho)
        return [sum(c[1:raters]), c[raters], c[0]]
    return cells(categories, raters, props, rho)


def model_floor(categories, raters, props):
    """Lowest kappa at which every GOF cell is still a probability (the cells vanish there)."""
    if categories == 2:
        return max(-s ** (raters - 1) / (1 - s ** (raters - 1)) for s in (props[0], 1 - props[0]))
    floor = max(-p / (raters - 1 - p) for p in props)
    return max(floor, -1 / (raters - 2)) if raters >= 3 else floor


def _in_model(categories, raters, props, rho):
    if categories != 2:  # a product of factors can be positive with an even number of negative ones
        if any((1 - rho) + r * rho <= 0 or p * (1 - rho) + r * rho <= 0
               for p in props for r in range(1, raters)):
            return False
    return all(math.isfinite(c) and c > 0 for c in cells(categories, raters, props, rho))


def _calc_it(c0, c1, n):
    """kappaSize's .CalcIT: sum of ((n P(rho0)) - (n P(rho1)))^2 / (n P(rho1)), NaN terms dropped."""
    total = 0.0
    for a, b in zip(c0, c1):
        d = (n * a) - (n * b)
        term = d * d / (n * b) if b != 0 else (math.nan if d == 0 else math.inf)
        if not math.isnan(term):
            total += term
    return total


def _checked_cells(categories, raters, props, rho):
    c = cells(categories, raters, props, rho)
    if not all(math.isfinite(x) and x > 0 for x in c):
        raise InputError("The agreement-pattern probabilities cannot be computed for these proportions "
                         "(a proportion is too close to 0).")
    return c


def _chi2_quantile(p):
    from scipy import stats
    return float(stats.chi2.ppf(p, 1))


def ci_n(categories, raters, props, kappa0, kappa_l, kappa_u, alpha):
    """kappaSize CIBinary/CI3-5Cats: the n reported (kappa_u None = one-sided lower limit).

    kappaSize starts at n = 10 and adds one subject until the expected chi-square at each limit
    exceeds the critical value by 0.001. The chi-square is n times a slope, so n is found from the
    slope and then checked with the package's own expression, as the package's loop would.
    """
    limits = [kappa_l] if kappa_u is None else [kappa_l, kappa_u]
    crit = _chi2_quantile(1 - 2 * alpha if kappa_u is None else 1 - alpha)
    c0 = _checked_cells(categories, raters, props, kappa0)
    c_lim = [_checked_cells(categories, raters, props, k) for k in limits]
    slope = min(_calc_it(c0, c, 1.0) for c in c_lim)
    guess = (crit + 0.001) / slope if slope > 0 else math.inf
    if not guess <= MAX_SUBJECTS:
        raise InputError(f"The target limits are too close to kappa0: more than {MAX_SUBJECTS:,} subjects would be "
                         f"needed. Widen the interval.")

    def done(n):  # the package's loop condition, negated
        return all(abs(_calc_it(c0, c, n) - 0.001) >= crit for c in c_lim)

    n = max(11, math.ceil(guess))
    while n > 11 and done(n - 1):
        n -= 1
    while not done(n):
        n += 1
    return n


def fixed_n_bound(categories, raters, props, kappa0, n, alpha):
    """kappaSize FixedNBinary/FixedN3-5Cats: the expected one-sided lower limit for n subjects.

    Walks kappa down from kappa0 in steps of 0.001, as the package does. Returns (bound, None), or
    (None, floor) when the walk leaves the model before the limit is reached (the package would
    return a value outside the model there).
    """
    crit = _chi2_quantile(1 - 2 * alpha)
    c0 = _checked_cells(categories, raters, props, kappa0)
    floor = model_floor(categories, raters, props)
    rho, stat = kappa0, 0.0
    while abs(stat - 0.001) < crit:
        rho = rho - 0.001
        if rho <= floor or not _in_model(categories, raters, props, rho):
            return None, floor
        stat = _calc_it(c0, cells(categories, raters, props, rho), n)
    return rho, None


def _ncx2_1_cdf(x, ncp):
    """P(chi-square with 1 df and noncentrality ncp <= x) = P(|Z + sqrt(ncp)| <= sqrt(x))."""
    from scipy.special import ndtr
    a, b = math.sqrt(x), math.sqrt(ncp)
    return float(ndtr(a - b) - ndtr(-a - b))


def power_lambda(alpha, power):
    """kappaSize's .powchi(1, alpha, power)[1]: the 1-df noncentrality, by the package's bisection."""
    chival = _chi2_quantile(1 - alpha)
    conf = 1 - (1 - power) * 2
    llim = (1 - conf) / 2
    uc = [chival, 2 * chival, 3 * chival]
    while _ncx2_1_cdf(chival, uc[0]) < llim:
        uc = [uc[0] / 4, uc[0], uc[2]]
    while _ncx2_1_cdf(chival, uc[2]) > llim:
        uc = [uc[0], uc[2], uc[2] + chival]
    diff = 1.0
    while diff > 1e-05:
        if _ncx2_1_cdf(chival, uc[1]) < llim:
            uc = [uc[0], (uc[0] + uc[1]) / 2, uc[1]]
        else:
            uc = [uc[1], (uc[1] + uc[2]) / 2, uc[2]]
        diff = abs(_ncx2_1_cdf(chival, uc[1]) - llim)
    return uc[1]


def power_n(categories, raters, props, kappa0, kappa1, alpha, power):
    """kappaSize PowerBinary/Power3-5Cats: (unrounded N, noncentrality, per-subject chi-square)."""
    c0 = _checked_cells(categories, raters, props, kappa0)
    c1 = _checked_cells(categories, raters, props, kappa1)
    per_subject = 0.0
    for a, b in zip(c1, c0):
        d = a - b
        per_subject += d * d / b
    lam = power_lambda(alpha, power)
    n = lam / per_subject if per_subject > 0 else math.inf
    if not n <= MAX_SUBJECTS:
        raise InputError(f"kappa0 and kappa1 are too close for these proportions: more than {MAX_SUBJECTS:,} "
                         f"subjects would be needed.")
    return n, lam, per_subject


def min_expected_count(categories, raters, props, rhos, n):
    """Smallest expected count among the pooled GOF cells at the given agreement levels."""
    return min(n * c for rho in rhos if rho is not None for c in pooled_cells(categories, raters, props, rho))


# ---------------------------------------------------------------- Monte Carlo check (binary rating)

def patterns(raters, props, rho):
    """Rating patterns of one subject, (j, raters - j) ratings in the two categories, j = 0..raters, with
    their probabilities under the Altaye-Donner-Klar model; and the indices of the two unanimous patterns."""
    import numpy as np
    counts = np.array([(j, raters - j) for j in range(raters + 1)], dtype=float)
    probs = np.array(_binary_cells(raters, props[0], rho))
    return counts, probs / probs.sum(), [raters, 0]


def summarise(tables, counts, unanimous, raters):
    """Per study (row of pattern counts): share of ratings per category, subjects unanimous per category."""
    n = tables.sum(axis=1, keepdims=True)
    return (tables @ counts) / (n * raters), tables[:, unanimous].astype(float)


def _gof(raters, share, unanimous, n, rho):
    """Pearson chi-square of each study over the cells all raters agree on category 1 / on category 2 /
    any disagreement, at agreement rho, the prevalence estimated by the study's share of ratings."""
    import numpy as np
    rho = np.asarray(rho, dtype=float)
    r = rho[:, None] if rho.ndim else rho
    expected = n * np.column_stack([(1 - rho) * (1 - (share ** raters).sum(axis=1)),
                                    (1 - r) * share ** raters + r * share])
    observed = np.column_stack([n - unanimous.sum(axis=1), unanimous])
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(expected > 0, (observed - expected) ** 2 / expected,
                         np.where(observed > 0, np.inf, 0.0))
    return terms.sum(axis=1)


def _min_chi_square_kappa(raters, share, unanimous, n):
    """Minimum chi-square estimate of kappa in each study: golden-section search over the kappas at
    which every cell is a probability (the chi-square is convex in kappa there)."""
    import numpy as np
    with np.errstate(divide="ignore", invalid="ignore"):
        s = share ** (raters - 1)
        floor = np.clip(np.where(share > 0, -s / (1 - s), -np.inf).max(axis=1), -1.0, 0.0)
    a, b = floor + 1e-9, np.full_like(floor, 1 - 1e-9)
    g = (math.sqrt(5) - 1) / 2
    for _ in range(90):
        c, d = b - g * (b - a), a + g * (b - a)
        left = _gof(raters, share, unanimous, n, c) < _gof(raters, share, unanimous, n, d)
        a, b = np.where(left, a, c), np.where(left, d, b)
    return (a + b) / 2


def ci_outcomes(raters, share, unanimous, n, kappa0, kappa_l, kappa_u, alpha):
    """Per study: does its interval {kappa: chi-square <= critical value} contain kappa0, and does it lie
    within the targets? kappa_u None = one-sided interval [L, 1)."""
    crit = _chi2_quantile(1 - 2 * alpha if kappa_u is None else 1 - alpha)

    def x2(rho):
        return _gof(raters, share, unanimous, n, rho)

    m = _min_chi_square_kappa(raters, share, unanimous, n)
    nonempty = x2(m) <= crit
    if kappa_u is None:  # L is the root below the estimate m
        covered = nonempty & ((kappa0 >= m) | (x2(kappa0) <= crit))
        reached = nonempty & (kappa_l <= m) & (x2(kappa_l) >= crit)
    else:
        covered = x2(kappa0) <= crit
        reached = nonempty & (kappa_l <= m) & (m <= kappa_u) & (x2(kappa_l) >= crit) & (x2(kappa_u) >= crit)
    return covered, reached


def rejects(raters, share, unanimous, n, kappa0, alpha):
    """Per study: does the two-sided goodness-of-fit test reject kappa = kappa0?"""
    return _gof(raters, share, unanimous, n, kappa0) > _chi2_quantile(1 - alpha)


def _simulate(rng, raters, props, rho, n, draws):
    counts, probs, unanimous = patterns(raters, props, rho)
    return summarise(rng.multinomial(n, probs, size=draws), counts, unanimous, raters)


def simulate_ci(raters, props, kappa0, kappa_l, kappa_u, alpha, n, draws, seed):
    """Monte Carlo (true kappa = kappa0): share of studies whose interval contains kappa0 / lies within
    the targets."""
    import numpy as np
    share, unanimous = _simulate(np.random.default_rng(seed), raters, props, kappa0, n, draws)
    covered, reached = ci_outcomes(raters, share, unanimous, n, kappa0, kappa_l, kappa_u, alpha)
    return float(covered.mean()), float(reached.mean())


def simulate_power(raters, props, kappa0, kappa1, alpha, n, draws, seed):
    """Monte Carlo: share of studies rejecting kappa0 when the truth is kappa1 (power), then kappa0 (size)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    rates = []
    for truth in (kappa1, kappa0):
        share, unanimous = _simulate(rng, raters, props, truth, n, draws)
        rates.append(float(rejects(raters, share, unanimous, n, kappa0, alpha).mean()))
    return rates[0], rates[1]


def mc_available(categories, raters):
    """The check runs only where its analysis is the published one and stays close to its level (module docstring)."""
    return categories == 2 and raters == 2


MC_ANALYSIS = ("the published goodness-of-fit {} (Donner and Eliasziw 1992), the prevalence estimated by the study's "
               "overall share of ratings")
MC_UNAVAILABLE = ("Not available for more than two raters or for 3-5 categories: analysing each simulated study with "
                  "the category shares taken from all of its ratings, as Donner and Eliasziw (1992) do for two raters, "
                  "rejects a true kappa too often in these designs even in large studies (nearly 9% instead of 5% "
                  "with 6 raters, a 20% finding and kappa0 = 0.4), so the check would misstate how the planned study "
                  "behaves.")


def mc_se(p, draws):
    return math.sqrt(p * (1 - p) / draws)


# ---------------------------------------------------------------- wording shared by the analyses

def model_text(categories, raters):
    if categories > 2:
        return "Dirichlet-multinomial (Altaye, Donner and Eliasziw 2001)"
    if raters == 2:
        return "Donner and Eliasziw (1992)"
    return ("Altaye, Donner and Klar (2001), in which with probability kappa all raters give one shared "
            "rating and otherwise each rates independently")


def raters_text(raters):
    return "both raters" if raters == 2 else f"all {raters} raters"


def props_text(props):
    return ", ".join(f"{p:.4g}" for p in props)


def common_notes(out, table, categories, raters, rescaled):
    out.note(table, f"Agreement model: {model_text(categories, raters)}. kappa here is the intraclass (Fleiss-type) "
                    f"kappa of this model; for a pair of raters it equals Cohen's kappa when both use the categories "
                    f"with the same frequencies. The figure is for the goodness-of-fit analysis of kappa, not for "
                    f"Wald or bootstrap intervals.")
    if rescaled:
        out.note(table, "The proportions entered did not sum exactly to 1 and were rescaled to do so.")


def sparse_note(out, table, smallest, simulate_hint=True):
    if smallest < 5:
        out.note(table, f"The smallest expected count among the goodness-of-fit cells (all raters agree on a "
                        f"category, or any disagreement) is {smallest:.3g}, below 5: the large-sample "
                        f"approximation behind this figure may be inaccurate"
                        + ("; the Monte Carlo check shows how the planned study behaves." if simulate_hint else "."))
