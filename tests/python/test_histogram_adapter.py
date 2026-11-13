"""Native histogram adapter: frozen references, explicit nulls and local plot data."""
import ast
import json
import sys
import unittest
from unittest.mock import patch

from cpjtest import ROOT,number,factor,text,run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import execute
import cpj_histogram_adapter as adapter

CORE=json.loads((ROOT/'tests/fixtures/histogram-core.json').read_text())['fixtures']
GEOMETRY=json.loads((ROOT/'tests/fixtures/histogram-geometry.json').read_text())['fixtures']


def request(values,**options):
    return dict(analysis='pyjjhistostats',columns={'Measurement':number(values)},
        options=dict(dep=['Measurement'],**options),row_ids=[str(10+3*i) for i in range(len(values))])


class HistogramAdapter(unittest.TestCase):
    def test_all_mean_reference_configurations(self):
        for f in CORE:
            for ref in f['runs']:
                # Extreme-offset automatic binning has an explicit refusal policy;
                # a wide manual bin preserves the independently validated inference.
                req=request(f['values'],resultssubtitle=True,enableOneSampleTest=True,
                    testValue=ref['reference'],conflevel=ref['confidence'],
                    changebinwidth=True,binwidth=max(1,abs(f['summary']['mean'])) if f['id']=='offset_degenerate' else 1e101 if f['id']=='large_scale' else 1.1)
                got=execute(req)
                self.assertEqual(got['status'],'ok',(f['id'],got.get('error')))
                row=got['tables']['meanTest']['rows'][0]
                for key in ('reference','difference','stderr','df','statistic','p','status'):
                    target=ref[key]
                    if target is None or isinstance(target,str):self.assertEqual(row[key],target,(f['id'],key))
                    else:self.assertLessEqual(abs(row[key]-target),abs(target)*1e-10 if target else 1e-12,(f['id'],key))
                limits=got['tables']['meanLimits']['rows']
                for i,prefix in enumerate(('mean_','difference_')):
                    for key in ('lower','upper'):
                        target=ref[prefix+key]
                        if target is None:self.assertIsNone(limits[i][key])
                        else:self.assertLessEqual(abs(limits[i][key]-target),2e-7*max(1,abs(target)))
                self.assertEqual(limits[0]['confidence'],ref['confidence'])

    def test_all_geometry_reference_configurations(self):
        for f in GEOMETRY:
            for ref in f['runs']:
                got=execute(request(f['values'],changebinwidth=not ref['automatic'],
                    binwidth=ref['width'] if not ref['automatic'] else 1.1,showBins=True))
                if ref['geometry_status']=='error':
                    self.assertEqual(got['status'],'input_error',f['id']);continue
                self.assertEqual(got['status'],'ok',(f['id'],got.get('error')))
                audit=got['tables']['binning']['rows'][0]
                self.assertEqual(audit['status'],ref['geometry_status'])
                rows=got['tables'].get('bins',{}).get('rows',[])
                self.assertEqual([b['count'] for b in rows],[b['count'] for b in ref['bins']])
                if ref['bins']:
                    plot=got['plots']['histogramPlot']
                    for key in ('lower','upper','count'):self.assertEqual(plot['columns'][key],[b[key] for b in rows])
                else:self.assertNotIn('histogramPlot',got['plots'])

    def test_off_switch_never_calls_inference_and_custom_null_roles(self):
        with patch.object(adapter,'one_sample_core',side_effect=RuntimeError('must not call')):
            got=execute(request([0,1,2],testValue='unused',conflevel='unused'))
            self.assertEqual(got['status'],'ok')
            self.assertNotIn('meanTest',got['tables'])
        default=execute(request([0,1,2],resultssubtitle=True,testValue=100))
        custom=execute(request([0,1,2],resultssubtitle=True,enableOneSampleTest=True,testValue=.75))
        self.assertEqual(default['tables']['meanTest']['rows'][0]['reference'],0)
        self.assertEqual(custom['tables']['meanTest']['rows'][0]['difference'],.25)
        self.assertEqual(default['tables']['meanLimits']['rows'][0],custom['tables']['meanLimits']['rows'][0])

    def test_subject_identity_rows_mean_line_and_no_sampling(self):
        req=request([1,None,2,5],showCases=True,showBins=True,centralityline=True)
        req['columns']['ID']=text(['001',None,'01','1']);req['options']['subject']='ID'
        got=execute(req);self.assertEqual(got['status'],'ok',got.get('error'))
        cases=got['tables']['cases']['rows']
        self.assertEqual([r['sourceID'] for r in cases],['10','16','19'])
        self.assertEqual([r['subjectID'] for r in cases],['001','01','1'])
        self.assertEqual(len(got['plots']['histogramPlot']['boundaries']),1)
        self.assertAlmostEqual(got['plots']['histogramPlot']['boundaries'][0],8/3)
        req['columns']['ID']=text(['001',None,'001','1'])
        self.assertEqual(execute(req)['status'],'input_error')
        got=execute(request(list(range(1001)),showCases=True))
        self.assertEqual(len(got['tables']['cases']['rows']),1000)
        self.assertEqual(sum(got['plots']['histogramPlot']['columns']['count']),1001)
        self.assertTrue(got['tables']['cases']['notes'])

    def test_unsupported_restored_requests_and_role_guards(self):
        for options in ({'grvar':'Group'},{'typestatistics':'nonparametric'},{'alternative':'less'},
                        {'clinicalPreset':'custom'},{'showPlot':'yes'},{'enableOneSampleTest':1},
                        {'changebinwidth':True,'binwidth':0},{'resultssubtitle':True,'conflevel':1}):
            self.assertEqual(execute(request([1,2,3],**options))['status'],'input_error',options)
        req=request([1,2,3]);req['options']['dep']=['Measurement','Extra']
        self.assertEqual(execute(req)['status'],'input_error')
        req=request([1,2,3]);req['columns']['Measurement']=factor(['1','2','3'])
        self.assertEqual(execute(req)['status'],'input_error')

    def test_native_defaults_contract_and_subprocess(self):
        path=ROOT/'inst/python/analyses/jjstatsplot/pyjjhistostats.py'
        spec=ast.literal_eval(next(n.value for n in ast.parse(path.read_text()).body if isinstance(n,ast.Assign)))
        defaults={o['name']:o.get('default') for o in spec['options']}
        for key in ('changebinwidth','resultssubtitle','enableOneSampleTest','centralityline'):
            self.assertFalse(defaults[key])
        self.assertEqual(defaults['binwidth'],1.1);self.assertEqual(defaults['conflevel'],.95)
        self.assertEqual(spec['menuSubgroup'],'Distribution')
        req=request([0,1,2],resultssubtitle=True)
        got=run_analysis(req['analysis'],req['columns'],req['options'],row_ids=req['row_ids'])
        self.assertEqual(got['status'],'ok',got.get('error'))
        json.dumps(got,allow_nan=False)


if __name__=='__main__':unittest.main()
