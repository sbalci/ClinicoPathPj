import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np
from cpjtest import ROOT, factor, number, rows, run_analysis

sys.path.insert(0, str(ROOT / "inst/python"))
spec = importlib.util.spec_from_file_location("dotdecision", ROOT / "inst/python/analyses/pydotdecision.py")
dot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dot)


class DotDecision(unittest.TestCase):
    def run_case(self, values=(1, 2, 2, 4, 5, 6), labels=("N", "N", "P", "N", "P", "P"), **opts):
        options = dict(marker="x", reference="g", positive="P", cutoff="2", direction="high")
        options.update(opts)
        return run_analysis("pydotdecision", {"x": number(values), "g": factor(labels)}, options)

    def test_ties_and_missing(self):
        result = self.run_case((1, 2, 2, 4, 5, 6, None, 8),
                               ("N", "N", "P", "N", "P", "P", "P", None))
        self.assertEqual(result["status"], "ok", result.get("error"))
        self.assertEqual([r["n"] for r in rows(result, "counts")], [3, 2, 0, 1])
        self.assertEqual(rows(result, "metrics")[0]["estimate"], 1)
        self.assertIn(r"excluded\: 2", result["texts"]["summary"])
        self.assertIn('"rows": [1, 2, 3, 4, 5, 6]', result["htmls"]["explorer"])

    def test_reverse_direction_and_undefined_predictions(self):
        self.assertEqual([r["n"] for r in rows(self.run_case(direction="low"), "counts")], [1, 2, 2, 1])
        got = self.run_case(cutoff="100")
        self.assertIsNone(rows(got, "metrics")[2]["estimate"])
        self.assertIsNone(rows(got, "metrics")[2]["lower"])

    def test_automatic_matches_independent_brute_force(self):
        rng = np.random.default_rng(42)
        for direction in ("high", "low"):
            for criterion in ("errors", "youden"):
                for _ in range(40):
                    x = rng.integers(-5, 6, 50).astype(float)
                    truth = np.r_[np.ones(9, dtype=bool), np.zeros(41, dtype=bool)]
                    cuts = sorted(set(x) | {float(np.nextafter(x.max(), np.inf) if direction == "high"
                                                  else np.nextafter(x.min(), -np.inf))})
                    def score(c):
                        tp, fp, fn, tn = dot.confusion(x, truth, c, direction)
                        return fp + fn if criterion == "errors" else -(tp / 9 - fp / 41)
                    scores = [score(c) for c in cuts]
                    best = min(scores)
                    expected = next(c for c, v in zip(cuts, scores) if abs(v - best) < 1e-12)
                    self.assertEqual(dot.automatic_cutoff(x, truth, direction, criterion)[0], expected)

    def test_objectives_can_differ(self):
        x = np.array([1, 1, 1, 2, 3, 4, 5, 5, 5], dtype=float)
        truth = np.array([0, 0, 0, 0, 0, 0, 1, 0, 0], dtype=bool)
        self.assertNotEqual(dot.automatic_cutoff(x, truth, "high", "errors")[0],
                            dot.automatic_cutoff(x, truth, "high", "youden")[0])

    def test_validation(self):
        for opts in ({"cutoff": "nan"}, {"cutoff": "inf"}, {"cutoff": "hello"},
                     {"positive": None}):
            self.assertEqual(self.run_case(**opts)["status"], "input_error")
        self.assertEqual(self.run_case((0, 1), ("N", "P"), logScale=True)["status"], "input_error")
        self.assertEqual(self.run_case((1, 2), ("P", "P"))["status"], "input_error")

    def test_html_user_labels_cannot_close_script(self):
        payload = {"marker": '</script><img src=x onerror="alert(1)">', "values": []}
        content = dot.html_document(payload)
        self.assertNotIn(payload["marker"], content)
        self.assertEqual(content.count("</script>"), 1)
        self.assertIn("\\u003c/script\\u003e", content)


if __name__ == "__main__":
    unittest.main()
