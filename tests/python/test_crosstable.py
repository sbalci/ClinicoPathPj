import sys
import unittest
import numpy as np
from cpjtest import ROOT, factor, number, run_analysis
sys.path.insert(0, str(ROOT/'inst/python'))
from cpj_crosstable import calculate, compare, quantiles
from cpj_runtime import Factor, InputError


def f(values, levels=None):
    levels = levels or list(dict.fromkeys(v for v in values if v is not None))
    return Factor(np.array([levels.index(v) if v is not None else -1 for v in values],dtype=int),levels)


class CrossTable(unittest.TestCase):
    def test_group_denominators_missingness_and_unused_levels(self):
        data=dict(g=f(['A','A','B','B',None],['B','A','unused']),
                  cat=f(['X',None,'X','Y','Y'],['Y','X','unused']),x=np.array([1.,2,3,4,5]))
        r=calculate(data,dict(vars=['cat','x'],group='g',numericMode='continuous'))
        self.assertEqual((r['total'],r['retained'],r['excluded'],r['missingGroup']),(5,4,1,1))
        self.assertEqual([(v['scope'],v['group'],v['n']) for v in r['cohort']],
                         [('Overall','',4),('Group','B',2),('Group','A',2)])
        cats=[v for v in r['categories'] if v['scope']=='Overall']
        self.assertEqual([(v['level'],v['n'],v['valid'],v['percent']) for v in cats],
                         [('Y',1,3,1/3),('X',2,3,2/3),('unused',0,3,0),('(Missing)',1,3,None)])
        complete=calculate(data,dict(vars=['cat','x'],group='g',numericMode='continuous',excl=True))
        self.assertEqual(complete['retained'],3)
        self.assertEqual(complete['continuous'][0]['mean'],8/3)

    def test_typing_before_missing_group_drop_and_explicit_override(self):
        data=dict(g=f(['A']*3+['B']*3+[None]),x=np.arange(7,dtype=float))
        r=calculate(data,dict(vars=['x'],group='g'))
        self.assertEqual(r['typing'][0]['kind'],'continuous')
        d=dict(g=f(['A']*3+['B']*3),x=np.array([1.,2,3,1,2,3]))
        auto=calculate(d,dict(vars=['x'],group='g'))
        self.assertEqual(auto['typing'][0]['kind'],'categorical')
        self.assertEqual(auto['typing'][0]['rule'],'Numeric ≤6 distinct: categorical')
        explicit=calculate(d,dict(vars=['x'],group='g',numericMode='continuous'))
        self.assertEqual(explicit['typing'][0]['kind'],'continuous')
        self.assertEqual(explicit['tests'][0]['method'],'Wilcoxon exact (ties)')

    def test_hand_exact_rank_sum_and_pearson(self):
        row=compare(np.arange(1.,11),np.array([0]*5+[1]*5),[0,1],'continuous','chisq')
        self.assertEqual(row['method'],'Wilcoxon exact');self.assertEqual(row['statistic'],0)
        self.assertAlmostEqual(row['p'],2/252)
        x=np.array([0]*30+[1]*30+[0]*12+[1]*30)
        g=np.array([0]*60+[1]*42)
        row=compare(x,g,[0,1],'categorical','chisq')
        self.assertEqual(row['method'],'Pearson χ²');self.assertEqual(row['df'],1)
        table=np.array([[30,12],[30,30]],dtype=float)
        expected=np.outer(table.sum(axis=1),table.sum(axis=0))/table.sum()
        self.assertAlmostEqual(row['statistic'],float(np.sum((table-expected)**2/expected)))

    def test_sparse_fisher_and_larger_exact_are_distinct(self):
        x=np.array([0,0,1,1]);g=np.array([0,0,1,1])
        row=compare(x,g,[0,1],'categorical','chisq')
        self.assertEqual(row['method'],'Fisher 2×2');self.assertAlmostEqual(row['p'],1/3)
        larger=compare(np.array([0,1,2,0,1,2]),np.array([0,0,0,1,1,1]),[0,1],'categorical','chisq')
        self.assertIsNone(larger['p']);self.assertIn('no Pearson substitution',larger['reason'])

    def test_all_missing_variable_and_constant_continuous(self):
        data=dict(g=f(['A','A','B','B']),empty=np.full(4,np.nan),constant=np.ones(4))
        r=calculate(data,dict(vars=['empty','constant'],group='g',numericMode='continuous',p_adjust='BH'))
        self.assertIsNone(r['tests'][0]['p']);self.assertIsNone(r['tests'][0]['adjusted'])
        self.assertEqual(r['tests'][1]['p'],1.)
        self.assertEqual(r['tests'][1]['adjusted'],1.)
        self.assertEqual(r['testFamily'],1)
        self.assertIsNone(r['continuous'][0]['mean']);self.assertEqual(r['continuous'][3]['sd'],0)

    def test_true_missing_literal_labels_and_scope_collision(self):
        data=dict(g=f(['Overall','Overall','B','B']),
                  cat=Factor(np.array([0,1,2,-1]),['NA',None,'(Missing)']))
        r=calculate(data,dict(vars=['cat'],group='g'))
        overall=[v for v in r['categories'] if v['scope']=='Overall']
        self.assertEqual([(v['level'],v['n']) for v in overall],[('NA',1),('(Missing)',1),('(Missing 2)',2)])
        self.assertEqual({v['scope'] for v in r['cohort']},{'Overall','Group'})
        self.assertEqual(r['cohort'][1]['group'],'Overall')

    def test_mean_sd_and_type7_against_independent_fixtures(self):
        data=dict(g=f(['A']*4+['B']*4),x=np.arange(1.,9))
        r=calculate(data,dict(vars=['x'],group='g'))
        overall=r['continuous'][0]
        self.assertEqual((overall['mean'],overall['q1'],overall['median'],overall['q3']),(4.5,2.75,4.5,6.25))
        self.assertAlmostEqual(overall['sd'],6**.5)
        np.testing.assert_allclose(quantiles(np.array([-1.7e308,1.7e308])),[-8.5e307,0.,8.5e307],rtol=1e-15)

    def test_multiplicity_excludes_unavailable_tests(self):
        data=dict(g=f(['A']*5+['B']*5),x=np.arange(1.,11),y=np.arange(1.,11)*2,
                  missing=np.full(10,np.nan))
        r=calculate(data,dict(vars=['x','y','missing'],group='g',numericMode='continuous',p_adjust='bonferroni'))
        self.assertEqual(r['testFamily'],2)
        self.assertAlmostEqual(r['tests'][0]['adjusted'],4/252)
        self.assertIsNone(r['tests'][2]['adjusted'])

    def test_runtime_summary_display_does_not_change_inference(self):
        d=dict(g=factor(['A']*5+['B']*5),x=number(range(1,11)),cat=factor(['<script>','X']*5))
        a=run_analysis('pycrosstable',d,dict(vars=['x','cat'],group='g',cont='mean'))
        b=run_analysis('pycrosstable',d,dict(vars=['x','cat'],group='g',cont='median'))
        self.assertEqual(a['status'],'ok',a.get('error'));self.assertEqual(a['tables'],b['tables'])
        self.assertEqual(a['htmls'],{});self.assertEqual(a['plots'],{})
        self.assertIn('<script>',[v['level'] for v in a['tables']['categories']['rows']])

    def test_tied_exact_against_independent_label_enumeration(self):
        from itertools import combinations
        from cpj_crosstable import tied_rank_exact
        fixtures=[([1,2,2,3,4,5,2,3,4,4,6,8],6),([0,0,1,2,3],2),([0,0,1,2,3],3),([2]*8,3)]
        for values,k in fixtures:
            # Independent pairwise rank construction, without scipy rankdata.
            rank2=[2*sum(v<x for v in values)+sum(v==x for v in values)+1 for x in values]
            observed=sum(rank2[:k])
            sums=[sum(rank2[i] for i in selected) for selected in combinations(range(len(values)),k)]
            expected=min(1,2*min(sum(v<=observed for v in sums),sum(v>=observed for v in sums))/len(sums))
            self.assertAlmostEqual(tied_rank_exact(np.array(values),k),expected,places=14)

    def test_invalid_inputs_and_group_limit(self):
        good=dict(g=f(['A','B']),x=np.array([1.,2]))
        cases=[(good,dict(vars=['g'],group='g')),(good,dict(vars=['x'],group='x')),
               (good,dict(vars=['x','x'],group='g')),
               (dict(g=f(['A','A']),x=np.array([1.,2])),dict(vars=['x'],group='g')),
               (dict(g=f(['A','B']),x=np.array([1.,np.inf])),dict(vars=['x'],group='g')),
               (dict(g=f(['A','B']),x=np.array([1.])),dict(vars=['x'],group='g')),
               (dict(g=f([None,None]),x=np.array([1.,2])),dict(vars=['x'],group='g')),
               (good,dict(vars=['x'],group='g',p_adjust='bad'))]
        for data,options in cases:
            with self.assertRaises(InputError): calculate(data,options)
        with self.assertRaises(InputError):
            calculate(dict(g=f([str(i) for i in range(11)]),x=np.arange(11.)),dict(vars=['x'],group='g'))
