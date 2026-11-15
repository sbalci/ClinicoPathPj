"""Independent survival oracle, risk-set identities, boundaries and refusals."""
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
from cpj_kaplan_meier import kaplan_meier_core
from cpj_runtime import InputError

spec=importlib.util.spec_from_file_location('km_oracle',ROOT/'tools/check-kaplan-meier-core.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
FIXTURES=json.loads(oracle.FIXTURE.read_text())['fixtures']


class KaplanMeierCore(unittest.TestCase):
    def test_frozen_independent_survival_and_poisson_reference(self):
        result=oracle.verify()
        self.assertEqual(result['configurations'],156)
        self.assertEqual(result['datasets'],26)
        self.assertEqual(result['fixture_sha256'],
            '029cb9c667506eef572bb7b94f36950a9df98e20483e53332fba3bc22891140e')

    def test_hand_risk_sets_ties_greenwood_and_query_intervals(self):
        got=kaplan_meier_core([1,2,2,3],[1,1,0,0],queries=[3,0,2,1,1.5,4,2])
        curve=got['curve']
        self.assertEqual([r['n_risk'] for r in curve],[4,3,1])
        self.assertEqual([r['events'] for r in curve],[1,1,0])
        self.assertEqual([r['censored'] for r in curve],[0,1,1])
        self.assertEqual([r['survival'] for r in curve],[.75,.5,.5])
        self.assertAlmostEqual(curve[1]['greenwood'],.25)
        self.assertEqual(curve[1]['se'],.25)
        self.assertEqual(got['median']['estimate'],2)
        self.assertEqual(got['rate']['person_time'],8)
        self.assertEqual(got['rate']['estimate'],.25)
        self.assertEqual(got['omitted_timepoints'],[4])
        rows=got['selected']
        self.assertEqual([r['time'] for r in rows],[0,1,1.5,2,3])
        self.assertEqual([r['n_risk'] for r in rows],[4,4,3,3,1])
        self.assertEqual([r['events'] for r in rows],[0,1,0,1,0])
        self.assertEqual([r['cumulative_events'] for r in rows],[0,1,1,2,2])

    def test_origin_terminal_zero_and_zero_exposure(self):
        got=kaplan_meier_core([0,0,1],[1,0,1],queries=[0,1,2])
        self.assertAlmostEqual(got['selected'][0]['survival'],2/3)
        self.assertEqual(got['selected'][0]['n_risk'],3)
        last=got['selected'][-1]
        self.assertEqual((last['survival'],last['n_risk'],last['events']),(0,0,0))
        self.assertEqual(last['status'],'terminal_zero_extension')
        for field in ('se','lower','upper'):self.assertIsNone(last[field])
        for event in (0,1):
            got=kaplan_meier_core([0],[event],queries=[0,1])
            self.assertEqual(got['rate']['status'],'unavailable_zero_person_time')
            for field in ('estimate','lower','upper'):self.assertIsNone(got['rate'][field])
            self.assertEqual(got['curve'][0]['survival'],1-event)

    def test_half_survival_midpoint_and_terminal_plateau_rules(self):
        middle=kaplan_meier_core([1,2,4,8],[1,1,0,1])
        terminal=kaplan_meier_core([1,2,7,9],[1,1,0,0])
        self.assertEqual(middle['median']['estimate'],5)
        self.assertEqual(terminal['median']['estimate'],2)
        self.assertEqual(kaplan_meier_core([1,2],[1,1])['median']['estimate'],1.5)

    def test_all_censored_and_reverse_followup_without_fallback(self):
        censored=kaplan_meier_core([1,2,3,4],[0]*4,queries=[0,1,4,5])
        self.assertTrue(all(r['survival']==1 and r['lower'] is None and r['upper'] is None
                            for r in censored['curve']))
        self.assertTrue(all(v is None for v in censored['median'].values()))
        self.assertEqual(censored['reverse']['median']['estimate'],2.5)
        self.assertEqual(censored['rate']['estimate'],0)
        self.assertEqual(censored['rate']['lower'],0)
        self.assertGreater(censored['rate']['upper'],0)
        events=kaplan_meier_core([1,2,3,4],[1]*4)
        self.assertTrue(all(v is None for v in events['reverse']['median'].values()))

    def test_timefix_transitive_chains_and_raw_person_time(self):
        times=[1e8,1e8+1,1e8+2,1e8+8]
        fixed=kaplan_meier_core(times,[1,0,1,0])
        exact=kaplan_meier_core(times,[1,0,1,0],timefix=False)
        self.assertEqual(fixed['effective_times'],[1e8,1e8,1e8,1e8+8])
        self.assertEqual(fixed['timefix_changed_rows'],2)
        self.assertEqual(len(exact['curve']),4)
        self.assertEqual(len(fixed['curve']),2)
        self.assertEqual(fixed['rate']['person_time'],sum(times))
        tiny=kaplan_meier_core([0,1e-9,2e-9],[1,0,1])
        self.assertEqual(tiny['effective_times'],[0,0,0])
        self.assertGreater(tiny['rate']['person_time'],0)

    def test_complete_pair_union_and_original_subject_labels(self):
        got=kaplan_meier_core([0,None,2,3,None],[1,0,None,0,None],
            subject_ids=['001',None,None,'01',None])
        self.assertEqual((got['missing_time'],got['missing_event'],got['excluded_missing']),(2,2,3))
        self.assertEqual(got['retained_indices'],[0,3])
        self.assertEqual(got['retained_subject_ids'],['001','01'])
        for ids in (['x','x'],['x',None],['x',''],np.ma.array(['x','y'])):
            with self.assertRaises(InputError):kaplan_meier_core([1,2],[1,0],subject_ids=ids)

    def test_permutation_unit_declaration_and_explicit_time_scaling(self):
        t=np.array([1.,2.,2.,4.,8.]);e=np.array([1,1,0,0,1])
        original=kaplan_meier_core(t,e,timefix=False)
        reverse=kaplan_meier_core(t[::-1],e[::-1],timefix=False)
        self.assertEqual(original['curve'],reverse['curve'])
        declared=kaplan_meier_core(t,e,timefix=False,unit='years')
        self.assertEqual(original['curve'],declared['curve'])
        self.assertEqual(original['rate'],declared['rate'])
        scaled=kaplan_meier_core(t*7,e,timefix=False)
        for before,after in zip(original['curve'],scaled['curve']):
            self.assertEqual(after['time'],before['time']*7)
            self.assertEqual(after['survival'],before['survival'])
            self.assertEqual(after['se'],before['se'])
        self.assertEqual(scaled['rate']['person_time'],7*original['rate']['person_time'])
        for key in ('estimate','lower','upper'):
            self.assertAlmostEqual(scaled['rate'][key],original['rate'][key]/7)

    def test_all_reference_count_probability_and_interval_identities(self):
        for f in FIXTURES:
            got=kaplan_meier_core(**oracle.inputs(f))
            for curve in (got['curve'],got['reverse']['curve']):
                risk=got['n_complete'];previous=1
                for row in curve:
                    self.assertEqual(row['n_risk'],risk)
                    self.assertLessEqual(row['survival'],previous)
                    self.assertGreaterEqual(row['survival'],0)
                    risk-=row['events']+row['censored'];previous=row['survival']
                    if 0<row['survival']<1:
                        self.assertLessEqual(row['lower'],row['survival'])
                        self.assertGreaterEqual(row['upper'],row['survival'])
                        self.assertAlmostEqual(row['se']**2,row['survival']**2*row['greenwood'])
                self.assertEqual(risk,0)
            self.assertEqual(sum(r['events'] for r in got['selected']),got['events'])
            self.assertEqual(sum(r['censored'] for r in got['selected']),got['censored'])
            json.dumps(got,allow_nan=False)

    def test_invalid_known_values_even_on_incomplete_pairs(self):
        for time,event in (([1,-1],[1,None]),([1,float('inf')],[1,None]),
                ([1,None],[1,2]),([1,None],[1,-1]),([1,None],[1,.5]),
                ([1,None],[1,float('inf')]),([1,True],[1,0]),([1,2],[1,True]),
                ([1,'2'],[1,0]),([[1,2]],[1,0]),([1,2],[1]),([None],[None]),
                ([],[]),(np.ma.array([1,2]),[1,0])):
            with self.subTest(time=str(time),event=str(event)),self.assertRaises(InputError):
                kaplan_meier_core(time,event)

    def test_numeric_extremes_and_resource_refusals(self):
        got=kaplan_meier_core([5e-324],[1],timefix=False)
        self.assertEqual(got['rate']['status'],'unavailable_numeric_range')
        self.assertIsNone(got['rate']['estimate'])
        json.dumps(got,allow_nan=False)
        with self.assertRaises(InputError):kaplan_meier_core([1e308,1e308],[1,0])
        with self.assertRaises(InputError):kaplan_meier_core([1]*100001,[0]*100001)
        got=kaplan_meier_core([1]*100000,[0]*100000)
        self.assertEqual(got['n_complete'],100000)
        self.assertEqual(len(got['curve']),1)
        self.assertEqual(got['curve'][0]['n_risk'],100000)

    def test_invalid_requested_times_confidence_and_controls(self):
        for queries in ([None],[-1],[float('inf')],[True],['1'],[[1]],np.ma.array([1]),[0]*201):
            with self.subTest(queries=str(queries)),self.assertRaises(InputError):
                kaplan_meier_core([1,2],[1,0],queries=queries)
        for confidence in (True,None,float('nan'),.49,1,.9991,'0.95'):
            with self.assertRaises(InputError):kaplan_meier_core([1,2],[1,0],confidence=confidence)
        for unit in (None,1,[],np.array('months'),'hours'):
            with self.assertRaises(InputError):kaplan_meier_core([1,2],[1,0],unit=unit)
        for fixed in (0,1,None,'false'):
            with self.assertRaises(InputError):kaplan_meier_core([1,2],[1,0],timefix=fixed)

    def test_checker_rejects_six_statistical_corruptions(self):
        original=oracle.kaplan_meier_core
        for kind in ('risk','events','survival','interval','median','person_time'):
            def changed(*args,**kwargs):
                got=copy.deepcopy(original(*args,**kwargs))
                if kind=='risk':got['curve'][0]['n_risk']+=1
                if kind=='events':got['curve'][0]['events']+=1
                if kind=='survival':got['curve'][0]['survival']*=.5
                if kind=='interval':
                    r=next(r for r in got['curve'] if r['lower'] is not None)
                    r['lower'],r['upper']=r['upper'],r['lower']
                if kind=='median':got['median']['estimate']=0
                if kind=='person_time':got['rate']['person_time']+=1
                return got
            with patch.object(oracle,'kaplan_meier_core',changed),self.assertRaises(AssertionError):oracle.verify()


if __name__=='__main__':unittest.main()
