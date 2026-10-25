"""Tests for inst/python/analyses/pycotest.py, run through the runtime exactly as the R bridge runs it.

Deterministic oracle: an independent R implementation of the textbook formulas, not of the analysis
code. Gardner et al.'s conditional covariances (Prev Vet Med 2000;45:107-122), truncated to their
Frechet bounds, and Bayes' theorem on the joint 2x2 tables. Run with
/Library/Frameworks/R.framework/Versions/4.6/Resources/bin/Rscript --vanilla (R 4.6, base stats only):

    gardner <- function(se1, sp1, se2, sp2, prev, phiD = 0, phiN = 0) {
        vD <- sqrt(se1 * (1 - se1) * se2 * (1 - se2))
        vN <- sqrt(sp1 * (1 - sp1) * sp2 * (1 - sp2))
        bD <- c(max(-se1 * se2, -(1 - se1) * (1 - se2)), min(se1 * (1 - se2), se2 * (1 - se1)))
        bN <- c(max(-(1 - sp1) * (1 - sp2), -sp1 * sp2), min((1 - sp1) * sp2, sp1 * (1 - sp2)))
        covD <- min(max(phiD * vD, bD[1]), bD[2])
        covN <- min(max(phiN * vN, bN[1]), bN[2])
        D <- c(se1 * se2 + covD, se1 * (1 - se2) - covD, (1 - se1) * se2 - covD, (1 - se1) * (1 - se2) + covD)
        N <- c((1 - sp1) * (1 - sp2) + covN, (1 - sp1) * sp2 - covN, sp1 * (1 - sp2) - covN, sp1 * sp2 + covN)
        pD <- c(1 - D[4], D[2], D[3], D[1], D[4]); pN <- c(1 - N[4], N[2], N[3], N[1], N[4])
        post <- prev * pD / (prev * pD + (1 - prev) * pN)
        list(D = D, N = N, lr = pD / pN, odds = prev / (1 - prev) * pD / pN, post = post,
             relative = post / prev, phi = c(covD / vD, covN / vN), cov = c(covD, covN),
             rangeD = bD / vD, rangeN = bN / vN)
    }

Values were printed with sprintf("%.17g"). Rows are in table order: either positive, test 1 only,
test 2 only, both positive, both negative; joint cells in the order ++, +-, -+, --.

Monte Carlo oracle (same R session, the Jeffreys posterior Beta(x + 0.5, n - x + 0.5), x = value * n):
- One uncertain input with a monotone effect has a closed form: the limits are the transformed Beta
  quantiles, f(qbeta(0.025, a, b)) and f(qbeta(0.975, a, b)). Their Monte Carlo standard error for N
  draws is sqrt(t (1 - t) / N) |f'(x_t)| / dbeta(x_t, a, b), t = 0.025, with f' by central differences.
- Every input uncertain under dependence has no closed form: R drew 4e6 draws (set.seed(20261018),
  rbeta, four chunks of 1e6), discarded those at which the fixed phi is outside the covariance bounds,
  and took quantile(type = 7). Standard errors: sqrt(t (1 - t) / N_accepted) / density(post)(q),
  inflated by sqrt(1 + N_accepted / 4e6) for the oracle's own error.
Agreement is required within 4 standard errors. The standard errors were checked against the spread
of 300 seeds of this analysis at 20000 draws (agreement within a few percent).
"""
import ast
import math
import re
import unittest
from pathlib import Path

from cpjtest import rows, run_analysis

ROOT = Path(__file__).resolve().parents[2]
_tree = ast.parse((ROOT / "inst" / "python" / "analyses" / "pycotest.py").read_text(encoding="utf-8"))
SPEC = next(ast.literal_eval(node.value) for node in _tree.body
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "SPEC")
DEFAULTS = {option["name"]: option["default"] for option in SPEC["options"]}


def cotest(**options):
    return run_analysis("pycotest", options=dict(DEFAULTS, **options))


def column(result, table, name):
    return [row[name] for row in rows(result, table)]


def notes(result, table):
    return result["tables"][table]["notes"]


def notices(result):
    return [notice["text"] for notice in result["notices"]]


# gardner(.80, .90, .75, .95, .10)  -- also the umbrella's exact fractions 190/451, 40/211, 10/37, 120/129, 10/1549
C1 = {"post": [0.42128603104212853, 0.18957345971563988, 0.27027027027027006, 0.93023255813953487, 0.0064557779212395085],
      "lr": [6.5517241379310338, 2.1052631578947376, 3.3333333333333295, 119.99999999999993, 0.05847953216374268],
      "odds": [0.72796934865900376, 0.23391812865497086, 0.37037037037036996, 13.333333333333327, 0.0064977257959714096],
      "relative": [4.2128603104212852, 1.8957345971563988, 2.7027027027027004, 9.3023255813953476, 0.064557779212395083],
      "D": [0.60000000000000009, 0.20000000000000001, 0.14999999999999997, 0.049999999999999989],
      "N": [0.0050000000000000036, 0.094999999999999973, 0.04500000000000004, 0.85499999999999998],
      "rangeD": [-0.28867513459481287, 0.8660254037844386], "rangeN": [-0.076471911290187281, 0.68824720161168562]}
CASES = {  # options -> gardner(...) for the dependent model
    # gardner(.80, .90, .75, .95, .10, phiD = .05, phiN = .05)  (the analysis defaults)
    "default": ({}, {
        "post": [0.42461655999787529, 0.18815666613177121, 0.27342822400198247, 0.89104898339976124, 0.0075368919206070398],
        "lr": [6.6417431825406137, 2.0858827369035216, 3.3869386305814295, 73.605929534578394, 0.068347152386078497],
        "odds": [0.73797146472673492, 0.23176474854483575, 0.37632651450904775, 8.1784366149531547, 0.0075941280428976103],
        "relative": [4.2461655999787524, 1.881566661317712, 2.7342822400198243, 8.9104898339976124, 0.075368919206070389],
        "D": [0.60866025403784452, 0.19133974596215564, 0.14133974596215559, 0.058660254037844375],
        "N": [0.0082691742076555098, 0.09173082579234447, 0.041730825792344536, 0.85826917420765547],
        "phi": [0.049999999999999996, 0.050000000000000003], "cov": [0.0086602540378443848, 0.0032691742076555066]}),
    # gardner(.80, .90, .75, .95, .10, phiD = .30, phiN = .005)
    "strong with disease": ({"depPos": 0.30, "depNeg": 0.005}, {
        "post": [0.40818145498509678, 0.14802423303132156, 0.19603922615473637, 0.93150164624423715, 0.013072151540542688],
        "lr": [6.207363939184031, 1.5636807394439318, 2.194576020113399, 122.39001897900086, 0.11920766452028755],
        "odds": [0.68970710435378124, 0.17374230438265911, 0.2438417800125999, 13.598890997666762, 0.013245296057809728],
        "relative": [4.0818145498509679, 1.4802423303132155, 1.9603922615473637, 9.3150164624423706, 0.13072151540542687],
        "D": [0.65196152422706644, 0.14803847577293369, 0.098038475772933648, 0.10196152422706631],
        "N": [0.0053269174207655539, 0.094673082579234416, 0.04467308257923449, 0.8553269174207655],
        "phi": [0.29999999999999999, 0.0050000000000000001], "cov": [0.051961524227066312, 0.00032691742076555063]}),
    # gardner(.95, .85, .70, .95, .05, phiD = .15, phiN = .10)  (the umbrella's hpv_pap worked example)
    "hpv_pap": ({"sens1": 0.95, "spec1": 0.85, "sens2": 0.70, "spec2": 0.95, "prevalence": 0.05,
                 "depPos": 0.15, "depNeg": 0.10}, {
        "post": [0.21653861754322551, 0.095424551260014853, 0.029454206960780559, 0.7007638829878996, 0.0019317381397657013],
        "lr": [5.2513548535345675, 2.0043286344613551, 0.57661362943254346, 44.495009191125412, 0.036774062514662025],
        "odds": [0.27638709755445096, 0.10549098076112397, 0.030348085759607554, 2.341842589006601, 0.0019354769744558962],
        "relative": [4.3307723508645095, 1.9084910252002969, 0.5890841392156112, 14.015277659757992, 0.038634762795314026],
        "D": [0.67998123826657852, 0.27001876173342138, 0.020018761733421389, 0.029981238266578655],
        "N": [0.015282191208136701, 0.13471780879186332, 0.034717808791863342, 0.81528219120813672],
        "phi": [0.14999999999999999, 0.10000000000000001], "cov": [0.01498123826657864, 0.0077821912081366936],
        "rangeD": [-0.15018785229652773, 0.35043832202523134], "rangeN": [-0.09637388493048539, 0.54611868127275043]}),
}
MG = {"nSens1": 40, "nSpec1": 60, "nSens2": 40, "nSpec2": 80, "nPrev": 200, "depPos": 0.60, "depNeg": 0.50}


class Close:
    def assertClose(self, got, expected, rel=1e-10):
        self.assertEqual(len(got), len(expected))
        for g, e in zip(got, expected):
            if e is None:
                self.assertIsNone(g)
            else:
                self.assertTrue(math.isclose(g, e, rel_tol=rel, abs_tol=1e-15), f"{got} != {expected}")

    def assertWithin(self, got, expected, se, k=4):
        for g, e, s in zip(got, expected, se):
            self.assertLessEqual(abs(g - e), k * s, f"{g} vs {e}: {abs(g - e) / s:.2f} standard errors")


class PointEstimates(unittest.TestCase, Close):
    def test_independence_matches_the_oracle_and_the_exact_fractions(self):
        result = cotest(indep=True)
        self.assertEqual(result["status"], "ok", result["error"])
        for name in ("post", "lr", "odds", "relative"):
            self.assertClose(column(result, "posttest", {"post": "prob"}.get(name, name)), C1[name])
        self.assertClose(column(result, "posttest", "prob"), [190 / 451, 40 / 211, 10 / 37, 120 / 129, 10 / 1549])
        # sens / (1 - spec) and (1 - sens) / spec: 8, 2/9, 15, 5/19
        self.assertClose(column(result, "params", "plr"), [8, 15])
        self.assertClose(column(result, "params", "nlr"), [2 / 9, 5 / 19])
        self.assertClose(column(result, "joint", "pD"), C1["D"][1:3] + [C1["D"][0], C1["D"][3]])
        self.assertClose(column(result, "joint", "pN"), C1["N"][1:3] + [C1["N"][0], C1["N"][3]])
        self.assertClose(column(result, "dependence", "low"), [C1["rangeD"][0], C1["rangeN"][0]])
        self.assertClose(column(result, "dependence", "high"), [C1["rangeD"][1], C1["rangeN"][1]])
        self.assertEqual(column(result, "dependence", "entered"), [None, None])
        self.assertEqual(column(result, "dependence", "fitted"), [0, 0])
        self.assertIn("Model: the two tests are conditionally independent.", notes(result, "posttest"))

    def test_dependence_matches_the_gardner_covariance_oracle(self):
        for case, (options, oracle) in CASES.items():
            with self.subTest(case=case):
                result = cotest(**options)
                for name in ("post", "lr", "odds", "relative"):
                    self.assertClose(column(result, "posttest", {"post": "prob"}.get(name, name)), oracle[name])
                d, n = oracle["D"], oracle["N"]
                self.assertClose(column(result, "joint", "pD"), [d[1], d[2], d[0], d[3]])
                self.assertClose(column(result, "joint", "pN"), [n[1], n[2], n[0], n[3]])
                self.assertClose(column(result, "dependence", "fitted"), oracle["phi"])
                self.assertClose(column(result, "dependence", "cov"), oracle["cov"])
                if "rangeD" in oracle:
                    self.assertClose(column(result, "dependence", "low"), [oracle["rangeD"][0], oracle["rangeN"][0]])
                    self.assertClose(column(result, "dependence", "high"), [oracle["rangeD"][1], oracle["rangeN"][1]])
                self.assertEqual(notices(result), [])
                self.assertTrue(any("the combined likelihood ratio is not their product" in note
                                    for note in notes(result, "params")))
                # the umbrella's prevalence-source caveat (cotest.b.R, typical_ranges)
                self.assertTrue(any("Prevalence should be the pre-test probability in the population you are testing, "
                                    "not the figure from the study that validated the test." in note
                                    for note in notes(result, "params")))

    def test_port_matches_the_umbrella_cotest(self):
        # ClinicoPathJamoviModule tests/testthat/test-cotest-validation.R (blinded decimal oracle O3, O4, O5,
        # O7, O8 and SET D), cotest(test1_sens = ..., cond_dep_pos = ..., cond_dep_neg = ...). SET D's last
        # value is not asserted there; it is gardner(.80, .90, .75, .95, .10, phiD = .90, phiN = .90)$post[5].
        cases = [
            ({"depPos": 0.30, "depNeg": 0.005}, [0.40818145498509689, 0.14802423303132151, 0.19603922615473655,
                                                 0.93150164624423714, 0.013072151540542687]),
            ({"depPos": 0.005, "depNeg": 0.30}, [0.45684185072954382, 0.22690781639499999, 0.39495376168898448,
                                                 0.73062375814644352, 0.0064205311781305106]),
            ({"sens2": 0.70, "prevalence": 0.20, "depPos": -0.50, "depNeg": 0.10},
             [0.64356416902453806, 0.45882321188430380, 0.56521666851463169, 0.91549371623996344, 0]),
            ({"spec1": 0.99, "spec2": 0.90, "depNeg": 0.40},
             [0.51122545311173804, 1, 0.14856915898032723, 0.87118202376641142, 0.0071899370989020580]),
            (CASES["hpv_pap"][0], [0.21653861754322547, 0.095424551260014853, 0.029454206960780547,
                                   0.70076388298789970, 0.0019317381397656998]),
            ({"depPos": 0.90, "depNeg": 0.90}, [8 / 17, 0.10, None, 0.625, 0.024096385542168669]),
        ]
        for options, expected in cases:
            with self.subTest(options=options):
                self.assertClose(column(cotest(**options), "posttest", "prob"), expected)

    def test_negative_correlation_truncated_at_its_floor(self):
        # gardner(.80, .90, .70, .95, .20, phiD = -.50, phiN = .10)
        result = cotest(sens2=0.70, prevalence=0.20, depPos=-0.50, depNeg=0.10)
        self.assertClose(column(result, "posttest", "prob"),
                         [0.64356416902453795, 0.45882321188430386, 0.56521666851463137, 0.91549371623996345, 0])
        self.assertClose(column(result, "posttest", "lr"),
                         [7.2222163216676458, 3.3913000110877918, 5.1999847057950257, 43.333758177774911, 0])
        self.assertClose(column(result, "dependence", "fitted"), [-0.32732683535398854, 0.10000000000000001])
        self.assertClose(column(result, "dependence", "low"), [-0.32732683535398854, -0.076471911290187281])
        self.assertClose(column(result, "joint", "pD")[3:], [0])  # two negatives cannot occur with disease
        self.assertTrue(any(text.startswith("The correlation (phi) entered for subjects with disease, -0.5, is not "
                                            "attainable with these sensitivities (attainable range -0.327 to 0.764)")
                            for text in notices(result)))
        self.assertTrue(any(note.startswith("Both Tests Negative: under the dependence entered this combination of "
                                            "results cannot occur in subjects with disease, so its probability is 0 "
                                            "by construction") for note in notes(result, "posttest")))
        self.assertIn("(requested -0.5 among diseased, truncated to the nearest value the entered sensitivities allow)",
                      result["texts"]["summary"].replace("\\", ""))

    def test_a_correlation_just_beyond_its_limit_is_still_truncated(self):
        # gardner(.80, .90, .75, .95, .10, phiD = .87, phiN = .05): raw ++ 0.750688 against its limit 0.75
        result = cotest(depPos=0.87, ci=True, nPrev=200)
        self.assertClose(column(result, "posttest", "prob"),
                         [0.3854349096379408, 0.057105172158564206, 0, 0.90972764360238334, 0.025238431985055741])
        self.assertClose(column(result, "dependence", "fitted"), [0.8660254037844386, 0.050000000000000003])
        self.assertTrue(any(text.startswith("The correlation (phi) entered for subjects with disease, 0.87, is not "
                                            "attainable with these sensitivities (attainable range -0.289 to 0.866), so "
                                            "the probability that both tests are positive in that group was truncated "
                                            "from 0.7507 to its limit 0.7500.") for text in notices(result)))
        self.assertTrue(notes(result, "intervals")[0].startswith("No interval was computed: a correlation is at, or was "
                                                                 "truncated to, the limit"))

    def test_a_combination_impossible_without_disease_is_certain_by_construction(self):
        # gardner(.80, .99, .75, .90, .10, phiD = .05, phiN = .40): lr[2] = Inf, post[2] = 1
        result = cotest(spec1=0.99, spec2=0.90, depNeg=0.40)
        self.assertClose(column(result, "posttest", "prob"),
                         [0.51122545311173806, 1, 0.14856915898032727, 0.8711820237664113, 0.0071899370989020562])
        self.assertEqual(rows(result, "posttest")[1]["lr"], None)  # infinite, so not displayed as a number
        self.assertEqual(rows(result, "posttest")[1]["odds"], None)
        self.assertClose(column(result, "dependence", "fitted"), [0.049999999999999996, 0.3015113445777638])
        self.assertClose(column(result, "dependence", "high"), [0.8660254037844386, 0.3015113445777638])
        self.assertTrue(any(text.startswith("The correlation (phi) entered for subjects without disease, 0.4, is not "
                                            "attainable") for text in notices(result)))
        self.assertIn("Test 1 Positive Only: under the dependence entered this combination of results cannot occur in "
                      "subjects without disease, so its probability is 1 by construction, not an estimate (its LR and "
                      "odds are infinite). Move the correlation toward 0.", notes(result, "posttest"))

    def test_a_combination_impossible_in_both_groups_has_no_probability(self):
        # gardner(.80, .90, .75, .95, .10, phiD = .90, phiN = .90): post[3] is NaN (0/0)
        result = cotest(depPos=0.90, depNeg=0.90)
        third = rows(result, "posttest")[2]
        self.assertEqual([third[k] for k in ("prob", "relative", "odds", "lr")], [None] * 4)
        self.assertClose(column(result, "dependence", "fitted"), [0.8660254037844386, 0.68824720161168562])
        self.assertIn("Test 2 Positive Only: under the dependence entered this combination of results cannot occur "
                      "in either group, so no post-test probability exists. Move the correlation toward 0.",
                      notes(result, "posttest"))
        self.assertEqual(len(notices(result)), 2)  # both groups truncated

    def test_zero_correlation_reproduces_independence(self):
        dependent = cotest(depPos=0, depNeg=0)
        self.assertClose(column(dependent, "posttest", "prob"), C1["post"])
        # under independence the correlation boxes are ignored
        self.assertClose(column(cotest(indep=True, depPos=0.9, depNeg=-0.9), "posttest", "prob"), C1["post"])

    def test_checks_on_the_entered_values(self):
        weak = notices(cotest(sens1=0.50, spec1=0.55, name2="Ki67", sens2=0.20, spec2=0.30, indep=True))
        self.assertTrue(any(t.startswith("Test 1 has low discriminatory power") for t in weak))
        self.assertTrue(any(t.startswith("Ki67 is below the chance diagonal") for t in weak))
        self.assertTrue(any(t.startswith("Low prevalence (below 5%)") for t in notices(cotest(prevalence=0.049))))
        self.assertEqual(notices(cotest(prevalence=0.051)), [])
        self.assertTrue(any(t.startswith("Very high prevalence (above 95%)") for t in notices(cotest(prevalence=0.951))))
        high = cotest(prevalence=0.501)["notices"]
        self.assertEqual(high, [{"type": "INFO", "text": "High prevalence (above 50%) detected. Ensure this reflects "
                                                        "your actual clinical population."}])

    def test_unusable_values_are_input_errors(self):
        for options in ({"sens1": 0}, {"prevalence": 1}, {"depPos": 1.5}, {"nPrev": -1}):
            with self.subTest(options=options):
                result = cotest(**options)
                self.assertEqual(result["status"], "input_error")
        self.assertIn("Test 1 sensitivity (0-1) must lie strictly between 0 and 1", cotest(sens1=0)["error"]["message"])

    def test_names_label_every_table_and_are_escaped_in_the_summary(self):
        result = cotest(name1=" HPV ", name2="Pap *cytology*")
        self.assertEqual(column(result, "params", "test"), ["HPV", "Pap *cytology*"])
        self.assertEqual(column(result, "posttest", "scenario")[1:3], ["HPV Positive Only", "Pap *cytology* Positive Only"])
        self.assertEqual(column(result, "joint", "pattern")[:2], ["HPV Positive Only", "Pap *cytology* Positive Only"])
        summary = result["texts"]["summary"]
        self.assertIn("Pap \\*cytology\\*", summary)
        self.assertNotIn("Pap *cytology*", summary)

    def test_the_summary_states_the_numbers_the_model_and_their_limits(self):
        text = cotest()["texts"]["summary"].replace("\\", "")
        self.assertIn("- **Either Test Positive (Parallel Rule):** 42.5% (4.25x increase); combined likelihood ratio "
                      "6.64; by the usual rule of thumb, a moderate shift towards disease.", text)
        self.assertIn("Co-testing with Test 1 (sensitivity 80%, specificity 90%) and Test 2 (sensitivity 75%, "
                      "specificity 95%) at a pre-test probability of 10.0% gave calculated post-test probabilities of "
                      "disease of 42.5% after a positive result on either test (the parallel rule; 4.25x increase), "
                      "89.1% when both tests were positive (8.91x increase) and 0.75% when both were negative "
                      "(reduced to 0.0754x of prevalence).", text)
        self.assertIn("These dependence values are the analysis defaults, not estimates from data.", text)
        self.assertIn("were treated as exact, so these probabilities carry no uncertainty interval.", text)
        self.assertNotIn("analysis defaults", cotest(depPos=0.2)["texts"]["summary"])
        # a tiny probability keeps its significant digits instead of reading 0.0% (umbrella VAL-cotest-09)
        tiny = cotest(prevalence=0.001, indep=True)["texts"]["summary"].replace("\\", "")
        self.assertIn("0.0059% when both were negative", tiny)
        self.assertIn("Sensitivity, specificity and prevalence are treated as exact, so these post-test probabilities "
                      "carry no uncertainty interval. Tick Uncertainty intervals", notes(cotest(), "posttest")[-1])


class Display(unittest.TestCase, Close):
    """Probabilities are shown with the interpretation's formatter, never as jamovi's one-decimal '0.0 %'."""

    def test_a_tiny_residual_risk_is_shown_as_in_the_interpretation(self):
        # screening setting: both tests negative leaves a small but real risk
        result = cotest(prevalence=0.01, sens1=0.95, spec1=0.90, sens2=0.95, spec2=0.90, indep=True)
        exact, text = column(result, "posttest", "prob"), column(result, "posttest", "probText")
        self.assertGreater(exact[-1], 0)
        self.assertLess(100 * exact[-1], 0.05)              # jamovi's pc format would print '0.0 %'
        self.assertGreater(float(text[-1].rstrip("%")), 0)  # the table shows the real, small risk
        unescaped = re.sub(r"\\(.)", r"\1", result["texts"]["summary"])  # the summary is Markdown-escaped
        self.assertIn(text[-1], unescaped)  # ... exactly as the interpretation does
        self.assertTrue(all(cell.endswith("%") for cell in column(result, "joint", "pDText")))

    def test_confirmatory_specificity_up_to_0_999_is_accepted(self):
        result = cotest(spec1=0.999, spec2=0.995, indep=True)
        self.assertEqual(result["status"], "ok", result["console"])
        self.assertNotEqual(column(result, "posttest", "probText")[3], "100%")  # both positive: high, not certain


class Intervals(unittest.TestCase, Close):
    def test_prevalence_alone_gives_its_transformed_jeffreys_quantiles(self):
        # f(qbeta(c(.025, .975), .10 * 200 + .5, .90 * 200 + .5), LR) with the C1 likelihood ratios
        result = cotest(indep=True, ci=True, nPrev=200)
        self.assertWithin(column(result, "intervals", "lower"),
                          [0.30997643673832354, 0.12614116277433793, 0.18603464248941312, 0.89163329370520084,
                           0.0039936971960272188],
                          [0.0010790182160611646, 0.00055607617218335792, 0.00076389896053288473,
                           0.00048743681091839618, 2.0066581507482521e-05])
        self.assertWithin(column(result, "intervals", "upper"),
                          [0.53090573801717955, 0.26668502949859862, 0.36540638878850773, 0.95397901801651575,
                           0.010000929640772024],
                          [0.00098480437102773321, 0.0007733242264855001, 0.00091694705396198623,
                           0.00017360695981459982, 3.9151426137113991e-05])
        self.assertClose(column(result, "intervals", "prob"), C1["post"])
        method = notes(result, "intervals")
        self.assertTrue(method[0].startswith("95% percentile intervals over 20000 Monte Carlo draws (seed 1; numpy "))
        self.assertIn("Jeffreys posterior Beta(x + 0.5, n - x + 0.5), with x = value times n (not rounded)", method[1])
        self.assertIn("the prevalence (n = 200). Held at the entered value (n = 0): Test 1 sensitivity, Test 1 "
                      "specificity, Test 2 sensitivity and Test 2 specificity.", method[1])
        self.assertTrue(method[1].endswith("The tests were assumed conditionally independent in every draw."))
        self.assertFalse(any("discarded" in note for note in method))
        self.assertTrue(method[-1].startswith("The intervals reflect only the sampling uncertainty of the values with "
                                              "a sample size. They do not cover bias"))
        self.assertIn("Point estimates from the values entered; their uncertainty intervals are in the Uncertainty "
                      "Intervals table.", notes(result, "posttest"))

    def test_one_sensitivity_alone_gives_its_transformed_jeffreys_quantiles(self):
        # gardner(qbeta(c(.025, .975), .80 * 50 + .5, .20 * 50 + .5), .90, .75, .95, .10)$post, sorted per row
        result = cotest(indep=True, ci=True, nSens1=50)
        self.assertWithin(column(result, "intervals", "lower"),
                          [0.41309889755581231, 0.16466648741498319, 0.16632448759637045, 0.91827540442105926,
                           0.0034879227676123839],
                          [8.5721409482098106e-05, 0.00026504746829121258, 0.00095763204438427472,
                           0.00014460531832755075, 2.4004621203365612e-05])
        self.assertWithin(column(result, "intervals", "upper"),
                          [0.42714578156252736, 0.20691348251708225, 0.37631875098419665, 0.93699239294642089,
                           0.010474786515157201],
                          [4.6775244652143161e-05, 0.00013684009511629098, 0.00093575373785696053,
                           4.9230365606990044e-05, 4.1325210067618772e-05])

    def test_dependent_draws_agree_with_an_r_monte_carlo_and_report_the_discards(self):
        # R: 4e6 draws (set.seed(20261018)); 24.40455% discarded; quantile(type = 7) of the rest
        result = cotest(ci=True, **MG)
        self.assertWithin(column(result, "intervals", "lower"),
                          [0.28421882380409258, 0.026101722795019908, 0.018140709150625565, 0.47680451674556756,
                           0.0097483212388770994],
                          [0.00157567715081353, 0.0008117700567411753, 0.00086479605915499918, 0.0020878253430991912,
                           7.6738161073040657e-05])
        self.assertWithin(column(result, "intervals", "upper"),
                          [0.63586474532851134, 0.4620305509397904, 0.88552995594661776, 0.81696478217000323,
                           0.035092564962818679],
                          [0.0021018979919847458, 0.005705165322894867, 0.0050076387123389873, 0.0014291884188900774,
                           0.00022349353630428628])
        discard = next(note for note in notes(result, "intervals") if "were discarded" in note)
        count = int(discard.split(" of ")[0])
        self.assertWithin([count / 20000], [0.2440455], [0.0030371639232164437])
        self.assertTrue(discard.endswith(f"the intervals use the remaining {20000 - count}, so they are conditional on "
                                         f"values at which those correlations can occur."))
        self.assertTrue(any(note.endswith("The correlations (phi) were held fixed at the entered values.")
                            for note in notes(result, "intervals")))
        # accepted AND requested draws: the draws option and the seed are what reproduce the result
        self.assertTrue(notes(result, "intervals")[0].startswith(
            f"95% percentile intervals over {20000 - count} of 20000 Monte Carlo draws (seed 1; numpy "))
        summary = result["texts"]["summary"].replace("\\", "")
        self.assertIn(f"over {20000 - count} of 20000 Monte Carlo draws (seed 1)", summary)
        self.assertIn("the correlations were held fixed, and draws at which they are not attainable were discarded.",
                      summary)

    def test_the_seed_reproduces_the_draws(self):
        first, again, other = cotest(ci=True, **MG), cotest(ci=True, **MG), cotest(ci=True, seed=2, **MG)
        self.assertEqual(rows(first, "intervals"), rows(again, "intervals"))
        self.assertNotEqual(rows(first, "intervals"), rows(other, "intervals"))
        self.assertTrue(notes(other, "intervals")[0].startswith("95% percentile intervals over "))
        self.assertIn("(seed 2; numpy ", notes(other, "intervals")[0])

    def test_intervals_are_withheld_with_a_reason(self):
        def why(**options):
            result = cotest(ci=True, **options)
            self.assertEqual(column(result, "intervals", "lower"), [None] * 5)
            self.assertEqual(column(result, "intervals", "upper"), [None] * 5)
            self.assertTrue(notes(result, "posttest")[-1].endswith("Uncertainty Intervals says why none was computed."))
            return notes(result, "intervals")

        self.assertTrue(why()[0].startswith("No interval was computed: every sample size is 0"))
        self.assertTrue(why(spec1=0.99, spec2=0.90, depNeg=0.40, nPrev=100)[0].startswith(
            "No interval was computed: a correlation is at, or was truncated to, the limit"))
        # 1000 draws x 0.005 = 5 expected beyond each limit of a 99% interval, fewer than 10
        self.assertEqual(why(indep=True, nPrev=200, ciWidth=99, draws=1000)[0],
                         "No interval was computed: 1000 draws are fewer than the 2000 needed for a 99% interval (at "
                         "least 10 draws expected beyond each limit). Increase the number of draws.")
        # under strong dependence most draws are discarded: 1000 draws, phi near its limit at the entered values
        self.assertIn("draws remained after discarding those at which the fixed correlations are not attainable",
                      why(nSens1=10, nSens2=10, depPos=0.85, draws=1000)[0])

    def test_the_plot_holds_each_probability_with_its_interval_and_the_prevalence(self):
        result = cotest(ci=True, showPlot=True, indep=True, nPrev=200)
        plot = result["plots"]["probPlot"]
        self.assertEqual(plot["kind"], "interval")
        self.assertClose([plot["reference"]], [10])
        self.assertClose(plot["columns"]["estimate"], [100 * p for p in C1["post"]])
        self.assertClose(plot["columns"]["lower"], [100 * p for p in column(result, "intervals", "lower")])
        self.assertEqual(plot["xlab"], "Post-test probability of disease, % (bars: 95% uncertainty interval; dashed "
                                       "line: prevalence)")
        plain = cotest(showPlot=True, depPos=0.90, depNeg=0.90)["plots"]["probPlot"]
        self.assertEqual(len(plain["columns"]["label"]), 4)  # the impossible combination has no point
        self.assertEqual(plain["columns"]["lower"], [None] * 4)
        self.assertNotIn("probPlot", cotest()["plots"])


if __name__ == "__main__":
    unittest.main()
