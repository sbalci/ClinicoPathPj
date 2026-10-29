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
