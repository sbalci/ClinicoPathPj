import copy
import json
import sys
import unittest
from collections import Counter
import numpy as np
from cpjtest import ROOT, factor, run_analysis
sys.path.insert(0, str(ROOT / 'inst/python'))
from cpj_runtime import Factor, InputError
from cpj_alluvial import calculate, geometry, validate_geometry


def f(values, levels=None):
    levels = levels or list(dict.fromkeys(v for v in values if v is not None))
    return Factor(np.array([levels.index(v) if v is not None else -1 for v in values], dtype=int), levels)


class Alluvial(unittest.TestCase):
    def test_missing_default_collision_and_exclusion(self):
        d = dict(a=f(['A', 'A', '(Missing)', None, 'NA'], ['NA','A','(Missing)','(Missing 2)','unused']),
                 b=f(['X', None, 'Y', 'X', 'Y']))
        r = calculate(d, dict(vars=['a','b']))
        self.assertEqual((r['n'],r['excluded'],r['missingRows'],r['missingLabel']), (5,0,2,'(Missing 3)'))
        self.assertEqual(sum(v['n'] for v in r['flows']),5)
        self.assertIn('NA',[v['label'] for v in r['categories']])
        self.assertNotIn('unused',[v['label'] for v in r['categories']])
        x = calculate(d, dict(vars=['a','b'],excl=True))
        self.assertEqual((x['n'],x['excluded']), (3,2))
        self.assertFalse(any('(Missing 3)' in v['labels'] for v in x['flows']))

    def test_joint_counts_and_marginals_independent_counter(self):
        values = [('A','X','L')]*12+[('A','Y','L')]*5+[('B','X','H')]*2+[('B','Y','H')]
        d = {name:f([row[j] for row in values]) for j,name in enumerate('abc')}
        r = calculate(d,dict(vars=list('abc')))
        self.assertEqual({tuple(v['labels']):v['n'] for v in r['flows']},dict(Counter(values)))
        for axis in range(3):
            expected = Counter(row[axis] for row in values)
            self.assertEqual({v['label']:v['n'] for v in r['categories'] if v['axis']==axis},dict(expected))
            self.assertAlmostEqual(sum(v['percent'] for v in r['categories'] if v['axis']==axis),1)

    def test_geometry_conservation_tiling_and_unequal_widths(self):
        d = dict(a=f(['A']*9+['B']),b=f(['X']*7+['Y']*3),c=f(['P']*10))
        r = calculate(d,dict(vars=['a','b','c']));g = validate_geometry(geometry(r))
        for flow in r['flows']:
            segments = [s for s in g['ribbons'] if s['flow']==flow['id']]
            self.assertEqual(len(segments),2)
            self.assertTrue(all(s['n']==flow['n'] for s in segments))
        self.assertEqual(sorted(set(s['n'] for s in g['ribbons'])),[1,2,7])
        for node in g['nodes']:
            for side,axis in [('source',node['axis']),('target',node['axis']-1)]:
                if not 0<=axis<2: continue
                slots=sorted((s[side],s['n']) for s in g['ribbons'] if s['axis']==axis
                             and node['y']<=s[side]<node['y']+node['n'])
                self.assertEqual(sum(count for _,count in slots),node['n'])
                cursor=node['y']
                for start,count in slots:
                    self.assertAlmostEqual(start,cursor);cursor+=count
                self.assertAlmostEqual(cursor,node['y']+node['n'])

    def test_genuine_missing_level_and_separator_labels(self):
        d = dict(a=Factor(np.array([0,1,-1,2]),['NA',None,'A → B']),b=f(['x']*4))
        r=calculate(d,dict(vars=['a','b']))
        self.assertEqual((r['n'],r['missingRows']), (4,2))
        self.assertEqual({tuple(v['labels']):v['n'] for v in r['flows']},
                         {('NA','x'):1,('A → B','x'):1,('(Missing)','x'):2})

    def test_invalid_and_bounded_inputs(self):
        good=dict(a=f(['A']),b=f(['X']))
        for d,o in [(good,dict(vars=['a'])),(good,dict(vars=['a','a'])),
                    (dict(a=np.array([1]),b=f(['X'])),dict(vars=['a','b'])),
                    (dict(a=f([None]),b=f(['X'])),dict(vars=['a','b'],excl=True)),
                    (dict(a=f(['A']),b=f(['X','Y'])),dict(vars=['a','b'])),
                    (dict(a=f(['A']*10001),b=f(['X']*10001)),dict(vars=['a','b'])),
                    (dict(a=Factor(np.array([4]),['A']),b=f(['X'])),dict(vars=['a','b']))]:
            with self.assertRaises(InputError): calculate(d,o)
        with self.assertRaises(InputError):
            calculate(dict(a=f([str(i) for i in range(21)]),b=f(['X']*21)),dict(vars=['a','b']))
        pairs=[(str(i),str(j)) for i in range(8) for j in range(8)]
        with self.assertRaises(InputError):
            calculate(dict(a=f([a for a,b in pairs]),b=f([b for a,b in pairs])),dict(vars=['a','b']))

    def test_runtime_optional_views_and_safe_literal_labels(self):
        d=dict(a=factor(['</script><img src=x onerror=alert(1)>','A → B','A → B']),b=factor(['X','Y','Y']))
        r=run_analysis('pyalluvial',d,dict(vars=['a','b'],showFlowTable=True))
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual([v['n'] for v in r['tables']['flows']['rows']],[2,1])
        content=r['htmls']['explorer']
        self.assertNotIn('</script><img',content);self.assertIn('\\u003c/script\\u003e',content)
        self.assertNotIn('https:',content);self.assertIn('aria-label="Highlighted flow"',content)
        self.assertIn('mouseenter',content);self.assertIn("select.addEventListener('change'",content)
        hidden=run_analysis('pyalluvial',d,dict(vars=['a','b'],showPlot=False,interactive=False))
        self.assertEqual(hidden['tables'],r['tables']);self.assertEqual(hidden['plots'],{});self.assertEqual(hidden['htmls'],{})

    def test_static_geometry_and_exact_ribbon_widths(self):
        from cpj_plots import figure
        g=geometry(calculate(dict(a=f(['A']*9+['B']),b=f(['X']*10)),dict(vars=['a','b'])))
        state=dict(kind='alluvial',columns=dict(payload=[json.dumps(g)]))
        fig=figure(state,width=900,height=600)
        from matplotlib.patches import PathPatch,Rectangle
        ribbons=[p for p in fig.axes[0].patches if isinstance(p,PathPatch)]
        self.assertEqual([p.get_path().vertices[4,1]-p.get_path().vertices[3,1] for p in ribbons],[9,1])
        self.assertEqual([p.get_height() for p in fig.axes[0].patches if isinstance(p,Rectangle)],[9,1,10])
        for key,value in [('height',float('nan')),('n',0)]:
            bad=copy.deepcopy(g);bad[key]=value
            with self.assertRaises(ValueError):validate_geometry(bad)

    def test_four_axes_all_missing_and_single_category(self):
        r=calculate({v:f([None,None]) for v in 'abcd'},dict(vars=list('abcd')))
        self.assertEqual((len(r['flows']),len(r['categories']),r['n']), (1,4,2))
        self.assertEqual([v['n'] for v in geometry(r)['ribbons']],[2,2,2])
