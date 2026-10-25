"""pyexacttests against R 4.6.0 (oracle calls below; values pasted from R with %.17g, Exact's with %.12g).

Fisher, FISHER: R's own stats::fisher.test code with its uniroot() calls given tol = 1e-300, so the
estimate and limits are exact to rounding. As shipped (uniroot's default tol, eps^0.25) fisher.test is
coarse: for matrix(c(40, 1, 2, 35), 2) its upper 95% limit is 16384.0 instead of 29014.35, and its
estimate 512.57 instead of 511.62. The p-value involves no root finding and is identical either way.
    ft <- stats::fisher.test
    body(ft) <- do.call(substitute, list(body(ft), list(uniroot = quote((function(...)
        stats::uniroot(..., tol = 1e-300, maxiter = 10000))))))
    environment(ft) <- environment(stats::fisher.test)
    ft(matrix(c(a, c, b, d), 2), alternative = alt, conf.level = level)  # rows = groups, column 1 = event
Barnard and Boschloo, UNCONDITIONAL: Exact 3.3,
    exact.test(matrix(c(a, c, b, d), 2), alternative = alt, method = "z-pooled" or "boschloo",
               npNumbers = 1000, to.plot = FALSE)$p.value
after giving the optimise() that refines the nuisance parameter tol = 1e-12 (its default leaves errors near
1e-9; Exact rounds p to 12 significant digits):
    bc <- get("binomialCode", envir = asNamespace("Exact"))
    body(bc) <- do.call(substitute, list(body(bc), list(optimise = quote((function(...)
        stats::optimise(..., tol = 1e-12))))))
    environment(bc) <- asNamespace("Exact")
    assignInNamespace("binomialCode", bc, "Exact")
Where the supremum is at pi -> 0 (p = 1) Exact, whose grid stops at pi = 1e-5, reports slightly less than 1;
those cases are checked against the closed form in test_supremum_at_the_boundary.
McNemar, MCNEMAR: binom.test(b, b + c, 0.5, alternative = alt, conf.level = level); odds ratio b/c and
conf.int / (1 - conf.int). Same as exact2x2::mcnemar.exact for two-sided 95%: for b = 11, c = 3 it gives
p 0.057373046875000035, OR 3.6666666666666665, CI 0.96859819314651641 to 20.468769603442912.
Risk difference, NEWCOMBE: Newcombe (1998) method 10 from prop.test(x, n, correct = FALSE,
conf.level = L)$conf.int, L = level (two-sided) or 2 * level - 1 (one-sided bound; other limit -1 or 1):
    p1 - p2 - sqrt((p1 - l1)^2 + (u2 - p2)^2),  p1 - p2 + sqrt((u1 - p1)^2 + (p2 - l2)^2)
"""
import importlib.util
import math
import signal
import sys
import unittest

from cpjtest import ROOT, factor, number, rows, run_analysis

Inf = math.inf


def _load():
    sys.path.insert(0, str(ROOT / "inst" / "python"))
    handler = signal.getsignal(signal.SIGINT)  # importing cpj_runtime resets SIGINT for its own process
    spec = importlib.util.spec_from_file_location(
        "pyexacttests", ROOT / "inst" / "python" / "analyses" / "meddecide/pyexacttests.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    signal.signal(signal.SIGINT, handler)
    return module


X = _load()

# (a, b, c, d, alternative, level): (p, estimate, lower, upper); a/b = events/non-events in the comparison group
FISHER = {
    (7, 8, 12, 3, "two-sided", 0.95): (0.12813593203398313, 0.23094194095879916, 0.029292871845823281, 1.3772717024332291),
    (7, 8, 12, 3, "two-sided", 0.9): (0.12813593203398313, 0.23094194095879916, 0.039954012216846017, 1.0943189343992759),
    (7, 8, 12, 3, "less", 0.95): (0.06406796601699162, 0.23094194095879916, 0, 1.0943189343992754),
    (7, 8, 12, 3, "less", 0.9): (0.06406796601699162, 0.23094194095879916, 0, 0.83893071867070268),
    (7, 8, 12, 3, "greater", 0.95): (0.98953023488255876, 0.23094194095879916, 0.039954012216846038, Inf),
    (7, 8, 12, 3, "greater", 0.9): (0.98953023488255876, 0.23094194095879916, 0.056247944145235693, Inf),
    (3, 7, 9, 2, "two-sided", 0.95): (0.029973122852379845, 0.10940273727990615, 0.0071139314837343065, 0.98795973055934783),
    (3, 7, 9, 2, "two-sided", 0.9): (0.029973122852379845, 0.10940273727990615, 0.010746092785506334, 0.7569319552488325),
    (3, 7, 9, 2, "less", 0.95): (0.024172422005239374, 0.10940273727990615, 0, 0.75693195524883217),
    (3, 7, 9, 2, "less", 0.9): (0.024172422005239374, 0.10940273727990615, 0, 0.55570523780119951),
    (3, 7, 9, 2, "greater", 0.95): (0.99828190385465931, 0.10940273727990615, 0.010746092785506339, Inf),
    (3, 7, 9, 2, "greater", 0.9): (0.99828190385465931, 0.10940273727990615, 0.016806441795818364, Inf),
    (2, 0, 5, 9, "two-sided", 0.95): (0.17499999999999991, Inf, 0.25161719495902035, Inf),
    (2, 0, 5, 9, "two-sided", 0.9): (0.17499999999999991, Inf, 0.38952465492214872, Inf),
    (2, 0, 5, 9, "less", 0.95): (1, Inf, 0, Inf),
    (2, 0, 5, 9, "less", 0.9): (1, Inf, 0, Inf),
    (2, 0, 5, 9, "greater", 0.95): (0.17499999999999988, Inf, 0.38952465492214916, Inf),
    (2, 0, 5, 9, "greater", 0.9): (0.17499999999999988, Inf, 0.63384325881782344, Inf),
    (0, 5, 7, 3, "two-sided", 0.95): (0.025641025641025654, 0, 0, 0.87916335596231276),
    (0, 5, 7, 3, "two-sided", 0.9): (0.025641025641025654, 0, 0, 0.62921543355646381),
    (0, 5, 7, 3, "less", 0.95): (0.018648018648018669, 0, 0, 0.62921543355646348),
    (0, 5, 7, 3, "less", 0.9): (0.018648018648018669, 0, 0, 0.42437314868149989),
    (0, 5, 7, 3, "greater", 0.95): (1, 0, 0, Inf),
    (0, 5, 7, 3, "greater", 0.9): (1, 0, 0, Inf),
    (1, 20, 15, 4, "two-sided", 0.95): (1.6342174295455735e-06, 0.015880302050101568, 0.00030249294385742431, 0.1489013506416568),
    (1, 20, 15, 4, "two-sided", 0.9): (1.6342174295455735e-06, 0.015880302050101568, 0.00061511182783892707, 0.11725284974800705),
    (1, 20, 15, 4, "less", 0.95): (1.3104573727488105e-06, 0.015880302050101568, 0, 0.11725284974800705),
    (1, 20, 15, 4, "less", 0.9): (1.3104573727488105e-06, 0.015880302050101568, 0, 0.088323096068743057),
    (1, 20, 15, 4, "greater", 0.95): (0.99999998458285444, 0.015880302050101568, 0.00061511182783892772, Inf),
    (1, 20, 15, 4, "greater", 0.9): (0.99999998458285444, 0.015880302050101568, 0.0012731957146605917, Inf),
    (40, 2, 1, 35, "two-sided", 0.95): (1.2619695693844304e-18, 511.62353412690982, 51.644066270578335, 29014.34822145919),
    (40, 2, 1, 35, "two-sided", 0.9): (1.2619695693844304e-18, 511.62353412690982, 65.514318058143971, 14253.333722968162),
    (40, 2, 1, 35, "less", 0.95): (1, 511.62353412690982, 0, 14253.333722968851),
    (40, 2, 1, 35, "less", 0.9): (1, 511.62353412690982, 0, 6871.2102737730556),
    (40, 2, 1, 35, "greater", 0.95): (1.2619695693844309e-18, 511.62353412690982, 65.514318058143687, Inf),
    (40, 2, 1, 35, "greater", 0.9): (1.2619695693844309e-18, 511.62353412690982, 87.080020586439815, Inf),
    (6, 4, 4, 6, "two-sided", 0.95): (0.65628179869665937, 2.1581607046244233, 0.27739041336559983, 19.145228047361989),
    (6, 4, 4, 6, "two-sided", 0.9): (0.65628179869665937, 2.1581607046244233, 0.36318480468379999, 14.115474739083957),
    (6, 4, 4, 6, "less", 0.95): (0.91055229600121235, 2.1581607046244233, 0, 14.11547473908395),
    (6, 4, 4, 6, "less", 0.9): (0.91055229600121235, 2.1581607046244233, 0, 10.017313513830215),
    (6, 4, 4, 6, "greater", 0.95): (0.32814089934832957, 2.1581607046244233, 0.36318480468380027, Inf),
    (6, 4, 4, 6, "greater", 0.9): (0.32814089934832957, 2.1581607046244233, 0.49432310169030047, Inf),
    (7, 5, 2, 11, "two-sided", 0.95): (0.041405303540180363, 7.0181527267648427, 0.90252403920249968, 93.440181911092964),
    (7, 5, 2, 11, "two-sided", 0.9): (0.041405303540180363, 7.0181527267648427, 1.1614938161217994, 62.367427097719414),
    (7, 5, 2, 11, "less", 0.95): (0.99674249562525241, 7.0181527267648427, 0, 62.367427097719371),
    (7, 5, 2, 11, "less", 0.9): (0.99674249562525241, 7.0181527267648427, 0, 40.361905136255992),
    (7, 5, 2, 11, "greater", 0.95): (0.033495759860008065, 7.0181527267648427, 1.1614938161217998, Inf),
    (7, 5, 2, 11, "greater", 0.9): (0.033495759860008065, 7.0181527267648427, 1.5558775158051235, Inf),
    (5, 0, 1, 9, "two-sided", 0.95): (0.001998001998001998, Inf, 2.6677243865637901, Inf),
    (5, 0, 1, 9, "two-sided", 0.9): (0.001998001998001998, Inf, 3.7681492518773658, Inf),
    (5, 0, 1, 9, "less", 0.95): (1, Inf, 0, Inf),
    (5, 0, 1, 9, "less", 0.9): (1, Inf, 0, Inf),
    (5, 0, 1, 9, "greater", 0.95): (0.0019980019980019984, Inf, 3.7681492518773689, Inf),
    (5, 0, 1, 9, "greater", 0.9): (0.0019980019980019984, Inf, 5.6620710583671894, Inf),
    (12, 30, 25, 18, "two-sided", 0.95): (0.0085429521190048142, 0.29250771793513236, 0.10529610548015414, 0.77517226527418548),
    (12, 30, 25, 18, "two-sided", 0.9): (0.0085429521190048142, 0.29250771793513236, 0.12264630546565879, 0.67552552018560752),
    (12, 30, 25, 18, "less", 0.95): (0.0054575874288981408, 0.29250771793513236, 0, 0.6755255201856073),
    (12, 30, 25, 18, "less", 0.9): (0.0054575874288981408, 0.29250771793513236, 0, 0.57608534113549237),
    (12, 30, 25, 18, "greater", 0.95): (0.99862263568182319, 0.29250771793513236, 0.12264630546565874, Inf),
    (12, 30, 25, 18, "greater", 0.9): (0.99862263568182319, 0.29250771793513236, 0.14590341090510472, Inf),
    # comparison B (2/13) against reference A (7/12): the table of the analysis tests with the groups swapped
    (2, 11, 7, 5, "two-sided", 0.95): (0.04140530354018037, 0.14248763726476643, 0.010702033959560221, 1.1080037279490451),
    (500, 501, 480, 520, "two-sided", 0.95): (0.39562634739519609, 1.0811288127497567, 0.90374817886777226, 1.2934289416861169),
}

# (a, b, c, d, alternative): (Barnard p, Boschloo p)
UNCONDITIONAL = {
    (7, 8, 12, 3, "two-sided"): (0.0682183093232, 0.0682183093232),  # scipy.stats.barnard_exact: 0.0681534327315
    (7, 8, 12, 3, "less"): (0.0341091546616, 0.0341091546616),  # scipy (its documented example): 0.0340767163658
    (7, 8, 12, 3, "greater"): (1, 0.977121534757),
    (3, 7, 9, 2, "two-sided"): (0.0270442962646, 0.0266036987305),  # scipy: 0.0244383457013 and 0.0274699365308
    (3, 7, 9, 2, "less"): (0.0137349682654, 0.0137349682654),
    (3, 7, 9, 2, "greater"): (1, 0.98938497044),
    (2, 0, 5, 9, "two-sided"): (0.116984270979, 0.106048583984),  # scipy boschloo_exact (2 x one-sided): 0.160075639976
    (2, 0, 5, 9, "less"): (1, 1),
    (2, 0, 5, 9, "greater"): (0.116980343283, 0.0800378199879),
    (0, 5, 7, 3, "two-sided"): (0.0147094726562, 0.0147094726562),
    (0, 5, 7, 3, "less"): (0.00954953694925, 0.00757347410596),
    (0, 5, 7, 3, "greater"): (1, 1),
    (1, 20, 15, 4, "two-sided"): (5.9877311287e-07, 7.08120381179e-07),
    (1, 20, 15, 4, "less"): (3.26528053886e-07, 3.26528053886e-07),
    (1, 20, 15, 4, "greater"): (1, 0.999997876142),
    (40, 2, 1, 35, "two-sided"): (3.48726111363e-19, 3.48726111363e-19),
    (40, 2, 1, 35, "less"): (1, 1),
    (40, 2, 1, 35, "greater"): (2.01526550809e-19, 2.01526550809e-19),
    (6, 4, 4, 6, "two-sided"): (0.523474661508, 0.503444671631),
    (6, 4, 4, 6, "less"): (1, 0.790313720703),  # Exact's Barnard: 0.999900014499, see test_supremum_at_the_boundary
    (6, 4, 4, 6, "greater"): (0.261737330754, 0.251722335815),
    (7, 5, 2, 11, "two-sided"): (0.0297732837751, 0.0297732837751),
    (7, 5, 2, 11, "less"): (1, 0.989797231144),
    (7, 5, 2, 11, "greater"): (0.0171588002794, 0.0154583515318),
    (5, 0, 1, 9, "two-sided"): (0.00067138671875, 0.00067138671875),
    (5, 0, 1, 9, "less"): (1, 1),
    (5, 0, 1, 9, "greater"): (0.000475862810758, 0.000475862810758),
    (12, 30, 25, 18, "two-sided"): (0.00623866300385, 0.0066529569137),
    (12, 30, 25, 18, "less"): (0.00324019144934, 0.00315967424251),
    (12, 30, 25, 18, "greater"): (1, 0.997580634051),
    (2, 11, 7, 5, "two-sided"): (0.0297732837751, 0.0297732837751),
    # 1 - Fisher's p is 8.2e-12 here: a looser tie tolerance (1e-10) merges table (0, 0), Fisher's p = 1, into
    # Boschloo's rejection region and gives 1
    (2, 17, 31, 2, "greater"): (1, 0.999999929281),
}

# 500/1000 vs 480/1000, two-sided (Barnard, Boschloo): exact.test(matrix(c(500, 480, 500, 520), 2), ...) as above
# (7 s and 75 s). A separate full-enumeration R computation (|z| or Fisher's p rounded to 12 digits, the sum over the
# rejection region maximised over a 2000-point pi grid, then optimize(tol = 1e-14)) gives 0.529845365449854 and
# 0.381742147705521; Exact's Barnard is 1.7e-11 (relative) lower.
BIG = (0.529845365441, 0.381742147706)

# (b, c, alternative, level): (p, odds ratio, lower, upper)
MCNEMAR = {
    (11, 3, "two-sided", 0.95): (0.057373046875000042, 3.6666666666666665, 0.96859819314651641, 20.468769603442912),
    (11, 3, "two-sided", 0.9): (0.057373046875000042, 3.6666666666666665, 1.1475052083721222, 15.365827607183087),
    (11, 3, "less", 0.95): (0.9935302734375, 3.6666666666666665, 0, 15.365827607183087),
    (11, 3, "less", 0.9): (0.9935302734375, 3.6666666666666665, 0, 11.273379111933766),
    (11, 3, "greater", 0.95): (0.028686523437500021, 3.6666666666666665, 1.1475052083721227, Inf),
    (11, 3, "greater", 0.9): (0.028686523437500021, 3.6666666666666665, 1.3982130639717236, Inf),
    (5, 0, "two-sided", 0.95): (0.062500000000000014, Inf, 0.9163558573154601, Inf),
    (5, 0, "two-sided", 0.9): (0.062500000000000014, Inf, 1.2186736836827581, Inf),
    (5, 0, "less", 0.95): (1, Inf, 0, Inf),
    (5, 0, "less", 0.9): (1, Inf, 0, Inf),
    (5, 0, "greater", 0.95): (0.031250000000000007, Inf, 1.2186736836827585, Inf),
    (5, 0, "greater", 0.9): (0.031250000000000007, Inf, 1.7097138638119553, Inf),
    (0, 4, "two-sided", 0.95): (0.125, 0, 0, 1.5148668593658703),
    (0, 4, "two-sided", 0.9): (0.125, 0, 0, 1.1147425268811277),
    (0, 4, "less", 0.95): (0.0625, 0, 0, 1.1147425268811277),
    (0, 4, "less", 0.9): (0.0625, 0, 0, 0.77827941003892287),
    (0, 4, "greater", 0.95): (1, 0, 0, Inf),
    (0, 4, "greater", 0.9): (1, 0, 0, Inf),
    (30, 12, "two-sided", 0.95): (0.0079158973348967352, 2.5, 1.2429631350621515, 5.3616684835077661),
    (30, 12, "two-sided", 0.9): (0.0079158973348967352, 2.5, 1.3728787821812889, 4.7509055897746846),
    (30, 12, "less", 0.95): (0.99855637601285707, 2.5, 0, 4.7509055897746846),
    (30, 12, "less", 0.9): (0.99855637601285707, 2.5, 0, 4.1463196219472778),
    (30, 12, "greater", 0.95): (0.0039579486674483676, 2.5, 1.3728787821812893, Inf),
    (30, 12, "greater", 0.9): (0.0039579486674483676, 2.5, 1.5410285581297756, Inf),
}

# (x1, n1, x2, n2, alternative, level): (difference, lower, upper)
NEWCOMBE = {
    (7, 12, 2, 13, "two-sided", 0.95): (0.42948717948717952, 0.053064023172772978, 0.67876633803607511),
    (7, 12, 2, 13, "two-sided", 0.9): (0.42948717948717952, 0.11254969173867774, 0.65084670933022615),
    (7, 12, 2, 13, "less", 0.95): (0.42948717948717952, -1, 0.65084670933022615),
    (7, 12, 2, 13, "less", 0.9): (0.42948717948717952, -1, 0.6132934034044325),
    (7, 12, 2, 13, "greater", 0.95): (0.42948717948717952, 0.11254969173867774, 1),
    (7, 12, 2, 13, "greater", 0.9): (0.42948717948717952, 0.18377871818870628, 1),
    (0, 10, 0, 20, "two-sided", 0.95): (0, -0.16112515805281927, 0.27753279986288903),
    (0, 10, 0, 20, "two-sided", 0.9): (0, -0.11915783736096437, 0.21294197008340682),
    (0, 10, 0, 20, "less", 0.95): (0, -1, 0.21294197008340682),
    (0, 10, 0, 20, "less", 0.9): (0, -1, 0.14106868209054091),
    (0, 10, 0, 20, "greater", 0.95): (0, -0.11915783736096437, 1),
    (0, 10, 0, 20, "greater", 0.9): (0, -0.075886979110764419, 1),
    (10, 10, 0, 7, "two-sided", 0.95): (1, 0.54991721626540491, 1),
    (10, 10, 0, 7, "two-sided", 0.9): (1, 0.64921099931872273, 1),
    (10, 10, 0, 7, "less", 0.95): (1, -1, 1),
    (10, 10, 0, 7, "less", 0.9): (1, -1, 1),
    (10, 10, 0, 7, "greater", 0.95): (1, 0.64921099931872273, 1),
    (10, 10, 0, 7, "greater", 0.9): (1, 0.76332598636733595, 1),
    (3, 10, 9, 11, "two-sided", 0.95): (-0.5181818181818183, -0.75047802513993511, -0.095021892729778068),
    (3, 10, 9, 11, "two-sided", 0.9): (-0.5181818181818183, -0.72865867791654249, -0.16194731826281245),
    (3, 10, 9, 11, "less", 0.95): (-0.5181818181818183, -1, -0.16194731826281245),
    (3, 10, 9, 11, "less", 0.9): (-0.5181818181818183, -1, -0.24288076975920714),
    (3, 10, 9, 11, "greater", 0.95): (-0.5181818181818183, -0.72865867791654249, 1),
    (3, 10, 9, 11, "greater", 0.9): (-0.5181818181818183, -0.69742352689293297, 1),
}


class Oracle(unittest.TestCase):
    def assertClose(self, got, expected, rel=1e-10):
        if expected in (0, Inf, -Inf) or got in (0, Inf, -Inf):
            self.assertEqual(got, expected)
        else:
            self.assertLessEqual(abs(got - expected), rel * abs(expected), f"{got!r} vs {expected!r}")

    def assertAllClose(self, got, expected):
        self.assertEqual(len(got), len(expected))
        for value, want in zip(got, expected):
            self.assertClose(value, want)


class Fisher(Oracle):
    def test_matches_fisher_test(self):
        for (a, b, c, d, alternative, level), expected in FISHER.items():
            with self.subTest(table=(a, b, c, d), alternative=alternative, level=level):
                self.assertAllClose(X.fisher(a, b, c, d, alternative, level), expected)

    def test_an_empty_margin_leaves_the_odds_ratio_undefined(self):
        # fisher.test(matrix(c(0, 0, 4, 6), 2)) reports p = 1 with the meaningless estimate 0 and interval (0, Inf)
        self.assertEqual(X.fisher(0, 4, 0, 6, "two-sided", 0.95), (1.0, None, None, None))
        self.assertEqual(X.fisher(3, 0, 5, 0, "greater", 0.95), (1.0, None, None, None))


class Unconditional(Oracle):
    def test_matches_exact_test(self):
        for (a, b, c, d, alternative), expected in UNCONDITIONAL.items():
            for method, want in zip(("barnard", "boschloo"), expected):
                with self.subTest(table=(a, b, c, d), alternative=alternative, method=method):
                    self.assertClose(X.unconditional(method, a, a + b, c, c + d, alternative), want)

    def test_supremum_at_the_boundary(self):
        # Observed proportions equal, or reversed for the one-sided alternative: table (0, 0) (statistic 0) is in
        # the rejection region and has probability -> 1 as pi -> 0, so the supremum is 1. Exact searches pi in
        # [1e-5, 0.99999] only and reports 0.999900014499 for (6, 4, 4, 6) 'less', 0.9999800005 for (1, 1, 1, 1).
        for a, b, c, d, alternative in ((6, 4, 4, 6, "less"), (1, 1, 1, 1, "less"), (1, 1, 1, 1, "greater"),
                                        (5, 5, 5, 5, "greater")):
            self.assertEqual(X.unconditional("barnard", a, a + b, c, c + d, alternative), 1.0)

    def test_boschloo_is_never_larger_than_fisher(self):
        # Boschloo's test orders the tables by Fisher's p-value, so its p-value is at most Fisher's
        # (scipy's two-sided version, twice the smaller one-sided p, does not guarantee it).
        for n1, n2 in ((5, 7), (4, 4)):
            for x1 in range(n1 + 1):
                for x2 in range(n2 + 1):
                    for alternative in ("two-sided", "less", "greater"):
                        fisher_p = X.fisher(x1, n1 - x1, x2, n2 - x2, alternative, 0.95)[0]
                        boschloo_p = X.unconditional("boschloo", x1, n1, x2, n2, alternative)
                        self.assertLessEqual(boschloo_p, fisher_p * (1 + 1e-9), (x1, n1, x2, n2, alternative))


class McNemar(Oracle):
    def test_matches_binom_test(self):
        for (b, c, alternative, level), expected in MCNEMAR.items():
            with self.subTest(b=b, c=c, alternative=alternative, level=level):
                self.assertAllClose(X.mcnemar(b, c, alternative, level), expected)

    def test_no_discordant_pairs(self):
        self.assertEqual(X.mcnemar(0, 0, "two-sided", 0.95), (None, None, None, None))


class Newcombe(Oracle):
    def test_published_examples(self):
        # Newcombe RG, Stat Med 1998;17:873-90, Table II, method 10
        for (x1, n1, x2, n2), interval in (((56, 70, 48, 80), (0.0524, 0.3339)), ((9, 10, 3, 10), (0.1705, 0.8090)),
                                           ((0, 10, 0, 20), (-0.1611, 0.2775))):
            _, lower, upper = X.newcombe(x1, n1, x2, n2, "two-sided", 0.95)
            self.assertEqual((round(lower, 4), round(upper, 4)), interval)

    def test_matches_prop_test_wilson_limits(self):
        for (x1, n1, x2, n2, alternative, level), expected in NEWCOMBE.items():
            with self.subTest(table=(x1, n1, x2, n2), alternative=alternative, level=level):
                self.assertAllClose(X.newcombe(x1, n1, x2, n2, alternative, level), expected)


BASE = {"group": "g", "outcome": "y", "counts": None, "event": "yes", "refLevel": "B", "design": "independent",
        "alternative": "twoSided", "ciWidth": 95}
# group A: 7 of 12 with the event, group B: 2 of 13; plus one row without a group and one without an outcome
TRIAL = {"g": factor(["A"] * 12 + ["B"] * 13 + [None, "A"]),
         "y": factor(["yes"] * 7 + ["no"] * 5 + ["yes"] * 2 + ["no"] * 11 + ["yes", None])}
# 49 pairs: 20 positive twice, 11 positive only first, 3 positive only second, 15 negative twice
PAIRS = {"f": factor(["pos"] * 31 + ["neg"] * 18),
         "s": factor(["pos"] * 20 + ["neg"] * 11 + ["pos"] * 3 + ["neg"] * 15)}
PAIRED = dict(BASE, group="f", outcome="s", event="pos", design="paired", refLevel=None)


def aggregated(cells, levels=("no", "yes")):
    """Columns for (group, outcome, count) rows."""
    return {"g": factor([g for g, _, _ in cells]), "y": factor([y for _, y, _ in cells], levels=list(levels)),
            "w": number([w for _, _, w in cells])}


class Analysis(Oracle):
    def run_ok(self, columns, options):
        result = run_analysis("pyexacttests", columns=columns, options=options)
        self.assertEqual(result["status"], "ok", result.get("error") or result["console"])
        return result

    def run_error(self, columns, options):
        result = run_analysis("pyexacttests", columns=columns, options=options)
        self.assertEqual(result["status"], "input_error", result["console"])
        return result["error"]["message"]

    def assertRow(self, row, expected):
        for key, value in expected.items():
            if value is None or isinstance(value, str):
                self.assertEqual(row[key], value, key)
            else:
                self.assertClose(row[key], value)

    def test_independent_groups(self):
        result = self.run_ok(TRIAL, BASE)
        self.assertEqual(rows(result, "crosstab"), [
            {"label": "A", "event": 7, "nonevent": 5, "total": 12},
            {"label": "B", "event": 2, "nonevent": 11, "total": 13},
            {"label": "Total", "event": 9, "nonevent": 16, "total": 25}])
        p, estimate, lower, upper = FISHER[(7, 5, 2, 11, "two-sided", 0.95)]
        barnard, boschloo = UNCONDITIONAL[(7, 5, 2, 11, "two-sided")]
        tests = rows(result, "tests")
        self.assertEqual([row["test"] for row in tests],
                         ["Fisher's exact test", "Barnard's exact test", "Boschloo's exact test"])
        for row, want in zip(tests, (p, barnard, boschloo)):
            self.assertClose(row["p"], want)
        odds, risk = rows(result, "effects")
        self.assertRow(odds, {"measure": "Odds ratio, A vs B (conditional MLE)", "estimate": estimate, "lower": lower,
                              "upper": upper})
        difference, rd_lower, rd_upper = NEWCOMBE[(7, 12, 2, 13, "two-sided", 0.95)]
        self.assertRow(risk, {"measure": "Risk difference, A minus B", "estimate": difference, "lower": rd_lower,
                              "upper": rd_upper})
        crosstab_notes = result["tables"]["crosstab"]["notes"]
        self.assertIn("Rows: g. Columns: y, event = yes, no event = no.", crosstab_notes)
        self.assertIn("2 row(s) with a missing value were excluded.", crosstab_notes)
        self.assertIn("Two-sided p-values.", result["tables"]["tests"]["notes"])
        effect_notes = result["tables"]["effects"]["notes"]
        self.assertIn("Odds ratio = odds of yes in A divided by the odds in B; risk difference = proportion with yes "
                      "in A minus that in B.", effect_notes)
        self.assertIn("the sample odds ratio ad/bc is 7.7.", effect_notes[2])
        # p = .041 while the exact 95% interval 0.903 to 93.4 contains 1: the two are explained, not left to clash
        self.assertEqual(effect_notes[3],
                         "Fisher's two-sided p-value and the 95% odds-ratio interval disagree about an odds ratio of 1. "
                         "As in R's fisher.test, the p-value sums the probabilities of all tables no more likely than "
                         "the observed one, while the interval combines two one-sided tests at 2.5% each, so the two "
                         "can differ near the 5% boundary.")
        self.assertEqual(result["texts"]["summary"],
                         "**yes** in **A**: 7 of 12 (58.3%); in **B**: 2 of 13 (15.4%). Odds ratio 7.02 (95% CI "
                         "0.903 to 93.4); risk difference 42.9 percentage points (95% CI 5.3 to 67.9). Two-sided "
                         "p-values: Fisher's exact test p = .041, Barnard's p = .030, Boschloo's p = .030. Fisher's "
                         "p-value and the odds-ratio interval disagree about an odds ratio of 1 (see the note under "
                         "Effect Sizes).")

    def test_reference_group_sets_the_direction(self):
        result = self.run_ok(TRIAL, dict(BASE, refLevel="A"))
        self.assertEqual([row["label"] for row in rows(result, "crosstab")], ["B", "A", "Total"])
        p, estimate, lower, upper = FISHER[(2, 11, 7, 5, "two-sided", 0.95)]
        self.assertClose(rows(result, "tests")[0]["p"], p)
        self.assertRow(rows(result, "effects")[0], {"estimate": estimate, "lower": lower, "upper": upper})
        difference, rd_lower, rd_upper = NEWCOMBE[(7, 12, 2, 13, "two-sided", 0.95)]
        self.assertRow(rows(result, "effects")[1], {"estimate": -difference, "lower": -rd_upper, "upper": -rd_lower})

    def test_one_sided_alternative(self):
        result = self.run_ok(TRIAL, dict(BASE, alternative="greater"))
        p, estimate, lower, _ = FISHER[(7, 5, 2, 11, "greater", 0.95)]
        barnard, boschloo = UNCONDITIONAL[(7, 5, 2, 11, "greater")]
        for row, want in zip(rows(result, "tests"), (p, barnard, boschloo)):
            self.assertClose(row["p"], want)
        self.assertRow(rows(result, "effects")[0], {"estimate": estimate, "lower": lower, "upper": None})
        self.assertRow(rows(result, "effects")[1], {"upper": 1.0})
        self.assertIn("One-sided p-values; the alternative is that yes is more likely in A than in B.",
                      result["tables"]["tests"]["notes"])
        self.assertIn("The upper limit of the one-sided odds-ratio interval is infinite (shown as '.').",
                      result["tables"]["effects"]["notes"])
        self.assertIn("Odds ratio 7.02 (95% lower confidence bound 1.16)", result["texts"]["summary"])
        # a one-sided bound inverts the one-sided test, so it always agrees with the p-value
        self.assertFalse(any("disagree" in note for note in result["tables"]["effects"]["notes"]))
        self.assertNotIn("disagree", result["texts"]["summary"])

    def test_counts_give_the_same_result_as_rows(self):
        cells = [("A", "yes", 7), ("A", "no", 5), ("B", "yes", 2), ("B", "no", 11), ("B", "no", None)]
        weighted = self.run_ok(aggregated(cells), dict(BASE, counts="w"))
        unweighted = self.run_ok(TRIAL, BASE)
        for table in ("crosstab", "tests", "effects"):
            self.assertEqual(rows(weighted, table), rows(unweighted, table))
        self.assertIn("1 row(s) with a missing value were excluded.", weighted["tables"]["crosstab"]["notes"])

    def test_a_zero_cell_gives_an_infinite_odds_ratio(self):
        result = self.run_ok(aggregated([("A", "yes", 5), ("A", "no", 0), ("B", "yes", 1), ("B", "no", 9)]),
                             dict(BASE, counts="w"))
        p, _, lower, _ = FISHER[(5, 0, 1, 9, "two-sided", 0.95)]
        self.assertClose(rows(result, "tests")[0]["p"], p)
        self.assertRow(rows(result, "effects")[0], {"estimate": None, "lower": lower, "upper": None})
        self.assertIn("A zero cell makes the odds ratio and its upper limit infinite (shown as '.').",
                      result["tables"]["effects"]["notes"])
        self.assertFalse(any("disagree" in note for note in result["tables"]["effects"]["notes"]))  # wholly above 1
        # reference A: 1 of 10 against 5 of 5, an interval wholly below 1 that agrees with p = .002
        # (ft(matrix(c(1, 5, 9, 0), 2)), ft = fisher.test with tightened uniroot as in the module docstring)
        swapped = self.run_ok(aggregated([("A", "yes", 5), ("A", "no", 0), ("B", "yes", 1), ("B", "no", 9)]),
                              dict(BASE, counts="w", refLevel="A"))
        self.assertRow(rows(swapped, "effects")[0], {"estimate": 0, "lower": 0, "upper": 0.37485131711378467})
        self.assertFalse(any("disagree" in note for note in swapped["tables"]["effects"]["notes"]))

    def test_default_reference_is_the_first_level(self):
        # Unset reference = first level (A): the odds ratio is the reciprocal of the B-reference one, with
        # the interval inverted, the risk difference changes sign and the two-sided p-values are the same.
        # That is the orientation of jamovi's Contingency Tables and of fisher.test(table(g, y)) here.
        by_b = self.run_ok(TRIAL, BASE)
        default = self.run_ok(TRIAL, dict(BASE, refLevel=None))
        (odds_b, risk_b), (odds, risk) = rows(by_b, "effects"), rows(default, "effects")
        self.assertEqual(odds["measure"], "Odds ratio, B vs A (conditional MLE)")
        self.assertClose(odds["estimate"], 1 / odds_b["estimate"])
        self.assertAllClose([odds["lower"], odds["upper"]], [1 / odds_b["upper"], 1 / odds_b["lower"]])
        self.assertAllClose([risk["estimate"], risk["lower"], risk["upper"]],
                            [-risk_b["estimate"], -risk_b["upper"], -risk_b["lower"]])
        self.assertAllClose([r["p"] for r in rows(default, "tests")], [r["p"] for r in rows(by_b, "tests")])
        self.assertTrue(any("chosen before seeing the results" in n for n in default["tables"]["tests"]["notes"]))

    def test_no_events(self):
        columns = {"g": factor(["A"] * 10 + ["B"] * 20), "y": factor(["no"] * 30, levels=["no", "yes"])}
        result = self.run_ok(columns, BASE)
        self.assertEqual([row["p"] for row in rows(result, "tests")], [1.0, 1.0, 1.0])
        self.assertRow(rows(result, "effects")[0], {"estimate": None, "lower": None, "upper": None})
        difference, lower, upper = NEWCOMBE[(0, 10, 0, 20, "two-sided", 0.95)]
        self.assertRow(rows(result, "effects")[1], {"estimate": difference, "lower": lower, "upper": upper})
        self.assertIn("The odds ratio is undefined because no subject has yes.", result["tables"]["effects"]["notes"])
        self.assertTrue(result["texts"]["summary"].endswith("Barnard's p = 1.000, Boschloo's p = 1.000."))

    def test_large_groups_skip_the_unconditional_tests(self):
        cells = [("A", "yes", 500), ("A", "no", 501), ("B", "yes", 480), ("B", "no", 520)]
        result = self.run_ok(aggregated(cells), dict(BASE, counts="w"))
        p, estimate, lower, upper = FISHER[(500, 501, 480, 520, "two-sided", 0.95)]
        self.assertEqual([row["p"] is None for row in rows(result, "tests")], [False, True, True])
        self.assertClose(rows(result, "tests")[0]["p"], p)
        self.assertRow(rows(result, "effects")[0], {"estimate": estimate, "lower": lower, "upper": upper})
        self.assertTrue(any(note.startswith("Barnard's and Boschloo's tests were not computed")
                            for note in result["tables"]["tests"]["notes"]))
        # p = .396 and the interval 0.904 to 1.293 contains 1: they agree, so no disagreement note
        self.assertFalse(any("disagree" in note for note in result["tables"]["effects"]["notes"]))

    def test_groups_of_1000_are_computed(self):
        # The largest groups Barnard and Boschloo enumerate. Barnard's supremum lies at pi = 0.00085, where the
        # discrete z distribution makes |z| >= 0.89 likely, so it exceeds Fisher's p (the note says it can).
        result = self.run_ok(aggregated([("A", "yes", 500), ("A", "no", 500), ("B", "yes", 480), ("B", "no", 520)]),
                             dict(BASE, counts="w"))
        fisher_p, barnard, boschloo = (row["p"] for row in rows(result, "tests"))
        self.assertClose(fisher_p, 0.39539967809402732)  # fisher.test(matrix(c(500, 480, 500, 520), 2))$p.value
        self.assertClose(barnard, BIG[0])
        self.assertClose(boschloo, BIG[1])
        self.assertGreater(barnard, fisher_p)
        self.assertIn("Boschloo's p-value is never larger than Fisher's, but Barnard's can be.",
                      result["tables"]["tests"]["notes"][1])
        self.assertFalse(any("not computed" in note for note in result["tables"]["tests"]["notes"]))

    def test_paired(self):
        result = self.run_ok(PAIRS, PAIRED)
        self.assertEqual(rows(result, "crosstab"), [
            {"label": "pos", "event": 20, "nonevent": 11, "total": 31},
            {"label": "neg", "event": 3, "nonevent": 15, "total": 18},
            {"label": "Total", "event": 23, "nonevent": 26, "total": 49}])
        p, estimate, lower, upper = MCNEMAR[(11, 3, "two-sided", 0.95)]
        self.assertEqual([row["test"] for row in rows(result, "tests")], ["Exact McNemar test"])
        self.assertClose(rows(result, "tests")[0]["p"], p)
        self.assertRow(rows(result, "effects")[0], {"measure": "Odds ratio, paired (b/c)", "estimate": estimate,
                                                    "lower": lower, "upper": upper})
        self.assertIn("Rows: f. Columns: s, event = pos. Each count is a number of pairs.",
                      result["tables"]["crosstab"]["notes"])
        self.assertTrue(result["tables"]["effects"]["notes"][0].startswith(
            "Odds ratio b/c = pairs with pos only at f divided by pairs with pos only at s; above 1 means pos is more "
            "frequent at f."))
        self.assertEqual(result["texts"]["summary"],
                         "**pos** at **f**: 31 of 49 (63.3%) pairs; at **s**: 23 of 49 (46.9%). Of the 14 discordant "
                         "pairs, 11 had **pos** only at **f** and 3 only at **s**: exact McNemar test p = .057 "
                         "(two-sided); paired odds ratio 3.67 (95% CI 0.969 to 20.5).")
        self.assertEqual(result["notices"], [])

    def test_paired_one_sided_with_an_ignored_reference_group(self):
        result = self.run_ok(PAIRS, dict(PAIRED, alternative="greater", ciWidth=90, refLevel="neg"))
        p, estimate, lower, _ = MCNEMAR[(11, 3, "greater", 0.9)]
        self.assertClose(rows(result, "tests")[0]["p"], p)
        self.assertRow(rows(result, "effects")[0], {"estimate": estimate, "lower": lower, "upper": None})
        self.assertTrue(result["tables"]["tests"]["notes"][0].endswith(
            "One-sided p; the alternative is that pos is more frequent at f than at s."))
        self.assertEqual([notice["type"] for notice in result["notices"]], ["INFO"])

    def test_paired_without_discordant_pairs(self):
        result = self.run_ok({"f": factor(["pos", "neg", "neg"]), "s": factor(["pos", "neg", "neg"])}, PAIRED)
        self.assertIsNone(rows(result, "tests")[0]["p"])
        self.assertRow(rows(result, "effects")[0], {"estimate": None, "lower": None, "upper": None})
        self.assertEqual(result["tables"]["tests"]["notes"],
                         ["There are no discordant pairs, so the test and the odds ratio are undefined."])

    def test_user_text_is_escaped_in_the_interpretation(self):
        columns = {"g": factor(["A_1", "A_1", "B*2", "B*2"]), "y": factor(["yes", "no", "no", "no"])}
        summary = self.run_ok(columns, dict(BASE, refLevel=None))["texts"]["summary"]
        self.assertIn("**A\\_1**", summary)
        self.assertIn("**B\\*2**", summary)

    def test_input_errors(self):
        counts = aggregated([("A", "yes", 5), ("A", "no", 1.5), ("B", "yes", 1), ("B", "no", 9)])
        self.assertIn("whole numbers", self.run_error(counts, dict(BASE, counts="w")))
        counts["w"] = number([5, -1, 1, 9])
        self.assertIn("whole numbers", self.run_error(counts, dict(BASE, counts="w")))
        three = {"g": factor(["A", "A", "B", "B"]), "y": factor(["yes", "no", "maybe", "no"])}
        message = self.run_error(three, BASE)
        self.assertIn("needs a 2x2 table, but 'y' gives 3 categories here (yes, maybe, no)", message)
        self.assertIn("jamovi's Contingency Tables, whose Fisher's exact test uses R's fisher.test.", message)
        groups = {"g": factor(["A", "B", "C"]), "y": factor(["yes", "no", "no"])}
        self.assertIn("'g' gives 3 categories here", self.run_error(groups, BASE))
        one = {"g": factor(["A", "A"], levels=["A", "B"]), "y": factor(["yes", "no"])}
        self.assertEqual(self.run_error(one, BASE), "'g' needs two groups with data; it has 1.")
        unused = {"g": factor(["A", "B"], levels=["A", "B", "C"]), "y": factor(["yes", "no"])}
        self.assertIn("The reference group 'C' has no observations", self.run_error(unused, dict(BASE, refLevel="C")))
        self.assertEqual(self.run_error(TRIAL, dict(BASE, outcome="g", event="A")), "Choose two different variables.")
        self.assertEqual(self.run_error({"g": number([1, 2]), "y": factor(["yes", "no"])}, BASE),
                         "'g' must be a nominal or ordinal variable.")
        mismatch = {"f": factor(["pos", "negative"]), "s": factor(["pos", "neg"])}
        self.assertIn("'f' has 'negative' where 's' has 'neg'", self.run_error(mismatch, PAIRED))
        absent = {"f": factor(["positive", "neg"]), "s": factor(["pos", "neg"])}
        self.assertIn("'pos' is not a level of 'f'", self.run_error(absent, PAIRED))


if __name__ == "__main__":
    unittest.main()
