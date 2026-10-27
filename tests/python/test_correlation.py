"""Hand fixtures, missingness, multiplicity, degeneracy and safe local outputs."""
import sys,unittest
import numpy as np
from cpjtest import ROOT,run_analysis,number
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_correlation import calculate,adjust
from cpj_runtime import InputError

class Correlation(unittest.TestCase):
    def test_hand_calculated_pearson_and_sample_counts(self):
        p=calculate({'a':np.array([1.,2,3,4]),'b':np.array([1.,2,4,3])},dict(dep=['a','b']))
        r=p['pairs'][0];self.assertAlmostEqual(r['estimate'],.8);self.assertEqual(r['n'],4)
        self.assertAlmostEqual(r['p'],.2);self.assertEqual(r['adjusted'],r['p'])
        self.assertLess(r['lower'],.8);self.assertGreater(r['upper'],.8)

    def test_missingness_and_constant_pairs_are_not_zero(self):
        d={'a':np.array([1.,2,3,4,np.nan]),'b':np.array([2.,3,5,np.nan,7]),'c':np.ones(5)}
        p=calculate(d,dict(dep=list(d),naHandling='pairwise'))
        self.assertEqual([r['n'] for r in p['pairs']],[3,4,4]);self.assertIsNone(p['pairs'][1]['estimate'])
        self.assertEqual(p['pairs'][1]['reason'],'Constant variable');self.assertIsNone(p['matrix'][2][2])
        q=calculate(d,dict(dep=list(d)));self.assertEqual([r['n'] for r in q['pairs']],[3,3,3])
        self.assertIsNone(q['pairs'][0]['lower'])

    def test_multiplicity_uses_all_planned_pairs(self):
        self.assertEqual(adjust([.01,.04,None],'holm'),[.03,.08,None])
        np.testing.assert_allclose(adjust([.01,.04,None],'BH')[:2],[.03,.06])
        self.assertEqual(adjust([.01,.04,None],'bonferroni'),[.03,.12,None])
        self.assertEqual(adjust([None,None],'holm'),[None,None])

    def test_extended_adjustments_and_invariants(self):
        for method in ['hochberg','hommel','BY']:
            self.assertEqual(adjust([None,None],method),[None,None])
            self.assertEqual(adjust([.02],method),[.02])
            self.assertEqual(adjust([0.,1.,None],method),[0.,1.,None])
            p=[.01,.04,None,.04,.2]
            q=adjust(p,method)
            self.assertIsNone(q[2]);self.assertEqual(q[1],q[3])
            self.assertTrue(all(a<=b<=1 for a,b in zip([v for v in p if v is not None],[v for v in q if v is not None])))
            reverse=adjust(p[::-1],method)[::-1]
            self.assertEqual(q,reverse)
        np.testing.assert_allclose(adjust([.01,.04,None],'BY')[:2],[.055,.11])
        np.testing.assert_allclose(adjust([.01,.04,None],'hochberg')[:2],[.03,.08])
        np.testing.assert_allclose(adjust([.01,.04,None],'hommel')[:2],[.03,.08])
        with self.assertRaises(InputError):adjust([.1],'unsupported')

    def test_spearman_ties_and_insufficient_pairs(self):
        p=calculate({'a':np.array([1.,1,2,3]),'b':np.array([1.,2,3,4])},dict(dep=['a','b'],typestatistics='nonparametric'))
        self.assertAlmostEqual(p['pairs'][0]['estimate'],3/np.sqrt(10));self.assertIsNone(p['pairs'][0]['lower'])
        q=calculate({'a':np.array([1.,2]),'b':np.array([2.,1])},dict(dep=['a','b']))
        self.assertIsNone(q['pairs'][0]['estimate']);self.assertIsNone(q['pairs'][0]['p'])

    def test_validation_and_all_missing_cohort(self):
        for d,opts in [({'a':np.array([1.]),'b':np.array([np.inf])},dict(dep=['a','b'])),({'a':np.array([]),'b':np.array([])},dict(dep=['a','b'])),({'a':np.ones(3)},dict(dep=['a','a']))]:
            with self.assertRaises(InputError):calculate(d,opts)
        p=calculate({'a':np.array([np.nan]*4),'b':np.arange(4.)},dict(dep=['a','b']))
        self.assertEqual(p['commonRows'],0);self.assertIsNone(p['pairs'][0]['estimate'])

    def test_runtime_contract_and_escaped_names(self):
        name='</script><img src=x>'
        r=run_analysis('pyjjcorrmat',{name:number([1,2,3,4]),'b':number([2,4,3,6])},dict(dep=[name,'b']))
        self.assertEqual(r['status'],'ok',r.get('error'));self.assertNotIn('</script><img',r['htmls']['explorer'])
        self.assertIn('\\u003c',r['htmls']['explorer']);self.assertEqual(len(r['plots']['matrix']['columns']['value']),4)
        self.assertEqual(r['tables']['correlations']['rows'][0]['n'],4)
