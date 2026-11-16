"""Frozen independent R comparisons, hand risk sets, explicit refusals and mutations."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import Factor,InputError
from cpj_grouped_survival import grouped_survival_core
from cpj_kaplan_meier import kaplan_meier_core
s=importlib.util.spec_from_file_location('grouped_oracle',ROOT/'tools/check-grouped-survival-core.py')
oracle=importlib.util.module_from_spec(s);s.loader.exec_module(oracle)
FIXTURES=json.loads(oracle.FIXTURE.read_text())['fixtures']


def factor(codes,levels=('B','A','Unused')):return Factor(np.array(codes,dtype=int),list(levels))
def fixture(name,timefix=True):return next(f for f in FIXTURES if f['id']==name and f['timefix']==timefix and abs(f['confidence']-.95)<1e-12)
def run(f,**options):
    a=f['inputs'];args=dict(queries=f['queries'],confidence=f['confidence'],timefix=f['timefix']);args.update(options)
    return grouped_survival_core(a['time'],a['event'],factor(a['codes'],a['levels']),**args)


class GroupedSurvivalCore(unittest.TestCase):
    def test_frozen_independent_R_reference(self):
        report=oracle.verify();self.assertEqual(report['datasets'],30);self.assertEqual(report['configurations'],180)
        self.assertEqual(report['checks'],133020)
        self.assertEqual(report['fixture_sha256'],'db8e3902d7920fc3b1a306fd91de235e5b7cb81124b24fbab79208fe1739c381')

    def test_hand_logrank_counts_covariance_score_and_df(self):
        r=run(fixture('hand_two'))['logrank']
        np.testing.assert_allclose(r['observed'],[1,3])
        np.testing.assert_allclose(r['expected'],[37/30,83/30])
        np.testing.assert_allclose(r['score'],[-7/30,7/30])
        v=641/900;np.testing.assert_allclose(r['variance'],[[v,-v],[-v,v]])
        self.assertAlmostEqual(r['statistic'],49/641);self.assertEqual(r['df'],1)
        self.assertEqual(r['trace'][1]['group_risk'],[2,3])
        self.assertEqual(r['trace'][1]['group_events'],[0,1])
        self.assertAlmostEqual(sum(r['score']),0)
        np.testing.assert_allclose(np.array(r['variance']).sum(axis=0),0,atol=1e-15)

    def test_finite_population_correction_with_multiple_tied_deaths(self):
        r=grouped_survival_core([1,1,2,2],[1,1,0,0],factor([0,1,0,1]))['logrank']
        np.testing.assert_allclose(r['variance'],[[1/3,-1/3],[-1/3,1/3]])
        self.assertEqual((r['statistic'],r['df'],r['p']),(0,1,1))
        self.assertEqual(r['trace'][0]['group_risk'],[2,2])
        self.assertEqual(r['trace'][0]['group_events'],[1,1])

    def test_log_scale_CI_and_strict_group_horizons_do_not_change_single_cohort(self):
        r=grouped_survival_core([1,2,1,3],[1,1,0,0],factor([0,0,1,1]),queries=[0,1,2,3,4])
        self.assertEqual(r['confidence_method'],'log')
        first,second=r['groups']
        self.assertEqual(first['selected'][0]['lower'],1)
        self.assertEqual(first['curve'][0]['upper'],1)
        self.assertIsNone(first['curve'][-1]['lower'])
        self.assertEqual(first['omitted_timepoints'],[3,4])
        self.assertEqual(second['omitted_timepoints'],[4])
        self.assertEqual([x['survival'] for x in second['selected']],[1]*4)
        self.assertEqual(first['median']['estimate'],1.5)
        single=kaplan_meier_core([1,2],[1,1],queries=[0,1,2,3,4])
        self.assertIsNone(single['selected'][0]['lower'])
        self.assertNotEqual(first['curve'][0]['lower'],single['curve'][0]['lower'])
        self.assertEqual(single['omitted_timepoints'],[])
        self.assertEqual(single['selected'][-1]['status'],'terminal_zero_extension')

    def test_global_time_normalization_changes_cross_group_risk_sets(self):
        fixed=run(fixture('global_near_tie_chain'));exact=run(fixture('global_near_tie_chain',False))
        self.assertEqual(fixed['effective_times'],[1e8,1e8,1e8,1e8+8])
        self.assertEqual(fixed['timefix_changed_rows'],2)
        self.assertEqual(fixed['logrank']['trace'][0]['events'],2)
        self.assertEqual(exact['timefix_changed_rows'],0)
        self.assertNotEqual(fixed['logrank']['expected'],exact['logrank']['expected'])

    def test_common_complete_case_union_declared_order_and_literal_NA(self):
        f=fixture('genuine_NA_level');r=run(f)
        self.assertEqual((r['n_source'],r['n_complete'],r['missing_group']),(7,5,2))
        self.assertEqual(r['active_codes'],[0,2,3]);self.assertEqual(r['inactive_codes'],[])
        # A category named Unused is still retained when it is actually observed.
        ordered=run(fixture('permuted_declared_order'))
        self.assertEqual(ordered['active_codes'],[0,2]);self.assertEqual(ordered['inactive_codes'],[1])
        self.assertEqual([x['label'] for x in r['groups']],['NA','A','Unused'])
        self.assertEqual(r['retained_indices'],[0,2,3,5,6])
        for g in r['groups']:
            self.assertEqual(g['n'],len(g['source_indices']))
        r=run(fixture('missing_roles'))
        self.assertEqual(r['n_source']-r['n_complete'],r['excluded_missing'])
        self.assertLess(r['excluded_missing'],r['missing_time']+r['missing_event']+r['missing_group'])

    def test_unavailable_inference_is_not_fabricated(self):
        for name,status in [('one_group','unavailable_one_group'),('all_censored','unavailable_no_events'),
                            ('zero_expected_group','unavailable_no_between_group_information'),
                            ('joint_terminal','unavailable_singular_variance')]:
            got=run(fixture(name));test=got['logrank']
            self.assertEqual(test['status'],status)
            for k in ('statistic','p','df'):self.assertIsNone(test[k])
            self.assertTrue(got['groups'])
        got=run(fixture('all_censored'))
        self.assertTrue(all(p['survival']==p['lower']==p['upper']==1 for g in got['groups'] for p in g['curve']))

    def test_permutation_group_relabeling_unit_and_source_identity(self):
        f=fixture('hand_two');a=f['inputs'];original=run(f)
        order=[5,2,0,4,3,1]
        permuted=grouped_survival_core([a['time'][i] for i in order],[a['event'][i] for i in order],
            factor([a['codes'][i] for i in order]),queries=f['queries'])
        self.assertEqual(permuted['logrank'],original['logrank'])
        for x,y in zip(permuted['groups'],original['groups']):self.assertEqual(x['curve'],y['curve'])
        swapped=grouped_survival_core(a['time'],a['event'],factor([1-c for c in a['codes']],['A','B','Unused']))
        self.assertAlmostEqual(swapped['logrank']['statistic'],original['logrank']['statistic'])
        np.testing.assert_allclose(swapped['logrank']['score'],original['logrank']['score'][::-1])
        ids=['001','01','a','b','c','d'];with_ids=run(f,subject_ids=ids,unit='years')
        self.assertEqual(with_ids['retained_subject_ids'],ids)
        self.assertEqual(with_ids['groups'],original['groups'])
        for wrong in (ids[:-1],['x']*6,[None]+ids[1:]):
            with self.assertRaises(InputError):run(f,subject_ids=wrong)

    def test_invalid_roles_statuses_and_option_types(self):
        f=fixture('hand_two');a=f['inputs']
        for opts in (dict(timefix=1),dict(confidence=True),dict(unit='seconds'),dict(queries=[None]),
                     dict(queries=[-1]),dict(queries=[float('inf')]),dict(queries=[True]),dict(queries=[0]*201)):
            with self.subTest(opts=opts),self.assertRaises(InputError):run(f,**opts)
        for t,e,g in [([1,2],[1,0],factor([0])),([1,None],[1,2],factor([0,-1])),
                      ([-1,2],[None,0],factor([-1,1])),([None,None],[1,0],factor([0,1])),
                      ([True,2],[1,0],factor([0,1])),([1,2],[True,False],factor([0,1])),
                      ([1,2],[1,0],Factor(np.array([0.,1.]),['A','B'])),
                      ([1,2],[1,0],factor([0,1],['A','A']))]:
            with self.assertRaises(InputError):grouped_survival_core(t,e,g)
        with self.assertRaises(InputError):grouped_survival_core(np.ma.array([1,2]),[1,0],factor([0,1]))

    def test_resource_caps_and_large_valid_cohorts(self):
        n=100000;r=grouped_survival_core(np.ones(n),np.arange(n)%2,factor(np.arange(n)%3,['A','B','C']))
        self.assertEqual(r['n_complete'],n);self.assertEqual(r['events'],50000)
        self.assertEqual(len(r['logrank']['trace']),1)
        self.assertEqual(sum(g['n'] for g in r['groups']),n)
        n=1002;r=grouped_survival_core(np.arange(n),np.ones(n),factor(np.arange(n)%2))
        self.assertEqual(len(r['logrank']['trace']),1000);self.assertEqual(r['logrank']['trace_truncated'],2)
        for n,k in [(100001,2),(21,21)]:
            with self.assertRaises(InputError):grouped_survival_core(np.ones(n),np.ones(n),factor(np.arange(n)%k,[str(i) for i in range(k)]))
        r=grouped_survival_core([1e300,2e300,3e300,4e300],[1,0,1,0],factor([0,1,0,1]))
        json.dumps(r,allow_nan=False)

    def test_reject_statistical_mutations_against_independent_oracle(self):
        source=(ROOT/'inst/python/cpj_grouped_survival.py').read_text()
        mutations={
            'tie_correction':('scale=d*(n-d)/(n-1)','scale=d'),
            'censors_removed_early':('probabilities=risk/n','probabilities=(risk-(counts-deaths))/(n-int((counts-deaths).sum()))'),
            'timefix_disabled':('effective=_effective_times(tt,timefix)','effective=tt.copy()'),
            'wrong_CI':("confidence_method='log',suppress_boundaries=False","confidence_method='log-log',suppress_boundaries=False"),
            'extrapolation':('extend_terminal_zero=False','extend_terminal_zero=True'),
            'missing_group':('keep=~np.isnan(t)&~np.isnan(e)&(codes>=0)','keep=~np.isnan(t)&~np.isnan(e)'),
            'wrong_df':('len(eligible)-1','len(eligible)')}
        for name,(before,after) in mutations.items():
            self.assertIn(before,source);namespace={'__name__':'grouped_mutation'}
            exec(compile(source.replace(before,after),'<mutation '+name+'>','exec'),namespace)
            with self.subTest(mutation=name),patch.object(oracle,'grouped_survival_core',namespace['grouped_survival_core']):
                with self.assertRaises(AssertionError):oracle.verify()

if __name__=='__main__':unittest.main()
