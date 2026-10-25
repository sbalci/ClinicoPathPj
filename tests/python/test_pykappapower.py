"""pykappapower: kappaSize's power-based sample size (PowerBinary, Power3Cats, Power4Cats, Power5Cats) and the
Monte Carlo check of the planned study.

Oracles: kappaSize 1.2 in R 4.6.0 (each call quoted at its value), and the exact enumeration pw() of the R
script at the end of tests/python/test_pykappaci.py.
"""
import itertools
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "inst" / "python"))

import numpy as np  # noqa: E402
from scipy.special import gammaln  # noqa: E402

import cpj_kappasize as ks  # noqa: E402
from cpjtest import rows, run_analysis  # noqa: E402

OPTIONS = {"outcome": "2", "props": "0.30", "raters": "2", "kappa0": 0.4, "kappa1": 0.6, "alpha": 0.05,
           "power": 0.8, "simulate": False, "draws": 2000, "seed": 20261018}


def exact_power(raters, props, kappa0, kappa1, alpha, n):
    """Exact P(reject kappa0) when the truth is kappa1 and kappa0, from the analysis' own test."""
    counts, probs1, unanimous = ks.patterns(raters, props, kappa1)
    probs0 = ks.patterns(raters, props, kappa0)[1]
    bars = np.array(list(itertools.combinations(range(n + len(probs1) - 1), len(probs1) - 1)))
    t = np.diff(np.hstack([np.full((len(bars), 1), -1), bars, np.full((len(bars), 1), n + len(probs1) - 1)]),
                axis=1) - 1
    share, una = ks.summarise(t, counts, unanimous, raters)
    rejected = ks.rejects(raters, share, una, n, kappa0, alpha)
    log_coef = gammaln(n + 1) - gammaln(t + 1).sum(axis=1)
    return tuple(np.exp(log_coef + (t * np.log(p)).sum(axis=1))[rejected].sum() for p in (probs1, probs0))


class Engine(unittest.TestCase):
    def assertSizes(self, categories, props, kappa0, kappa1, alpha, power, expected):
        for raters, want in zip(range(2, 7), expected):
            got = ks.power_n(categories, raters, props, kappa0, kappa1, alpha, power)[0]
            self.assertAlmostEqual(got, want, delta=1e-10 * want, msg=f"raters = {raters}")

    def test_noncentrality_is_the_packages_bisection(self):
        # kappaSize:::.powchi(1, 0.05, 0.8)[1], .powchi(1, 0.01, 0.9)[1], .powchi(1, 0.2, 0.5)[1]
        for args, want in [((0.05, 0.8), 7.848918181247349), ((0.01, 0.9), 14.879111994306729),
                           ((0.2, 0.5), 1.6079410892462538)]:
            self.assertAlmostEqual(ks.power_lambda(*args), want, delta=1e-12 * want)

    def test_binary_matches_kappasize_for_every_rater_count(self):
        # kappaSize::PowerBinary(kappa0 = 0.4, kappa1 = 0.6, props = 0.3, raters = r, alpha = 0.05, power = 0.8)$N
        self.assertSizes(2, [0.3, 0.7], 0.4, 0.6, 0.05, 0.8, [190.45640239802236, 105.52166516789086,
                                                               80.611580116054711, 68.741641037771231,
                                                               61.698727249136127])
        # kappaSize::PowerBinary(kappa0 = 0.6, kappa1 = 0.4, props = 0.15, raters = r, alpha = 0.01, power = 0.9)$N
        self.assertSizes(2, [0.15, 0.85], 0.6, 0.4, 0.01, 0.9, [452.50005300332811, 294.00144573690136,
                                                                 233.78037794340861, 197.82628794903184,
                                                                 173.38587737122418])

    def test_three_to_five_categories_match_kappasize(self):
        # kappaSize::Power3Cats(kappa0 = 0.4, kappa1 = 0.6, props = c(0.2, 0.3, 0.5), raters = r, alpha = 0.05,
        #                       power = 0.8)$N
        self.assertSizes(3, [0.2, 0.3, 0.5], 0.4, 0.6, 0.05, 0.8, [114.64923476187315, 62.421574353220755,
                                                                    45.481213917202382, 37.066466960741302,
                                                                    32.000658267243715])
        # kappaSize::Power4Cats(kappa0 = 0.5, kappa1 = 0.7, props = c(0.1, 0.2, 0.3, 0.4), raters = r,
        #                       alpha = 0.05, power = 0.9)$N
        self.assertSizes(4, [0.1, 0.2, 0.3, 0.4], 0.5, 0.7, 0.05, 0.9, [119.81600996186849, 68.793627149813929,
                                                                         51.638171485086126, 42.897057446796175,
                                                                         37.531629651888124])
        # kappaSize::Power5Cats(kappa0 = 0.6, kappa1 = 0.8, props = c(0.1, 0.15, 0.2, 0.25, 0.3), raters = r,
        #                       alpha = 0.1, power = 0.8)$N
        self.assertSizes(5, [0.1, 0.15, 0.2, 0.25, 0.3], 0.6, 0.8, 0.1, 0.8, [54.776924683729909,
                                                                               32.594751965158693,
                                                                               24.930811500869098,
                                                                               20.94775030486058,
                                                                               18.465017731568505])

    def test_a_rare_finding_typed_first_or_second_gives_the_same_n(self):
        # kappaSize::PowerBinary(0.4, 0.6, props = 0.01, raters = 6)$N = 1569.9960955674358; with props = 0.99 the
        # package's expanded polynomials lose digits (1569.996095565423) -- the port is accurate either way.
        for p in (0.01, 0.99):
            got = ks.power_n(2, 6, [p, 1 - p], 0.4, 0.6, 0.05, 0.8)[0]
            self.assertAlmostEqual(got, 1569.9960955674358, delta=1e-12 * got)


class MonteCarlo(unittest.TestCase):
    def test_test_on_every_possible_study_matches_the_r_enumeration(self):
        for design, expected in [  # (raters, props, kappa0, kappa1, alpha, n), pw() in the R script: (power, size)
                ((2, [0.3, 0.7], 0.4, 0.6, 0.05, 191), (0.81782417351593995, 0.051920497191875879)),
                ((3, [0.3, 0.7], 0.3, 0.7, 0.05, 27), (0.79307770064996996, 0.060813413449530632))]:
            for got, want in zip(exact_power(*design), expected):
                self.assertAlmostEqual(got, want, delta=1e-10 * want, msg=str(design))

    def test_seeded_simulation_agrees_with_the_exact_values(self):
        design = (3, [0.3, 0.7], 0.3, 0.7, 0.05, 27)
        got = ks.simulate_power(*design, 20000, 20261018)
        self.assertEqual(got, ks.simulate_power(*design, 20000, 20261018))  # reproducible
        for value, exact in zip(got, (0.79307770064996996, 0.060813413449530632)):
            self.assertLess(abs(value - exact), 4 * ks.mc_se(exact, 20000))


class Analysis(unittest.TestCase):
    def test_default_design(self):
        result = run_analysis("pykappapower", options=OPTIONS)
        self.assertEqual(result["status"], "ok", result["error"])
        # ceiling(kappaSize::PowerBinary(kappa0 = 0.4, kappa1 = 0.6, props = 0.3, raters = 2)$N) = 191
        self.assertEqual(rows(result, "size"), [{"n": 191, "categories": 2, "raters": 2, "props": "0.3, 0.7",
                                                 "kappa0": 0.4, "kappa1": 0.6, "alpha": 0.05, "power": 0.8}])
        notes = result["tables"]["size"]["notes"]
        self.assertTrue(notes[0].startswith("kappaSize power approach: N = lambda / 0.0412111, rounded up to 191,"))
        self.assertIn("lambda = 7.84892 is the noncentrality giving a 1-df chi-square test power 0.8 at two-sided "
                      "alpha = 0.05", notes[0])
        self.assertTrue(notes[0].endswith("The category proportions are treated as known."))
        self.assertTrue(notes[1].startswith("Agreement model: Donner and Eliasziw (1992)."))
        self.assertEqual(len(notes), 2)
        self.assertNotIn("check", result["tables"])
        self.assertEqual(result["texts"]["summary"],
                         "**191 subjects**, each rated by both raters, give a two-sided goodness-of-fit test at "
                         "alpha = 0.05 an approximate power of 0.8 to reject kappa = 0.4 when the true kappa is 0.6 (above the "
                         "null).")

    def test_alternative_below_the_null_and_more_categories(self):
        below = run_analysis("pykappapower", options=dict(OPTIONS, props="0.15", kappa0=0.6, kappa1=0.4,
                                                          alpha=0.01, power=0.9))
        self.assertEqual(rows(below, "size")[0]["n"], 453)  # ceiling(452.50005300332811), see Engine
        self.assertIn("kappa1 is below kappa0: this sizes a study to show that agreement is WORSE than kappa0.",
                      below["tables"]["size"]["notes"])
        self.assertIn("(below the null)", below["texts"]["summary"])
        five = run_analysis("pykappapower", options=dict(OPTIONS, outcome="5", props="0.1 0.15 0.2 0.25 0.3",
                                                         raters="4", kappa0=0.6, kappa1=0.8, alpha=0.1))
        self.assertEqual(rows(five, "size")[0]["n"], 25)  # ceiling(Power5Cats(..., raters = 4)$N = 24.93)

    def test_unusable_input_is_an_input_error(self):
        for options, message in [
                (dict(OPTIONS, kappa1=0.4), "The null kappa (kappa0) and the alternative kappa (kappa1) must differ."),
                (dict(OPTIONS, alpha=0.2, power=0.2), "The power must exceed alpha."),
                (dict(OPTIONS, kappa1=0.4000001), "more than 1,000,000,000 subjects would be needed"),
                (dict(OPTIONS, props="0.3, 0.6"), "they sum to 0.9")]:
            result = run_analysis("pykappapower", options=options)
            self.assertEqual(result["status"], "input_error")
            self.assertIn(message, result["error"]["message"])

    def test_monte_carlo_check_states_seed_and_draws_and_is_reproducible(self):
        options = dict(OPTIONS, simulate=True)
        result = run_analysis("pykappapower", options=options)
        check = rows(result, "check")
        self.assertEqual([(r["statistic"], r["planned"]) for r in check],
                         [("Power (true kappa = 0.6)", 0.8), ("Type I error (true kappa = 0.4)", 0.05)])
        for row, exact in zip(check, (0.81782417351593995, 0.051920497191875879)):  # pw(2, 2, ...) at N = 191
            self.assertLess(abs(row["simulated"] - exact), 4 * ks.mc_se(exact, 2000))
            self.assertAlmostEqual(row["se"], math.sqrt(row["simulated"] * (1 - row["simulated"]) / 2000), places=15)
        # what is shown is what the stated draws and seed give
        self.assertEqual(tuple(r["simulated"] for r in check),
                         ks.simulate_power(2, [0.3, 0.7], 0.4, 0.6, 0.05, 191, 2000, 20261018))
        self.assertEqual(result["tables"]["check"]["notes"],
                         ["2,000 simulated studies of 191 subjects for each row, random seed 20261018; each analysed "
                          "with the published goodness-of-fit test of kappa = 0.4 (Donner and Eliasziw 1992), the "
                          "prevalence estimated by the study's overall share of ratings."])
        self.assertIn("In 2,000 simulated studies (seed 20261018) the test rejected kappa = 0.4 in",
                      result["texts"]["summary"])
        self.assertEqual(rows(run_analysis("pykappapower", options=options), "check"), check)
        self.assertNotEqual(rows(run_analysis("pykappapower", options=dict(options, seed=7)), "check"), check)

    def test_no_monte_carlo_check_for_three_to_five_categories(self):
        result = run_analysis("pykappapower", options=dict(OPTIONS, outcome="3", props="0.2, 0.3, 0.5",
                                                           simulate=True))
        self.assertEqual(rows(result, "size")[0]["n"], 115)  # ceiling(Power3Cats(..., raters = 2)$N = 114.65)
        self.assertEqual(result["tables"]["check"], {"rows": [], "notes": [ks.MC_UNAVAILABLE]})

    def test_no_monte_carlo_check_for_more_than_two_raters(self):
        # The plug-in test is liberal there even in large studies (cpj_kappasize docstring), so no check is shown.
        result = run_analysis("pykappapower", options=dict(OPTIONS, raters="3", simulate=True))
        self.assertEqual(rows(result, "size")[0]["n"], 106)  # ceiling(PowerBinary(..., raters = 3)$N = 105.52)
        self.assertEqual(result["tables"]["check"], {"rows": [], "notes": [ks.MC_UNAVAILABLE]})
        self.assertNotIn("simulated", result["texts"]["summary"])


if __name__ == "__main__":
    unittest.main()
