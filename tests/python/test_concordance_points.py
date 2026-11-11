"""Numerical-first CCC prototype: independent references and boundary contracts."""
import json
import math
import sys
import unittest

import numpy as np
from cpjtest import ROOT

sys.path.insert(0, str(ROOT / 'inst/python'))
from cpj_concordance import concordance
from cpj_runtime import InputError


class ConcordancePoints(unittest.TestCase):
    def test_known_answers_and_population_divisor(self):
        # x=(0,1,2): mean=1, population variance=2/3. y=x+1:
        # CCC=(4/3)/(4/3+1)=4/7. n-1 moments would incorrectly give 2/3.
        result = concordance([0, 1, 2], [1, 2, 3])
        self.assertAlmostEqual(result['ccc'], 4/7, places=14)
        self.assertAlmostEqual(result['precision'], 1.)
        self.assertAlmostEqual(result['bias_correction'], 4/7, places=14)
        self.assertEqual(result['moment_divisor'], 'n')
        self.assertNotAlmostEqual(result['ccc'], 2/3)
        scaled = concordance([-1, 0, 1], [-2, 0, 2])
        self.assertAlmostEqual(scaled['ccc'], .8, places=14)
        negative = concordance([-1, 0, 1], [1, 0, -1])
        self.assertAlmostEqual(negative['ccc'], -1.)
        self.assertAlmostEqual(negative['precision'], -1.)
        self.assertAlmostEqual(negative['bias_correction'], 1.)

    def test_zero_correlation_has_defined_bias_factor(self):
        # Covariance=0, vx=2/3, vy=2; direct Cb=sqrt(3)/2.
        result = concordance([-1, 0, 1], [1, -2, 1])
        self.assertEqual(result['ccc'], 0.)
        self.assertEqual(result['precision'], 0.)
        self.assertAlmostEqual(result['bias_correction'], math.sqrt(3)/2, places=14)

    def test_independent_R_and_DescTools_oracles(self):
        fixture = json.loads((ROOT / 'tests/fixtures/concordance-points.json').read_text())
        for case in fixture['cases']:
            x = [float('nan') if value is None else value for value in case['x']]
            y = [float('nan') if value is None else value for value in case['y']]
            if case['n_complete'] < 3:
                with self.assertRaisesRegex(InputError, 'at least three complete'):
                    concordance(x, y)
                continue
            result = concordance(x, y)
            for key in ('ccc', 'precision', 'bias_correction'):
                self.assertAlmostEqual(result[key], case['expected'][key], delta=1e-12,
                                       msg=(case['id'], key))
            for key in ('n_input', 'n_complete', 'missing_x', 'missing_y',
                        'missing_either', 'missing_both', 'retained_indices'):
                self.assertEqual(result[key], case[key], (case['id'], key))

    def test_independently_enumerated_degenerate_cases(self):
        fixture = json.loads((ROOT / 'tests/fixtures/concordance-points.json').read_text())
        for case in fixture['degenerate_cases']:
            x = [float('nan') if value is None else value for value in case['x']]
            y = [float('nan') if value is None else value for value in case['y']]
            if case['n_complete'] < 3:
                with self.assertRaises(InputError):
                    concordance(x, y)
                continue
            result = concordance(x, y)
            for key in ('ccc', 'precision', 'bias_correction'):
                self.assertEqual(result[key], case['expected'][key], (case['id'], key))

    def test_missing_pairs_and_positions(self):
        result = concordance([0, np.nan, 1, 2, np.nan, 3],
                             [1, 5, np.nan, 3, np.nan, 4])
        self.assertEqual(result['retained_indices'], [0, 3, 5])
        self.assertEqual([result[key] for key in ('n_input', 'n_complete', 'missing_x',
                         'missing_y', 'missing_either', 'missing_both')], [6, 3, 2, 2, 3, 1])
        self.assertEqual(result['ccc'], concordance([0, 2, 3], [1, 3, 4])['ccc'])

    def test_constants_do_not_fabricate_precision_or_perfect_concordance(self):
        identical = concordance([5, 5, 5], [5, 5, 5])
        for key in ('ccc', 'precision', 'bias_correction'):
            self.assertIsNone(identical[key])
        self.assertIn('0/0', identical['undefined_reason'])
        for x, y in [([1, 1, 1], [2, 2, 2]), ([0, 1, 2], [1.7]*3),
                     ([1.7]*17, list(range(17)))]:
            result = concordance(x, y)
            self.assertEqual(result['ccc'], 0.)
            self.assertEqual(result['bias_correction'], 0.)
            self.assertIsNone(result['precision'])
            self.assertIn('constant', result['precision_undefined_reason'])

    def test_symmetry_invariance_and_decomposition(self):
        x = np.array([0., 1., 3., 7., 9.])
        y = np.array([1., 4., 2., 8., 10.])
        base = concordance(x, y)
        for a, b in [(y, x), (x[::-1], y[::-1]),
                     (np.tile(x, 3), np.tile(y, 3)),
                     (x+1e12, y+1e12), (-3*x, -3*y),
                     (x*1e-300, y*1e-300), (x*1e300, y*1e300)]:
            result = concordance(a, b)
            for key in ('ccc', 'precision', 'bias_correction'):
                self.assertAlmostEqual(result[key], base[key], delta=1e-13, msg=key)
        self.assertAlmostEqual(base['ccc'], base['precision']*base['bias_correction'],
                               delta=1e-14)

    def test_overflow_safe_origin_and_unresolved_dynamic_range(self):
        result = concordance([-1e308, 0., 1e308], [-1e308, 0., 1e308])
        self.assertAlmostEqual(result['ccc'], 1.)
        with self.assertRaisesRegex(InputError, 'numerically unresolved'):
            concordance([1e-300, 2e-300, 3e-300], [1e300, 2e300, 3e300])

    def test_invalid_inputs_and_resource_boundary(self):
        good = [1, 2, 3]
        bad = [[], [1, 2], [np.nan]*3, [1, np.inf, 3], [True, 2, 3],
               ['1', '2', '3'], [1+1j]*3, [[1], [2], [3]], [2**54]*3,
               np.ma.array(good, mask=[False, True, False]),
               np.array(['2026-01-01']*3, dtype='datetime64[D]')]
        for values in bad:
            with self.assertRaises(InputError):
                concordance(values, good)
        with self.assertRaises(InputError):
            concordance([1]*5001, [2]*5001)
        self.assertEqual(concordance(np.arange(5000), np.arange(5000))['n_complete'], 5000)
        self.assertIsNone(concordance(good, good)['confidence_interval'])


if __name__ == '__main__':
    unittest.main()
