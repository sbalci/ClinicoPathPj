"""Independent standardized-effect oracles, invariants and explicit failure boundaries."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor, InputError
import cpj_standardized as engine
from cpj_estimation import between_estimation, within_estimation

spec = importlib.util.spec_from_file_location('standardized_oracle', ROOT/'tools/check-standardized-effects.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


def independent(a,b,**kwargs):
    return engine.between_standardized(list(a)+list(b),
        Factor(np.array([0]*len(a)+[1]*len(b)),['First','Second','unused']),
        'First','Second',standardizer='pooled',**kwargs)


class StandardizedEffects(unittest.TestCase):
    def test_independent_R_package_and_mixture_oracles(self):
        result=oracle.verify()
        self.assertEqual(result['checks'],2060)
        self.assertEqual(result['configurations'],160)
        self.assertEqual(result['mixture_grid'],20)

    def test_hand_pooled_denominator_and_exact_small_sample_J(self):
        result=independent([1,5],[3,8])['standardized']
        pooled=math.sqrt(((1-3)**2+(5-3)**2+(3-5.5)**2+(8-5.5)**2)/2)
        self.assertAlmostEqual(result['standardizer_sd'],pooled)
        self.assertAlmostEqual(result['cohens_d'],-2.5/pooled)
        self.assertAlmostEqual(result['correction'],1/math.sqrt(math.pi))
        self.assertAlmostEqual(result['hedges_g'],result['cohens_d']/math.sqrt(math.pi))
        self.assertNotAlmostEqual(result['correction'],1-3/7)

    def test_explicit_estimands_and_no_raw_default_change(self):
        got=independent([1,3,5],[0,2,8,15])
        self.assertEqual(got['raw']['method'],'student')
        self.assertEqual(got['standardized']['estimand'],'population_delta')
        default=between_estimation([1,3,5,0,2,8,15],Factor(np.array([0,0,0,1,1,1,1]),['First','Second']),'First','Second')
        self.assertEqual(default['method'],'welch')
        self.assertNotIn('standardized',default)
        self.assertNotIn('g_lower',got['standardized'])
        self.assertNotIn('g_upper',got['standardized'])

    def test_paired_difference_denominator_and_covariance(self):
        a=[10,12,8,15,9,18];b=[8,11,9,12,7,14]
        got=engine.within_standardized(a,b,standardizer='difference')
        expected=np.mean(np.array(a)-b)/np.std(np.array(a)-b,ddof=1)
        self.assertAlmostEqual(got['standardized']['cohens_d'],expected)
        self.assertEqual(got['standardized']['estimand'],'population_delta_z')
        self.assertNotAlmostEqual(expected,(np.mean(a)-np.mean(b))/math.sqrt((np.var(a,ddof=1)+np.var(b,ddof=1))/2))
        self.assertEqual(got['raw'],within_estimation(a,b))

    def test_symmetry_confidence_nesting_and_scale_invariance(self):
        a=np.array([1,2,5,7.]);b=np.array([2,4,6,8,11.])
        baseline=independent(a,b)['standardized']
        reverse=independent(b,a)['standardized']
        for k in ('cohens_d','hedges_g'):self.assertAlmostEqual(reverse[k],-baseline[k])
        self.assertAlmostEqual(reverse['delta_lower'],-baseline['delta_upper'])
        self.assertAlmostEqual(reverse['delta_upper'],-baseline['delta_lower'])
        for scale in (1e-100,1e100):
            scaled=independent(a*scale,b*scale)['standardized']
            for k in ('cohens_d','hedges_g','delta_lower','delta_upper'):self.assertAlmostEqual(scaled[k],baseline[k])
        wider=independent(a,b,confidence=.999)['standardized']
        self.assertLess(wider['delta_lower'],baseline['delta_lower'])
        self.assertGreater(wider['delta_upper'],baseline['delta_upper'])

    def test_complete_pair_identity_and_exact_labels(self):
        got=engine.within_standardized([None,10,12,8,15,None,18,9],[1,8,11,None,12,7,14,7],
            standardizer='difference',subject_ids=['x','001','01','x','1',None,'a','b'])
        self.assertEqual(got['raw']['retained_indices'],[1,2,4,6,7])
        self.assertEqual(got['raw']['retained_subject_ids'],['001','01','1','a','b'])
        with self.assertRaises(InputError):
            engine.within_standardized([1,2,3],[2,0,2],standardizer='difference',subject_ids=['x','x','z'])

    def test_invalid_standardizers_and_inputs(self):
        for value in (None,True,1,[],np.array(['pooled']), 'welch','marginal'):
            with self.assertRaises(InputError):
                engine.between_standardized([1,2,3,4],Factor(np.array([0,0,1,1]),['a','b']),
                    'a','b',standardizer=value)
            with self.assertRaises(InputError):
                engine.within_standardized([1,2,4],[0,1,2],standardizer=value)
        for a,b in (([1,2],[0,1]),([1,float('inf'),3],[1,2,4]),([True,2,3],[1,2,4])):
            with self.assertRaises(InputError):engine.within_standardized(a,b,standardizer='difference')
        with self.assertRaises(InputError):independent([1,2],[3,4],confidence=True)

    def test_degenerate_has_no_invented_effect_or_limits(self):
        for result in (independent([1,1,1],[3,3,3]),
                       engine.within_standardized([1,2,4],[0,1,3],standardizer='difference')):
            out=result['standardized']
            self.assertEqual(out['status'],'degenerate')
            for key in ('cohens_d','hedges_g','correction','standardizer_sd','delta_lower','delta_upper'):
                self.assertIsNone(out[key])
            json.dumps(result,allow_nan=False)

    def test_out_of_range_keeps_points_with_explicit_null_interval(self):
        result=independent([100,101,102],[0,1,2])
        out=result['standardized']
        self.assertEqual(result['raw']['status'],'ok')
        self.assertEqual(out['status'],'interval_unavailable')
        self.assertTrue(math.isfinite(out['cohens_d']))
        self.assertIsNone(out['delta_lower']);self.assertIsNone(out['delta_upper'])
        self.assertIn('qualified numerical range',out['reason'])
        json.dumps(result,allow_nan=False)

    def test_solver_failures_preserve_points_without_fallback(self):
        with patch.object(engine.nct,'cdf',return_value=float('nan')):
            got=independent([1,3,5],[0,2,4,8])['standardized']
        self.assertEqual(got['status'],'interval_unavailable')
        self.assertIsNone(got['ncp_lower'])
        self.assertTrue(math.isfinite(got['hedges_g']))
        with patch.object(engine,'brentq',side_effect=RuntimeError('programming error')):
            with self.assertRaises(RuntimeError):independent([1,3,5],[0,2,4,8])
        with patch.object(engine,'brentq',return_value=(0,SimpleNamespace(converged=True))):
            got=independent([1,3,5],[0,2,4,8])['standardized']
        self.assertEqual(got['status'],'interval_unavailable')
        self.assertIn('probability check',got['reason'])
        original_brentq=engine.brentq
        def exhausted(*args,**kwargs):
            kwargs['maxiter']=0
            return original_brentq(*args,**kwargs)
        with patch.object(engine,'brentq',side_effect=exhausted):
            got=independent([1,3,5],[0,2,4,8])['standardized']
        self.assertEqual(got['status'],'interval_unavailable')
        self.assertIn('did not converge',got['reason'])
        self.assertIsNone(got['delta_upper'])

    def test_frozen_oracle_rejects_five_mutations(self):
        original=engine._standardize
        def mutated(kind):
            def run(raw,standardizer):
                result=copy.deepcopy(original(raw,standardizer));out=result['standardized']
                if out['status']!='ok':return result
                if kind=='reference_SD' and raw['design']=='independent':
                    out['standardizer_sd']=raw['summaries']['second']['sd']
                    out['cohens_d']=raw['difference']/out['standardizer_sd']
                elif kind=='approximate_J':
                    out['correction']=1-3/(4*raw['df']-1)
                    out['hedges_g']=out['correction']*out['cohens_d']
                elif kind=='scaled_delta_interval':
                    out['delta_lower']*=out['correction'];out['delta_upper']*=out['correction']
                elif kind=='reversed_contrast':out['cohens_d']*=-1
                elif kind=='lost_pair_covariance' and raw['design']=='paired':
                    out['standardizer_sd']=math.sqrt(sum(raw['summaries'][k]['sd']**2 for k in ('first','second')))
                    out['cohens_d']=raw['difference']/out['standardizer_sd']
                return result
            return run
        for kind in ('reference_SD','approximate_J','scaled_delta_interval','reversed_contrast','lost_pair_covariance'):
            with self.subTest(kind=kind),patch.object(engine,'_standardize',side_effect=mutated(kind)):
                with self.assertRaises(AssertionError):oracle.verify()


if __name__=='__main__':unittest.main()
