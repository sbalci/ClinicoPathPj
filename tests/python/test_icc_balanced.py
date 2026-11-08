"""Numerical prototype only: these tests do not qualify a public jamovi analysis."""
import json
import sys
import unittest
import numpy as np
from cpjtest import ROOT
sys.path.insert(0, str(ROOT / 'inst/python'))
from cpj_icc import calculate_icc, MODELS


class BalancedICC(unittest.TestCase):
    def test_independent_r_references(self):
        fixtures = json.loads((ROOT / 'tests/fixtures/icc-balanced.json').read_text())['cases']
        self.assertEqual(len(fixtures), 90)
        disagreements = 0
        def check_interval(actual, expected):
            if expected[0] > expected[1] or expected[1] > 1:
                self.assertIsNone(actual)  # never present an inverted oracle interval
            else:
                np.testing.assert_allclose(actual, expected, atol=1e-9, rtol=1e-10)
        for case in fixtures:
            with self.subTest(name=case['name'], model=case['model'], confidence=case['confidence']):
                result = calculate_icc(case['x'], case['model'], case['confidence'])
                self.assertAlmostEqual(result['estimate'], case['estimate'], places=10)
                self.assertAlmostEqual(result['estimate'], case['psych_estimate'], places=10)
                if case['model'] == 'icc2k':
                    self.assertIsNone(result['interval'])
                    candidate = result['candidate_intervals']
                    check_interval(candidate['frozen_irr'], case['irr_interval'])
                    check_interval(candidate['transformed_single'], case['psych_interval'])
                    disagreements += not np.allclose(case['irr_interval'], case['psych_interval'], atol=1e-9)
                else:
                    check_interval(result['interval'], case['irr_interval'])
                    check_interval(result['interval'], case['psych_interval'])
        self.assertGreater(disagreements, 0)

    def test_hand_anova_and_cohort(self):
        x = np.array([[1,2,3],[4,5,7],[7,9,8],[10,12,13]],float)
        extended = np.vstack([x[0], [1,np.nan,3], x[1:]])
        result = calculate_icc(extended, 'icc31')
        self.assertEqual(result['retained_indices'], [0,2,3,4])
        self.assertEqual((result['input'],result['n'],result['excluded']), (5,4,1))
        # Independent centered-sums ANOVA in original units.
        grand = sum(map(sum,x))/12
        ss_subject = sum((sum(row)/3-grand)**2 for row in x)*3
        ss_rater = sum((sum(x[:,j])/4-grand)**2 for j in range(3))*4
        total = sum((v-grand)**2 for row in x for v in row)
        a = ss_subject/3
        b = (total-ss_subject-ss_rater)/6
        self.assertAlmostEqual(result['estimate'], (a-b)/(a+2*b))
        self.assertFalse(result['public_analysis'])

    def test_common_location_scale_and_permutation(self):
        x = np.array([[1,2,4],[4,3,7],[7,10,9],[12,14,16]],float)
        for model in MODELS:
            a = calculate_icc(x,model)
            for changed in [x*1e200, x*1e-200, x+100, x[::-1,::-1], -x]:
                b = calculate_icc(changed,model)
                self.assertAlmostEqual(a['estimate'],b['estimate'],places=11)
                if a['interval'] is not None:
                    np.testing.assert_allclose(a['interval'],b['interval'],atol=1e-10)

    def test_degenerate_cases_do_not_claim_certainty(self):
        for model in MODELS:
            a = calculate_icc(np.ones((5,3)),model)
            self.assertIsNone(a['estimate'])
            self.assertIsNone(a['interval'])
            perfect = calculate_icc(np.tile(np.arange(5)[:,None],(1,3)),model)
            self.assertAlmostEqual(perfect['estimate'],1)
            self.assertIsNone(perfect['interval'])
            self.assertTrue(perfect['notices'])

    def test_negative_estimates_not_clipped(self):
        x = [[1,6,1],[2,5,3],[3,4,5],[4,3,2],[5,2,4],[6,1,6]]
        for model in MODELS:
            result = calculate_icc(x,model)
            self.assertLess(result['estimate'],0)
            self.assertIn('Negative',str(result['notices']))

    def test_inadmissible_average_ratio_is_not_reported_as_high_reliability(self):
        result = calculate_icc([[1,4],[2,3],[3,2],[4,1]], 'icc2k')
        self.assertIsNone(result['estimate'])
        self.assertIsNone(result['interval'])
        self.assertAlmostEqual(result['unconstrained_estimate'],4)
        self.assertIn('inadmissible',str(result['notices']))

    def test_invalid_inputs_and_explicit_bounds(self):
        for x in [[],[1,2],[[True,False]]*3,[['1','2']]*3,[[np.inf,1],[2,3]],
                  [[np.nan,1],[2,np.nan]],np.ones((3,21)),np.ones((5001,2))]:
            with self.subTest(shape=np.asarray(x).shape), self.assertRaises(ValueError):
                calculate_icc(x)
        for confidence in [True,.7,1,float('nan'),'95']:
            with self.assertRaises(ValueError):
                calculate_icc([[1,2],[3,5]],confidence=confidence)
        with self.assertRaises(ValueError):
            calculate_icc([[1,2],[3,5]],model='unknown')
