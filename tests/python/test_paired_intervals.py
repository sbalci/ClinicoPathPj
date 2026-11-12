"""Pinned Newcombe references, identities, boundary arithmetic and opt-in isolation."""
import importlib.util
import json
import sys
import unittest

import numpy as np
from cpjtest import ROOT
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_paired_interval import newcombe_interval, MAX_INTERVAL_N
from cpj_paired_decision import paired_decision
from cpj_runtime import InputError


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load('paired_interval_reference', 'tools/check-paired-intervals.py')
inputs = load('paired_decision_inputs', 'tools/check-paired-decision.py').inputs
CASES = json.loads((ROOT/'tests/fixtures/paired-decision.json').read_text())['fixtures']


class PairedIntervals(unittest.TestCase):
    def test_independent_pinned_R_and_MPFR_references(self):
        result = oracle.verify()
        self.assertEqual(result['failures'], 0)
        self.assertGreater(result['checks'], 30000)

    def test_exact_small_sample_coverage_matches_independent_R(self):
        checker = load('paired_interval_coverage', 'tools/check-paired-interval-coverage.py')
        result = checker.profile(sizes=(5,))
        self.assertEqual(result['profiles'], 27)
        self.assertEqual(result['tables'][0]['table_count'], 56)
        self.assertTrue(all(abs(r['mass_sum']-1) <= 1e-12 for r in result['rows']))

    def test_positive_correlation_correction_and_threshold(self):
        result = newcombe_interval([10, 2, 3, 12])
        denominator = np.sqrt(12*15*13*14)
        self.assertAlmostEqual(result['phi'], (120-6-27/2)/denominator)
        self.assertEqual(newcombe_interval([1, 1, 0, 1])['phi'], 0.)
        self.assertLess(newcombe_interval([1, 4, 5, 2])['phi'], 0.)

    def test_transposition_and_complementation_identities(self):
        for cells in ([2, 1, 3, 4], [0, 1, 0, 0], [200, 100, 0, 200], [499999, 1, 0, 500000]):
            a, b, c, d = cells
            result = newcombe_interval(cells)
            for changed in ([a, c, b, d], [d, c, b, a]):
                inverse = newcombe_interval(changed)
                self.assertAlmostEqual(inverse['estimate'], -result['estimate'], places=13)
                self.assertAlmostEqual(inverse['lower'], -result['upper'], places=13)
                self.assertAlmostEqual(inverse['upper'], -result['lower'], places=13)
                self.assertAlmostEqual(inverse['phi'], result['phi'], places=13)

    def test_single_pair_and_degenerate_margins(self):
        for cells in ([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]):
            result = newcombe_interval(cells)
            self.assertEqual(result['phi'], 0.)
            self.assertLessEqual(result['lower'], result['estimate'])
            self.assertGreaterEqual(result['upper'], result['estimate'])
            self.assertGreater(result['upper']-result['lower'], 0.)
        empty = newcombe_interval([0, 0, 0, 0])
        self.assertEqual(empty['status'], 'empty')
        self.assertTrue(all(empty[k] is None for k in ('estimate', 'lower', 'upper', 'phi')))

    def test_identical_outcomes_are_not_declared_equivalent(self):
        result = newcombe_interval([5, 0, 0, 5])
        self.assertEqual(result['estimate'], 0.)
        self.assertLess(result['lower'], 0.)
        self.assertGreater(result['upper'], 0.)

    def test_confidence_nesting(self):
        for cells in ([1, 1, 7, 12], [59, 6, 16, 80], [200, 100, 0, 200]):
            results = [newcombe_interval(cells, c) for c in (.8, .95, .99)]
            self.assertTrue(all(x['lower'] >= y['lower'] and x['upper'] <= y['upper']
                                for x, y in zip(results, results[1:])))

    def test_large_count_integer_products_do_not_overflow(self):
        result = newcombe_interval([200, 100, 0, 200])
        self.assertEqual(result['n'], 500)
        self.assertAlmostEqual(result['estimate'], .2)
        self.assertTrue(np.isfinite(result['lower']) and np.isfinite(result['upper']))
        result = newcombe_interval([0, MAX_INTERVAL_N, 0, 0])
        self.assertEqual(result['upper'], 1.)
        self.assertLess(result['lower'], 1.)

    def test_input_validation(self):
        for bad in (None, '1234', {}, [], [0]*3, [0]*5, np.zeros((2, 2)),
                    np.ma.array([1, 2, 3, 4], mask=[False, True, False, False])):
            with self.subTest(bad=str(bad)), self.assertRaises(InputError):
                newcombe_interval(bad)
        for value in (True, np.bool_(True), -1, .5, float('nan'), float('inf'), '1', None, MAX_INTERVAL_N+1):
            with self.subTest(value=value), self.assertRaises(InputError):
                newcombe_interval([1, value, 1, 1])
        with self.assertRaises(InputError):
            newcombe_interval([300000]*4)
        for confidence in (True, None, .79, 1., '95', float('nan')):
            with self.assertRaises(InputError):
                newcombe_interval([1]*4, confidence)

    def test_opt_in_and_absent_class_policy(self):
        args = inputs(next(f for f in CASES if f['id'] == 'one_class_positive'))
        default = paired_decision(**args)
        self.assertNotIn('lower', default['pairs'][0]['accuracy'])
        expanded = paired_decision(**args, difference_intervals=True)
        absent = expanded['pairs'][0]['specificity']
        self.assertIsNone(absent['lower']); self.assertIsNone(absent['upper'])
        self.assertEqual(absent['interval_status'], 'absent_class')
        self.assertEqual(expanded['pairs'][0]['accuracy']['p'], default['pairs'][0]['accuracy']['p'])
        for bad in (1, None, 'yes'):
            with self.assertRaises(InputError):
                paired_decision(**args, difference_intervals=bad)


if __name__ == '__main__': unittest.main()
