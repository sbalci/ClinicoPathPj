"""Empirical ROC/paired DeLong source core with explicit orientation and cohort."""
import importlib.util
import json
import sys
import unittest
import numpy as np
from cpjtest import ROOT
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_roc import roc_analysis
from cpj_runtime import Factor, InputError
REF=Factor(np.array([0]*4+[1]*4),['Negative','Positive'])
MARKERS={'A':np.array([1.,2,3,4,2,3,3,5]),'B':np.array([1.,4,2,3,2,3,5,4])}


class ROC(unittest.TestCase):
    def test_independent_R_pROC_kernel_and_threshold_oracle(self):
        spec=importlib.util.spec_from_file_location('roc_check',ROOT/'tools/check-roc-delong.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertTrue(module.check())

    def test_hand_auc_ties_and_exact_threshold_counts(self):
        r=roc_analysis(REF,MARKERS,'Positive');m=r['models'][0]
        self.assertEqual(m['auc'],21/32)
        p=next(x for x in m['points'] if x['cutoff']==3)
        self.assertEqual([p[k] for k in ('tp','fp','fn','tn')],[3,2,1,2])
        self.assertEqual(m['points'][0]['cutoff'],None)
        self.assertEqual(m['points'][0]['rule'],'none positive')
        self.assertEqual((m['points'][-1]['tpr'],m['points'][-1]['fpr']),(1.,1.))
        area=sum((b['fpr']-a['fpr'])*(a['tpr']+b['tpr'])/2 for a,b in zip(m['points'],m['points'][1:]))
        self.assertEqual(area,m['auc'])

    def test_fixed_orientation_outcome_reversal_and_factor_level_order(self):
        base=roc_analysis(REF,MARKERS,'Positive')
        lower=roc_analysis(REF,MARKERS,'Positive',{'A':'lower','B':'lower'})
        changed=roc_analysis(REF,MARKERS,'Negative')
        reordered=roc_analysis(Factor(1-REF.codes,['Positive','Negative']),MARKERS,'Positive')
        renamed=roc_analysis(Factor(REF.codes,['control','NA']),MARKERS,'NA')
        self.assertEqual(renamed['positive'],'NA');self.assertEqual(renamed['n_complete'],8)
        for i,m in enumerate(base['models']):
            self.assertAlmostEqual(lower['models'][i]['auc'],1-m['auc'])
            self.assertAlmostEqual(changed['models'][i]['auc'],1-m['auc'])
            for field in ('auc','variance','se','lower','upper'):
                self.assertAlmostEqual(reordered['models'][i][field],m[field])
                self.assertAlmostEqual(renamed['models'][i][field],m[field])
        self.assertLess(lower['models'][0]['auc'],.5)
        self.assertAlmostEqual(changed['comparisons'][0]['difference'],-base['comparisons'][0]['difference'])

    def test_monotonic_transform_sign_and_row_permutation(self):
        base=roc_analysis(REF,MARKERS,'Positive')
        permutation=np.array([4,0,6,1,7,2,5,3])
        cases=[(REF,{k:v**3 for k,v in MARKERS.items()},None),
               (REF,{k:-v for k,v in MARKERS.items()},{k:'lower' for k in MARKERS}),
               (Factor(REF.codes[permutation],REF.levels),{k:v[permutation] for k,v in MARKERS.items()},None)]
        for ref,markers,direction in cases:
            got=roc_analysis(ref,markers,'Positive',direction)
            for a,b in zip(base['models'],got['models']):
                for f in ('auc','variance','se','lower','upper'):self.assertAlmostEqual(a[f],b[f],places=12)
            for f in ('difference','variance','se','z','p','lower','upper'):
                self.assertAlmostEqual(base['comparisons'][0][f],got['comparisons'][0][f],places=12)

    def test_pairwise_order_covariance_and_difference_uncertainty(self):
        base=roc_analysis(REF,MARKERS,'Positive');c=base['comparisons'][0];matrix=np.array(base['covariance'])
        self.assertAlmostEqual(c['variance'],matrix[0,0]+matrix[1,1]-2*matrix[0,1],places=14)
        self.assertGreaterEqual(np.min(np.linalg.eigvalsh(matrix)),-1e-14)
        swap=roc_analysis(REF,dict(reversed(list(MARKERS.items()))),'Positive')['comparisons'][0]
        self.assertAlmostEqual(swap['difference'],-c['difference'])
        self.assertAlmostEqual(swap['z'],-c['z']);self.assertAlmostEqual(swap['p'],c['p'])
        self.assertAlmostEqual(swap['lower'],-c['upper'])
        self.assertEqual(base['multiplicity'],'none')

    def test_common_cohort_missingness_and_original_positions(self):
        ref=Factor(np.r_[REF.codes,-1],REF.levels)
        markers={'A':np.r_[MARKERS['A'],8.], 'B':np.r_[MARKERS['B'],9.]}
        markers['A'][0]=np.nan;markers['B'][6]=np.nan
        got=roc_analysis(ref,markers,'Positive')
        self.assertEqual(got['retained_indices'],[1,2,3,4,5,7])
        self.assertEqual((got['n_complete'],got['n_excluded']),(6,3))
        self.assertEqual(got['missing_by_marker'],{'A':1,'B':1});self.assertEqual(got['missing_reference'],1)
        expected=roc_analysis(Factor(REF.codes[[1,2,3,4,5,7]],REF.levels),
                              {k:v[[1,2,3,4,5,7]] for k,v in MARKERS.items()},'Positive')
        self.assertEqual(got['models'],expected['models']);self.assertEqual(got['comparisons'],expected['comparisons'])
        markers['C']=np.full(9,np.nan)
        with self.assertRaises(InputError):roc_analysis(ref,markers,'Positive')

    def test_inference_unavailable_for_boundary_zero_variance_and_insufficient_groups(self):
        r=roc_analysis(REF,{'perfect':REF.codes.astype(float),'inverted':-REF.codes.astype(float),'constant':np.ones(8)},'Positive')
        self.assertEqual([m['auc'] for m in r['models']],[1.,0.,.5])
        for m in r['models']:
            self.assertEqual(m['inference_status'],'unavailable');self.assertIsNone(m['lower']);self.assertIsNone(m['se'])
        for c in r['comparisons']:
            self.assertEqual(c['status'],'unavailable');self.assertIsNone(c['p'])
        identical=roc_analysis(REF,{'A':MARKERS['A'],'B':MARKERS['A']},'Positive')
        self.assertEqual(identical['comparisons'][0]['difference'],0)
        self.assertIsNone(identical['comparisons'][0]['p'])
        one=roc_analysis(Factor(np.array([0,1]),REF.levels),{'A':[0.,1.]},'Positive')
        self.assertEqual(one['models'][0]['auc'],1);self.assertIsNone(one['covariance'])

    def test_confidence_nesting_raw_and_bounded_limits(self):
        runs=[roc_analysis(REF,MARKERS,'Positive',confidence=c) for c in (.8,.95,.99)]
        for a,b in zip(runs,runs[1:]):
            for x,y in zip(a['models'],b['models']):
                self.assertEqual(x['auc'],y['auc']);self.assertLessEqual(y['lower'],x['lower']);self.assertGreaterEqual(y['upper'],x['upper'])
            self.assertEqual(a['comparisons'][0]['p'],b['comparisons'][0]['p'])
        m=runs[1]['models'][0];self.assertGreater(m['raw_upper'],1);self.assertEqual(m['upper'],1)

    def test_extreme_scores_have_finite_json_safe_endpoints(self):
        marker=np.array([-1.,-.8,-.3,.1,-.7,-.1,.3,.9])*1e308
        r=roc_analysis(REF,{'A':marker},'Positive')
        json.dumps(r,allow_nan=False)
        self.assertTrue(all(p['cutoff'] is None or np.isfinite(p['cutoff']) for p in r['models'][0]['points']))
        small=roc_analysis(REF,{'A':marker*1e-308},'Positive')
        self.assertEqual(r['models'][0]['auc'],small['models'][0]['auc'])

    def test_invalid_roles_options_scores_and_resource_guards(self):
        for confidence in (True,float('nan'),.79,1.,'95'):
            with self.assertRaises(InputError):roc_analysis(REF,MARKERS,'Positive',confidence=confidence)
        for reference in [None,Factor(REF.codes,None),Factor(REF.codes,'AB'),Factor(REF.codes,['x','x']),
                          Factor(REF.codes,['Negative','Positive','unused']),Factor(REF.codes.astype(float),REF.levels),
                          Factor(np.ma.array(REF.codes,mask=[True]+[False]*7),REF.levels),
                          Factor(np.array([0,0,0,0,1,1,1,2]),REF.levels)]:
            with self.assertRaises(InputError):roc_analysis(reference,MARKERS,'Positive')
        for direction in [{'A':'auto','B':'higher'},{'A':'higher'}, {'A':np.array([1,2]),'B':'higher'}]:
            with self.assertRaises(InputError):roc_analysis(REF,MARKERS,'Positive',directions=direction)
        for markers in [{},{'A':np.arange(7.)},{'A':np.ones(8,dtype=bool)},
                        {'A':np.array([0,1,2,3,4,5,6,np.inf])},{'A':['1']*8},
                        {str(i):np.arange(8.) for i in range(4)}]:
            with self.assertRaises(InputError):roc_analysis(REF,markers,'Positive')
        with self.assertRaises(InputError):roc_analysis(REF,MARKERS,None)
        with self.assertRaises(InputError):roc_analysis(Factor(np.zeros(8,dtype=int),REF.levels),MARKERS,'Positive')
        with self.assertRaises(InputError):roc_analysis(Factor(np.zeros(5001,dtype=int),REF.levels),{'A':np.arange(5001.)},'Positive')
