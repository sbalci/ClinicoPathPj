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

    def test_partial_pearson_residuals_and_degrees_of_freedom(self):
        rng=np.random.default_rng(71);z=rng.normal(size=40);a=z+rng.normal(size=40);b=2*z+rng.normal(size=40)
        p=calculate(dict(a=a,b=b,z=z),dict(dep=['a','b','z'],partial=True))
        design=np.column_stack([np.ones(40),z]);ra=a-design@np.linalg.lstsq(design,a,rcond=None)[0];rb=b-design@np.linalg.lstsq(design,b,rcond=None)[0]
        self.assertAlmostEqual(p['pairs'][0]['estimate'],np.corrcoef(ra,rb)[0,1],places=12)
        self.assertEqual(p['pairs'][0]['df'],37);self.assertEqual(p['pairs'][0]['controls'],1)
        for options in [dict(dep=['a','b']),dict(dep=['a','b','z'],naHandling='pairwise'),dict(dep=['a','b','z'],naHandling='unsupported')]:
            with self.assertRaises(InputError):calculate(dict(a=a,b=b,z=z),dict(options,partial=True))
        for data,reason in [(dict(a=a,b=b,z=np.ones(40)),'Constant'),(dict(a=a,b=b,z=a+b),'Singular'),(dict(a=a[:3],b=b[:3],z=z[:3]),'degrees')]:
            result=calculate(data,dict(dep=['a','b','z'],partial=True))
            self.assertTrue(all(r['estimate'] is None and reason in r['reason'] for r in result['pairs']))
        short=calculate(dict(a=a[:4],b=b[:4],z=z[:4]),dict(dep=['a','b','z'],partial=True))
        self.assertEqual(short['pairs'][0]['df'],1);self.assertIsNone(short['pairs'][0]['lower'])

    def test_partial_spearman_ranks_common_cohort_with_ties(self):
        from scipy import stats
        a=np.array([1.,1,2,3,5,8,np.nan,13]);b=np.array([5.,2,2,8,4,9,3,10]);z=np.array([1.,3,2,5,4,7,6,8])
        keep=np.isfinite(a);ranks=stats.rankdata(np.column_stack([a[keep],b[keep],z[keep]]),axis=0,method='average')
        design=np.column_stack([np.ones(keep.sum()),ranks[:,2]])
        residuals=[ranks[:,i]-design@np.linalg.lstsq(design,ranks[:,i],rcond=None)[0] for i in [0,1]]
        result=calculate(dict(a=a,b=b,z=z),dict(dep=['a','b','z'],partial=True,typestatistics='nonparametric'))
        row=result['pairs'][0];self.assertAlmostEqual(row['estimate'],np.corrcoef(*residuals)[0,1],places=12)
        self.assertEqual((row['n'],row['excluded'],row['controls'],row['df']),(7,1,1,4))
        self.assertIsNone(row['lower']);self.assertIsNone(row['upper'])
        self.assertGreaterEqual(row['p'],0);self.assertLessEqual(row['p'],1)
        singular=calculate(dict(a=a,b=a,z=z),dict(dep=['a','b','z'],partial=True,typestatistics='nonparametric'))
        self.assertTrue(all(row['estimate'] is None for row in singular['pairs']))
        empty=calculate({k:np.full(4,np.nan) for k in ['a','b','z']},dict(dep=['a','b','z'],partial=True,typestatistics='nonparametric'))
        self.assertEqual(empty['commonRows'],0);self.assertTrue(all(row['estimate'] is None for row in empty['pairs']))

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
