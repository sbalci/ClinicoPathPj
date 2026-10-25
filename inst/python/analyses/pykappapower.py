"""Sample size for a kappa study by the power approach (kappaSize PowerBinary, Power3-5Cats)."""

from cpj_runtime import InputError

SPEC = {
    "name": "pykappapower",
    "title": "Kappa Sample Size by Power (Python)",
    "menuGroup": "ClinicoPathPj",
    "menuSubgroup": "Agreement",
    "version": "0.1.0",
    "options": [
        {"name": "outcome", "type": "List", "title": "Outcome categories", "default": "2", "options": [
            {"name": "2", "title": "2 (binary)"}, {"name": "3", "title": "3"},
            {"name": "4", "title": "4"}, {"name": "5", "title": "5"}]},
        {"name": "props", "type": "String", "title": "Expected proportion of each category", "default": "0.20, 0.80"},
        {"name": "raters", "type": "List", "title": "Raters", "default": "2", "options": [
            {"name": "2", "title": "2"}, {"name": "3", "title": "3"}, {"name": "4", "title": "4"},
            {"name": "5", "title": "5"}, {"name": "6", "title": "6"}]},
        {"name": "kappa0", "type": "Number", "title": "Null kappa to reject (kappa0)", "default": 0.4, "min": 0.01,
         "max": 0.99},
        {"name": "kappa1", "type": "Number", "title": "Alternative kappa to detect (kappa1)", "default": 0.6,
         "min": 0.01, "max": 0.99},
        {"name": "alpha", "type": "Number", "title": "Two-sided alpha", "default": 0.05, "min": 0.001, "max": 0.2},
        {"name": "power", "type": "Number", "title": "Power", "default": 0.8, "min": 0.01, "max": 0.99},
        {"name": "simulate", "type": "Bool", "title": "Monte Carlo check of the planned study", "default": False},
        {"name": "draws", "type": "Integer", "title": "Simulated studies", "default": 2000, "min": 100,
         "max": 20000},
        {"name": "seed", "type": "Integer", "title": "Random seed", "default": 20261018, "min": 1,
         "max": 2147483647},
    ],
    "results": [
        {"name": "summary", "type": "Text", "title": "Interpretation"},
        {"name": "size", "type": "Table", "title": "Required Sample Size", "columns": [
            {"name": "n", "title": "Subjects", "type": "integer"},
            {"name": "categories", "title": "Categories", "type": "integer"},
            {"name": "raters", "title": "Raters", "type": "integer"},
            {"name": "props", "title": "Proportions", "type": "text"},
            {"name": "kappa0", "title": "Null kappa", "type": "number"},
            {"name": "kappa1", "title": "Alternative kappa", "type": "number"},
            {"name": "alpha", "title": "Alpha", "type": "number"},
            {"name": "power", "title": "Power", "type": "number"},
        ]},
        {"name": "check", "type": "Table", "title": "Monte Carlo Check", "visible": "(simulate)", "columns": [
            {"name": "statistic", "title": "", "type": "text"},
            {"name": "planned", "title": "Planned", "type": "number"},
            {"name": "simulated", "title": "Simulated", "type": "number"},
            {"name": "se", "title": "Monte Carlo SE", "type": "number"},
        ]},
    ],
}


def run(data, options, out):
    import math

    import cpj_kappasize as ks

    categories, raters = int(options["outcome"]), int(options["raters"])
    kappa0, kappa1, alpha, power = options["kappa0"], options["kappa1"], options["alpha"], options["power"]
    props, rescaled = ks.parse_props(options["props"], categories)
    if kappa0 == kappa1:
        raise InputError("The null kappa (kappa0) and the alternative kappa (kappa1) must differ.")
    if not alpha < power:
        raise InputError("The power must exceed alpha.")

    exact, lam, per_subject = ks.power_n(categories, raters, props, kappa0, kappa1, alpha, power)
    n = math.ceil(exact)
    out.row("size", n=n, categories=categories, raters=raters, props=ks.props_text(props), kappa0=kappa0,
            kappa1=kappa1, alpha=alpha, power=power)
    out.note("size", f"kappaSize power approach: N = lambda / "
                     f"{per_subject:.6g}, rounded up to {n:,}, where {per_subject:.6g} is the expected goodness-of-fit "
                     f"chi-square per subject between kappa1 and kappa0 and lambda = {lam:.6g} is the noncentrality "
                     f"giving a 1-df chi-square test power {power:g} at two-sided alpha = {alpha:g} (kappaSize's "
                     f"bisection, to within 0.00001 in power). The category proportions are treated as known.")
    ks.common_notes(out, "size", categories, raters, rescaled)
    if kappa1 < kappa0:
        out.note("size", "kappa1 is below kappa0: this sizes a study to show that agreement is WORSE than kappa0.")
    ks.sparse_note(out, "size", ks.min_expected_count(categories, raters, props, [kappa0, kappa1], n),
                   ks.mc_available(categories, raters))

    direction = "above" if kappa1 > kappa0 else "below"
    text = (f"**{n:,} subjects**, each rated by {ks.raters_text(raters)}, give a two-sided goodness-of-fit test at "
            f"alpha = {alpha:g} an approximate power of {power:g} to reject kappa = {kappa0:g} when the true kappa is {kappa1:g} "
            f"({direction} the null).")

    if options["simulate"] and not ks.mc_available(categories, raters):
        out.note("check", ks.MC_UNAVAILABLE)
    elif options["simulate"]:
        draws, seed = int(options["draws"]), int(options["seed"])
        rejected, size = ks.simulate_power(raters, props, kappa0, kappa1, alpha, n, draws, seed)
        out.row("check", statistic=f"Power (true kappa = {kappa1:g})", planned=power, simulated=rejected,
                se=ks.mc_se(rejected, draws))
        out.row("check", statistic=f"Type I error (true kappa = {kappa0:g})", planned=alpha, simulated=size,
                se=ks.mc_se(size, draws))
        out.note("check", f"{draws:,} simulated studies of {n:,} subjects for each row, random seed {seed}; each "
                          f"analysed with {ks.MC_ANALYSIS.format(f'test of kappa = {kappa0:g}')}.")
        text += (f" In {draws:,} simulated studies (seed {seed}) the test rejected kappa = {kappa0:g} in "
                 f"{100 * rejected:.1f}% when the true kappa was {kappa1:g} (planned {100 * power:g}%) and in "
                 f"{100 * size:.1f}% when it was {kappa0:g} (planned {100 * alpha:g}%).")
    out.markdown("summary", text)
