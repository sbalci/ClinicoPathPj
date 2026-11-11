"""Paired bootstrap is a separately specified source-only experiment."""
import hashlib
import importlib.util
import json
import sys
import unittest
import numpy as np
from scipy.stats import bootstrap
from cpjtest import ROOT
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_concordance import concordance
from cpj_concordance_bootstrap import bootstrap_concordance_interval
from cpj_runtime import InputError
X=np.array([-1,-1,1,1]*3,dtype=float)
Y=np.array([-1,1,0,2]*3,dtype=float)


class BootstrapConcordance(unittest.TestCase):
    def test_independent_R_reference_distribution_and_quantiles(self):
        spec=importlib.util.spec_from_file_location('bootstrap_check',ROOT/'tools/check-concordance-bootstrap.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertTrue(module.check())

    def test_seed_replay_global_rng_and_explicit_indices(self):
        state=np.random.get_state()
        a=bootstrap_concordance_interval(X,Y,resamples=399,seed=7,return_distribution=True)
        self.assertEqual(a,bootstrap_concordance_interval(X,Y,resamples=399,seed=7,return_distribution=True))
        self.assertNotEqual(a['index_sha256'],bootstrap_concordance_interval(X,Y,resamples=399,seed=8)['index_sha256'])
        now=np.random.get_state()
        self.assertEqual(state[0],now[0]);np.testing.assert_array_equal(state[1],now[1]);self.assertEqual(state[2:],now[2:])
        indices=np.random.Generator(np.random.PCG64(7)).integers(0,12,size=(399,12),dtype=np.int64)
        b=bootstrap_concordance_interval(X,Y,resamples=399,indices=indices,seed=99,return_distribution=True)
        for field in ('distribution','lower','upper','se','index_sha256'):
            self.assertEqual(a[field],b[field])
        self.assertIsNone(b['seed']);self.assertEqual(b['index_source'],'supplied')
        self.assertEqual(b['index_sha256'],hashlib.sha256(indices.astype('<i8').tobytes()).hexdigest())
        self.assertEqual(a['point'],concordance(X,Y))

    def test_SciPy_percentile_with_same_generator_and_independent_statistic(self):
        def statistic(a,b,axis=-1):
            ma,mb=np.mean(a,axis=axis,keepdims=True),np.mean(b,axis=axis,keepdims=True)
            return (2*np.mean((a-ma)*(b-mb),axis=axis)/
                    (np.var(a,axis=axis)+np.var(b,axis=axis)+np.squeeze((ma-mb)**2,axis=axis)))
        ref=bootstrap((X,Y),statistic,paired=True,vectorized=True,method='percentile',
                      n_resamples=399,batch=64,rng=np.random.Generator(np.random.PCG64(14)))
        got=bootstrap_concordance_interval(X,Y,resamples=399,seed=14,return_distribution=True)
        np.testing.assert_allclose(got['distribution'],ref.bootstrap_distribution,atol=1e-12,rtol=0)
        self.assertAlmostEqual(got['lower'],ref.confidence_interval.low,places=12)
        self.assertAlmostEqual(got['upper'],ref.confidence_interval.high,places=12)
        self.assertAlmostEqual(got['se'],ref.standard_error,places=12)

    def test_pairing_swap_scale_offset_and_source_missing_audit(self):
        base=bootstrap_concordance_interval(X,Y,resamples=399,seed=31)
        for a,b in [(Y,X),(X+1e12,Y+1e12),(X*1e300,Y*1e300),(X*1e-300,Y*1e-300),(-X,-Y)]:
            got=bootstrap_concordance_interval(a,b,resamples=399,seed=31)
            for field in ('estimate','lower','upper','se'):
                self.assertAlmostEqual(got[field],base[field],places=12)
        x=np.r_[np.nan,X,3.];y=np.r_[1.,Y,np.nan]
        got=bootstrap_concordance_interval(x,y,resamples=399,seed=31)
        self.assertEqual(got['point']['retained_indices'],list(range(1,13)))
        for field in ('estimate','lower','upper','se','index_sha256'):
            self.assertEqual(got[field],base[field])
        permutation=np.array([2,8,1,4,7,3,0,11,10,9,6,5]);inverse=np.argsort(permutation)
        indices=np.random.default_rng(31).integers(0,12,(399,12),dtype=np.int64)
        reordered=bootstrap_concordance_interval(X[permutation],Y[permutation],resamples=399,indices=inverse[indices])
        for field in ('lower','upper','se'):
            self.assertAlmostEqual(reordered[field],base[field],places=12)

    def test_undefined_draw_is_counted_without_redrawing(self):
        x=np.arange(12.);y=x.copy();y[1:]+=1
        indices=np.tile(np.arange(12),(199,1));indices[0,:]=0
        got=bootstrap_concordance_interval(x,y,resamples=199,indices=indices,return_distribution=True)
        self.assertEqual(got['undefined_resamples'],1);self.assertEqual(got['resamples_evaluated'],199)
        self.assertIsNone(got['distribution'][0]);self.assertEqual(len(got['distribution']),199)
        self.assertEqual(got['status'],'unavailable')
        for f in ('lower','upper','se'):self.assertIsNone(got[f])

    def test_boundaries_and_degenerate_distribution(self):
        for x,y in [(X,X),(X,-X),(np.ones(12),np.ones(12))]:
            r=bootstrap_concordance_interval(x,y,resamples=199)
            self.assertEqual(r['status'],'unavailable');self.assertEqual(r['resamples_evaluated'],0)
        for x,y in [(np.ones(12),Y),(np.ones(12),np.full(12,2.))]:
            r=bootstrap_concordance_interval(x,y,resamples=199)
            self.assertEqual(r['status'],'unavailable');self.assertEqual(r['undefined_resamples'],0)
            self.assertIn('degenerate',r['reason'])

    def test_nested_confidence_reuses_same_distribution(self):
        intervals=[bootstrap_concordance_interval(X,Y,confidence=c,resamples=399,seed=42) for c in (.8,.95,.99)]
        self.assertEqual(len({r['index_sha256'] for r in intervals}),1)
        for inner,outer in zip(intervals,intervals[1:]):
            self.assertLessEqual(outer['lower'],inner['lower']);self.assertGreaterEqual(outer['upper'],inner['upper'])

    def test_resource_options_and_malformed_index_guards(self):
        for kw in [dict(resamples=198),dict(resamples=True),dict(resamples=199.),dict(resamples=10000),
                   dict(seed=-1),dict(seed=True),dict(seed=2**32),dict(seed=1.),dict(confidence=True),
                   dict(confidence=float('nan')),dict(confidence=.79),dict(confidence=1),
                   dict(return_distribution='yes'),dict(checkpoint='yes')]:
            with self.assertRaises(InputError):bootstrap_concordance_interval(X,Y,**kw)
        for indices in [np.zeros((199,12),dtype=bool),np.zeros((199,12)),np.full((199,12),-1),
                        np.full((199,12),12),np.zeros((199,11),dtype=int),[[1],[1,2]]]:
            with self.assertRaises(InputError):bootstrap_concordance_interval(X,Y,resamples=199,indices=indices)
        for n in (0,1,9):
            with self.assertRaises(InputError):bootstrap_concordance_interval(X[:n],Y[:n])
        with self.assertRaises(InputError):bootstrap_concordance_interval(np.arange(5000.),np.arange(5000.)+1,resamples=9999)

    def test_checkpoint_cancellation_propagates_and_recovery_is_deterministic(self):
        calls=[]
        class Cancelled(Exception):pass
        def checkpoint():
            calls.append(1)
            if len(calls)==2:raise Cancelled()
        with self.assertRaises(Cancelled):bootstrap_concordance_interval(X,Y,resamples=199,checkpoint=checkpoint)
        self.assertEqual(len(calls),2)
        a=bootstrap_concordance_interval(X,Y,resamples=199,seed=18)
        calls.clear()
        b=bootstrap_concordance_interval(X,Y,resamples=199,seed=18,checkpoint=lambda:calls.append(1))
        self.assertEqual(a,b);self.assertEqual(len(calls),5)
