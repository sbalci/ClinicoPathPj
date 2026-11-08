"""Shared ICC engine through the actual jamovi Python request/result contract."""
import json
import unittest
from cpjtest import ROOT,number,text,factor,run_analysis


def fixture():
    return dict(a=number([1,2,4,7,9,12,20,None]),b=number([0,3,2,4,7,10,None,None]),
                c=number([2,2,5,6,8,14,22,None]),case=text(['01','1','NA','C4','C5','C6','drop','drop']))


class ICCIntegration(unittest.TestCase):
    def test_six_models_against_independent_r_fixture_and_source_rows(self):
        refs=json.loads((ROOT/'tests/fixtures/icc-balanced.json').read_text())['cases']
        for case in [c for c in refs if c['name']=='three_raters' and c['confidence']==.95]:
            with self.subTest(model=case['model']):
                result=run_analysis('pyagreement',fixture(),dict(vars=['a','b','c'],subject='case',
                    method='icc',iccType=case['model'],showICCCases=True,blandAltmanPlot=True,showPairs=True),
                    row_ids=['2','4','7','9','13','18','20','25'])
                self.assertEqual(result['status'],'ok',result.get('error'))
                audit=result['tables']['iccAudit']['rows'][0]
                self.assertEqual([audit[k] for k in ['input','retained','excluded','raters']],[8,6,2,3])
                row=result['tables']['iccStatistics']['rows'][0]
                self.assertAlmostEqual(row['estimate'],case['estimate'],places=10)
                if case['model']=='icc2k':
                    self.assertIsNone(row['lower']);self.assertIsNone(row['upper'])
                    self.assertIn('Do not choose',str(result['notices']))
                else:
                    self.assertAlmostEqual(row['lower'],case['irr_interval'][0],places=10)
                    self.assertAlmostEqual(row['upper'],case['irr_interval'][1],places=10)
                self.assertFalse(result['plots'])
                self.assertNotIn('statistics',result['tables'])
                self.assertNotIn('pairs',result['tables'])
                self.assertEqual([r['sourceID'] for r in result['tables']['iccCases']['rows']],['2','4','7','9','13','18'])
                self.assertEqual([r['case'] for r in result['tables']['iccCases']['rows']],['01','1','NA','C4','C5','C6'])
                self.assertNotIn('candidate_intervals',json.dumps(result))

    def test_missing_duplicate_ids_and_invalid_design_clear_results(self):
        options=dict(method='icc',vars=['a','b','c'],subject='case')
        for ids in [['x','x','y','z','q','r','drop','drop'],
                    ['x',None,'y','z','q','r','drop','drop']]:
            data=fixture();data['case']=text(ids)
            result=run_analysis('pyagreement',data,options)
            self.assertEqual(result['status'],'input_error')
            self.assertFalse(result['plots'])
        for change in [dict(iccType='invalid'),dict(confLevel=.5),dict(vars=['a','a']),
                       dict(method='invalid')]:
            self.assertEqual(run_analysis('pyagreement',fixture(),dict(options,**change))['status'],'input_error')
        data=fixture();data['a']=factor(['yes']*8)
        self.assertEqual(run_analysis('pyagreement',data,options)['status'],'input_error')

    def test_pending_and_inactive_controls_do_not_change_estimates(self):
        options=dict(method='icc',vars=['a','b','c'])
        a=run_analysis('pyagreement',fixture(),options)
        b=run_analysis('pyagreement',fixture(),dict(options,showPairs=True,blandAltmanPlot=True,
                                                  baConfidenceLevel=.99))
        self.assertEqual(a['tables']['iccStatistics'],b['tables']['iccStatistics'])
        higher=run_analysis('pyagreement',fixture(),dict(options,confLevel=.99))
        self.assertLess(higher['tables']['iccStatistics']['rows'][0]['lower'],a['tables']['iccStatistics']['rows'][0]['lower'])
        pending=run_analysis('pyagreement',fixture(),dict(options,vars=['a']))
        self.assertEqual(pending['status'],'ok')
        self.assertNotIn('iccStatistics',pending['tables'])
