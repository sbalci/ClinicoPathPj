"""pykappafixedn: kappaSize's lowest expected kappa for a fixed N (FixedNBinary, FixedN3Cats, FixedN4Cats,
FixedN5Cats). Oracles: kappaSize 1.2 in R 4.6.0, each call quoted at its value."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "inst" / "python"))

import cpj_kappasize as ks  # noqa: E402
from cpjtest import rows, run_analysis  # noqa: E402

OPTIONS = {"outcome": "2", "props": "0.20, 0.80", "raters": "2", "kappa0": 0.6, "n": 100, "alpha": 0.05}


class Engine(unittest.TestCase):
    def assertBounds(self, categories, props, kappa0, n, alpha, expected):
        for raters, want in zip(range(2, 7), expected):
            got, floor = ks.fixed_n_bound(categories, raters, props, kappa0, n, alpha)
            self.assertIsNone(floor)
            self.assertAlmostEqual(got, want, delta=1e-10 * abs(want), msg=f"raters = {raters}")

    def test_binary_matches_kappasize_for_every_rater_count(self):
        # kappaSize::FixedNBinary(kappa0 = 0.6, n = 100, props = 0.2, raters = r, alpha = 0.05)$kappaL, r = 2..6
        self.assertBounds(2, [0.2, 0.8], 0.6, 100, 0.05, [0.41799999999999982, 0.46099999999999985,
                                                           0.47699999999999987, 0.48599999999999988,
                                                           0.49399999999999988])
        # kappaSize::FixedNBinary(kappa0 = 0.8, n = 50, props = 0.45, raters = r, alpha = 0.1)$kappaL
        self.assertBounds(2, [0.45, 0.55], 0.8, 50, 0.1, [0.66299999999999992, 0.69799999999999995,
                                                           0.70899999999999996, 0.71299999999999997,
                                                           0.71599999999999997])

    def test_three_to_five_categories_match_kappasize(self):
        # kappaSize::FixedN3Cats(kappa0 = 0.6, n = 80, props = c(0.2, 0.3, 0.5), raters = r, alpha = 0.05)$kappaL
        self.assertBounds(3, [0.2, 0.3, 0.5], 0.6, 80, 0.05, [0.46199999999999986, 0.49599999999999989,
                                                               0.5089999999999999, 0.5159999999999999,
                                                               0.52099999999999991])
        # kappaSize::FixedN4Cats(kappa0 = 0.7, n = 150, props = c(0.1, 0.2, 0.3, 0.4), raters = r,
        #                        alpha = 0.025)$kappaL
        self.assertBounds(4, [0.1, 0.2, 0.3, 0.4], 0.7, 150, 0.025, [0.59699999999999986, 0.62099999999999989,
                                                                      0.62999999999999989, 0.6349999999999999,
                                                                      0.6379999999999999])
        # kappaSize::FixedN5Cats(kappa0 = 0.5, n = 60, props = c(0.1, 0.15, 0.2, 0.25, 0.3), raters = r,
        #                        alpha = 0.1)$kappaL
        self.assertBounds(5, [0.1, 0.15, 0.2, 0.25, 0.3], 0.5, 60, 0.1, [0.39399999999999991, 0.41799999999999993,
                                                                          0.42599999999999993, 0.43099999999999994,
                                                                          0.43399999999999994])

    def test_a_negative_limit_inside_the_model(self):
        # kappaSize::FixedNBinary(kappa0 = 0.1, n = 11, props = 0.5, raters = 2, alpha = 0.05)$kappaL
        self.assertAlmostEqual(ks.fixed_n_bound(2, 2, [0.5, 0.5], 0.1, 11, 0.05)[0], -0.36300000000000038,
                               delta=1e-12)

    def test_a_walk_that_leaves_the_model_gives_no_value(self):
        # kappaSize::FixedNBinary(kappa0 = 0.01, n = 100, props = 0.02, raters = 3, alpha = 0.2)$kappaL is -0.841,
        # far below -0.02^2 / (1 - 0.02^2) = -0.0004, the lowest kappa at which every cell is a probability.
        bound, floor = ks.fixed_n_bound(2, 3, [0.02, 0.98], 0.01, 100, 0.2)
        self.assertIsNone(bound)
        self.assertAlmostEqual(floor, -0.02 ** 2 / (1 - 0.02 ** 2), places=15)


class Analysis(unittest.TestCase):
    def test_default_design(self):
        result = run_analysis("pykappafixedn", options=OPTIONS)
        self.assertEqual(result["status"], "ok", result["error"])
        row = rows(result, "bound")[0]
        self.assertAlmostEqual(row.pop("kappaL"), 0.41799999999999982, delta=1e-12)  # FixedNBinary, see Engine
        self.assertEqual(row, {"n": 100, "categories": 2, "raters": 2, "props": "0.2, 0.8", "kappa0": 0.6,
                               "interval": "95% one-sided"})
        notes = result["tables"]["bound"]["notes"]
        self.assertTrue(notes[0].startswith("kappaSize fixed-sample approach: kappa is stepped down from 0.6 by "
                                            "0.001 until the expected goodness-of-fit chi-square exceeds the "
                                            "one-sided critical value."))
        self.assertIn("lies up to about 0.001 below the exact limit", notes[0])
        self.assertTrue(notes[1].startswith("Agreement model: Donner and Eliasziw (1992)."))
        self.assertEqual(len(notes), 2)
        self.assertEqual(result["texts"]["summary"],
                         "With 100 subjects, each rated by both raters, the expected lower limit of the one-sided "
                         "95% confidence interval for kappa is **0.418** if the study observes the anticipated kappa "
                         "of 0.6: such a study would rule out kappa values below 0.418.")

    def test_four_categories(self):
        options = dict(OPTIONS, outcome="4", props="0.1, 0.2, 0.3, 0.4", raters="3", kappa0=0.7, n=150, alpha=0.025)
        row = rows(run_analysis("pykappafixedn", options=options), "bound")[0]
        self.assertAlmostEqual(row["kappaL"], 0.62099999999999989, delta=1e-12)  # FixedN4Cats, see Engine
        self.assertEqual(row["interval"], "97.5% one-sided")

    def test_limit_at_or_below_zero_is_explained(self):
        result = run_analysis("pykappafixedn", options=dict(OPTIONS, props="0.5", kappa0=0.1, n=11))
        self.assertAlmostEqual(rows(result, "bound")[0]["kappaL"], -0.36300000000000038, delta=1e-12)
        notes = result["tables"]["bound"]["notes"]
        self.assertIn("The expected lower limit is not above 0: even if the study observes kappa0, it could not rule "
                      "out agreement no better than chance.", notes)
        self.assertTrue(any(n.startswith("The smallest expected count among the goodness-of-fit cells") and
                            "is 1.75, below 5" in n for n in notes))
        self.assertTrue(result["texts"]["summary"].endswith("It could not rule out agreement no better than chance."))

    def test_limit_outside_the_model_is_not_shown(self):
        result = run_analysis("pykappafixedn", options=dict(OPTIONS, props="0.02", raters="3", kappa0=0.01,
                                                            alpha=0.2))
        self.assertEqual(result["status"], "ok", result["error"])
        self.assertIsNone(rows(result, "bound")[0]["kappaL"])
        self.assertIn("Not available: the limit lies within about 0.001 of -0.0004002, the lowest kappa this model "
                      "allows for these proportions and raters", result["tables"]["bound"]["notes"][-1])
        self.assertIn("could rule out practically no value of kappa that the model allows", result["texts"]["summary"])

    def test_unusable_proportions_are_an_input_error(self):
        result = run_analysis("pykappafixedn", options=dict(OPTIONS, outcome="3"))
        self.assertEqual(result["status"], "input_error")
        self.assertEqual(result["error"]["message"], "Enter 3 proportions, one per outcome category; got 2.")
        # a prevalence whose complement rounds to 1 used to raise ZeroDivisionError in model_floor
        tiny = run_analysis("pykappafixedn", options=dict(OPTIONS, props="1e-60"))
        self.assertEqual(tiny["status"], "input_error", tiny["error"])
        self.assertIn("a proportion is too close to 0", tiny["error"]["message"])


if __name__ == "__main__":
    unittest.main()
