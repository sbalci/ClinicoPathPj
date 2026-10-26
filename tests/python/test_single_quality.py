import importlib.util
import json
from pathlib import Path
import sys
import unittest
import numpy as np
from cpjtest import ROOT, factor, number, text, rows, run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_single_quality import screen
from cpj_runtime import Factor,Output,InputError

class SingleQuality(unittest.TestCase):
    def test_independent_r_fixtures(self):
        fixtures=json.loads((ROOT/'tests/fixtures/single-quality-oracles.json').read_text())['cases']
        for case in fixtures:
            x=np.array([np.nan if v is None else v for v in case['x']],float)
            r=screen(x,case['transform']);keep=~r['missing']
            self.assertEqual(r['transform'],case['applied'])
            self.assertEqual(r['mad_available'],case['mad_available'])
            np.testing.assert_array_equal(r['flags'][keep],np.array(case['flags'],bool).reshape(-1,3))
            np.testing.assert_array_equal(r['votes'][keep],case['votes'])
            np.testing.assert_array_equal(r['selected'][keep],case['selected'])
            for field,key in [('z','z'),('modified','modified')]:
                expected=[np.nan if v is None else v for v in case[key]]
                np.testing.assert_allclose(r[field][keep],expected,rtol=1e-10,atol=1e-10,equal_nan=True)
            if case['q'] is not None:
                np.testing.assert_allclose([r['stats'][k] for k in ('q1','median','q3')],case['q'],rtol=1e-12)

    def test_small_samples_and_zero_mad(self):
        r=screen(np.r_[np.zeros(8),100.]);self.assertTrue(r['informative']);self.assertEqual(r['selected'].sum(),1)
        r=screen(np.r_[np.zeros(10),100.]);self.assertEqual(r['selected'].sum(),1);self.assertFalse(r['mad_available'])
        self.assertFalse(screen(np.array([1.,2.]))['assessed'])
        self.assertEqual(screen(np.repeat(7.,20))['selected'].sum(),0)

    def test_cv_and_sequences(self):
        r=screen(np.array([np.nan,np.nan,1.,2.,np.nan]))
        self.assertEqual((r['runs'],r['longest_missing'],r['trailing_missing']),(3,2,1))
        self.assertAlmostEqual(r['stats']['cv'],np.std([1,2],ddof=1)/1.5)
        self.assertIsNone(screen(np.array([-1.,0.,1.]))['stats']['cv'])
        self.assertIsNone(screen(np.array([0.,.001]))['stats']['cv'])

    def test_categories_and_true_missing(self):
        f=Factor(np.array([0,1,0,-1]),['NA',' B ','unused'],True)
        r=screen(f);self.assertEqual((r['kind'],r['n'],r['distinct'],r['repeats']),('Ordinal',3,2,1))
        self.assertEqual([v['value'] for v in r['frequencies']],['NA',' B '])
        self.assertFalse(r['assessed'])
        self.assertFalse(screen(np.array(['A']*95+['B']*5,object))['frequencies'][1]['rare'])

    def test_runtime_and_aligned_output(self):
        spec=importlib.util.spec_from_file_location('single',ROOT/'inst/python/analyses/descriptives/pycheckdata.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        ids=[str(i*3+7) for i in range(12)];out=Output(module.SPEC,row_ids=ids)
        module.run({'x':np.r_[np.zeros(10),100.,np.nan]},dict(var='x',showOutliers=True,showDistribution=True,showPatterns=True,showInteractive=True),out)
        self.assertEqual(out.outputs['screeningFlag']['values'],[0]*10+[1,None])
        self.assertEqual(out.outputs['screeningFlag']['row_ids'],ids)
        self.assertEqual(out.tables['outliers']['rows'][0]['row'],ids[10])
        self.assertIn('Filtering does not recalculate',out.htmls['explorer'])
        result=run_analysis('pycheckdata',{'g':factor(['NA','B',None],levels=['NA','B','unused'])},dict(var='g',showDuplicates=True,showInteractive=True))
        self.assertEqual(result['status'],'ok',result.get('error'))
        self.assertEqual(rows(result,'overview')[0]['valid'],2)
        self.assertEqual(len(rows(result,'frequencies')),2)

    def test_validation(self):
        for x in [np.array([]),np.array([float('inf')])]:
            with self.assertRaises(InputError):screen(x)
        for opts in [dict(transform='bad'),dict(rare_threshold=0),dict(cv_min_mean=float('nan'))]:
            with self.assertRaises(InputError):screen(np.arange(20.),**opts)
        r=screen(np.array([np.nan,np.nan]));self.assertEqual(r['n'],0)
        self.assertFalse(r['assessed'])

    def test_native_point_geometry_preserves_raw_measurements(self):
        from cpj_plots import figure
        f=figure(dict(kind='points',columns=dict(x=[1,2,3],y=[.5,100.5,.5],group=['Not flagged','Flagged','Not flagged'])))
        np.testing.assert_array_equal(f.axes[0].collections[0].get_offsets(),[[1,.5],[3,.5]])
        np.testing.assert_array_equal(f.axes[0].collections[1].get_offsets(),[[2,100.5]])
        f.clear()
