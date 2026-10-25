"""pykappaci: kappaSize's confidence-interval sample size (CIBinary, CI3Cats, CI4Cats, CI5Cats) and the
Monte Carlo check of the planned study.

Oracles: kappaSize 1.2 in R 4.6.0 (each call quoted at its value), and an exact enumeration of every
possible study in R (the script at the end of this file). Before these tests were written the port was
also compared with kappaSize on 2,320 random designs (K = 2..5, R = 2..6, every engine): n identical in
800/800, FixedN identical in 800/800, power N within 3.3e-13 relative in 720/720.
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
from cpj_runtime import InputError  # noqa: E402
from cpjtest import rows, run_analysis  # noqa: E402

OPTIONS = {"outcome": "2", "props": "0.20, 0.80", "raters": "2", "kappa0": 0.6, "citype": "two_sided",
           "kappaL": 0.4, "kappaU": 0.8, "alpha": 0.05, "simulate": False, "draws": 2000, "seed": 20261018}


def tables(n, cells):
    """Every study of n subjects: all count vectors over the pattern cells (stars and bars)."""
    bars = np.array(list(itertools.combinations(range(n + cells - 1), cells - 1)))
    edges = np.hstack([np.full((len(bars), 1), -1), bars, np.full((len(bars), 1), n + cells - 1)])
    return np.diff(edges, axis=1) - 1


def exact_ci(raters, props, kappa0, kappa_l, kappa_u, alpha, n):
    """Exact P(coverage), P(within targets) of the GOF interval, from the analysis' own decision rule."""
    counts, probs, unanimous = ks.patterns(raters, props, kappa0)
    t = tables(n, len(probs))
    weight = np.exp(gammaln(n + 1) - gammaln(t + 1).sum(axis=1) + (t * np.log(probs)).sum(axis=1))
    share, una = ks.summarise(t, counts, unanimous, raters)
    covered, reached = ks.ci_outcomes(raters, share, una, n, kappa0, kappa_l, kappa_u, alpha)
    return weight[covered].sum(), weight[reached].sum()


class Engine(unittest.TestCase):
    def test_binary_two_sided_matches_kappasize_for_every_rater_count(self):
        # kappaSize::CIBinary(kappa0 = 0.6, kappaL = 0.4, kappaU = 0.8, props = 0.2, raters = r, alpha = 0.05)$n
        for r, n in zip(range(2, 7), [118, 71, 56, 47, 42]):
            self.assertEqual(ks.ci_n(2, r, [0.2, 0.8], 0.6, 0.4, 0.8, 0.05), n)
        # kappaSize::CIBinary(kappa0 = 0.75, kappaL = 0.6, kappaU = 0.9, props = 0.35, raters = r, alpha = 0.1)$n
        for r, n in zip(range(2, 7), [85, 51, 40, 36, 33]):
            self.assertEqual(ks.ci_n(2, r, [0.35, 0.65], 0.75, 0.6, 0.9, 0.1), n)

    def test_binary_one_sided_matches_kappasize_for_every_rater_count(self):
        # kappaSize::CIBinary(kappa0 = 0.7, kappaL = 0.5, kappaU = NA, props = 0.1, raters = r, alpha = 0.05)$n
        for r, n in zip(range(2, 7), [131, 88, 71, 59, 51]):
            self.assertEqual(ks.ci_n(2, r, [0.1, 0.9], 0.7, 0.5, None, 0.05), n)

    def test_three_to_five_categories_match_kappasize(self):
        # kappaSize::CI3Cats(kappa0 = 0.6, kappaL = 0.4, kappaU = 0.8, props = c(0.2, 0.3, 0.5), raters = r,
        #                    alpha = 0.05)$n
        for r, n in zip(range(2, 7), [57, 31, 23, 19, 16]):
            self.assertEqual(ks.ci_n(3, r, [0.2, 0.3, 0.5], 0.6, 0.4, 0.8, 0.05), n)
        # kappaSize::CI4Cats(kappa0 = 0.7, kappaL = 0.5, kappaU = 0.85, props = c(0.1, 0.2, 0.3, 0.4), raters = r,
        #                    alpha = 0.05)$n
        for r, n in zip(range(2, 7), [44, 26, 19, 17, 16]):
            self.assertEqual(ks.ci_n(4, r, [0.1, 0.2, 0.3, 0.4], 0.7, 0.5, 0.85, 0.05), n)
        # kappaSize::CI5Cats(kappa0 = 0.5, kappaL = 0.3, kappaU = NA, props = c(0.1, 0.15, 0.2, 0.25, 0.3),
        #                    raters = r, alpha = 0.1)$n  (one-sided; 11 is the package's floor)
        for r, n in zip(range(2, 7), [17, 11, 11, 11, 11]):
            self.assertEqual(ks.ci_n(5, r, [0.1, 0.15, 0.2, 0.25, 0.3], 0.5, 0.3, None, 0.1), n)

    def test_the_packages_stopping_margin_is_kept(self):
        # kappaSize stops once the chi-square exceeds the critical value by 0.001, which here is one subject above
        # the plain minimum (ceiling(qchisq(0.95, 1) / slope) = 90 for the first design):
        # kappaSize::CIBinary(kappa0 = 0.5, kappaL = 0.3, kappaU = 0.7, props = 0.4, raters = 2)$n = 91
        # kappaSize::CIBinary(kappa0 = 0.7, kappaL = 0.5, kappaU = 0.9, props = 0.3, raters = 3)$n = 50
        # kappaSize::CIBinary(kappa0 = 0.6, kappaL = 0.45, kappaU = 0.75, props = 0.4, raters = 5)$n = 52
        for design, n in [((2, [0.4, 0.6], 0.5, 0.3, 0.7), 91), ((3, [0.3, 0.7], 0.7, 0.5, 0.9), 50),
                          ((5, [0.4, 0.6], 0.6, 0.45, 0.75), 52)]:
            raters, props, kappa0, kappa_l, kappa_u = design
            self.assertEqual(ks.ci_n(2, raters, props, kappa0, kappa_l, kappa_u, 0.05), n)

    def test_binary_answer_does_not_depend_on_which_category_is_typed_first(self):
        # kappaSize::CIBinary(kappa0 = 0.7, kappaL = 0.5, kappaU = 0.9, props = 0.05 or 0.95, raters = 6)$n: 141 both
        self.assertEqual(ks.ci_n(2, 6, [0.05, 0.95], 0.7, 0.5, 0.9, 0.05), 141)
        self.assertEqual(ks.ci_n(2, 6, [0.95, 0.05], 0.7, 0.5, 0.9, 0.05), 141)

    def test_proportions_are_validated(self):
        self.assertEqual(ks.parse_props("0.2", 2), ([0.2, 0.8], False))
        self.assertEqual(ks.parse_props("0.2;0.3 | 0.5", 3), ([0.2, 0.3, 0.5], False))
        props, rescaled = ks.parse_props("0.333, 0.333, 0.333", 3)
        self.assertTrue(rescaled)
        self.assertAlmostEqual(sum(props), 1, places=15)
        for text, categories, message in [
                ("0.2, 0.3", 3, "Enter 3 proportions, one per outcome category; got 2."),
                ("0.2, 0.7", 2, "they sum to 0.9"), ("20%, 80%", 2, "not percentages"), ("20, 80", 2, "not percentages"),
                ("0,20 0,80", 2, "decimal comma"), ("0.2, x", 2, "could not be read"), ("", 2, "Enter the expected"),
                ("0.2 0.8 0", 3, "strictly between 0 and 1"), ("nan", 2, "could not be read"),
                ("1e-60", 2, "a proportion is too close to 0")]:  # 1 - 1e-60 rounds to 1
            with self.assertRaises(InputError, msg=text) as caught:
                ks.parse_props(text, categories)
            self.assertIn(message, str(caught.exception))


class MonteCarlo(unittest.TestCase):
    # Exact values: every possible study enumerated in R (script at the end of this file). The analyses run the
    # check for two raters only (ks.mc_available); the 3- and 4-rater designs check the helpers, which take any R.
    def test_decision_rule_on_every_possible_study_matches_the_r_enumeration(self):
        cases = [  # (raters, props, kappa0, kappaL, kappaU, alpha, n), (coverage, P(within targets)): ci() below
            ((2, [0.2, 0.8], 0.6, 0.4, 0.8, 0.05, 118), (0.94586653217667949, 0.26936920996023672)),
            # one-sided, the analysis' own design: ci(2, 2, c(0.1, 0.9), 0.7, 0.5, NA, 0.05, 131); a second,
            # independent enumeration (grid + optimize, no convexity assumed) gives 0.95623055713516003, 0.49496482042900469
            ((2, [0.1, 0.9], 0.7, 0.5, None, 0.05, 131), (0.95623055713515881, 0.49496482042900414)),
            ((3, [0.3, 0.7], 0.6, 0.3, None, 0.05, 17), (0.96669481100470434, 0.50754921520661778)),
            ((4, [0.4, 0.6], 0.6, 0.3, 0.85, 0.05, 15), (0.93559474044661073, 0.1272170652989548)),
        ]
        for design, expected in cases:
            for got, want in zip(exact_ci(*design), expected):
                self.assertAlmostEqual(got, want, delta=1e-10 * want, msg=str(design))

    def test_the_plug_in_test_is_liberal_for_six_raters(self):
        # Backs the "nearly 9% instead of 5%" in ks.MC_UNAVAILABLE (6 raters, prevalence 0.2, kappa0 0.4, n = 2000;
        # 8.75% with 200,000 draws). Two raters stay close to 5%: 0.0519 exactly at n = 191 (test_pykappapower).
        counts, probs, unanimous = ks.patterns(6, [0.2, 0.8], 0.4)
        studies = np.random.default_rng(20261018).multinomial(2000, probs, size=20000)
        size = ks.rejects(6, *ks.summarise(studies, counts, unanimous, 6), 2000, 0.4, 0.05).mean()
        self.assertLess(abs(size - 0.0875), 4 * ks.mc_se(0.0875, 20000))

    def test_seeded_simulation_agrees_with_the_exact_values(self):
        for design, (coverage, reached) in [
                ((4, [0.4, 0.6], 0.6, 0.3, 0.85, 0.05, 15), (0.93559474044661073, 0.1272170652989548)),
                ((3, [0.3, 0.7], 0.6, 0.3, None, 0.05, 17), (0.96669481100470434, 0.50754921520661778))]:
            got = ks.simulate_ci(*design, 20000, 20261018)
            self.assertEqual(got, ks.simulate_ci(*design, 20000, 20261018))  # reproducible
            for value, exact in zip(got, (coverage, reached)):
                self.assertLess(abs(value - exact), 4 * ks.mc_se(exact, 20000), msg=str(design))


class Analysis(unittest.TestCase):
    def test_default_design(self):
        result = run_analysis("pykappaci", options=OPTIONS)
        self.assertEqual(result["status"], "ok", result["error"])
        self.assertEqual(rows(result, "size"), [{"n": 118, "categories": 2, "raters": 2, "props": "0.2, 0.8",
                                                 "kappa0": 0.6, "kappaL": 0.4, "kappaU": 0.8,
                                                 "interval": "95% two-sided"}])
        notes = result["tables"]["size"]["notes"]
        self.assertTrue(notes[0].startswith("kappaSize confidence-interval approach (Rotondi and Donner 2012): the "
                                            "smallest number of subjects, at least 11,"))
        self.assertTrue(notes[1].startswith("Agreement model: Donner and Eliasziw (1992). kappa here is the "
                                            "intraclass (Fleiss-type) kappa"))
        self.assertEqual(len(notes), 2)
        self.assertNotIn("check", result["tables"])  # simulation off
        self.assertTrue(result["texts"]["summary"].startswith(
            "**118 subjects**, each rated by both raters, are needed for the expected 95% confidence limits around "
            "an anticipated kappa of 0.6 to reach 0.4 and 0.8. These are expected limits, reached if the study "
            "observes kappa = 0.6; if it observes less, the lower limit will usually fall below 0.4."))

    def test_one_sided_three_categories_and_sparse_cells(self):
        one = run_analysis("pykappaci", options=dict(OPTIONS, citype="one_sided", kappaU=0.5, props="0.1",
                                                     kappa0=0.7, kappaL=0.5))
        self.assertEqual(rows(one, "size")[0]["n"], 131)
        self.assertIsNone(rows(one, "size")[0]["kappaU"])  # ignored for a one-sided interval
        self.assertEqual(rows(one, "size")[0]["interval"], "95% one-sided")
        self.assertIn("expected lower limit of the one-sided 95% confidence interval", one["texts"]["summary"])
        three = run_analysis("pykappaci", options=dict(OPTIONS, outcome="3", props="0.2, 0.3, 0.5", raters="4"))
        self.assertEqual(rows(three, "size")[0]["n"], 23)  # CI3Cats(..., raters = 4)$n, see Engine
        self.assertIn("Agreement model: Dirichlet-multinomial (Altaye, Donner and Eliasziw 2001).",
                      three["tables"]["size"]["notes"][1])
        sparse = run_analysis("pykappaci", options=dict(OPTIONS, raters="6"))
        self.assertEqual(rows(sparse, "size")[0]["n"], 42)
        # all raters positive at kappaL: 42 * (0.6 * 0.2^6 + 0.4 * 0.2) = 3.36
        self.assertIn("The smallest expected count among the goodness-of-fit cells (all raters agree on a "
                      "category, or any disagreement) is 3.36, below 5", sparse["tables"]["size"]["notes"][-1])
        self.assertIn("Altaye, Donner and Klar (2001), in which with probability kappa all raters give one shared "
                      "rating", sparse["tables"]["size"]["notes"][1])

    def test_rescaled_proportions_are_reported(self):
        result = run_analysis("pykappaci", options=dict(OPTIONS, outcome="3", props="0.333; 0.333; 0.333"))
        self.assertEqual(rows(result, "size")[0]["props"], "0.3333, 0.3333, 0.3333")
        self.assertIn("The proportions entered did not sum exactly to 1 and were rescaled to do so.",
                      result["tables"]["size"]["notes"])

    def test_unusable_input_is_an_input_error(self):
        for options, message in [
                (dict(OPTIONS, kappaL=0.6), "The target lower limit (kappaL) must be below the anticipated kappa"),
                (dict(OPTIONS, kappaU=0.6), "The target upper limit (kappaU) must be above the anticipated kappa"),
                (dict(OPTIONS, kappaL=0.5999999, kappaU=0.6000001), "more than 1,000,000,000 subjects"),
                (dict(OPTIONS, outcome="3"), "Enter 3 proportions, one per outcome category; got 2.")]:
            result = run_analysis("pykappaci", options=options)
            self.assertEqual(result["status"], "input_error")
            self.assertIn(message, result["error"]["message"])

    def test_monte_carlo_check_states_seed_and_draws_and_is_reproducible(self):
        options = dict(OPTIONS, simulate=True)
        result = run_analysis("pykappaci", options=options)
        check = rows(result, "check")
        self.assertEqual([r["statistic"] for r in check],
                         ["Interval contains the true kappa (coverage)", "Interval within the target limits"])
        self.assertEqual(check[0]["planned"], 0.95)
        self.assertIsNone(check[1]["planned"])
        for row, exact in zip(check, (0.94586653217667949, 0.26936920996023672)):  # exact: R enumeration above
            self.assertLess(abs(row["simulated"] - exact), 4 * ks.mc_se(exact, 2000))
            self.assertAlmostEqual(row["se"], math.sqrt(row["simulated"] * (1 - row["simulated"]) / 2000), places=15)
        # what is shown is what the stated draws and seed give
        self.assertEqual(tuple(r["simulated"] for r in check),
                         ks.simulate_ci(2, [0.2, 0.8], 0.6, 0.4, 0.8, 0.05, 118, 2000, 20261018))
        notes = result["tables"]["check"]["notes"]
        self.assertEqual(notes[0], "2,000 simulated studies of 118 subjects, random seed 20261018, true kappa 0.6; "
                                   "each analysed with the published goodness-of-fit interval (Donner and Eliasziw "
                                   "1992), the prevalence estimated by the study's overall share of ratings.")
        self.assertIn("'Interval within the target limits' has no planned value", notes[1])
        self.assertIn("In 2,000 simulated studies (seed 20261018) the interval contained the true kappa in",
                      result["texts"]["summary"])
        self.assertEqual(rows(run_analysis("pykappaci", options=options), "check"), check)
        self.assertNotEqual(rows(run_analysis("pykappaci", options=dict(options, seed=7)), "check"), check)

    def test_no_monte_carlo_check_for_three_to_five_categories(self):
        result = run_analysis("pykappaci", options=dict(OPTIONS, outcome="3", props="0.2, 0.3, 0.5", simulate=True))
        self.assertEqual(rows(result, "size")[0]["n"], 57)  # CI3Cats(..., raters = 2)$n, see Engine
        self.assertEqual(result["tables"]["check"], {"rows": [], "notes": [ks.MC_UNAVAILABLE]})
        self.assertTrue(ks.MC_UNAVAILABLE.startswith("Not available for more than two raters or for 3-5 categories:"))
        self.assertNotIn("simulated", result["texts"]["summary"])

    def test_no_monte_carlo_check_for_more_than_two_raters(self):
        # The plug-in analysis is liberal there even in large studies: 6 raters, prevalence 0.2, kappa0 0.4,
        # n = 2000 rejects a true kappa0 in 8.75% (200,000 seeded draws, SE 0.06%), against 5% (cpj_kappasize docstring).
        result = run_analysis("pykappaci", options=dict(OPTIONS, raters="6", simulate=True))
        self.assertEqual(rows(result, "size")[0]["n"], 42)  # CIBinary(..., raters = 6)$n, see Engine
        self.assertEqual(result["tables"]["check"], {"rows": [], "notes": [ks.MC_UNAVAILABLE]})
        self.assertTrue(result["tables"]["size"]["notes"][-1].endswith("may be inaccurate."))  # no pointer to a check
        self.assertNotIn("simulated", result["texts"]["summary"])


if __name__ == "__main__":
    unittest.main()

# R oracle for the exact values (R 4.6.0; every possible study enumerated; f = category shares):
#
# comps <- function(n, k) if (k == 1) matrix(n, 1, 1) else do.call(rbind, lapply(n:0, function(i) cbind(i, comps(n - i, k - 1))))
# pat <- function(K, R, f, k) {  # rating patterns of one subject and their probabilities
#   X <- if (K == 2) cbind(0:R, R - (0:R)) else comps(R, K)
#   p <- apply(X, 1, function(x) if (K == 2) (1 - k) * choose(R, x[1]) * f[1]^x[1] * f[2]^x[2] + k * f[1] * (x[1] == R) + k * f[2] * (x[2] == R)
#          else factorial(R) / prod(factorial(x)) * prod(unlist(lapply(1:K, function(i) f[i] * (1 - k) + seq_len(x[i]) * k - k))) / prod((1 - k) + (0:(R - 1)) * k))
#   list(X = X, p = p, una = sapply(1:K, function(i) which(X[, i] == R)))
# }
# x2 <- function(O, P, n, R, k) {  # Pearson X2 over the pooled cells, shares plugged in
#   s <- (O %*% P$X) / (n * R); K <- ncol(s)
#   a <- if (K == 2) (1 - k) * s^R + k * s else { a <- s; for (r in 1:(R - 1)) a <- a * (s * (1 - k) + r * k) / ((1 - k) + r * k); a }
#   E <- n * cbind(1 - rowSums(a), a); Ob <- cbind(n - rowSums(O[, P$una, drop = FALSE]), O[, P$una, drop = FALSE])
#   rowSums(ifelse(E > 0, (Ob - E)^2 / E, ifelse(Ob > 0, Inf, 0)))
# }
# lims <- function(o, P, n, R, crit) {  # interval of one study by optimize() and uniroot()
#   o <- matrix(o, 1); s <- (o %*% P$X)[1, ] / (n * R); if (max(s) == 1) return(c(-Inf, Inf))
#   fl <- if (ncol(P$X) == 2) max(-s^(R - 1) / (1 - s^(R - 1))) else max(-s[s > 0] / (R - 1 - s[s > 0]), if (R > 2) -1 / (R - 2))
#   h <- function(k) x2(o, P, n, R, k); a <- fl + 1e-10; b <- 1 - 1e-10
#   m <- optimize(h, c(a, b), tol = 1e-12)$minimum; if (h(m) > crit) return(c(NA, NA))
#   c(if (h(a) < crit) fl else uniroot(function(k) h(k) - crit, c(a, m), tol = 1e-12)$root,
#     if (h(b) < crit) 1 else uniroot(function(k) h(k) - crit, c(m, b), tol = 1e-12)$root)
# }
# prob <- function(O, p) exp(apply(O, 1, function(o) dmultinom(o, prob = p, log = TRUE)))
# ci <- function(K, R, f, k0, kL, kU, alpha, n) {  # exact coverage and P(within targets); kU = NA: one-sided
#   P <- pat(K, R, f, k0); O <- comps(n, nrow(P$X)); w <- prob(O, P$p)
#   L <- t(apply(O, 1, lims, P = P, n = n, R = R, crit = qchisq(if (is.na(kU)) 1 - 2 * alpha else 1 - alpha, 1)))
#   ok <- !is.na(L[, 1]); hi <- if (is.na(kU)) Inf else kU
#   c(sum(w[ok & L[, 1] <= k0 & (is.na(kU) | L[, 2] >= k0)]), sum(w[ok & L[, 1] >= kL & L[, 2] <= hi]))
# }
# pw <- function(K, R, f, k0, k1, alpha, n) {  # exact power and size of the GOF test of kappa0
#   P <- pat(K, R, f, k1); O <- comps(n, nrow(P$X)); rej <- x2(O, P, n, R, k0) > qchisq(1 - alpha, 1)
#   c(sum(prob(O, P$p)[rej]), sum(prob(O, pat(K, R, f, k0)$p)[rej]))
# }
# ci(2, 2, c(0.2, 0.8), 0.6, 0.4, 0.8, 0.05, 118); ci(2, 3, c(0.3, 0.7), 0.6, 0.3, NA, 0.05, 17)
# ci(2, 4, c(0.4, 0.6), 0.6, 0.3, 0.85, 0.05, 15); ci(2, 2, c(0.1, 0.9), 0.7, 0.5, NA, 0.05, 131)
# pw(2, 2, c(0.3, 0.7), 0.4, 0.6, 0.05, 191); pw(2, 3, c(0.3, 0.7), 0.3, 0.7, 0.05, 27)
