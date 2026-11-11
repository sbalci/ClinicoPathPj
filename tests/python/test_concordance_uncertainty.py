"""Numerical CCC intervals: independent fixtures, domains and invariants."""
import importlib.util
import json
import sys
import unittest
import numpy as np
from cpjtest import ROOT
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_concordance_uncertainty import concordance_interval
from cpj_concordance import concordance
from cpj_runtime import InputError

X=np.array([-1,-1,1,1]*3,dtype=float)
Y=np.array([-1,1,0,2]*3,dtype=float)


class ConcordanceUncertainty(unittest.TestCase):
    def test_independent_frozen_R_matrix(self):
        spec=importlib.util.spec_from_file_location('ci_check',ROOT/'tools/check-concordance-intervals.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertTrue(module.check())

    def test_boundary_uses_stable_high_precision_arithmetic(self):
        fixtures=json.loads((ROOT/'tests/fixtures/concordance-intervals.json').read_text())
        for f in fixtures['fixtures']:
            if f['id'] not in ('near_identity','near_reversal'):
                continue
            got=concordance_interval(f['x'],f['y'])
            self.assertEqual(got['arithmetic'],'decimal80_boundary')
            self.assertEqual(got['status'],'ok')
        self.assertEqual(concordance_interval(X,Y)['arithmetic'],'float64_scaled')

    def test_precision_transition_fixtures(self):
        fixtures=json.loads((ROOT/'tests/fixtures/concordance-intervals-transition.json').read_text())
        for f in fixtures['fixtures']:
            x=[float.fromhex(v) for v in f['input_hex']['x']]
            y=[float.fromhex(v) for v in f['input_hex']['y']]
            got=concordance_interval(x,y)
            self.assertEqual(got['status'],'ok')
            self.assertEqual(got['arithmetic'],'decimal80_boundary')
            reference=next(v for v in f['runs'] if v['confidence']==.95)
            self.assertAlmostEqual(got['transformed_se'],float(reference['z_se']),places=12)

    def test_hand_variance_and_se(self):
        for method in ('z-transform','asymptotic'):
            got=concordance_interval(X,Y,method=method)
            self.assertEqual(got['status'],'ok')
            self.assertAlmostEqual(got['estimate'],.4,places=14)
            self.assertAlmostEqual(got['variance'],179/3125,places=14)
            self.assertAlmostEqual(got['se']**2,179/3125,places=14)
            self.assertLess(got['lower'],.4);self.assertGreater(got['upper'],.4)

    def test_nesting_and_point_compatibility(self):
        point=concordance(X,Y)
        for method in ('z-transform','asymptotic'):
            last=None
            for confidence in (.8,.9,.95,.975,.99):
                got=concordance_interval(X,Y,confidence,method)
                self.assertEqual(got['point'],point)
                self.assertIsNone(got['point']['confidence_interval'])
                if last:
                    self.assertLess(got['lower'],last['lower'])
                    self.assertGreater(got['upper'],last['upper'])
                    self.assertEqual(got['estimate'],last['estimate'])
                last=got

    def test_metamorphic_units_order_and_rater_swap(self):
        for method in ('z-transform','asymptotic'):
            expected=concordance_interval(X,Y,method=method)
            cases=[(Y,X),(X[::-1],Y[::-1]),(X+1e12,Y+1e12),
                   (X*1e300,Y*1e300),(X*1e-300,Y*1e-300),(-3*X,-3*Y)]
            for x,y in cases:
                got=concordance_interval(x,y,method=method)
                for key in ('estimate','lower','upper','se','variance'):
                    self.assertAlmostEqual(got[key],expected[key],places=12)

    def test_missing_pairs_use_shared_cohort(self):
        x=np.r_[X,np.nan,5,np.nan];y=np.r_[Y,3,np.nan,np.nan]
        got=concordance_interval(x,y);expected=concordance_interval(X,Y)
        for key in ('estimate','lower','upper','variance','se'):
            self.assertEqual(got[key],expected[key])
        self.assertEqual(got['n_complete'],12)
        self.assertEqual(got['point']['missing_either'],3)
        self.assertEqual(got['point']['retained_indices'],list(range(12)))

    def test_undefined_is_not_a_zero_width_or_fallback_interval(self):
        cases=[(X,X),(X,-X),(X,np.ones(12)),(np.ones(12),np.ones(12)),
               (np.tile([-1,-1,1,1],3),np.tile([-1,1,-1,1],3))]
        for x,y in cases:
            for method in ('z-transform','asymptotic'):
                got=concordance_interval(x,y,method=method)
                self.assertEqual(got['status'],'unavailable')
                self.assertTrue(got['reason'])
                for key in ('lower','upper','se','variance','transformed_se'):
                    self.assertIsNone(got[key])
                self.assertEqual(got['method'],method)

    def test_normal_limits_are_not_silently_clipped(self):
        x=[0,0,1,1,2,2,3,3,4,4];y=[0,1,1,1,2,3,2,4,4,3]
        got=concordance_interval(x,y,.99,'asymptotic')
        self.assertGreater(got['upper'],1)
        transformed=concordance_interval(x,y,.99,'z-transform')
        self.assertLess(transformed['upper'],1)
        self.assertEqual(got['estimate'],transformed['estimate'])

    def test_reject_invalid_confidence_method_and_minimum(self):
        for value in (True,np.bool_(False),.79,1,float('nan'),float('inf'),'0.95',None):
            with self.assertRaises(InputError):concordance_interval(X,Y,value)
        for method in ('auto','wald','',None,[],'Z-transform'):
            with self.assertRaises(InputError):concordance_interval(X,Y,method=method)
        with self.assertRaisesRegex(InputError,'at least 10'):
            concordance_interval(range(9),range(9))
        with self.assertRaises(InputError):concordance_interval(range(10),[float('inf')]*10)


if __name__=='__main__':unittest.main()
