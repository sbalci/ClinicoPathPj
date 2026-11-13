"""Independent histogram/Student references, exact ties and refusal policies."""
import importlib.util
import json
import math
from fractions import Fraction
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
import cpj_histogram as engine
from cpj_runtime import InputError
spec=importlib.util.spec_from_file_location('histogram_oracle',ROOT/'tools/check-histogram-core.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)


class HistogramCore(unittest.TestCase):
    def test_independent_R_oracles_and_frozen_archive(self):
        result=oracle.verify()
        self.assertEqual(result['datasets'],21);self.assertEqual(result['configurations'],252)
        self.assertEqual(result['checks'],6538)
        self.assertEqual(result['fixture_sha256'],'54058633145b48688d2663908c9022f467b11c038dc8d4f706d2c72f570a5fe9')

    def test_exact_internal_and_outer_endpoint_ties(self):
        right=engine.histogram_core([0,1,2],breaks=[0,1,2],closure='right')
        left=engine.histogram_core([0,1,2],breaks=[0,1,2],closure='left')
        self.assertEqual([b['count'] for b in right['bins']],[2,1])
        self.assertEqual([b['count'] for b in left['bins']],[1,2])
        before,after=np.nextafter(1.,0.),np.nextafter(1.,2.)
        for closure,counts in [('right',[3,2]),('left',[2,3])]:
            got=engine.histogram_core([0,before,1,after,2],breaks=[0,1,2],closure=closure)
            self.assertEqual([b['count'] for b in got['bins']],counts)
            self.assertTrue(got['bins'][0]['lower_closed'])
            self.assertTrue(got['bins'][-1]['upper_closed'])

    def test_nonuniform_density_mass_and_empty_bins(self):
        got=engine.histogram_core([0,1,2,4],breaks=[0,1,2,3,4],closure='right')
        self.assertEqual([b['count'] for b in got['bins']],[2,1,0,1])
        uneven=engine.histogram_core([0,1,2,4],breaks=[0,1,4],closure='right')
        self.assertAlmostEqual(uneven['bins'][0]['density'],.5)
        self.assertAlmostEqual(uneven['bins'][1]['density'],1/6)
        self.assertEqual(sum(b['count'] for b in uneven['bins']),4)
        self.assertAlmostEqual(sum(b['proportion'] for b in uneven['bins']),1)
        self.assertAlmostEqual(sum(b['density']*(b['upper']-b['lower']) for b in uneven['bins']),1)

    def test_cohort_and_exact_retained_subject_identity(self):
        values=[1,None,2,3,np.nan];ids=['001',None,'01','1',None]
        for got in (engine.histogram_core(values,breaks=[0,2,4],closure='right',subject_ids=ids),
                    engine.one_sample_core(values,subject_ids=ids)):
            self.assertEqual(got['n_source'],5);self.assertEqual(got['n_complete'],3)
            self.assertEqual(got['excluded_missing'],2);self.assertEqual(got['retained_indices'],[0,2,3])
            self.assertEqual(got['retained_subject_ids'],['001','01','1'])
            self.assertEqual(got['summary']['median'],2)
            json.dumps(got,allow_nan=False)
        for ids in (['a','b','a'], ['a',None,'b'], ['a','b']):
            with self.assertRaises(InputError):engine.one_sample_core([1,2,3],subject_ids=ids)

    def test_invariance_permutation_shift_scale_and_reflection(self):
        x=np.array([-2.,-1,0,0,1,3]);edges=np.array([-3.,0,1,4])
        baseline=engine.histogram_core(x,breaks=edges,closure='right')
        counts=[b['count'] for b in baseline['bins']]
        for scale in (1e-100,1.,1e100):
            got=engine.histogram_core(x*scale,breaks=edges*scale,closure='right')
            self.assertEqual([b['count'] for b in got['bins']],counts)
            for b,a in zip(got['bins'],baseline['bins']):self.assertAlmostEqual(b['density']*scale,a['density'])
        shifted=engine.histogram_core(x+100,breaks=edges+100,closure='right')
        self.assertEqual([b['count'] for b in shifted['bins']],counts)
        permuted=engine.histogram_core(x[::-1],breaks=edges,closure='right')
        self.assertEqual(permuted['bins'],baseline['bins'])
        reflected=engine.histogram_core(-x,breaks=-edges[::-1],closure='left')
        self.assertEqual([b['count'] for b in reflected['bins']],counts[::-1])

    def test_one_sample_hand_calculation_two_sided_p_and_explicit_CI_targets(self):
        got=engine.one_sample_core([0,1,2],reference=.75)
        self.assertAlmostEqual(got['summary']['sd'],1)
        self.assertAlmostEqual(got['difference'],.25)
        self.assertAlmostEqual(got['stderr'],1/math.sqrt(3))
        self.assertEqual(got['df'],2)
        self.assertAlmostEqual(got['statistic'],math.sqrt(3)/4)
        # For df=2, two-sided t probability is 1-|t|/sqrt(t^2+2).
        self.assertAlmostEqual(got['p'],1-abs(got['statistic'])/math.sqrt(got['statistic']**2+2))
        for suffix in ('lower','upper'):
            self.assertAlmostEqual(got['difference_'+suffix],got['mean_'+suffix]-.75)
        self.assertNotIn('hedges_g',got)
        rational=engine.one_sample_core([0,1,2],reference=Fraction(3,4),confidence=Fraction(19,20))
        self.assertEqual(rational,got)

    def test_one_sample_reference_and_confidence_properties(self):
        x=np.array([1.,2,4,6,9])
        baseline=engine.one_sample_core(x,reference=2)
        shifted=engine.one_sample_core(x+100,reference=102)
        for key in ('difference','stderr','df','statistic','p','difference_lower','difference_upper'):
            self.assertAlmostEqual(shifted[key],baseline[key])
        reflected=engine.one_sample_core(-x,reference=-2)
        self.assertAlmostEqual(reflected['statistic'],-baseline['statistic'])
        self.assertAlmostEqual(reflected['difference_lower'],-baseline['difference_upper'])
        self.assertAlmostEqual(reflected['p'],baseline['p'])
        wider=engine.one_sample_core(x,reference=2,confidence=.999)
        self.assertLess(wider['mean_lower'],baseline['mean_lower'])
        self.assertGreater(wider['mean_upper'],baseline['mean_upper'])
        another=engine.one_sample_core(x,reference=-2)
        self.assertEqual(another['mean_lower'],baseline['mean_lower'])
        self.assertEqual(another['mean_upper'],baseline['mean_upper'])

    def test_singleton_and_constant_keep_points_without_fabricated_inference(self):
        single=engine.one_sample_core([3],reference=1)
        self.assertEqual(single['status'],'insufficient_n');self.assertEqual(single['difference'],2)
        self.assertIsNone(single['summary']['sd'])
        for values in ([0,0,0],[3,3,3],[1e14,1e14+.015625,1e14+.03125]):
            got=engine.one_sample_core(values)
            self.assertEqual(got['status'],'degenerate')
            for key in ('stderr','df','statistic','p','mean_lower','mean_upper','difference_lower','difference_upper'):
                self.assertIsNone(got[key])
            json.dumps(got,allow_nan=False)
        hist=engine.histogram_core([3],breaks=[2,4],closure='right')
        self.assertEqual(hist['bins'][0]['count'],1)

    def test_invalid_inputs_breaks_and_parameters(self):
        for values in ([],[None,np.nan],[1,True],[1,'2'],[1,float('inf')],np.array([[1,2]]),
                       np.array([1,2],dtype=bool),np.array([1+1j,2]),np.ma.array([1,2])):
            with self.subTest(values=str(values)),self.assertRaises(InputError):engine.one_sample_core(values)
        for reference in (None,True,'0',np.inf,np.nan,[],1+1j):
            with self.assertRaises(InputError):engine.one_sample_core([1,2,3],reference=reference)
        for confidence in (None,True,.49,1,np.inf,'0.95'):
            with self.assertRaises(InputError):engine.one_sample_core([1,2,3],confidence=confidence)
        for edges in ([0],[0,0,3],[0,3,2],[0,None,3],[0,np.inf],[-1e308,1e308]):
            with self.assertRaises(InputError):engine.histogram_core([1,2],breaks=edges,closure='right')
        for closure in (None,True,'Right','closed',[]):
            with self.assertRaises(InputError):engine.histogram_core([1,2],breaks=[0,3],closure=closure)
        with self.assertRaisesRegex(InputError,'cover every'):engine.histogram_core([0,3],breaks=[0,2],closure='right')

    def test_resource_and_numeric_range_guards(self):
        got=engine.histogram_core([0,.5,1],breaks=np.linspace(0,1,2001),closure='right')
        self.assertEqual(len(got['bins']),2000)
        with self.assertRaises(InputError):engine.histogram_core([0,1],breaks=np.linspace(0,1,2002),closure='right')
        with self.assertRaises(InputError):engine.one_sample_core(np.arange(100001))
        with self.assertRaisesRegex(InputError,'density'):engine.histogram_core([0,0],breaks=[0,1e-320],closure='right')
        with self.assertRaises(InputError):engine.one_sample_core([1e-200,2e-200,3e-200])
        with self.assertRaises(InputError):engine.one_sample_core([-1e308,1e308])
        with self.assertRaises(InputError):engine.one_sample_core([1e308],reference=-1e308)

    def test_independent_oracle_rejects_five_statistical_mutations(self):
        hist,mean=oracle.histogram_core,oracle.one_sample_core
        def bad_hist(kind):
            def call(*args,**kwargs):
                if kind=='closure':kwargs['closure']='left' if kwargs['closure']=='right' else 'right'
                result=hist(*args,**kwargs)
                if kind=='lost_count':result['bins'][0]['count']+=1
                return result
            return call
        def bad_mean(kind):
            def call(*args,**kwargs):
                result=mean(*args,**kwargs)
                if result['summary']['sd'] is not None and kind=='n_sd':
                    result['summary']['sd']*=math.sqrt((result['n_complete']-1)/result['n_complete'])
                if kind=='reference':result['difference']=result['summary']['mean']
                if kind=='one_tail' and result['p'] is not None:result['p']/=2
                return result
            return call
        for kind in ('closure','lost_count','n_sd','reference','one_tail'):
            target='histogram_core' if kind in ('closure','lost_count') else 'one_sample_core'
            changed=bad_hist(kind) if target=='histogram_core' else bad_mean(kind)
            with self.subTest(kind=kind),patch.object(oracle,target,changed):
                with self.assertRaises(AssertionError):oracle.verify()


if __name__=='__main__':unittest.main()
