import json,sys,unittest
import numpy as np
from cpjtest import ROOT,number,text,factor,run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import _decode,InputError
from cpj_agreement import calculate

OPTIONS=dict(vars=['a','b'])
def data(x=None,y=None):return dict(a=number(x if x is not None else [1,2,4,7]),b=number(y if y is not None else [0,3,2,4]))

class AgreementPairs(unittest.TestCase):
    def test_independent_R_oracles(self):
        fixtures=json.loads((ROOT/'tests/fixtures/agreement-pairs.json').read_text())
        self.assertEqual(len(fixtures),45)
        for f in fixtures:
            r=calculate(_decode(data(f['x'],f['y'])),dict(OPTIONS,baConfidenceLevel=f['coverage'],confLevel=f['confidence']))
            for key,value in f['expected'].items():self.assertAlmostEqual(r[key],value,places=11,msg=(f['name'],key))

    def test_paired_missingness_and_original_rows(self):
        d=data([1,2,4,None,3,None],[0,3,None,4,5,None]);d['id']=text(['01','1','drop','drop','NA',None])
        r=calculate(_decode(d),dict(OPTIONS,subject='id'),['2','5','8','11','15','20'])
        self.assertEqual((r['input'],r['n'],r['excluded'],r['firstOnlyMissing'],r['secondOnlyMissing'],r['bothMissing']),(6,3,3,1,1,1))
        self.assertEqual([v['sourceID'] for v in r['rows']],['2','5','15'])
        self.assertEqual([v['case'] for v in r['rows']],['01','1','NA'])
        self.assertEqual([v['difference'] for v in r['rows']],[1,-1,-2])

    def test_coverage_and_confidence_have_different_effects(self):
        d=_decode(data());base=calculate(d,OPTIONS)
        cover=calculate(d,dict(OPTIONS,baConfidenceLevel=.99));conf=calculate(d,dict(OPTIONS,confLevel=.99))
        self.assertLess(cover['lower'],base['lower']);self.assertGreater(cover['upper'],base['upper'])
        self.assertEqual(conf['lower'],base['lower']);self.assertEqual(conf['upper'],base['upper'])
        self.assertLess(conf['lowerLower'],base['lowerLower']);self.assertGreater(conf['biasUpper'],base['biasUpper'])

    def test_reversal_shift_and_scale(self):
        a=calculate(_decode(data()),OPTIONS);b=calculate(_decode(data()),dict(vars=['b','a']))
        self.assertAlmostEqual(b['bias'],-a['bias']);self.assertAlmostEqual(b['lower'],-a['upper'])
        self.assertAlmostEqual(b['lowerLower'],-a['upperUpper'])
        shifted=calculate(_decode(data([101,102,104,107],[100,103,102,104])),OPTIONS)
        self.assertEqual(shifted['bias'],a['bias']);self.assertEqual(shifted['sd'],a['sd'])
        scaled=calculate(_decode(data([2,4,8,14],[0,6,4,8])),OPTIONS)
        for key in ['bias','sd','lower','upper','lowerLower']:self.assertAlmostEqual(scaled[key],2*a[key])

    def test_reject_invalid_design_and_storage(self):
        self.assertTrue(calculate({},OPTIONS)['pending'])
        for options in [dict(vars=['a','a']),dict(vars=['a','b','c']),dict(OPTIONS,baConfidenceLevel=True),dict(OPTIONS,confLevel=.5)]:
            d=data();d['c']=number([1]*4)
            with self.assertRaises(InputError):calculate(_decode(d),options)
        for d in [data([1,2],[1,2]),data([1,2,float('inf')],[1,2,3]),dict(a=factor(['1']*4),b=number([1]*4))]:
            with self.assertRaises(InputError):calculate(_decode(d),OPTIONS)
        d=_decode(data());d.metadata['a']={'classes':['Date']}
        with self.assertRaises(InputError):calculate(d,OPTIONS)
        for labels in [['p','p','q','r'],['p',None,'q','r']]:
            d=data();d['id']=text(labels)
            with self.assertRaises(InputError):calculate(_decode(d),dict(OPTIONS,subject='id'))
        d=_decode(data([1e308,-1e308,1],[0,1e308,0]))
        with self.assertRaises(InputError):calculate(d,OPTIONS)

    def test_runtime_plot_and_degenerate_warning(self):
        r=run_analysis('pyagreement',data(),dict(OPTIONS,showPairs=True,blandAltmanPlot=True))
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['plots']['plot']['columns']['y'],[1,-1,2,3])
        self.assertEqual(len(r['tables']['statistics']['rows']),4)
        self.assertIn('pointwise',r['tables']['statistics']['notes'][0])
        self.assertEqual(len(r['tables']['pairs']['rows']),4)
        self.assertFalse(r['outputs'])
        constant=run_analysis('pyagreement',data([1,2,3],[1,2,3]),OPTIONS)
        self.assertEqual(constant['tables']['statistics']['rows'][0]['estimate'],0)
        self.assertIn('zero variation',str(constant['notices']))

    def test_plot_geometry_and_rejected_state(self):
        from cpj_plots import figure
        r=calculate(_decode(data()),OPTIONS)
        state=dict(kind='agreement',columns=dict(x=[v['mean'] for v in r['rows']],y=[v['difference'] for v in r['rows']],bias=[r['bias']]*4,lower=[r['lower']]*4,upper=[r['upper']]*4))
        fig=figure(state);ax=fig.axes[0]
        np.testing.assert_allclose(ax.collections[0].get_offsets(),[[v['mean'],v['difference']] for v in r['rows']])
        self.assertEqual(len(ax.lines),3)
        for line,key in zip(ax.lines,['bias','lower','upper']):self.assertEqual(list(line.get_ydata()),[r[key],r[key]])
        state['columns']['bias'][0]=100
        with self.assertRaises(ValueError):figure(state)

if __name__=='__main__':unittest.main()
