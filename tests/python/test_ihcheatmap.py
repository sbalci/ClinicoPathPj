"""Hand-calculated transformation, identity and native geometry fixtures."""
import sys,unittest,json
import numpy as np
from cpjtest import ROOT,run_analysis,number,factor,text
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_ihc import prepare, marker_pair
from cpj_runtime import Factor,InputError
from cpj_plots import figure

class IHC(unittest.TestCase):
    def test_linked_pairs_keep_clustered_identity_and_display_scale(self):
        d={'a':np.array([0.,10,1,11]),'b':np.array([0.,20,2,22]),
           'id':['same','same','other','other']}
        p=prepare(d,dict(markers=['a','b'],subject='id',scaling='zscore',clusterRows=True),['2','4','7','9'])
        pair=marker_pair(p,['a','b'],'b','a')
        self.assertEqual(pair['omitted'],0)
        for point in pair['points']:
            i=point['index']
            self.assertEqual(point['sourceRow'],p['rows'][i]['row'])
            self.assertEqual([point['y'],point['x']],p['values'][i])
        for x,y in [('a','a'),('absent','b')]:
            with self.assertRaises(InputError):marker_pair(p,['a','b'],x,y)

    def test_scatter_runtime_pairwise_missing_and_disabled_default(self):
        columns={'a':number([1,2,None,None]),'b':number([2,None,4,None])}
        r=run_analysis('pyihcheatmap',columns,dict(markers=['a','b'],showScatter=True))
        self.assertEqual(r['status'],'ok',r.get('error'))
        row=r['tables']['scatterCohort']['rows'][0]
        self.assertEqual([row[k] for k in ('retained','plotted','omitted')],[3,1,2])
        self.assertEqual(r['plots']['scatter']['columns']['x'],[1.])
        self.assertEqual(r['plots']['scatter']['columns']['y'],[2.])
        default=run_analysis('pyihcheatmap',columns,dict(markers=['a','b']))
        self.assertNotIn('scatter',default['plots'])
        self.assertEqual(default['plots']['heatmap'],r['plots']['heatmap'])
        empty=run_analysis('pyihcheatmap',{'a':number([1,None]),'b':number([None,2])},dict(markers=['a','b'],showScatter=True))
        self.assertEqual(empty['status'],'ok',empty.get('error'))
        self.assertEqual(empty['plots']['scatter']['columns']['x'],[])
        self.assertTrue(any('No complete pairs' in n['text'] for n in empty['notices']))

    def test_sample_sd_scaling_and_missingness_are_explicit(self):
        p=prepare({'a':np.array([1.,2,3,np.nan]),'b':np.array([10.,20,np.nan,np.nan])},dict(markers=['a','b'],scaling='zscore'))
        np.testing.assert_allclose([r[0] for r in p['values']],[-1,0,1])
        self.assertAlmostEqual(p['values'][0][1],-1/np.sqrt(2))
        self.assertIsNone(p['values'][2][1]);self.assertEqual(p['excluded'],1)
        self.assertEqual(p['summaries'][0]['sd'],1);self.assertEqual(p['missingCells'],1)

    def test_annotations_row_identity_and_complete_rows(self):
        d={'a':np.array([1.,np.nan,3]),'b':np.array([2.,4,6]),'g':Factor(np.array([0,-1,1]),['<A>','NA'],False),'id':['same','same',None]}
        p=prepare(d,dict(markers=['a','b'],group='g',subject='id',missing='complete'),['7','9','20'])
        self.assertEqual([r['row'] for r in p['rows']],['7','20'])
        self.assertEqual([r['group'] for r in p['rows']],['<A>','NA'])
        self.assertEqual([r['subject'] for r in p['rows']],['same',None])
        self.assertEqual(p['raw'],[[1.,2.],[3.,6.]])

    def test_constant_columns_keep_missing_and_warn(self):
        r=run_analysis('pyihcheatmap',{'a':number([3,3,None]),'b':number([1,2,3])},dict(markers=['a','b'],scaling='zscore'))
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['plots']['heatmap']['columns']['value'][::2],[0.,0.,None])
        self.assertTrue(any(n['type']=='WARNING' for n in r['notices']))

    def test_no_silent_imputation_or_sampling(self):
        d={'a':np.array([1.,np.nan]),'b':np.array([2.,3])}
        with self.assertRaisesRegex(InputError,'requires complete'):prepare(d,dict(markers=['a','b'],clusterRows=True))
        for bad in [{'a':np.array([np.inf]),'b':np.array([1.])},{'a':np.array([np.nan]),'b':np.array([1.])},{'a':np.arange(201.),'b':np.arange(201.)}]:
            with self.assertRaises(InputError):prepare(bad,dict(markers=['a','b']))
        with self.assertRaises(InputError):prepare(d,dict(markers=['a','a']))

    def test_clustering_preserves_rows_and_values(self):
        x=np.array([[0.,0],[10,10],[1,1],[11,11]])
        p=prepare({'a':x[:,0],'b':x[:,1]},dict(markers=['a','b'],clusterRows=True),['2','4','7','9'])
        order=[r['row'] for r in p['rows']]
        self.assertEqual({frozenset(order[:2]),frozenset(order[2:])},{frozenset(['2','7']),frozenset(['4','9'])})
        originals=dict(zip(['2','4','7','9'],x.tolist()))
        for row,values in zip(p['rows'],p['raw']):self.assertEqual(values,originals[row['row']])

    def test_runtime_plot_geometry_and_hostile_annotations(self):
        r=run_analysis('pyihcheatmap',{'a':number([1,None]),'b':number([2,3]),'g':text(['</script><img src=x>','NA'])},dict(markers=['a','b'],group='g'))
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertNotIn('</script><img',r['htmls']['explorer'])
        self.assertIn('\\u003c',r['htmls']['explorer'])
        f=figure(r['plots']['heatmap'],width=900,height=650)
        actual=f.axes[0].images[0].get_array()
        np.testing.assert_array_equal(actual.mask,[[False,False],[True,False]])
        np.testing.assert_allclose(actual.compressed(),[1,2,3])
        self.assertEqual(f.axes[0].images[0].norm(0),.5)
        self.assertTrue(all(v>.99 for v in f.axes[0].images[0].cmap(.5)[:3]));f.clear()

    def test_incomplete_runtime_is_input_error(self):
        r=run_analysis('pyihcheatmap',{'a':number([1,2])},dict(markers=['a']))
        self.assertEqual(r['status'],'input_error')
