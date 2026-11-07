import sys,unittest
import numpy as np
from cpjtest import ROOT,number,factor,run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import _decode,InputError
from cpj_censoring import calculate

def calc(a,b,**options):return calculate(_decode({'a':number(a),'b':number(b)}),dict(left='a',right='b',**options))

class IntervalCensoring(unittest.TestCase):
    def test_manual_types_order_and_accounting(self):
        r=calc([1,None,1,1,None,5,-3,0,4,None],[1,3,None,4,None,2,-1,0,4,0])
        self.assertEqual(r['codes'],[1,2,0,3,None,None,3,1,1,2])
        self.assertEqual([x['n'] for x in r['counts']],[1,3,2,2])
        self.assertEqual((r['retained'],r['invalid'],r['unknown'],r['negative']),(8,1,1,1))
        self.assertEqual(r['left'],[1,None,1,1,None,None,-3,0,4,None])
        self.assertEqual(r['right'],[1,3,None,4,None,None,-1,0,4,0])
        self.assertAlmostEqual(sum(x['percent'] for x in r['counts']),1)

    def test_infinite_endpoints_checked_before_normalizing(self):
        r=calc([-np.inf,1,-np.inf,np.inf,1,np.inf,None],
               [3,np.inf,np.inf,4,-np.inf,None,None])
        self.assertEqual(r['codes'],[2,0,None,None,None,None,None])
        self.assertEqual((r['invalid'],r['unknown'],r['infinite']),(2,3,6))
        self.assertEqual(r['left'],[None,1,None,None,None,None,None])
        self.assertEqual(r['right'],[3,None,None,None,None,None,None])
        self.assertEqual(r['rows'][3]['rawLeft'],'Inf')

    def test_all_unknown_and_all_invalid_have_no_fabricated_percentages(self):
        for a,b in [([None,None],[None,None]),([3,4],[2,1])]:
            r=calc(a,b);self.assertEqual(r['retained'],0)
            self.assertTrue(all(x['percent'] is None for x in r['counts']))
            self.assertEqual(r['left'],[None,None]);self.assertEqual(r['right'],[None,None])

    def test_signed_and_same_column_scales_and_invalid_storage(self):
        r=calculate(_decode({'a':number([-2,0,None])}),dict(left='a',right='a'))
        self.assertEqual(r['codes'],[1,1,None])
        for d,o in [({'a':factor(['1']),'b':number([2])},{}),
                    ({'a':number([]),'b':number([])},{}),
                    ({'a':number([1]),'b':number([2,3])},{}),
                    ({'a':number([1]),'b':number([2])},{'preview_rows':3})]:
            with self.assertRaises(InputError):calculate(_decode(d),dict(left='a',right='b',**o))
        d=_decode({'a':number([1]),'b':number([2])});d.metadata['a']={'classes':['Date']}
        with self.assertRaisesRegex(InputError,'date classes'):calculate(d,dict(left='a',right='b'))

    def test_runtime_native_tables_and_aligned_open_bounds(self):
        r=run_analysis('pyintervalcensoring',{'a':number([1,None,1,5,None]),'b':number([1,3,None,2,None])},
                       dict(left='a',right='b',showReport=True,showPlot=True),row_ids=['2','5','9','20','31'])
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['outputs']['leftOut']['values'],[1,None,1,None,None])
        self.assertEqual(r['outputs']['rightOut']['values'],[1,3,None,None,None])
        self.assertEqual(r['outputs']['kindOut']['values'],[1,2,0,None,None])
        self.assertEqual(r['outputs']['leftOut']['row_ids'],['2','5','9','20','31'])
        self.assertEqual(r['outputs']['leftOut']['title'],'Prepared interval left')
        self.assertEqual(r['tables']['cohort']['rows'][0]['retained'],3)
        self.assertEqual(r['tables']['preview']['rows'][1]['kind'],'Left-censored')
        self.assertIn('NO third event',r['texts']['summary'])
        self.assertEqual(r['plots']['distribution']['columns']['value'],[1,1,1,0])

    def test_infinity_transport_is_explicit_and_role_limited(self):
        import copy
        sys.path.insert(0,str(ROOT/'tools'));import generate
        spec=generate.read_spec(ROOT/'inst/python/analyses/jsurvival/pyintervalcensoring.py')
        generate.validate(spec,'pyintervalcensoring')
        self.assertIn('allowInfinite = c("left", "right")',generate.b_r(spec,'test'))
        for bad in [True,['missing'],['showPlot'],['left','left']]:
            changed=copy.deepcopy(spec);changed['allowInfinite']=bad
            with self.assertRaises(generate.SpecError):generate.validate(changed,'pyintervalcensoring')
        legacy=generate.read_spec(ROOT/'inst/python/analyses/jsurvival/pytimeinterval.py')
        self.assertNotIn('allowInfinite =',generate.b_r(legacy,'test'))

    def test_bounded_preview_and_no_optional_plot_payload(self):
        r=run_analysis('pyintervalcensoring',{'a':number(range(30)),'b':number(range(30))},dict(left='a',right='b',preview_rows=10))
        self.assertEqual(r['status'],'ok');self.assertEqual(len(r['tables']['preview']['rows']),10)
        self.assertFalse(r['plots'])

if __name__=='__main__':unittest.main()
