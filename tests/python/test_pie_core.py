"""Independent categorical/polar geometry, exact accumulation, identities and guards."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor, InputError
from cpj_pie import pie_core

spec = importlib.util.spec_from_file_location('pie_oracle',ROOT/'tools/check-pie-core.py')
oracle = importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
FIXTURES = json.loads(oracle.FIXTURE.read_text())['fixtures']


class PieCore(unittest.TestCase):
    def test_frozen_independent_R_and_actual_polar_build(self):
        result = oracle.verify()
        self.assertEqual(result['datasets'],12)
        self.assertEqual(result['fixture_sha256'],'478ff7b66b88b6a01cfa414c63b9c1ec9db278fc246466bbacaea3bd924668b7')

    def test_tiny_exact_counts_and_clockwise_anchors(self):
        got = pie_core(Factor(np.array([0,1]),['A','B']),weights=[1,3])
        a,b = got['cells']
        self.assertEqual((a['lower'],a['upper'],b['lower'],b['upper']),(.75,1,0,.75))
        self.assertEqual([c['count'] for c in got['cells']],[1,3])
        self.assertAlmostEqual(a['theta_center'],7*math.pi/4)
        self.assertAlmostEqual(a['anchor_x'],-math.sqrt(.5))
        self.assertAlmostEqual(a['anchor_y'],math.sqrt(.5))

    def test_expansion_permutation_and_scale_invariance(self):
        for f in FIXTURES[:5]:
            a,w = oracle.inputs(f);result=pie_core(a,weights=w)
            expanded=pie_core(Factor(np.repeat(a.codes,w),a.levels))
            self.assertEqual(result['cells'],expanded['cells'])
            reverse=pie_core(Factor(a.codes[::-1],a.levels),weights=w[::-1])
            self.assertEqual(result['cells'],reverse['cells'])
            scaled=pie_core(a,weights=np.array(w)*7)
            for before,after in zip(result['cells'],scaled['cells']):
                self.assertEqual(after['count'],7*before['count'])
                for key in ('proportion','lower','upper','theta_lower','theta_upper','anchor_x','anchor_y'):
                    self.assertEqual(before[key],after[key])

    def test_declared_zero_categories_and_single_active_circle(self):
        a=Factor(np.array([1,1,0]),['Zero','Only','Unused'])
        got=pie_core(a,weights=[2,3,0]);cells=got['cells']
        self.assertEqual([c['count'] for c in cells],[0,5,0])
        self.assertEqual([c['label'] for c in cells],a.levels)
        for c in (cells[0],cells[2]):
            self.assertEqual(c['lower'],c['upper']);self.assertIsNone(c['anchor_x'])
        self.assertEqual((cells[1]['theta_lower'],cells[1]['theta_upper']),(0,math.tau))

    def test_true_missing_level_and_literal_NA_keep_distinct(self):
        a=Factor(np.array([0,1,2,-1,0]),['NA',None,'Other'])
        got=pie_core(a,weights=[2,7,3,None,0])
        self.assertEqual(got['missing_outcome'],2)
        self.assertEqual(got['missing_frequency'],1)
        self.assertEqual(got['excluded_missing'],2)
        self.assertEqual(got['n_total'],5)
        self.assertEqual(got['n_complete'],3)
        self.assertEqual(got['missing_level_codes'],[1])
        self.assertEqual([c['label'] for c in got['cells']],['NA','Other'])

    def test_original_rows_and_exact_subject_labels(self):
        a=Factor(np.array([0,-1,1,0]),['A','B'])
        got=pie_core(a,subject_ids=['001',None,'01','1'])
        self.assertEqual(got['retained_indices'],[0,2,3])
        self.assertEqual(got['retained_subject_ids'],['001','01','1'])
        for ids in (['x',None,'x','y'],['x',None,None,'y'],['x',None,'','y']):
            with self.assertRaises(InputError):pie_core(a,subject_ids=ids)
        with self.assertRaises(InputError):pie_core(a,weights=[1]*4,subject_ids=['a','b','c','d'])

    def test_exact_integer_accumulation_and_limits(self):
        a=Factor(np.array([0,1,0]),['A','B'])
        got=pie_core(a,weights=[2**52-1,2**52-1,1])
        self.assertEqual(got['n_total'],2**53-1)
        self.assertEqual([c['count'] for c in got['cells']],[2**52,2**52-1])
        for w in ([2**52,2**52,1],[2**53,1,0]):
            with self.assertRaises(InputError):pie_core(a,weights=w)

    def test_bad_weights_refused_even_with_missing_factor(self):
        a=Factor(np.array([0,-1,1]),['A','B'])
        for w in ([1,-1,2],[1,.5,2],[1,float('inf'),2],[1,True,2],[1,'2',2],
                  [1,2],[[1,2,3]],np.ma.array([1,2,3])):
            with self.subTest(weights=str(w)),self.assertRaises(InputError):pie_core(a,weights=w)

    def test_empty_degenerate_and_resource_refusals(self):
        for a in (Factor(np.array([],dtype=int),['A']),Factor(np.array([-1]),['A']),
                  Factor(np.array([0]),[None]),Factor(np.array([2]),['A','B']),
                  Factor(np.array([0]),[str(i) for i in range(21)]),
                  Factor(np.array([0]),['A']+[None]*1000),
                  Factor(np.zeros(100001,dtype=int),['A']),
                  Factor(np.array([0.0]),['A']),Factor(np.ma.array([0]),['A'])):
            with self.subTest(levels=len(a.levels)),self.assertRaises(InputError):pie_core(a)
        with self.assertRaises(InputError):pie_core(Factor(np.array([0,1]),['A','B']),weights=[0,0])

    def test_polar_closure_and_no_gaps(self):
        for f in FIXTURES:
            a,w=oracle.inputs(f);cells=pie_core(a,weights=w)['cells']
            self.assertEqual(cells[0]['upper'],1);self.assertEqual(cells[-1]['lower'],0)
            self.assertAlmostEqual(sum(c['proportion'] for c in cells),1)
            for left,right in zip(cells,cells[1:]):self.assertEqual(left['lower'],right['upper'])

    def test_checker_rejects_four_corruptions(self):
        original=oracle.pie_core
        for kind in ('count','denominator','missingness','direction'):
            def changed(*args,**kwargs):
                got=copy.deepcopy(original(*args,**kwargs))
                if kind=='count':got['cells'][0]['count']+=1
                if kind=='denominator':got['cells'][0]['proportion']*=.5
                if kind=='missingness':got['n_complete']+=1
                if kind=='direction':got['cells'][0]['theta_lower']*=-1
                return got
            with patch.object(oracle,'pie_core',changed),self.assertRaises(AssertionError):oracle.verify()


if __name__=='__main__':unittest.main()
