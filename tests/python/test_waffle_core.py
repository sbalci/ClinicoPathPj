"""Independent waffle allocations, identities, geometry, mutation and refusal gates."""
import copy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_runtime import Factor, InputError
from cpj_waffle import waffle_core

spec = importlib.util.spec_from_file_location('waffle_oracle', ROOT/'tools/check-waffle-core.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


def factor(codes, labels=('A','B','C')):
    return Factor(np.array(codes, dtype=int), list(labels))


class WaffleCore(unittest.TestCase):
    def test_independent_R_allocation_and_actual_waffle_geometry(self):
        result = oracle.verify()
        self.assertEqual(result['configurations'], 140)
        self.assertEqual(result['baseline_matching_panels'], 150)
        self.assertEqual(result['baseline_truncation_panels'], 20)
        self.assertEqual(result['fixture_sha256'],
            '9d3efae5702e048df498a9b5cc687914ee8b64f6cc403938a6525b682769b642')

    def test_tied_remainders_and_no_addition_branch(self):
        got = waffle_core(factor([0,1,2]), weights=[1,1,1])
        self.assertEqual([c['tiles'] for c in got['panels'][0]['cells']], [33,33,34])
        for counts in ([29,57,14], [58,21,21], [0,100,0]):
            got = waffle_core(factor([0,1,2]), weights=counts)
            self.assertEqual([c['tiles'] for c in got['panels'][0]['cells']], list(counts))

    def test_fraction_oracle_extreme_valid_counts(self):
        for counts in ([2**52,2**52-2,1], [1,2**53-3,1], [100,100,100], [1,3,196]):
            total = sum(counts)
            quotas = [Fraction(100*c,total) for c in counts]
            floors = [int(q) for q in quotas]
            residual = 100-sum(floors)
            order = sorted(range(3), key=lambda i: (quotas[i]-floors[i],i), reverse=True)
            expected = [v+int(i in order[:residual]) for i,v in enumerate(floors)]
            got = waffle_core(factor([0,1,2]), weights=counts)
            self.assertEqual(got['n_total'], total)
            self.assertEqual([c['tiles'] for c in got['panels'][0]['cells']], expected)
            self.assertEqual(len(got['panels'][0]['geometry']), 100)

    def test_rare_and_zero_categories_are_audited(self):
        got = waffle_core(factor([0,1]), weights=[1,999])
        cells = got['panels'][0]['cells']
        self.assertEqual([c['tiles'] for c in cells], [0,100,0])
        self.assertTrue(cells[0]['omitted_positive'])
        self.assertFalse(cells[2]['omitted_positive'])
        self.assertEqual(cells[0]['count'], 1)
        self.assertEqual(cells[0]['proportion'], .001)
        self.assertAlmostEqual(sum(c['allocation_error'] for c in cells), 0)

    def test_facets_have_separate_denominators_and_inactive_levels(self):
        got = waffle_core(factor([0,1,0,1,2]), weights=[1,3,90,10,0],
            facet=factor([0,0,1,1,2], ['Small','Large','Zero','Unused']))
        self.assertEqual(got['inactive_facet_codes'], [2,3])
        self.assertEqual(got['n_total'], 104)
        self.assertEqual([p['n_total'] for p in got['panels']], [4,100])
        self.assertEqual([[c['tiles'] for c in p['cells']] for p in got['panels']],
            [[25,75,0],[90,10,0]])
        self.assertEqual([p['retained_indices'] for p in got['panels']], [[0,1],[2,3]])

    def test_missingness_union_literal_NA_and_subject_identity(self):
        got = waffle_core(factor([0,1,2,-1,0,2], ['NA',None,'Other']),
            facet=factor([0,0,1,-1,1,0], ['NA',None]),
            subject_ids=['001',None,None,None,None,'01'])
        self.assertEqual(got['retained_indices'], [0,5])
        self.assertEqual(got['retained_subject_ids'], ['001','01'])
        self.assertEqual((got['missing_group'],got['missing_facet'],got['excluded_missing']),
            (2,3,4))
        self.assertEqual(got['panels'][0]['label'], 'NA')
        self.assertEqual([c['label'] for c in got['panels'][0]['cells']], ['NA','Other'])
        for ids in (['x','x'], ['x',None], ['x','']):
            with self.assertRaises(InputError):
                waffle_core(factor([0,1]), subject_ids=ids)
        with self.assertRaises(InputError):
            waffle_core(factor([0,1]), weights=[1,1], subject_ids=['a','b'])

    def test_frequency_expansion_permutation_and_scaling(self):
        args = dict(group=factor([0,1,2,1]),weights=np.array([2,3,5,7]),
            facet=factor([0,0,1,1], ['Small','Large']))
        original = waffle_core(**args)
        expanded = waffle_core(Factor(np.repeat(args['group'].codes,args['weights']),args['group'].levels),
            facet=Factor(np.repeat(args['facet'].codes,args['weights']),args['facet'].levels))
        reverse = waffle_core(Factor(args['group'].codes[::-1],args['group'].levels),
            weights=args['weights'][::-1],facet=Factor(args['facet'].codes[::-1],args['facet'].levels))
        scaled = waffle_core(**dict(args,weights=args['weights']*17))
        for before,after,back,bigger in zip(original['panels'],expanded['panels'],
                reverse['panels'],scaled['panels']):
            self.assertEqual(before['cells'],after['cells'])
            self.assertEqual(before['cells'],back['cells'])
            self.assertEqual(before['geometry'],bigger['geometry'])
            self.assertEqual(bigger['n_total'],before['n_total']*17)

    def test_geometry_flip_partial_column_and_boundaries(self):
        a = factor([0,1])
        for rows in (1,5,7,10,100):
            standard = waffle_core(a,rows=rows)['panels'][0]['geometry']
            flipped = waffle_core(a,rows=rows,flip=True)['panels'][0]['geometry']
            self.assertEqual(len({(t['x'],t['y']) for t in standard}),100)
            self.assertEqual((standard[0]['x'],standard[0]['y']),(1,1))
            self.assertEqual((standard[-1]['x'],standard[-1]['y']),
                (99//rows+1,99%rows+1))
            for t,u in zip(standard,flipped):
                self.assertEqual((t['x'],t['y']),(u['y'],u['x']))
                self.assertEqual(t['xmax']-t['xmin'],1)
                self.assertEqual(t['ymax']-t['ymin'],1)

    def test_invalid_weights_even_on_missing_roles(self):
        a = factor([0,-1,1])
        for weights in ([1,-1,2],[1,.5,2],[1,float('inf'),2],[1,True,2],
                [1,'2',2],[1,2],[[1,2,3]],np.ma.array([1,2,3]),
                [2**53,0,1],[2**52,0,2**52],[0,None,0]):
            with self.subTest(weights=str(weights)),self.assertRaises(InputError):
                waffle_core(a,weights=weights)

    def test_invalid_factors_options_and_resources(self):
        for a in (factor([]),factor([-1]),factor([0],[None]),
                factor([3]),factor([0],[str(i) for i in range(21)]),
                factor([0],['A']+[None]*1000),factor([0]*100001),
                Factor(np.array([0.]),['A']),Factor(np.ma.array([0]),['A'])):
            with self.subTest(size=len(a.codes)),self.assertRaises(InputError):
                waffle_core(a)
        for rows in (0,101,1.5,True,'5',None):
            with self.subTest(rows=rows),self.assertRaises(InputError):
                waffle_core(factor([0]),rows=rows)
        for flip in (0,1,None,'false'):
            with self.assertRaises(InputError):waffle_core(factor([0]),flip=flip)
        for facet in (factor([0]),factor([0,1],[str(i) for i in range(9)]),
                factor([-1,-1]),factor([0,0],[None])):
            with self.assertRaises(InputError):waffle_core(factor([0,1]),facet=facet)

    def test_bounded_output_without_observation_expansion(self):
        got = waffle_core(factor([0]*8),weights=[10**12]*8,
            facet=factor(list(range(8)),[str(i) for i in range(8)]))
        self.assertEqual(sum(len(p['geometry']) for p in got['panels']),800)
        self.assertEqual(got['n_total'],8*10**12)
        json.dumps(got,allow_nan=False)

    def test_checker_rejects_five_corruptions(self):
        original = oracle.waffle_core
        for kind in ('count','denominator','allocation','geometry','missingness'):
            def changed(*args,**kwargs):
                got = copy.deepcopy(original(*args,**kwargs))
                if kind=='count':got['panels'][0]['cells'][0]['count']+=1
                if kind=='denominator':got['panels'][0]['n_total']+=1
                if kind=='allocation':got['panels'][0]['cells'][0]['tiles']+=1
                if kind=='geometry':got['panels'][0]['geometry'][0]['x']+=1
                if kind=='missingness':got['n_complete']+=1
                return got
            with patch.object(oracle,'waffle_core',changed),self.assertRaises(AssertionError):
                oracle.verify()


if __name__ == '__main__':
    unittest.main()
