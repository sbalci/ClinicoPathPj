"""General-moment uncertainty is a separately labelled source-only method."""
import importlib.util
import json
import math
import sys
import unittest
import numpy as np
from cpjtest import ROOT
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_concordance_empirical import empirical_concordance_interval
from cpj_concordance_uncertainty import concordance_interval
from cpj_concordance import concordance
from cpj_runtime import InputError
X=np.array([-1,-1,1,1]*3,dtype=float)
Y=np.array([-1,1,0,2]*3,dtype=float)


class EmpiricalConcordance(unittest.TestCase):
    def test_independent_R_and_MPFR_oracles(self):
        spec=importlib.util.spec_from_file_location('empirical_check',ROOT/'tools/check-concordance-empirical.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertTrue(module.check())

    def test_hand_influence_variance_and_distinct_method(self):
        got=empirical_concordance_interval(X,Y)
        self.assertAlmostEqual(got['estimate'],.4,places=14)
        self.assertAlmostEqual(got['variance'],23/625,places=14)
        self.assertAlmostEqual(got['mean_influence'],0,places=14)
        self.assertEqual(got['variance_method'],'empirical moment delta')
        self.assertNotEqual(got['variance'],concordance_interval(X,Y)['variance'])
        self.assertEqual(got['point'],concordance(X,Y))
        self.assertIsNone(got['point']['confidence_interval'])

    def test_zero_covariance_is_supported_when_variance_positive(self):
        x=np.tile([-1,-1,1,1],3);y=np.tile([-1,1,-1,1],3)
        got=empirical_concordance_interval(x,y)
        self.assertEqual(got['status'],'ok')
        self.assertEqual(got['estimate'],0.)
        self.assertAlmostEqual(got['variance'],1/12,places=14)
        self.assertEqual(concordance_interval(x,y)['status'],'unavailable')

    def test_units_swap_row_order_and_duplication(self):
        for method in ('empirical-z','empirical-normal'):
            base=empirical_concordance_interval(X,Y,method=method)
            for x,y in [(Y,X),(X[::-1],Y[::-1]),(X+1e12,Y+1e12),
                        (X*1e300,Y*1e300),(X*1e-300,Y*1e-300),(-3*X,-3*Y)]:
                got=empirical_concordance_interval(x,y,method=method)
                for key in ('estimate','variance','lower','upper'):
                    self.assertAlmostEqual(got[key],base[key],places=12)
            duplicated=empirical_concordance_interval(np.tile(X,2),np.tile(Y,2),method=method)
            self.assertAlmostEqual(duplicated['variance'],base['variance']/2,places=14)
            self.assertAlmostEqual(duplicated['se'],base['se']/math.sqrt(2),places=14)

    def test_overflow_safe_common_scaling(self):
        x=np.array([-.9,-.7,-.5,-.3,-.1,.1,.3,.5,.7,.9,.8,-.8])
        y=np.array([-.8,-.4,-.7,-.1,.1,-.1,.5,.3,.8,.6,.4,-.6])
        expected=empirical_concordance_interval(x,y)
        got=empirical_concordance_interval(x*1e308,y*1e308)
        self.assertEqual(got['status'],'ok')
        self.assertEqual(got['arithmetic'],'float64_scaled')
        for key in ('estimate','variance','se','lower','upper'):
            self.assertAlmostEqual(got[key],expected[key],places=12)

    def test_missing_pairs_preserve_shared_audit(self):
        got=empirical_concordance_interval(np.r_[X,np.nan,3,np.nan],np.r_[Y,2,np.nan,np.nan])
        base=empirical_concordance_interval(X,Y)
        self.assertEqual(got['point']['retained_indices'],list(range(12)))
        self.assertEqual(got['point']['missing_either'],3)
        for key in ('estimate','variance','lower','upper'):
            self.assertEqual(got[key],base[key])

    def test_confidence_nesting_and_normal_not_clipped(self):
        for method in ('empirical-z','empirical-normal'):
            low=empirical_concordance_interval(X,Y,.8,method)
            high=empirical_concordance_interval(X,Y,.99,method)
            self.assertEqual(low['estimate'],high['estimate'])
            self.assertEqual(low['variance'],high['variance'])
            self.assertLess(high['lower'],low['lower'])
            self.assertGreater(high['upper'],low['upper'])
        # The normal interval is explicitly unbounded; the transformed one is not.
        fixture=next(f for f in json.loads((ROOT/'tests/fixtures/concordance-empirical.json').read_text())['fixtures']
                     if f['id']=='minimum_boundary_n10')
        normal=empirical_concordance_interval(fixture['x'],fixture['y'],.99,'empirical-normal')
        transformed=empirical_concordance_interval(fixture['x'],fixture['y'],.99,'empirical-z')
        reference=next(v for v in fixture['expected']['mpfr256']['intervals'] if v['confidence']==.99)
        self.assertGreater(reference['normal'][1],1)
        self.assertAlmostEqual(normal['upper'],reference['normal'][1],places=12)
        self.assertGreater(normal['upper'],1)
        self.assertLess(transformed['upper'],1)

    def test_undefined_boundaries_and_zero_first_order_variance(self):
        for x,y in [(X,X),(X,-X),(X,np.ones(12)),(np.ones(12),np.ones(12)),
                    (np.ones(12),np.ones(12)*2)]:
            got=empirical_concordance_interval(x,y)
            self.assertEqual(got['status'],'unavailable')
            self.assertTrue(got['reason'])
            for key in ('variance','se','lower','upper'):
                self.assertIsNone(got[key])

    def test_invalid_options_and_design(self):
        for method in ('z-transform','asymptotic','auto',None,[]):
            with self.assertRaises(InputError):empirical_concordance_interval(X,Y,method=method)
        for confidence in (True,.79,1,float('nan'),'0.95'):
            with self.assertRaises(InputError):empirical_concordance_interval(X,Y,confidence)
        with self.assertRaises(InputError):empirical_concordance_interval(range(9),range(9))
        with self.assertRaises(InputError):empirical_concordance_interval([1]*10,[float('inf')]*10)


if __name__=='__main__':unittest.main()
