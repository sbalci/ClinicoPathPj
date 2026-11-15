"""Fixed-null independent reference, gating, support, numeric and identity tests."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor, InputError
from cpj_pie import pie_core
from cpj_pie_gof import pie_gof

s=importlib.util.spec_from_file_location('pie_gof_oracle',ROOT/'tools/check-pie-gof-core.py')
oracle=importlib.util.module_from_spec(s);s.loader.exec_module(oracle)
FIXTURES=json.loads(oracle.FIXTURE.read_text())['fixtures']


class PieGoodnessOfFit(unittest.TestCase):
    def test_frozen_independent_R_tests_and_baseline_subtitles(self):
        r=oracle.verify();self.assertEqual(r['datasets'],18);self.assertEqual(r['configurations'],72)
        self.assertEqual(r['baseline_subtitle_checks'],12)
        self.assertEqual(r['fixture_sha256'],'13b588b4ab5dc1de3bcaee1771679944d1c479f41389029706c356a6af62d240')

    def test_tiny_arithmetic_and_closed_form_tail(self):
        a=Factor(np.array([0,1,2]),['A','B','C'])
        g=pie_gof(a,weights=[1,2,3],enabled=True)['gof']
        self.assertEqual(g['statistic'],1);self.assertEqual(g['df'],2)
        self.assertAlmostEqual(g['p'],math.exp(-.5))
        self.assertEqual([r['contribution'] for r in g['rows']],[.5,0,.5])
        self.assertTrue(g['sparse_warning']);self.assertEqual(g['expected_below5'],3)

    def test_inference_off_does_not_parse_or_calculate(self):
        a,w=oracle.inputs(FIXTURES[0])
        with (patch('cpj_pie_gof._probabilities',side_effect=AssertionError('parsed')),
              patch('cpj_pie_gof.chi2.sf',side_effect=AssertionError('test called'))):
            result=pie_gof(a,weights=w,ratios='stale invalid text')
        self.assertEqual(result['descriptives'],pie_core(a,weights=w))
        self.assertEqual(result['gof']['rows'],[])
        for name in ('method','statistic','df','p','minimum_expected'):self.assertIsNone(result['gof'][name])

    def test_zero_count_null_support_and_one_category_unavailability(self):
        a=Factor(np.array([0,1]),['A','B','Zero'])
        g=pie_gof(a,weights=[12,8],enabled=True)['gof']
        self.assertEqual(g['df'],2);self.assertAlmostEqual(g['statistic'],11.2)
        self.assertEqual([r['observed'] for r in g['rows']],[12,8,0])
        self.assertAlmostEqual(sum(r['expected'] for r in g['rows']),20)
        g=pie_gof(Factor(np.array([0]),['Only']),enabled=True)['gof']
        self.assertEqual(g['status'],'unavailable');self.assertEqual(g['reason'],'one_declared_category')
        self.assertIsNone(g['p']);self.assertIsNone(g['df']);self.assertIsNone(g['rows'][0]['contribution'])

    def test_labelled_ratios_follow_reordering_and_scale(self):
        a=Factor(np.array([0,1,2]),['A','B','C'])
        ratios={'C':3,'A':1,'B':2}
        first=pie_gof(a,weights=[20,40,60],enabled=True,ratios=ratios)['gof']
        self.assertEqual(first['statistic'],0);self.assertEqual(first['p'],1)
        second=pie_gof(Factor(np.array([2,0,1]),['B','C','A']),weights=[20,40,60],enabled=True,ratios=ratios)['gof']
        self.assertEqual(first['statistic'],second['statistic']);self.assertEqual(first['p'],second['p'])
        for multiplier in (1e-200,1e200):
            got=pie_gof(a,weights=[20,40,60],enabled=True,ratios={k:v*multiplier for k,v in ratios.items()})['gof']
            for key in ('statistic','df','p'):self.assertAlmostEqual(first[key],got[key])

    def test_exact_expected_five_boundary_and_no_binomial_switch(self):
        a=Factor(np.array([0,1]),['A','B'])
        self.assertFalse(pie_gof(a,weights=[5,5],enabled=True)['gof']['sparse_warning'])
        sparse=pie_gof(a,weights=[4,1],enabled=True)['gof']
        self.assertEqual(sparse['method'],'pearson_chi_square_gof')
        self.assertEqual(sparse['status'],'sparse_approximation')
        self.assertAlmostEqual(sparse['statistic'],1.8)
        self.assertNotAlmostEqual(sparse['p'],.375)  # Exact two-sided binomial p.

    def test_ratios_reject_invalid_domain_and_inexact_support(self):
        a=Factor(np.array([0,1]),['01','1','Zero'])
        for ratios in ([],[1,1,1],{}, {'01':1,'1':1},{'01':1,'1':1,'Zero':1,'extra':1},
                       {'01':1,'1':True,'Zero':1},{'01':1,'1':'1','Zero':1},
                       {'01':1,'1':0,'Zero':1},{'01':1,'1':-1,'Zero':1},
                       {'01':1,'1':float('inf'),'Zero':1},{'01':1,'1':float('nan'),'Zero':1}):
            with self.subTest(ratios=ratios),self.assertRaises(InputError):pie_gof(a,enabled=True,ratios=ratios)
        for enabled in (None,1,'yes'):
            with self.assertRaises(InputError):pie_gof(a,enabled=enabled)

    def test_large_ratios_underflow_and_nonfinite_statistic_guards(self):
        a=Factor(np.array([0,1]),['A','B'])
        g=pie_gof(a,weights=[10,10],enabled=True,ratios={'A':1e308,'B':1e308})['gof']
        self.assertEqual(g['statistic'],0);self.assertEqual(g['p'],1)
        with self.assertRaises(InputError):pie_gof(a,enabled=True,ratios={'A':1e-320,'B':1e308})
        with self.assertRaises(InputError):pie_gof(a,weights=[10**15,1],enabled=True,ratios={'A':1e-320,'B':1})

    def test_missing_levels_id_audit_and_descriptives_are_unchanged(self):
        a=Factor(np.array([0,1,2,-1,0]),['NA',None,'Other'])
        ids=['001',None,'01',None,'1']
        result=pie_gof(a,subject_ids=ids,enabled=True,ratios={'NA':2,'Other':1})
        self.assertEqual(result['descriptives'],pie_core(a,subject_ids=ids))
        self.assertEqual(result['descriptives']['retained_subject_ids'],['001','01','1'])
        self.assertEqual([r['label'] for r in result['gof']['rows']],['NA','Other'])
        self.assertEqual(result['gof']['statistic'],0)

    def test_frozen_checker_rejects_five_corruptions(self):
        original=oracle.pie_gof
        for kind in ('statistic','df','p','expected','support'):
            def changed(*args,**kwargs):
                got=copy.deepcopy(original(*args,**kwargs));g=got['gof']
                if kwargs.get('enabled') and g['statistic'] is not None:
                    if kind=='statistic':g['statistic']+=1
                    if kind=='df':g['df']+=1
                    if kind=='p':g['p']=.12345
                    if kind=='expected':g['rows'][0]['expected']+=1
                    if kind=='support':g['rows']=g['rows'][:-1]
                return got
            with patch.object(oracle,'pie_gof',changed),self.assertRaises(AssertionError):oracle.verify()


if __name__=='__main__':unittest.main()
