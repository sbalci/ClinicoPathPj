"""Source inference, alignment and invalid-input gates for bounded estimation."""
import importlib.util
import json
import math
import sys
import unittest

import numpy as np

from cpjtest import ROOT
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_estimation import between_estimation, within_estimation
from cpj_runtime import Factor, InputError


def between(a=None, b=None, **kwargs):
    a = a if a is not None else [1., 3., 5., 8.]
    b = b if b is not None else [0., 2., 6., 10., 13.]
    return between_estimation(a+b, Factor(np.array([0]*len(a)+[1]*len(b)), ['A','B','unused']),
                              'A', 'B', **kwargs)


class EstimationCore(unittest.TestCase):
    def test_all_frozen_independent_R_targets(self):
        spec = importlib.util.spec_from_file_location('estimation_oracle', ROOT/'tools/check-estimation-core.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.verify()
        self.assertEqual(report['datasets'], 32)
        self.assertEqual(report['configurations'], 255)
        self.assertEqual(report['failures'], 0)

    def test_default_welch_and_explicit_student(self):
        welch, student = between(), between(equal_variances=True)
        self.assertEqual(welch['method'], 'welch')
        self.assertEqual(student['method'], 'student')
        self.assertEqual(student['df'], 7)
        self.assertNotAlmostEqual(welch['df'], student['df'])
        self.assertEqual(welch['difference'], student['difference'])

    def test_independent_contrast_reversal(self):
        values = [1.,3.,5.,8.,0.,2.,6.,10.,13.]
        groups = Factor(np.array([0]*4+[1]*5), ['A','B'])
        for equal in (False, True):
            a = between_estimation(values,groups,'A','B',equal_variances=equal)
            b = between_estimation(values,groups,'B','A',equal_variances=equal)
            for key in ('difference','statistic'):
                self.assertAlmostEqual(a[key],-b[key])
            self.assertAlmostEqual(a['lower'],-b['upper'])
            self.assertAlmostEqual(a['upper'],-b['lower'])
            self.assertAlmostEqual(a['p'],b['p'])

    def test_paired_orientation_and_covariance(self):
        a, b = [10.,12.,8.,15.,9.,18.], [8.,11.,9.,12.,7.,14.]
        result = within_estimation(a,b)
        reversed_ = within_estimation(b,a)
        independent = between(a,b)
        self.assertNotAlmostEqual(result['stderr'], independent['stderr'])
        self.assertEqual(result['df'], 5)
        self.assertAlmostEqual(result['p'], reversed_['p'])
        self.assertAlmostEqual(result['difference'], -reversed_['difference'])
        self.assertAlmostEqual(result['lower'], -reversed_['upper'])

    def test_internal_missingness_never_reorders_pairs(self):
        result = within_estimation([None,10,12,8,15,None,18,9], [1,8,11,None,12,7,14,7],
                                   subject_ids=['x','001','01','excluded','1',None,'a','b'])
        self.assertEqual(result['retained_indices'], [1,2,4,6,7])
        self.assertEqual(result['first_indices'], result['second_indices'])
        self.assertEqual(result['retained_subject_ids'], ['001','01','1','a','b'])
        self.assertEqual(result['missing_by_role'], dict(first=2,second=1))
        self.assertEqual(result['excluded_missing'],3)
        self.assertAlmostEqual(result['difference'],2.4)

    def test_independent_missing_audit_and_literal_NA_label(self):
        result = between_estimation([1,None,4,2,5,9,3],
            Factor(np.array([0,0,0,1,1,1,-1]), ['NA','B','unused']), 'NA','B')
        self.assertEqual(result['mapping']['first'],'NA')
        self.assertEqual(result['retained_indices'],[0,2,3,4,5])
        self.assertEqual(result['missing_by_role'],dict(outcome=1,group=1))

    def test_subject_ID_policy(self):
        for ids in (['x','x','y'], ['x',None,'y'], [1,2,3], ['','x','y'], ['x','y'], [[1],[2],[3]]):
            with self.subTest(ids=ids), self.assertRaises(InputError):
                within_estimation([1,2,4],[2,1,3],subject_ids=ids)
        self.assertEqual(within_estimation([1,2,4],[2,1,3],subject_ids=['001','01','1'])
                         ['retained_subject_ids'], ['001','01','1'])

    def test_zero_variance_is_not_infinite_significance(self):
        for result in (between([1]*4,[3]*5), between([0]*4,[0]*5),
                       within_estimation([1,2,4],[0,1,3]), within_estimation([1,2,4],[1,2,4])):
            self.assertEqual(result['status'],'degenerate')
            for key in ('stderr','df','statistic','p','lower','upper'):
                self.assertIsNone(result[key])
            json.dumps(result,allow_nan=False)

    def test_one_constant_group_is_supported(self):
        for equal in (False,True):
            result = between([4]*6,[-1,0,2,4,8],equal_variances=equal)
            self.assertEqual(result['status'],'ok')
            self.assertTrue(math.isfinite(result['p']))

    def test_small_samples_and_empty_data(self):
        for a,b in (([],[]),([1],[2,3]),([1,2],[3])):
            with self.assertRaises(InputError): between(a,b)
        for a,b in (([],[]),([1,2],[2,1]),([1,2,3],[2,1,None])):
            with self.assertRaises(InputError): within_estimation(a,b)

    def test_invalid_numeric_vectors(self):
        bad = ([True,2,3], ['1','2','3'], [1+0j,2,3], [[1,2,3]],
               [1,float('inf'),3], np.ma.array([1,2,3]), 1)
        for values in bad:
            with self.subTest(values=values), self.assertRaises(InputError):
                within_estimation(values,[1,3,2])
        with self.assertRaises(InputError): within_estimation([1,2,3],[1,2,3,4])
        with self.assertRaises(InputError): within_estimation([1,2,3]*33334,[1,2,4]*33334)

    def test_invalid_group_encodings_and_levels(self):
        for group in (Factor(np.array([0.,0.,1.,1.]),['A','B']),
                      Factor([False,0,1,1],['A','B']),
                      Factor(np.array([0,0,1,2]),['A','B']),
                      Factor(np.array([0,-2,1,1]),['A','B']),
                      Factor(np.array([0,0,1,1]),['A','A']),
                      Factor(np.array([0,1]),['A','B']), [0,0,1,1]):
            with self.subTest(group=group), self.assertRaises(InputError):
                between_estimation([1,2,3,4],group,'A','B')
        group = Factor(np.array([0,0,1,1]),['A','B'])
        for a,b in (('A','A'),('missing','B'),(None,'B')):
            with self.assertRaises(InputError): between_estimation([1,2,3,4],group,a,b)

    def test_no_implicit_third_group_exclusion(self):
        group = Factor(np.array([0,0,1,1,2]),['A','B','C'])
        with self.assertRaisesRegex(InputError,'exactly two'):
            between_estimation([1,2,3,4,5],group,'A','B')
        result = between_estimation([1,2,3,4,None],group,'A','B')
        self.assertEqual(result['excluded_missing'],1)

    def test_confidence_and_variance_parameter_validation(self):
        for confidence in (True,.49,1,float('nan'),float('inf'),'0.95'):
            with self.assertRaises(InputError): between(confidence=confidence)
            with self.assertRaises(InputError): within_estimation([1,2,3],[2,1,4],confidence=confidence)
        for value in (1,'False',None,np.bool_(True)):
            with self.assertRaises(InputError): between(equal_variances=value)
        for confidence in (.5,.999):
            self.assertEqual(between(confidence=confidence)['confidence'],confidence)

    def test_translation_and_scale_invariance(self):
        a,b = [1.,3.,5.,8.],[0.,2.,6.,10.,13.]
        original = between(a,b)
        for scale in (1e-100,1e100):
            result = between([x*scale for x in a],[x*scale for x in b])
            for key in ('difference','stderr','lower','upper'):
                self.assertAlmostEqual(result[key]/scale,original[key])
            self.assertAlmostEqual(result['p'],original['p'])
        shifted = between([x+1000 for x in a],[x+1000 for x in b])
        self.assertAlmostEqual(shifted['p'], original['p'])

    def test_precision_guard_and_exact_shifted_variance(self):
        a = 1e15+np.array([0,.125,.25,.375])
        b = 1e15+np.array([.125,.25,.375,.5])
        result = between(a.tolist(),b.tolist())
        self.assertEqual(result['status'],'degenerate')
        self.assertAlmostEqual(result['summaries']['first']['sd'],math.sqrt(5/192))

    def test_unsupported_numerical_range_is_explicit(self):
        for scale in (1e-200,1e200):
            with self.assertRaises(InputError):
                within_estimation([scale,2*scale,4*scale],[0,scale,3*scale])
        with self.assertRaises(InputError): between([-1e308,1e308],[-1e308,1e308])


if __name__ == '__main__':
    unittest.main()
