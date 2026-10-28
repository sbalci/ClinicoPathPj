import unittest,sys,importlib.util
from pathlib import Path
import numpy as np
from cpjtest import ROOT,number,run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_outliers import calculate
from cpj_runtime import InputError,Output

class Outliers(unittest.TestCase):
    def test_iqr_fences_and_strict_ties(self):
        r=calculate(dict(x=np.array([0.,1,2,3,4,20])),dict(vars=['x'],method='iqr'))
        self.assertEqual((r['summaries'][0]['lower'],r['summaries'][0]['upper']),(-3.,8.))
        self.assertEqual(r['aggregate'].tolist(),[0,0,0,0,0,1])
        ties=calculate(dict(x=np.array([-1.,0,1])),dict(vars=['x'],method='zscore',zscore_threshold=1))
        self.assertEqual(ties['aggregate'].tolist(),[0,0,0])
        iqr_ties=calculate(dict(x=np.array([-3.,0,1,2,3,6])),dict(vars=['x'],method='iqr',iqr_multiplier=1.3))
        self.assertEqual(iqr_ties['aggregate'].tolist(),[0]*6)
        # With all equal values IQR=0 still defines a nonflagged row.
        r=calculate(dict(x=np.ones(4)),dict(vars=['x'],method='iqr'))
        self.assertEqual(r['aggregate'].tolist(),[0]*4)

    def test_z_and_robust_zero_spread(self):
        r=calculate(dict(x=np.array([0.,0,0,0,10])),dict(vars=['x']))
        self.assertTrue(np.isnan(r['aggregate'][:4]).all());self.assertEqual(r['aggregate'][-1],1)
        r=calculate(dict(x=np.ones(4)),dict(vars=['x'],method='zscore'))
        self.assertTrue(np.isnan(r['aggregate']).all())
        r=calculate(dict(x=np.arange(10.)),dict(vars=['x'],method='zscore',zscore_threshold=1))
        reference=np.abs((np.arange(10.)-4.5)/np.sqrt(82.5/9))>1
        self.assertEqual(r['aggregate'].tolist(),reference.astype(int).tolist())

    def test_complete_cohort_nonfinite_and_any_variable_flags(self):
        d=dict(x=np.array([0.,1,2,3,4,20,np.nan,np.inf]),y=np.array([0.,1,2,3,4,5,20,30]))
        r=calculate(d,dict(vars=['x','y'],method='iqr'))
        self.assertEqual((r['n'],r['excluded']),(6,2));self.assertTrue(np.isnan(r['aggregate'][-2:]).all())
        self.assertEqual(r['aggregate'][:6].tolist(),[0,0,0,0,0,1])

    def test_validation(self):
        for d,o in [(dict(x=np.array([])),dict(vars=['x'])),(dict(x=np.array([np.nan,np.inf])),dict(vars=['x'])),(dict(x=np.array([1.])),dict(vars=['x'])),(dict(x=np.ones(10001)),dict(vars=['x'])),(dict(x=np.arange(3.)),dict(vars=['x','x'])),(dict(x=np.arange(3.)),dict(vars=['x'],zscore_threshold=0)),(dict(x=np.arange(3.)),dict(vars=['x'],method='bad'))]:
            with self.assertRaises(InputError):calculate(d,o)

    def test_runtime_and_sparse_source_rows(self):
        spec=importlib.util.spec_from_file_location('outliers_analysis',ROOT/'inst/python/analyses/descriptives/pyoutlierdetection.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        out=Output(m.SPEC,['2','5','9','12','15','20','30'])
        m.run(dict(x=np.array([0.,1,2,3,4,20,np.nan])),dict(vars=['x'],method='iqr',showRows=True,showPlot=True),out)
        self.assertEqual(out.outputs['screenFlags']['values'],[0,0,0,0,0,1,None])
        self.assertEqual(out.outputs['screenFlags']['measure_type'],'nominal')
        self.assertEqual([r['row'] for r in out.tables['rowPreview']['rows']],out.row_ids)
        self.assertEqual(out.plots['countPlot']['columns']['value'],[1])
        self.assertEqual(out.tables['rowPreview']['rows'][-2]['drivers'],'x')

    def test_flagged_measurement_values_keep_original_rows_and_outputs(self):
        spec=importlib.util.spec_from_file_location('outliers_details',ROOT/'inst/python/analyses/descriptives/pyoutlierdetection.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        data=dict(x=np.array([0.,1,2,3,4,20,np.nan]),y=np.array([0.,1,2,3,4,-20,30]))
        ids=['2','5','9','12','15','20','30'];opts=dict(vars=['x','y'],method='iqr',showRows=True,showPlot=True)
        before=Output(m.SPEC,ids);m.run(data,opts,before)
        after=Output(m.SPEC,ids);m.run(data,dict(opts,showFlaggedValues=True),after)
        details=after.tables['flaggedValues']['rows']
        self.assertEqual([(r['row'],r['variable'],r['value'],r['basis']) for r in details],[('20','x',20.,'IQR fences'),('20','y',-20.,'IQR fences')])
        self.assertEqual(after.outputs,before.outputs);self.assertEqual(after.plots,before.plots)
        self.assertEqual(after.tables['variables'],before.tables['variables'])
        self.assertEqual(after.tables['rowPreview'],before.tables['rowPreview'])
        self.assertIn('2 of 2 flagged measurements',after.texts['flaggedScope'])

    def test_flagged_measurements_cap_matches_without_truncating_analysis(self):
        spec=importlib.util.spec_from_file_location('outliers_limit',ROOT/'inst/python/analyses/descriptives/pyoutlierdetection.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        data=dict(x=np.array([0.]*1001+[10.]*1000));ids=[str(i+10) for i in range(2001)]
        out=Output(m.SPEC,ids);m.run(data,dict(vars=['x'],showFlaggedValues=True),out)
        details=out.tables['flaggedValues']['rows']
        self.assertEqual(len(details),500);self.assertEqual(details[0]['row'],ids[1001])
        self.assertEqual(details[-1]['row'],ids[1500]);self.assertEqual(details[0]['basis'],'Infinite Z (zero spread)')
        self.assertEqual(out.tables['variables']['rows'][0]['flagged'],1000)
        self.assertEqual(len(out.outputs['screenFlags']['values']),2001)
        self.assertIn('500 of 1000',out.texts['flaggedScope'])

    def test_no_flagged_measurements_has_explicit_empty_scope(self):
        result=run_analysis('pyoutlierdetection',dict(x=number([0,1,2,3,4])),dict(vars=['x'],method='iqr',showFlaggedValues=True))
        self.assertEqual(result['tables'].get('flaggedValues',{'rows':[]})['rows'],[])
        self.assertIn('0 of 0',result['texts']['flaggedScope'])
