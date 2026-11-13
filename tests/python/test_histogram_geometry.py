"""Frozen ggplot2 geometry, edge fuzz, mass and refusal policies."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import InputError
import cpj_histogram_geometry as engine
spec=importlib.util.spec_from_file_location('geometry_oracle',ROOT/'tools/check-histogram-geometry.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)


class HistogramGeometry(unittest.TestCase):
    def test_frozen_R_built_layer_references(self):
        result=oracle.verify()
        self.assertEqual(result['datasets'],20)
        self.assertEqual(result['fixture_sha256'],'e6e848f682b542e2bb1c40224db2b35ff5f7adeaf7421ce3f2937d4f9532cdd8')
        self.assertEqual(result['configurations'],54)

    def test_cancellation_mean_uses_independent_exact_arithmetic(self):
        ref=json.loads(oracle.FIXTURE.read_text())
        fixture=next(f for f in ref['fixtures'] if f['id']=='fuzzy_edge_neighbors')
        got=engine.histogram_geometry(fixture['values'],width=1)
        # Blinded Fraction.from_float oracle, frozen before the precision repair.
        exact=1080863913/144115188075855872
        self.assertEqual(got['summary']['mean'],exact)
        self.assertGreater(abs(fixture['summary']['mean']-exact)/abs(exact),1e-10)

    def test_automatic_width_and_manual_origin(self):
        got=engine.histogram_geometry([0,1,2])
        self.assertAlmostEqual(got['width'],2/np.sqrt(3))
        got=engine.histogram_geometry([0,1,2],width=1)
        self.assertEqual(got['raw_edges'],[-.5,.5,1.5,2.5])
        self.assertEqual([b['count'] for b in got['bins']],[1,1,1])
        self.assertTrue(got['bins'][0]['lower']<0)

    def test_fuzz_is_counting_only_and_keeps_empty_bins(self):
        x=[0,.5,.5+5e-9,.5+2e-8,3]
        got=engine.histogram_geometry(x,width=1)
        self.assertEqual([b['count'] for b in got['bins']],[3,1,0,1])
        self.assertEqual(got['raw_edges'],[-.5,.5,1.5,2.5,3.5])
        self.assertEqual(got['bins'][0]['lower'],-.5)
        self.assertEqual(got['bins'][0]['upper'],.5)
        self.assertEqual(sum(b['count'] for b in got['bins']),len(x))
        self.assertAlmostEqual(sum(b['density']*b['width'] for b in got['bins']),1)

    def test_constant_auto_unavailable_manual_recovery_and_subject_audit(self):
        for values in ([3],[3,3,3],[0,0]):
            got=engine.histogram_geometry(values)
            self.assertEqual(got['geometry_status'],'constant_auto')
            self.assertEqual(got['bins'],[]);self.assertEqual(got['width'],0)
            self.assertIn('manual',got['reason'])
            manual=engine.histogram_geometry(values,width=1.1)
            self.assertEqual(manual['geometry_status'],'ok')
            self.assertEqual(len(manual['bins']),1)
            self.assertEqual(manual['bins'][0]['count'],len(values))
        got=engine.histogram_geometry([1,None,2],width=1,subject_ids=['01',None,'1'])
        self.assertEqual(got['retained_indices'],[0,2])
        self.assertEqual(got['retained_subject_ids'],['01','1'])
        self.assertEqual(got['excluded_missing'],1)
        json.dumps(got,allow_nan=False)

    def test_invalid_widths_numeric_collapse_and_resource_limits(self):
        for width in (True,False,0,-1,'1',[],np.nan,np.inf,1+1j):
            with self.subTest(width=repr(width)),self.assertRaises(InputError):
                engine.histogram_geometry([0,1],width=width)
        for values,width in (([0,2001],1),([1e15,1e15+1],.001),([0,1],1e-300),([-1e308,1e308],None)):
            with self.assertRaises(InputError):engine.histogram_geometry(values,width=width)
        # Exactly 2,000 bins remain representable; a larger request is rejected.
        got=engine.histogram_geometry([0,1999],width=1)
        self.assertEqual(len(got['bins']),2000)

    def test_oracle_rejects_geometry_corruptions(self):
        original=oracle.histogram_geometry
        for kind in ('fuzz','origin','lost_count'):
            def changed(*args,**kwargs):
                got=original(*args,**kwargs)
                if got['bins']:
                    if kind=='fuzz':got['fuzzy_edges']=list(got['raw_edges'])
                    elif kind=='origin':got['raw_edges'][0]+=got['width']/2
                    else:got['bins'][0]['count']+=1
                return got
            with self.subTest(kind=kind),patch.object(oracle,'histogram_geometry',changed):
                with self.assertRaises(AssertionError):oracle.verify()


if __name__=='__main__':unittest.main()
