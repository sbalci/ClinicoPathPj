import sys,unittest,importlib.util
from pathlib import Path
import numpy as np
from cpjtest import ROOT,run_analysis,factor
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_tree import calculate
from cpj_runtime import Factor,InputError


def f(values,levels=None):
    levels=levels or list(dict.fromkeys(v for v in values if v is not None))
    return Factor(np.array([levels.index(v) if v is not None else -1 for v in values]),levels,False)


class CategoryTree(unittest.TestCase):
    def test_counts_partitions_and_denominators(self):
        d=dict(a=f(['X','X','X','Y','Y',None],['Y','X','unused']),b=f(['P','P','Q','P',None,'Q']))
        r=calculate(d,dict(vars=['a','b']))
        self.assertEqual((r['total'],r['n'],r['excluded'],r['unused']),(6,4,2,1))
        nodes=r['nodes'];self.assertEqual([v['n'] for v in nodes],[4,1,1,3,2,1])
        self.assertEqual([v['level'] for v in nodes],['Complete cohort','Y','P','X','P','Q'])
        self.assertEqual(nodes[4]['parentPercent'],2/3);self.assertEqual(nodes[4]['cohortPercent'],.5)
        for node in nodes:
            children=[v for v in nodes if v['parent']==node['node']]
            if children:self.assertEqual(sum(v['n'] for v in children),node['n'])
        self.assertEqual(sum(v['n'] for v in nodes if v['leaf']),4)

    def test_literal_missing_label_and_missing_factor_level(self):
        r=calculate(dict(a=Factor(np.array([0,1,2,-1]),['NA',None,'N'],False)),dict(vars=['a']))
        self.assertEqual((r['n'],r['excluded']),(2,2))
        self.assertEqual([v['level'] for v in r['nodes'][1:]],['NA','N'])

    def test_four_levels_and_one_class(self):
        r=calculate({v:f(['one','one']) for v in 'abcd'},dict(vars=list('abcd')))
        self.assertEqual(len(r['nodes']),5);self.assertTrue(r['nodes'][-1]['leaf'])
        self.assertTrue(all(v['parentPercent']==1 for v in r['nodes']))

    def test_node_boundaries_and_invalid_inputs(self):
        levels=[str(i) for i in range(101)]
        self.assertEqual(len(calculate(dict(a=f(levels[:100]),b=f(levels[:100])),dict(vars=['a','b']))['nodes']),201)
        for d,o in [(dict(a=f(levels),b=f(levels)),dict(vars=['a','b'])),(dict(a=f([None])),dict(vars=['a'])),(dict(a=f([])),dict(vars=['a'])),(dict(a=f(['X'])),dict(vars=['a','a'])),(dict(a=f(['X'])),dict(vars=[])),(dict(a=np.arange(3)),dict(vars=['a'])),(dict(a=f(['X']*10001)),dict(vars=['a'])),(dict(a=f(['X']),b=f(['X','Y'])),dict(vars=['a','b'])),(dict(a=Factor(np.array([2]),['X'],False)),dict(vars=['a']))]:
            with self.assertRaises(InputError):calculate(d,o)

    def test_runtime_options_and_escaped_local_tree(self):
        columns={'a':factor(['<script>alert(1)</script>','NA','NA']), 'b':factor(['x','x','y'])}
        r=run_analysis('pyvartree',columns,dict(vars=['a','b'],showPlot=True))
        self.assertEqual(r['status'],'ok',r.get('error'))
        content=r['htmls']['explorer'];self.assertIn('&lt;script&gt;',content);self.assertNotIn('<script>',content)
        self.assertIn('<details open>',content);self.assertIn('<summary>',content);self.assertNotIn('https:',content)
        self.assertEqual(sum(r['plots']['leafPlot']['columns']['value']),3)
        hidden=run_analysis('pyvartree',columns,dict(vars=['a','b'],showTree=False))
        self.assertEqual(hidden['tables'],r['tables']);self.assertEqual(hidden['htmls'],{});self.assertEqual(hidden['plots'],{})

    def test_paths_are_unambiguous_and_plot_is_bounded(self):
        r=run_analysis('pyvartree',dict(a=factor(['a / b']*40),b=factor([str(i) for i in range(40)])),dict(vars=['a','b'],showPlot=True))
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(len(r['tables']['nodes']['rows']),42)
        self.assertEqual(len(r['plots']['leafPlot']['columns']['value']),30)
        self.assertTrue(any('30 largest of 40' in v['text'] for v in r['notices']))
        self.assertIn('[["a", "a / b"], ["b", "0"]]',[v['path'] for v in r['tables']['nodes']['rows']])

    def test_example_avoids_common_csv_missing_tokens(self):
        import csv
        with (ROOT/'data/python_variable_tree_examples.csv').open() as handle:rows=list(csv.DictReader(handle))
        self.assertEqual(len(rows),38)
        self.assertFalse(any(v.strip().upper() in {'NA','NAN','NULL','N/A'} for row in rows for v in row.values()))
        columns={name:f([row[name] or None for row in rows]) for name in ['Tumor','Grade','Stage']}
        r=calculate(columns,dict(vars=list(columns)))
        self.assertEqual((r['n'],r['excluded']),(36,2))
        self.assertEqual([v['n'] for v in r['nodes'] if v['leaf']],[12,6,4,5,7,2])

    def test_path_visibility_does_not_change_result_contract(self):
        data=dict(a=factor(['X / Y','X / Y','Z']),b=factor(['P','Q','P']))
        compact=run_analysis('pyvartree',data,dict(vars=['a','b'],showPlot=True))
        detailed=run_analysis('pyvartree',data,dict(vars=['a','b'],showPlot=True,showPaths=True))
        self.assertEqual(compact['status'],'ok',compact.get('error'))
        self.assertEqual(compact['tables'],detailed['tables'])
        self.assertEqual(compact['plots'],detailed['plots'])
        self.assertEqual(compact['htmls'],detailed['htmls'])
        self.assertIn('[["a", "X / Y"], ["b", "P"]]',[r['path'] for r in compact['tables']['nodes']['rows']])

    def test_continuous_summaries_preserve_categorical_cohort(self):
        from cpj_tree import node_summaries
        d=dict(a=f(['X','X','X','Y','Y',None]),b=f(['P','P','Q','P',None,'Q']),score=np.array([1.,np.nan,3,5,99,7]))
        r=calculate(d,dict(vars=['a','b']));self.assertEqual(r['n'],4)
        leaves=node_summaries(d,r,'score');self.assertEqual(len(leaves),3)
        self.assertEqual([(v['nodeN'],v['valid'],v['missing'],v['mean'],v['sd']) for v in leaves],[(2,1,1,1.,None),(1,1,0,3.,None),(1,1,0,5.,None)])
        all_nodes=node_summaries(d,r,'score','allnodes')
        self.assertEqual((all_nodes[0]['nodeN'],all_nodes[0]['valid'],all_nodes[0]['missing'],all_nodes[0]['mean'],all_nodes[0]['sd']),(4,3,1,3.,2.))

    def test_continuous_undefined_and_extreme_moments(self):
        from cpj_tree import node_summaries,_mean_sd
        d=dict(a=f(['X','X','Y']),score=np.array([np.nan,np.nan,4.]))
        rows=node_summaries(d,calculate(d,dict(vars=['a'])),'score')
        self.assertEqual((rows[0]['valid'],rows[0]['missing'],rows[0]['mean'],rows[0]['sd']),(0,2,None,None))
        self.assertEqual((rows[1]['mean'],rows[1]['sd']),(4.,None))
        self.assertEqual(_mean_sd(np.array([1e308,1e308])),(1e308,0.))
        self.assertEqual(_mean_sd(np.array([1e-320,1e-320])),(1e-320,0.))
        self.assertAlmostEqual(_mean_sd(np.array([-1e308,1e308]))[1]/1e308,2**.5)
        with self.assertRaises(InputError):_mean_sd(np.array([-1.7e308,1.7e308]))

    def test_continuous_summary_validation(self):
        from cpj_tree import node_summaries
        d=dict(a=f(['X','Y']),score=np.array([1.,2.]));r=calculate(d,dict(vars=['a']))
        for variable,location in [('a','leafonly'),('absent','leafonly'),('score','wrong')]:
            with self.assertRaises(InputError):node_summaries(d,r,variable,location)
        for values in [np.array([1.]),np.array([1.,np.inf]),np.array(['x','y']),np.array([True,False])]:
            with self.assertRaises(InputError):node_summaries(dict(d,score=values),r,'score')

    def test_runtime_summary_labels_missing_role_and_count_invariance(self):
        from cpjtest import number
        name='<unsafe> marker';d=dict(a=factor(['X','X','Y',None]));d[name]=number([1,3,None,99])
        base=run_analysis('pyvartree',d,dict(vars=['a'],showPlot=True))
        waiting=run_analysis('pyvartree',d,dict(vars=['a'],showNodeSummary=True))
        self.assertEqual(waiting['status'],'ok');self.assertNotIn('nodeSummary',waiting['tables'])
        got=run_analysis('pyvartree',d,dict(vars=['a'],showNodeSummary=True,summaryvar=name,showPlot=True))
        self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertEqual(got['tables']['nodes'],base['tables']['nodes']);self.assertEqual(got['plots'],base['plots'])
        self.assertIn('&lt;unsafe&gt; marker',got['htmls']['explorer']);self.assertNotIn('<unsafe>',got['htmls']['explorer'])
        rows=got['tables']['nodeSummary']['rows'];self.assertEqual((rows[0]['valid'],rows[0]['mean']),(2,2.))
        self.assertEqual(rows[1]['valid'],0);self.assertIsNone(rows[1]['mean'])
        disabled=run_analysis('pyvartree',d,dict(vars=['a'],summaryvar=name,showPlot=True))
        self.assertEqual(disabled['tables'],base['tables']);self.assertEqual(disabled['htmls'],base['htmls'])

    def test_summary_moments_match_independent_python_statistics(self):
        import statistics
        from cpj_tree import _mean_sd
        rng=np.random.default_rng(902)
        for size in [2,3,25,100]:
            for location in [0.,1e14,1e-200]:
                values=rng.normal(size=size)+location
                got=_mean_sd(values)
                self.assertAlmostEqual(got[0],statistics.mean(values),delta=max(1e-12,abs(got[0])*2e-15))
                self.assertAlmostEqual(got[1],statistics.stdev(values),delta=1e-12)

    def test_reference_percent_uses_valid_values_without_changing_nodes(self):
        from cpj_tree import reference_summaries
        d=dict(a=f(['A']*4+['B']*2+[None]),ref=f(['Y','Y','N',None,'N',None,'Y']))
        r=calculate(d,dict(vars=['a']));rows=reference_summaries(d,r,'ref','Y')
        self.assertEqual((r['n'],r['excluded']),(6,1))
        self.assertEqual([(v['nodeN'],v['valid'],v['missing'],v['matches'],v['percent']) for v in rows],[(6,4,2,2,.5),(4,3,1,2,2/3),(2,1,1,0,0.)])
        same=reference_summaries(d,r,'a','A')
        self.assertEqual([v['percent'] for v in same],[4/6,1.,0.])

    def test_reference_missing_literal_and_unused_levels(self):
        from cpj_tree import reference_summaries
        d=dict(a=f(['A','A','B','B']),ref=Factor(np.array([0,1,1,-1]),['NA',None,'unused'],False))
        r=calculate(d,dict(vars=['a']));rows=reference_summaries(d,r,'ref','NA')
        self.assertEqual((rows[0]['valid'],rows[0]['matches'],rows[0]['percent']),(1,1,1.))
        self.assertIsNone(rows[-1]['percent']);self.assertEqual(rows[-1]['missing'],2)
        unused=reference_summaries(d,r,'ref','unused');self.assertEqual(unused[0]['percent'],0.)
        for level in [None,'bad']:
            with self.assertRaises(InputError):reference_summaries(d,r,'ref',level)
        with self.assertRaises(InputError):reference_summaries(dict(d,ref=np.arange(4)),r,'ref','NA')

    def test_reference_and_numeric_labels_coexist_and_roles_wait_independently(self):
        from cpjtest import number
        name='<Reference + A>';level='Yes / selected'
        d={'a':factor(['A','A','B',None]),name:factor([level,None,'Other',level]),'score':number([1,3,9,999])}
        opts=dict(vars=['a'],showPlot=True,showNodeSummary=True,summaryvar='score',summarylocation='allnodes')
        base=run_analysis('pyvartree',d,opts)
        waiting=run_analysis('pyvartree',d,dict(opts,pct=True,percvar=name))
        self.assertEqual(waiting['status'],'ok');self.assertEqual(waiting['tables'],base['tables'])
        got=run_analysis('pyvartree',d,dict(opts,pct=True,percvar=name,percvarLevel=level))
        self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertEqual(got['tables']['nodes'],base['tables']['nodes'])
        self.assertEqual(got['tables']['nodeSummary'],base['tables']['nodeSummary']);self.assertEqual(got['plots'],base['plots'])
        self.assertIn('&lt;Reference + A&gt;',got['htmls']['explorer']);self.assertIn('mean=',got['htmls']['explorer'])
        self.assertIn(level,got['htmls']['explorer']);self.assertEqual(got['tables']['referenceSummary']['rows'][0]['percent'],.5)
