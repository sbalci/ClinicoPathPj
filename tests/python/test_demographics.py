"""Frozen R cut/table agreement and independent demographic accounting invariants."""
import json
import sys
import unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_demographics import population, resolve_levels, age_breaks
from cpj_runtime import Factor, InputError, execute
from cpj_plots import figure, render
from cpjtest import number, factor


def gender(values,levels=('Female','Male')):
    return Factor(np.array([-1 if v is None else levels.index(v) for v in values]),list(levels))

class RFixtures(unittest.TestCase):
    def test_frozen_R_labels_and_base_R_counts_and_percentages(self):
        cases=json.loads((ROOT/'tests/fixtures/demographic-oracles.json').read_text())['cases']
        for i,c in enumerate(cases):
            with self.subTest(i=i):
                ages=np.array([np.nan if v is None else v for v in c['ages']])
                r=population(ages,gender(c['gender']),female='Female',male='Male',
                  **{k:c[k] for k in ('preset','width','custom','interval','percentage')})
                np.testing.assert_allclose(r['breaks'][:-1],c['breaks'],atol=1e-12)
                self.assertEqual(r['labels'],c['labels'])
                np.testing.assert_array_equal(r['counts'][:,0],c['female'])
                np.testing.assert_array_equal(r['counts'][:,1],c['male'])
                for j,key in enumerate(('fp','mp')):
                    np.testing.assert_allclose(r['percentages'][:,j],np.array([np.nan if x is None else x for x in c[key]]),atol=1e-14)

class Accounting(unittest.TestCase):
    def test_disjoint_exclusions_and_single_gender_denominator(self):
        a=np.array([np.nan,-1,5,18,65,100,120,6,22])
        g=gender(['Female']*7+['Other',None],['Female','Male','Other'])
        r=population(a,g,female='Female',male='Male',custom='18,65')
        self.assertEqual(r['reasons'],dict(total=9,missing=2,invalid=1,other=1,outside=1,retained=4))
        self.assertEqual(r['counts'].sum(),4)
        self.assertAlmostEqual(np.nansum(r['percentages'][:,0]),1)
        self.assertTrue(np.isnan(r['percentages'][:,1]).all())
        self.assertEqual(r['counts'].tolist(),[[1,0],[3,0]])

    def test_label_resolution_order_partial_and_single_level(self):
        self.assertEqual(resolve_levels(['M','F']),('F','M','labels'))
        self.assertEqual(resolve_levels(['Erkek','Kadın']),('Kadın','Erkek','labels'))
        self.assertEqual(resolve_levels(['B','A']),('B','A','order'))
        self.assertEqual(resolve_levels(['Male']), (None,'Male','single'))
        self.assertEqual(resolve_levels(['Female','X','Male'],male='Male'),('Female','Male','partial'))
        with self.assertRaises(InputError):resolve_levels(['F','M'],'F','F')
        with self.assertRaises(InputError):resolve_levels(['F','M'],'missing',None)

    def test_invalid_inputs_resource_bounds_and_custom_fallback(self):
        for width in (0,-1,np.inf,True,.001):
            with self.assertRaises(InputError):age_breaks(100,width=width)
        b,w,notices=age_breaks(20,custom='junk,nan,')
        self.assertEqual(w,5);self.assertEqual(len(notices),2)
        b,w,notices=age_breaks(20,custom='18,bad,65,18')
        self.assertEqual(b.tolist(),[18,65,np.inf]);self.assertIsNone(w)
        with self.assertRaises(InputError):population(np.array([1.,2.]),gender(['Female','Male']),custom='20')
        with self.assertRaises(InputError):population(np.array([np.nan,-1.]),gender(['Female','Male']))

    def test_runtime_tables_plot_and_disabled_output(self):
        columns={'a':number([0,5,65,85,None,-1]),'g':factor(['M','F','F','M','F','M'],levels=['M','F'])}
        opts=dict(age='a',gender='g',age_groups='who',plot_values='percent',pct_base='total',showInterpretation=True)
        r=execute(dict(analysis='pyagepyramid',columns=columns,options=opts))
        self.assertEqual(r['status'],'ok',r.get('error'))
        rows=r['tables']['population']['rows']
        self.assertEqual([x['band'] for x in rows],['0-4','5-9','65-69','85+','Total'])
        self.assertEqual(rows[-1]['total'],4)
        self.assertEqual(rows[-1]['femalePercent'],.5)
        self.assertEqual(sum(r['plots']['pyramid']['columns']['left']),50)
        self.assertEqual(sum(r['plots']['pyramid']['columns']['right']),50)
        opts['showplot']=False
        r=execute(dict(analysis='pyagepyramid',columns=columns,options=opts))
        self.assertFalse(r['plots'])

    def test_factor_age_labels_and_non_numeric_exclusions(self):
        columns={'a':factor(['0','65','bad',None],levels=['bad','65','0']),
                 'g':factor(['Female','Male','Female','Male'])}
        r=execute(dict(analysis='pyagepyramid',columns=columns,options=dict(age='a',gender='g',age_groups='who')))
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual([x['band'] for x in r['tables']['population']['rows']],['0-4','65-69','Total'])
        self.assertEqual([x['n'] for x in r['tables']['dataSummary']['rows']],[4,1,1,0,0,2])

    def test_pyramid_geometry_symmetry_and_labels(self):
        state=dict(kind='pyramid',columns=dict(label=['0-4','5-9'],left=[3,1],right=[1,2],
          leftLabel=['Female / F']*2,rightLabel=['Male / M']*2,title=['Profile $literal$']*2),xlab='Count',ylab='Age band')
        f=figure(state);ax=f.axes[0]
        self.assertEqual([p.get_width() for p in ax.patches],[-3,-1,1,2])
        np.testing.assert_allclose(ax.get_xlim(),(-3.3,3.3))
        self.assertEqual([t.get_text() for t in ax.get_yticklabels()],['0-4','5-9'])
        self.assertEqual(ax.get_title(),'Profile $literal$')
        f.clear()
        self.assertEqual(render(state)['mime'],'image/png')
        state['columns']['left'][0]=-1
        with self.assertRaisesRegex(ValueError,'nonnegative'):figure(state)
