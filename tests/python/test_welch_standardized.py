"""Unequal-variance prototype: independent oracles and explicit failure semantics."""
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_runtime import Factor, InputError
from cpj_estimation import between_estimation
import cpj_welch_standardized as engine
import cpj_standardized as existing
spec = importlib.util.spec_from_file_location('welch_oracle', ROOT/'tools/check-welch-standardized.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


def independent(a, b, **kwargs):
    return engine.between_welch_standardized(list(a)+list(b),
        Factor(np.array([0]*len(a)+[1]*len(b)), ['First', 'Second', 'unused']),
        'First', 'Second', standardizer='rms_variance', **kwargs)


class WelchStandardized(unittest.TestCase):
    def test_independent_references_and_actual_draw_coverage(self):
        result = oracle.verify()
        self.assertEqual(result['configurations'], 110)
        self.assertEqual(result['coverage_draws'], 24000)
        self.assertEqual(result['full_engine_interval_audits'], 48)
        self.assertEqual([p['status'] for p in result['profiles']].count('pass'), 11)
        self.assertEqual([p['status'] for p in result['profiles']].count('inconclusive'), 1)

    def test_denominator_and_df_are_distinct_from_pooled_and_mean_SD(self):
        a, b = [1, 4, 9], [-2, 0, 1, 2, 3, 4, 5, 6, 8, 9]
        r = independent(a, b)['standardized']
        v1, v2 = np.var(a, ddof=1), np.var(b, ddof=1)
        sd = math.sqrt((v1+v2)/2)
        self.assertAlmostEqual(r['standardizer_sd'], sd)
        self.assertAlmostEqual(r['d_rms'], (np.mean(a)-np.mean(b))/sd)
        self.assertAlmostEqual(r['sd_moment_df'], (v1+v2)**2/(v1*v1/2+v2*v2/9))
        self.assertNotAlmostEqual(r['welch_df'], r['sd_moment_df'])
        self.assertNotAlmostEqual(sd, (math.sqrt(v1)+math.sqrt(v2))/2)
        self.assertNotAlmostEqual(sd, math.sqrt((2*v1+9*v2)/11))
        self.assertFalse(r['correction_exact'])
        self.assertNotIn('hedges_g', r)

    def test_default_has_no_interval_computation_or_native_change(self):
        with patch.object(engine, '_plugin_interval', side_effect=AssertionError('unexpected inference')):
            r = independent([1, 3, 5], [0, 2, 8, 15])
        self.assertEqual(r['standardized']['status'], 'point_only')
        self.assertIsNone(r['standardized']['delta_lower'])
        self.assertFalse(r['standardized']['interval_is_approximate'])
        raw = between_estimation([1, 3, 5, 0, 2, 8, 15],
            Factor(np.array([0, 0, 0, 1, 1, 1, 1]), ['First', 'Second']), 'First', 'Second')
        self.assertEqual(r['raw'], raw)
        with self.assertRaises(InputError):
            existing.between_standardized([1, 2, 3, 4],
                Factor(np.array([0, 0, 1, 1]), ['A', 'B']), 'A', 'B', standardizer='rms_variance')

    def test_orientation_scale_confidence_and_unscaled_delta_limits(self):
        a, b = np.array([1, 4, 9.]), np.array([-2, 0, 2, 3, 5, 6, 8, 9.])
        r = independent(a, b, interval='welch_nct_plugin')['standardized']
        rev = independent(b, a, interval='welch_nct_plugin')['standardized']
        self.assertAlmostEqual(rev['d_rms'], -r['d_rms'])
        self.assertAlmostEqual(rev['delta_lower'], -r['delta_upper'])
        self.assertAlmostEqual(rev['delta_upper'], -r['delta_lower'])
        self.assertTrue(r['interval_is_approximate'])
        for scale in (1e-100, 1e100):
            scaled = independent(a*scale, b*scale, interval='welch_nct_plugin')['standardized']
            for key in ('d_rms', 'welch_J_point', 'delta_lower', 'delta_upper'):
                self.assertAlmostEqual(scaled[key], r[key])
        wider = independent(a, b, interval='welch_nct_plugin', confidence=.99)['standardized']
        self.assertLess(wider['delta_lower'], r['delta_lower'])
        self.assertGreater(wider['delta_upper'], r['delta_upper'])
        self.assertNotAlmostEqual(r['delta_lower'], r['delta_lower']*r['welch_J'])
        self.assertNotIn('g_lower', r)

    def test_one_constant_df1_preserves_point_without_gamma_singularity(self):
        r = independent([2, 2], [1, 5], interval='welch_nct_plugin')['standardized']
        self.assertEqual(r['welch_df'], 1)
        self.assertEqual(r['status'], 'interval_unavailable')
        self.assertTrue(math.isfinite(r['d_rms']))
        self.assertIsNone(r['welch_J']); self.assertIsNone(r['welch_J_point'])
        self.assertIn('greater than one', r['correction_reason'])
        self.assertIsNone(r['delta_lower'])
        self.assertIn('qualified numerical range', r['reason'])

    def test_degeneracy_zero_effect_and_extreme_statistic(self):
        for a, b in (([0, 0], [0, 0]), ([2, 2], [3, 3])):
            r = independent(a, b, interval='welch_nct_plugin')
            self.assertEqual(r['standardized']['status'], 'degenerate')
            self.assertIsNone(r['standardized']['d_rms'])
            json.dumps(r, allow_nan=False)
        r = independent([1, 3, 5], [0, 3, 6], interval='welch_nct_plugin')['standardized']
        self.assertEqual(r['d_rms'], 0)
        self.assertAlmostEqual(r['delta_lower'], -r['delta_upper'])
        r = independent([100, 101, 102], [0, 1, 2], interval='welch_nct_plugin')['standardized']
        self.assertEqual(r['status'], 'interval_unavailable')
        self.assertTrue(math.isfinite(r['d_rms']))

    def test_missingness_labels_subject_IDs_and_invalid_inputs(self):
        r = engine.between_welch_standardized([1, None, 4, 8, 2, 5, 9, 0],
            Factor(np.array([0, 0, 0, 0, 1, 1, 1, -1]), ['NA', '測定 B', 'unused']),
            'NA', '測定 B', standardizer='rms_variance', subject_ids=['001', None, '01', '1', 'a', 'b', 'c', None])
        self.assertEqual(r['raw']['retained_indices'], [0, 2, 3, 4, 5, 6])
        self.assertEqual(r['raw']['retained_subject_ids'], ['001', '01', '1', 'a', 'b', 'c'])
        self.assertEqual(r['raw']['mapping'], dict(first='NA', second='測定 B'))
        for value in (None, True, 1, [], np.array(['none']), 'pooled', 'unknown'):
            with self.assertRaises(InputError): independent([1, 2], [3, 4], interval=value)
        with self.assertRaises(InputError): independent([1, True], [3, 4])
        with self.assertRaises(InputError): independent([1, 2], [3, 4], subject_ids=['x']*4)
        with self.assertRaises(InputError):
            engine.between_welch_standardized([], None, 'A', 'B', standardizer='pooled')

    def test_inversion_against_existing_independent_R_and_mixture_grid(self):
        f = json.loads((ROOT/'tests/fixtures/standardized-effects.json').read_text())
        for x in f['inversion_grid']+f['mixture_grid']:
            limits = engine._plugin_interval(x['t'], x['df'], x['confidence'])
            for got, key in zip(limits, ('ncp_lower', 'ncp_upper')):
                self.assertLessEqual(abs(got-x[key]), 2e-7*max(1, abs(x[key])))

    def test_bundled_CDF_NaN_red_and_stable_tail_green(self):
        # Original shared solver fails at a negative-NCP bracket point on the
        # bundled SciPy; this prototype uses finite complementary SF instead.
        statistic, df = -6.448159123436948, 148.59436616559083
        if math.isnan(engine.nct.cdf(abs(statistic), df, -5.224079561718474)):
            with self.assertRaises(ArithmeticError): existing._noncentral_interval(statistic, df, .5)
        low, high = engine._plugin_interval(statistic, df, .5)
        self.assertAlmostEqual(low, -7.157131795652202, places=7)
        self.assertLess(low, high)

    def test_independent_oracle_rejects_five_statistical_mutations(self):
        original = oracle.between_welch_standardized
        def mutated(kind):
            def call(*args, **kwargs):
                got = original(*args, **kwargs)
                r, raw = got['standardized'], got['raw']
                if r['status'] != 'degenerate':
                    a, b = raw['summaries']['first'], raw['summaries']['second']
                    if kind == 'pooled':
                        sd = math.sqrt(((a['n']-1)*a['sd']**2+(b['n']-1)*b['sd']**2)/(a['n']+b['n']-2))
                        r['d_rms'] = raw['difference']/sd
                    elif kind == 'SD_df': r['welch_df'] = r['sd_moment_df']
                    elif kind == 'approximate_J': r['welch_J'] = 1-3/(4*r['welch_df']-1)
                    elif kind == 'J_scaled_CI' and r['delta_lower'] is not None:
                        r['delta_lower'] *= r['welch_J']
                    elif kind == 'reversed': r['d_rms'] = -r['d_rms']
                return got
            return call
        for kind in ('pooled', 'SD_df', 'approximate_J', 'J_scaled_CI', 'reversed'):
            with self.subTest(kind=kind), patch.object(oracle, 'between_welch_standardized', mutated(kind)):
                with self.assertRaises(AssertionError): oracle.verify()


    def test_numerical_failures_clear_only_limits_and_programming_errors_propagate(self):
        for failure in (ArithmeticError('failed residual'), RuntimeWarning('invalid CDF')):
            with patch.object(engine, '_plugin_interval', side_effect=failure):
                r = independent([1, 3, 5], [0, 2, 8, 15], interval='welch_nct_plugin')['standardized']
            self.assertEqual(r['status'], 'interval_unavailable')
            self.assertIsNotNone(r['d_rms']); self.assertIsNone(r['delta_lower'])
        with patch.object(engine, '_plugin_interval', side_effect=RuntimeError('bug')):
            with self.assertRaises(RuntimeError): independent([1, 3, 5], [0, 2, 8, 15], interval='welch_nct_plugin')
        with patch.object(engine, 'brentq', return_value=(0., SimpleNamespace(converged=False))):
            with self.assertRaises(ArithmeticError): engine._plugin_interval(1, 4, .95)
        with patch.object(engine.nct, 'cdf', return_value=1.00001):
            with self.assertRaises(ArithmeticError): engine._plugin_interval(1, 4, .95)


if __name__ == '__main__': unittest.main()
