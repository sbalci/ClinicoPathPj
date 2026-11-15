"""Independent summary/geometry fixtures and source-membership invariants."""
import copy
import importlib.util
import json
import sys
import unittest
from cpjtest import ROOT
import numpy as np

sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_lollipop import lollipop_core
from cpj_runtime import Factor,InputError

spec=importlib.util.spec_from_file_location('lollipop_reference',ROOT/'tools/check-lollipop-core.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


def factor(codes,levels=('A','B')):
    return Factor(np.array(codes),list(levels),False)


class LollipopCore(unittest.TestCase):
    def test_frozen_independent_R_and_ggplot2_geometry(self):
        report=checker.verify()
        self.assertEqual(report['configurations'],384)
        self.assertGreater(report['checks'],28000)

    def test_reference_mean_is_not_raw_mean(self):
        r=lollipop_core([10]*30+[50]*3+[52]*3,factor([0]*30+[1]*3+[2]*3,['A','B','C']))
        self.assertAlmostEqual(r['raw_summary']['mean'],16.833333333333332)
        self.assertAlmostEqual(r['reference_mean'],112/3)
        self.assertEqual(r['plotted_summary']['n'],3)
        self.assertEqual(r['raw_summary']['n'],36)

    def test_memberships_missing_levels_and_literal_NA(self):
        r=lollipop_core([1,99,None,5,7,3],factor([0,1,0,2,-1,0],['NA',None,'Other','unused']))
        self.assertEqual(r['retained_indices'],[0,3,5])
        self.assertEqual(r['unused_codes'],[3])
        self.assertEqual(r['missing_values'],1)
        self.assertEqual(r['missing_group'],2)
        self.assertEqual(r['points'][0]['source_indices'],[0,5])
        self.assertEqual(r['axis_levels'],['NA','Other'])

    def test_ties_stable_sort_and_horizontal_axis(self):
        r=lollipop_core([5,1,5,1],factor([0,0,1,1]),aggregation='none',
            sorting='value_desc',orientation='horizontal')
        self.assertEqual([p['source_indices'] for p in r['points']],[[0],[2],[1],[3]])
        self.assertEqual(r['highest_groups'],['A','B'])
        self.assertEqual(r['lowest_groups'],['A','B'])
        self.assertEqual(r['axis_levels'],['B','A'])
        self.assertEqual([p['slot'] for p in r['points']],[2,1,2,1])
        self.assertTrue(r['overplotting'])
        original=lollipop_core([5,1],factor([1,0]),aggregation='none',orientation='horizontal')
        self.assertEqual(original['axis_levels'],['A','B'])

    def test_group_aggregation_is_permutation_invariant(self):
        values=np.array([1,7,3,9,2]);codes=np.array([0,1,0,1,0]);permutation=[4,0,3,1,2]
        for mode in ('mean','median','sum'):
            a=lollipop_core(values,factor(codes),aggregation=mode)
            b=lollipop_core(values[permutation],factor(codes[permutation]),aggregation=mode)
            self.assertEqual([p['value'] for p in a['points']],[p['value'] for p in b['points']])
            membership=sorted(i for p in b['points'] for i in p['source_indices'])
            self.assertEqual(membership,list(range(5)))

    def test_shift_scale_and_reference_geometry(self):
        values=np.array([1.,7.,3.,9.]);groups=factor([0,1,0,1])
        for mode in ('mean','median','none'):
            a=lollipop_core(values,groups,aggregation=mode,baseline=-1)
            b=lollipop_core(values*2+100,groups,aggregation=mode,baseline=98)
            for p,q in zip(a['points'],b['points']):
                self.assertAlmostEqual(q['value'],p['value']*2+100)
                self.assertAlmostEqual(q['stem_end']-q['stem_start'],2*(p['stem_end']-p['stem_start']))
            self.assertAlmostEqual(b['reference_mean'],2*a['reference_mean']+100)
        tiny=lollipop_core(values*1e-100,groups)
        normal=lollipop_core(values,groups)
        self.assertAlmostEqual(tiny['raw_summary']['sd']/1e-100,normal['raw_summary']['sd'])

    def test_invalid_numeric_options_alignment_and_groups(self):
        invalid=[(['x',2],factor([0,1]),{}),([True,2],factor([0,1]),{}),
            ([1,float('inf')],factor([0,1]),{}),([1,2],factor([0]),{}),
            ([1,None],factor([0,1]),{}),([None,None],factor([0,1]),{}),
            ([1,2],factor([0,0]),{}),([1,2],factor([0,1]),{'aggregation':'bogus'}),
            ([1,2],factor([0,1]),{'sorting':[]}),([1,2],factor([0,1]),{'orientation':'diagonal'}),
            ([1,2],factor([0,1]),{'baseline':True}),([1,2],factor([0,1]),{'baseline':float('nan')})]
        for values,groups,options in invalid:
            with self.subTest(options=options,values=values),self.assertRaises(InputError):
                lollipop_core(values,groups,**options)

    def test_resource_and_derived_overflow_refusals(self):
        for values,groups,options in [
            ([1]*10001,factor([0,1]*5000+[0]),{'aggregation':'none'}),
            (list(range(51)),factor(range(51),[str(i) for i in range(51)]),{}),
            ([1e308,1e308,1],factor([0,0,1]),{'aggregation':'sum'}),
            ([-1e308,1e308],factor([0,1]),{}),
            ([1,1e308],factor([0,1]),{'baseline':-1e308})]:
            with self.subTest(options=options),self.assertRaises(InputError):
                lollipop_core(values,groups,**options)

    def test_json_serialization_and_no_inferential_fields(self):
        r=lollipop_core([1,2],factor([0,1]))
        json.dumps(r,allow_nan=False)
        self.assertIsNone(lollipop_core([1,2,2],factor([0,1,1]))['points'][0].get('stderr'))
        self.assertFalse({'p','lower','upper','effect'} & set(r))

    def test_extreme_constant_means_and_medians_remain_representable(self):
        for value in (1e308,1e-323,-1e308,0.):
            for aggregation in ('mean','median','none'):
                with self.subTest(value=value,aggregation=aggregation):
                    r=lollipop_core([value]*4,factor([0,0,1,1]),aggregation=aggregation)
                    self.assertEqual(r['raw_summary']['mean'],value)
                    self.assertEqual(r['reference_mean'],value)
                    self.assertTrue(all(p['value']==value for p in r['points']))

    def test_five_deliberate_corruptions_are_rejected(self):
        def corrupted(kind):
            def engine(*args,**kwargs):
                r=copy.deepcopy(lollipop_core(*args,**kwargs))
                if kind=='mean':r['reference_mean']+=1
                elif kind=='membership':r['points'][0]['source_indices']=[999]
                elif kind=='baseline':r['points'][0]['stem_start']+=1
                elif kind=='axis':r['axis_levels'].reverse()
                else:r['highest_groups']=['WRONG']
                return r
            return engine
        for kind in ('mean','membership','baseline','axis','ties'):
            with self.subTest(kind=kind),self.assertRaises(AssertionError):
                checker.verify(corrupted(kind))


if __name__=='__main__':
    unittest.main()
