"""Independent R hierarchy oracles, branch geometry, and source-identity contracts."""
import json
import sys
import unittest
import numpy as np
from cpjtest import ROOT, run_analysis, number
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_ihc import prepare
from cpj_plots import figure


class Trees(unittest.TestCase):
    def test_base_R_heights_and_all_cophenetic_pairs(self):
        cases=json.loads((ROOT/'tests/fixtures/ihc-tree-oracles.json').read_text())
        for case in cases:
            data={k:np.array([np.nan if v is None else v for v in values])
                  for k,values in case['columns'].items()}
            p=prepare(data,dict(markers=list(data),scaling=case['scaling'],missing='complete',
                               clusterRows=True,clusterColumns=True,showDendrograms=True),case['row_ids'])
            for key,prefix in [('rowTree','row'),('markerTree','marker')]:
                tree=p[key]
                np.testing.assert_allclose([b['height'] for b in tree['branches']],case[prefix+'_heights'],rtol=1e-12,atol=1e-12)
                for pair in case[prefix+'_pairs']:
                    got=next(b['height'] for b in tree['branches']
                             if pair['a'] in b['members'] and pair['b'] in b['members'])
                    self.assertAlmostEqual(got,pair['distance'],delta=1e-11)
                self.assertEqual(set(tree['branches'][-1]['members']),set(tree['leaves']))
                self.assertTrue(all(b['count']==len(b['members']) for b in tree['branches']))
            self.assertEqual(p['rowTree']['leaves'],[r['row'] for r in p['rows']])
            self.assertEqual(p['markerTree']['leaves'],p['markers'])

    def test_tree_geometry_and_default_heatmap_are_unchanged(self):
        columns={'a':number([0,10,1,11]),'b':number([0,20,2,22])}
        opts=dict(markers=['a','b'],clusterRows=True,clusterColumns=True)
        old=run_analysis('pyihcheatmap',columns,opts)
        new=run_analysis('pyihcheatmap',columns,dict(opts,showDendrograms=True))
        self.assertEqual(new['status'],'ok',new.get('error'))
        self.assertEqual(old['plots']['heatmap'],new['plots']['heatmap'])
        self.assertNotIn('rowDendrogram',old['plots'])
        self.assertEqual(len(new['tables']['merges']['rows']),4)
        state=new['plots']['rowDendrogram']
        f=figure(state,background='#222222',foreground='white')
        self.assertEqual(len(f.axes[0].lines),3)
        for i,line in enumerate(f.axes[0].lines):
            c=state['columns']
            self.assertEqual(list(line.get_xdata()),[c['xLeft'][i]]*2+[c['xRight'][i]]*2)
            self.assertEqual(list(line.get_ydata()),[c['leftHeight'][i],c['height'][i],c['height'][i],c['rightHeight'][i]])
        f.clear()

    def test_singleton_zero_distance_and_maximum_matrix(self):
        for n in [1,200]:
            markers=['m'+str(i) for i in range(20)]
            data={m:np.ones(n) for m in markers}
            p=prepare(data,dict(markers=markers,clusterRows=True,clusterColumns=True,showDendrograms=True))
            self.assertEqual(len(p['rowTree']['branches']),n-1)
            self.assertEqual(len(p['markerTree']['branches']),19)
            self.assertTrue(all(b['height']==0 for b in p['markerTree']['branches']))
        result=run_analysis('pyihcheatmap',{m:number([1]*200) for m in markers},
                            dict(markers=markers,clusterRows=True,clusterColumns=True,
                                 showDendrograms=True,showScatter=True))
        self.assertEqual(result['status'],'ok',result.get('error'))
        self.assertLess(len(result['htmls']['explorer'].encode()),1_500_000)
        f=figure(result['plots']['rowDendrogram']);self.assertEqual(len(f.axes[0].lines),199);f.clear()

    def test_unclustered_axes_have_no_fabricated_merges(self):
        columns={'a':number([1,2]),'b':number([3,4])}
        result=run_analysis('pyihcheatmap',columns,dict(markers=['a','b'],showDendrograms=True))
        self.assertEqual(result['status'],'ok',result.get('error'))
        self.assertNotIn('merges',result['tables'])
        self.assertNotIn('rowDendrogram',result['plots'])
