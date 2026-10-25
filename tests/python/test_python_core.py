"""New core analyses: mathematical identities, input failures and runtime serialization."""
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np
from cpjtest import ROOT, factor, number, rows, run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
import cpj_runtime as runtime
from cpj_accuracy import calculate, display


def run(name, columns=None, **options):
    result=runtime.execute(dict(analysis=name,columns=columns or {},options=options))
    json.dumps(result,allow_nan=False)
    return result


def ok(test, result):
    test.assertEqual(result['status'],'ok',result.get('error'))
    return result


class Accuracy(unittest.TestCase):
    def test_data_and_calculator_agree_with_ties_missing_and_unused_levels(self):
        data={'r':factor(['P','P','P','N','N','N',None,'P'],['N','P','unused']),
              't':factor(['+','+','-','+','-','-', '+',None],['-','+','unused'])}
        a=ok(self,run('pydecision',data,reference='r',test='t',referencePositive='P',testPositive='+'))
        b=ok(self,run('pydecisioncalculator',tp=2,fp=1,fn=1,tn=2))
        for table in ['counts','accuracy','ratios']:
            self.assertEqual(a['tables'][table],b['tables'][table])
        self.assertIn('excluded',a['texts']['summary'])

    def test_zero_cells_distinguish_infinite_undefined_and_zero(self):
        for counts,expected in [([10,0,0,10],'Infinite'),([0,0,10,10],'Undefined'),([0,10,10,0],'0')]:
            a=ok(self,run('pydecisioncalculator',**dict(zip(['tp','fp','fn','tn'],counts))))
            self.assertEqual(rows(a,'ratios')[2]['display'],expected)
        a=ok(self,run('pydecisioncalculator',tp=0,fp=0,fn=10,tn=10))
        self.assertIsNone(rows(a,'accuracy')[2]['estimate'])
        self.assertEqual(rows(a,'ratios')[0]['display'],'Undefined')
        self.assertEqual(rows(a,'ratios')[1]['estimate'],1)
        a=ok(self,run('pydecisioncalculator',tp=10,fp=3,fn=0,tn=0))
        self.assertEqual(rows(a,'ratios')[0]['estimate'],1)
        self.assertEqual(rows(a,'ratios')[1]['display'],'Undefined')

    def test_supplied_prevalence_stays_separate(self):
        a=ok(self,run('pydecisioncalculator',tp=90,fp=30,fn=20,tn=80,usePrevalence=True,prevalence=.1))
        self.assertAlmostEqual(rows(a,'accuracy')[2]['estimate'],.75)
        se,sp=90/110,80/110
        self.assertAlmostEqual(rows(a,'population')[1]['estimate'],.1*se/(.1*se+.9*(1-sp)))
        self.assertNotIn('lower',rows(a,'population')[1])

    def test_invalid_counts_empty_and_explicit_levels(self):
        for change in [dict(tp=-1),dict(tp=1.5),dict(tp=True),dict(tp=math.inf),
                       dict(tp=0,fp=0,fn=0,tn=0),dict(usePrevalence=True,prevalence=1)]:
            self.assertEqual(run('pydecisioncalculator',**change)['status'],'input_error')
        data={'r':factor(['N','P']),'t':factor(['N','P'])}
        self.assertEqual(run('pydecision',data,reference='r',test='t',testPositive='P')['status'],'input_error')
        data['r']=factor(['N','P','other']);data['t']=factor(['N','P','N'])
        self.assertEqual(run('pydecision',data,reference='r',test='t',testPositive='P',referencePositive='P')['status'],'input_error')

    def test_confidence_level_changes_intervals_not_estimates(self):
        a,b=calculate([90,30,20,80],90)[0],calculate([90,30,20,80],99)[0]
        for narrow,wide in zip(a,b):
            self.assertEqual(narrow['estimate'],wide['estimate'])
            self.assertGreater(narrow['lower'],wide['lower'])
            self.assertLess(narrow['upper'],wide['upper'])


class Sequential(unittest.TestCase):
    def test_independent_enumeration_of_all_patterns(self):
        a=ok(self,run('pysequentialtests',sens1=.73,sens2=.84,spec1=.91,spec2=.88,
                     prevalence=.17,populationSize=137,showCosts=True,cost1=3,cost2=11))
        strategies=rows(a,'strategies'); workload=rows(a,'workload')
        for i,label in enumerate(['Serial positive','Serial negative','Parallel']):
            sensitivity=specificity=second=0
            for disease,prior in [(1,.17),(0,.83)]:
                pa=.73 if disease else .09
                pb=.84 if disease else .12
                for first in [0,1]:
                    for other in [0,1]:
                        joint=(pa if first else 1-pa)*(pb if other else 1-pb)
                        pred=first and other if i==0 else first or other
                        sensitivity += joint if disease and pred else 0
                        specificity += joint if not disease and not pred else 0
                        second += prior*joint*(first if i==0 else (not first) if i==1 else 1)
            self.assertAlmostEqual(strategies[i]['sensitivity'],sensitivity)
            self.assertAlmostEqual(strategies[i]['specificity'],specificity)
            self.assertAlmostEqual(workload[i]['secondTests'],137*second)
            self.assertAlmostEqual(rows(a,'costs')[i]['total'],137*(3+second*11))
            self.assertAlmostEqual(sum(workload[i][k] for k in ['tp','fp','fn','tn']),137)
        self.assertEqual(strategies[1]['sensitivity'],strategies[2]['sensitivity'])
        self.assertNotEqual(workload[1]['secondTests'],workload[2]['secondTests'])

    def test_extreme_probabilities_and_invalid_inputs(self):
        for p in [0,1]:
            ok(self,run('pysequentialtests',prevalence=p,sens1=0,sens2=1,spec1=1,spec2=0))
        for opts in [dict(sens1=1.1),dict(cost1=-1),dict(populationSize=1.5)]:
            self.assertEqual(run('pysequentialtests',**opts)['status'],'input_error')


class Contingency(unittest.TestCase):
    def table(self,table,**options):
        r,c,w=[],[],[]
        for i,row in enumerate(table):
            for j,n in enumerate(row):r.append(str(i));c.append(str(j));w.append(n)
        return run('pychisqposttest',{'a':factor(r,sorted(set(r))+['unused']),
            'b':factor(c),'w':number(w)},rows='a',cols='b',counts='w',**options)

    def test_independent_pearson_and_residual_formula(self):
        tab=np.array([[12,20,5],[7,14,18],[21,3,8]])
        a=ok(self,self.table(tab.tolist(),adjustment='holm'))
        e=np.outer(tab.sum(axis=1),tab.sum(axis=0))/tab.sum()
        self.assertAlmostEqual(rows(a,'overall')[0]['statistic'],float(((tab-e)**2/e).sum()))
        self.assertEqual(len(rows(a,'pairs')),6)
        z=(tab-e)/np.sqrt(e*(1-tab.sum(axis=1)[:,None]/tab.sum())*(1-tab.sum(axis=0)[None,:]/tab.sum()))
        np.testing.assert_allclose([x['residual'] for x in rows(a,'cells')],z.ravel())

    def test_sparse_2x2_fisher_and_zero_margin_pruning(self):
        a=ok(self,self.table([[1,0],[0,1],[0,5]]))
        self.assertEqual(len(rows(a,'pairs')),2)  # the third pair has one nonzero column
        self.assertTrue(any('Fisher' in r['method'] for r in rows(a,'pairs')))
        a=ok(self,self.table([[1,0,0],[0,2,0],[0,0,3]],adjustment='bh'))
        self.assertEqual(len(rows(a,'pairs')),6)
        self.assertTrue(all('Fisher' in r['method'] for r in rows(a,'pairs')))
        a=ok(self,self.table([[1,2],[3,4]],adjustment='none'))
        self.assertEqual(rows(a,'pairs'),[])
        for tab in [[[1,-1],[2,3]],[[1,1.5],[2,3]],[[0,0],[0,0]]]:
            self.assertEqual(self.table(tab)['status'],'input_error')

    def test_pairwise_cap(self):
        a=ok(self,self.table([[1,2]]*33))
        self.assertNotIn('pairs',a['tables'])
        self.assertTrue(any('500' in n['text'] for n in a['notices']))


class Benford(unittest.TestCase):
    def test_digits_decimal_boundaries_and_exclusions(self):
        a=ok(self,run('pybenford',{'x':number([.3,1,20,333,4444,55555,0,-2,None])},measurement='x',digits=1))
        self.assertEqual([r['observed'] for r in rows(a,'frequencies')],[1,1,2,1,1,0,0,0,0])
        p=np.log10(1+1/np.arange(1,10))
        expected=6*p
        obs=np.array([1,1,2,1,1,0,0,0,0])
        self.assertAlmostEqual(rows(a,'test')[0]['statistic'],float(((obs-expected)**2/expected).sum()))
        self.assertAlmostEqual(rows(a,'test')[0]['mad'],float(np.mean(abs(obs/6-p))))
        self.assertEqual(a['plots']['digitPlot']['kind'],'bar')
        self.assertEqual(len(a['plots']['digitPlot']['columns']['label']),18)
        a=ok(self,run('pybenford',{'x':number([1e-320,1e200,.3,9.99])},measurement='x',digits=3))
        observed={r['digit']:r['observed'] for r in rows(a,'frequencies') if r['observed']}
        self.assertEqual(observed,{100:2,300:1,999:1})
        self.assertEqual(run('pybenford',{'x':number([0,-1,None])},measurement='x')['status'],'input_error')


class DecisionCurves(unittest.TestCase):
    def test_common_cohort_threshold_ties_and_reserved_names(self):
        data={'y':factor(['N','N','P','N','P','P','P']),
              'Treat all':number([.05,.1,.15,.2,.5,.9,None]),
              'other':number([.1,None,.2,.3,.6,.8,.9])}
        a=ok(self,run('pydecisioncurve',data,outcome='y',positive='P',models=['Treat all','other'],
                     thresholdMin=.05,thresholdMax=.5,thresholdStep=.1))
        self.assertEqual(rows(a,'cohort')[0]['n'],5)
        for row in rows(a,'curves'):
            t=row['threshold']; truth=np.array([0,1,0,1,1],dtype=bool)
            if row['model']=='Model: Treat all':pred=np.array([.05,.15,.2,.5,.9])>=t
            elif row['model']=='Model: other':pred=np.array([.1,.2,.3,.6,.8])>=t
            else:pred=np.repeat(row['model']=='Reference: treat all',5)
            tp=int(np.sum(truth & pred));fp=int(np.sum(~truth & pred))
            self.assertEqual(row['tp'],tp);self.assertEqual(row['fp'],fp)
            expected=tp/5-fp/5*t/(1-t)
            self.assertAlmostEqual(row['netBenefit'],expected)
            all_nb=3/5-2/5*t/(1-t)
            self.assertAlmostEqual(row['avoided'],100*(expected-all_nb)*(1-t)/t)
        tied=next(r for r in rows(a,'curves') if r['model']=='Model: Treat all' and r['threshold']==.15)
        self.assertEqual(tied['tp'],3)

    def test_invalid_probabilities_single_class_and_grid(self):
        for x in [[-.1,.2],[.1,1.2],[.1,math.inf]]:
            r=run('pydecisioncurve',{'y':factor(['N','P']),'p':number(x)},outcome='y',positive='P',models=['p'])
            self.assertEqual(r['status'],'input_error')
        for opts in [dict(thresholdMin=0),dict(thresholdStep=0),dict(thresholdMin=.5,thresholdMax=.1)]:
            r=run('pydecisioncurve',{'y':factor(['N','P']),'p':number([.1,.9])},outcome='y',positive='P',models=['p'],**opts)
            self.assertEqual(r['status'],'input_error')


class Subprocess(unittest.TestCase):
    def test_each_analysis_runs_through_the_real_runtime(self):
        cases=[('pydecisioncalculator',{},{}),('pysequentialtests',{},{}),
          ('pydecision',{'r':factor(['N','P']),'t':factor(['N','P'])},dict(reference='r',test='t',referencePositive='P',testPositive='P')),
          ('pychisqposttest',{'r':factor(['a','a','b','b']),'c':factor(['x','y','x','y'])},dict(rows='r',cols='c')),
          ('pybenford',{'x':number([.3,1,20,333,4444,55555])},dict(measurement='x')),
          ('pydecisioncurve',{'r':factor(['N','P']),'p':number([.1,.9])},dict(outcome='r',positive='P',models=['p']))]
        for name,columns,options in cases:
            ok(self,run_analysis(name,columns,options))
