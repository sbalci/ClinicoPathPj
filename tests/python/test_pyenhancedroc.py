"""Public runtime adapter must preserve the independent ROC engine contract."""
import json
import sys
import unittest
import numpy as np
from cpjtest import ROOT, number, factor, run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
import cpj_runtime
from cpj_runtime import Factor
from cpj_roc import roc_analysis
COLUMNS={'Reference':factor(['N']*4+['P']*4,['N','P']),
         'A':number([1,2,3,4,2,3,3,5]),'B':number([1,4,2,3,2,3,5,4])}
OPTIONS=dict(reference='Reference',positive='P',marker1='A',marker2='B',showCases=True,showThresholds=True,showROC=True)


def run(columns=COLUMNS,**kwargs):
    options=dict(OPTIONS);options.update(kwargs)
    r=cpj_runtime.execute(dict(analysis='pyenhancedroc',columns=columns,options=options,row_ids=['2','4','6','8','10','12','14','16']))
    json.dumps(r,allow_nan=False);return r


class EnhancedROC(unittest.TestCase):
    def test_public_runtime_matches_every_independent_fixture(self):
        fixtures=json.loads((ROOT/'tests/fixtures/roc-delong.json').read_text())['fixtures']
        for f in fixtures:
            names=list(f['markers']);dirs=f['directions'] if isinstance(f['directions'],list) else [f['directions']]
            codes=f['codes'];columns={'reference':dict(kind='factor',codes=[None if x==-1 else x for x in codes],levels=f['levels'])}
            columns.update({k:number([None if x=='NA' else x for x in (v if isinstance(v,list) else [v])]) for k,v in f['markers'].items()})
            options=dict(reference='reference',positive=f['positive'],showThresholds=True,showCases=True,showComparisons=True,showROC=True)
            for i,(name,direction) in enumerate(zip(names,dirs),1):options[f'marker{i}']=name;options[f'direction{i}']=direction
            r=cpj_runtime.execute(dict(analysis='pyenhancedroc',columns=columns,options=options))
            self.assertEqual(r['status'],'ok',(f['id'],r.get('error')))
            self.assertEqual(r['tables']['cohort']['rows'][0]['retained'],f['expected']['n_complete'])
            for observed,expected in zip(r['tables']['auc']['rows'],f['expected']['models']):
                ci=next(x for x in expected['intervals'] if x['confidence']==.95)
                self.assertAlmostEqual(observed['estimate'],expected['auc'],places=12)
                for k in ('se','lower','upper'):
                    if ci[k] is None:self.assertIsNone(observed[k])
                    else:self.assertAlmostEqual(observed[k],ci[k],places=12)
            expected_pairs=f['expected']['comparisons'];self.assertEqual(len(r['tables']['comparisons']['rows']),len(expected_pairs))
            for observed,expected in zip(r['tables']['comparisons']['rows'],expected_pairs):
                ci=next(x for x in expected['intervals'] if x['confidence']==.95)
                self.assertAlmostEqual(observed['difference'],expected['difference'],places=12)
                if ci['p'] is None:self.assertIsNone(observed['p'])
                else:self.assertAlmostEqual(observed['p'],ci['p'],places=12)

    def test_subprocess_bridge_payload_and_plot_matches_thresholds(self):
        r=run_analysis('pyenhancedroc',COLUMNS,OPTIONS,row_ids=[str(x) for x in [2,4,6,8,10,12,14,16]])
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual([x['sourceID'] for x in r['tables']['cases']['rows']],list(map(str,range(2,17,2))))
        points=r['plots']['rocPlot']['columns'];thresholds=r['tables']['thresholds']['rows']
        for name in ('A','B'):
            observed=[(x,y) for x,y,g in zip(points['x'],points['y'],points['group']) if g=='Score: '+name]
            expected=[(1-t['specificity'],t['sensitivity']) for t in thresholds if t['marker']==name]
            np.testing.assert_allclose(observed,expected,atol=1e-14)
        self.assertIn('unadjusted',r['texts']['summary'])
        self.assertIn('small classes',r['texts']['summary'])

    def test_optional_outputs_and_third_slot_without_second(self):
        r=run(showComparisons=False,showCases=False,showThresholds=False,showROC=False)
        for table in ('comparisons','cases','thresholds'):self.assertEqual(r['tables'].get(table,{}).get('rows',[]),[])
        self.assertNotIn('rocPlot',r['plots'])
        r=run(marker2=None,marker3='B',direction3='lower')
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['tables']['auc']['rows'][1]['direction'],'<=')
        self.assertIsNone(r['tables']['cases']['rows'][0]['score2'])
        self.assertEqual(r['tables']['cases']['rows'][0]['score3'],1)
        r=run(marker2=None)
        self.assertEqual(r['status'],'ok');self.assertEqual(r['tables']['comparisons']['rows'],[])

    def test_invalid_roles_and_empty_selection_refuse_without_partial_outputs(self):
        for kw in [dict(reference=None),dict(marker1=None),dict(positive=None),dict(marker2='A'),dict(direction1='auto'),dict(confLevel=1.)]:
            r=run(**kw);self.assertEqual(r['status'],'input_error',r.get('error'))
            self.assertEqual(r['tables'],{});self.assertEqual(r['plots'],{})
