"""Independent R fixtures and boundary/lifecycle contracts for two descriptive ports."""
import itertools
import json
import sys
import unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
import cpj_runtime
from cpj_binning import make_breaks, fisher_jenks, assign, labels_for
from cpj_descriptive import summarize
from cpjtest import number, factor


def run(name,values,**opts):
    return cpj_runtime.execute(dict(analysis=name,columns={'x':number(values)},
        options=dict({'var':'x'} if name=='pycategorize' else {'vars':['x']},**opts),
        row_ids=[str(3*i+2) for i in range(len(values))]))

class Oracles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.oracle=json.loads((ROOT/'tests/fixtures/descriptive-oracles.json').read_text())

    def test_summaries_moments_and_shapiro_agree_with_R(self):
        for case in self.oracle['summaries']:
            with self.subTest(case=case['name']):
                x=np.array([np.nan if v is None else v for v in case['x']])
                s=summarize(x[~np.isnan(x)],True,True)
                for key,value in case['expected'].items():
                    if key=='missing':continue
                    if value is None:self.assertIsNone(s[key],(case['name'],key))
                    else:self.assertAlmostEqual(s[key],value,delta=2e-7 if key in ('w','p') else 1e-10*max(1,abs(value)),msg=(case['name'],key))

    def test_all_R_break_assignment_label_and_closure_fixtures(self):
        for i,case in enumerate(self.oracle['categories']):
            with self.subTest(i=i,method=case['method'],values=case['x']):
                x=np.array([np.nan if v is None else v for v in case['x']])
                b,_=make_breaks(x[~np.isnan(x)],case['method'],case['nbins'],case['manual'],case['multiplier'],case['exclude'])
                np.testing.assert_allclose(b,case['breaks'],rtol=0,atol=1e-12)
                labels,_=labels_for(b,case['label_style'],case['custom'],case['include'],case['right'])
                self.assertEqual(labels,case['labels'])
                code=assign(x,b,case['include'],case['right'])
                self.assertEqual(code.tolist(),[-1 if v is None else v for v in case['codes']])
                self.assertEqual(np.bincount(code[code>=0],minlength=len(labels)).tolist(),case['counts'])

    def test_jenks_objective_matches_independent_exhaustive_partitions(self):
        for data in [[1,2,3,8,9,20,21],[0,0,1,2,2,3,5,5],[1,1,2,2,8,8,9,9]]:
            x=np.array(data,dtype=float);unique=np.unique(x)
            for k in range(2,min(4,len(unique))):
                b=fisher_jenks(x,k);code=assign(x,b)
                got=sum(float(np.sum((x[code==g]-np.mean(x[code==g]))**2)) for g in range(k))
                costs=[]
                for boundaries in itertools.combinations(range(1,len(unique)),k-1):
                    threshold=[(unique[j-1]+unique[j])/2 for j in boundaries]
                    split=np.digitize(x,threshold)
                    costs.append(sum(float(np.sum((x[split==g]-np.mean(x[split==g]))**2)) for g in range(k)))
                self.assertAlmostEqual(got,min(costs),places=10)

class Integration(unittest.TestCase):
    def test_summary_runtime_and_original_outlier_row(self):
        r=run('pysummarydata',[1,2,3,4,5,6,100,None],distr=True,outliers=True,report_sentences=True,show_guidance=True)
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['tables']['outlierRows']['rows'],[{'variable':'x','row':'20','value':100.}])
        self.assertIn('normality',r['texts']['text'])
        self.assertEqual(sum(r['plots']['distribution']['columns']['count']),7)

    def test_summary_small_constant_large_n_missing_and_disabled_panels(self):
        for x,why in [([1],'sample size'),([3]*8,'constant'),(list(range(5001)),'sample size')]:
            r=run('pysummarydata',x,distr=True)
            self.assertEqual(r['status'],'ok',r.get('error'))
            row=r['tables']['diagnostics']['rows'][0]
            self.assertIsNone(row['p']);self.assertIn(why,row['status'])
        r=run('pysummarydata',[1,2,3],showplot=False)
        self.assertNotIn('distribution',r['plots']);self.assertNotIn('diagnostics',r['tables'])
        self.assertNotIn('reportSentences',r['texts'])
        r=run('pysummarydata',[None,None])
        self.assertEqual(r['status'],'ok');self.assertFalse(r['tables'])
        self.assertEqual(run('pysummarydata',[])['status'],'input_error')

    def test_categorize_saved_values_metadata_and_missing_denominators(self):
        r=run('pycategorize',[-1,0,1,2,3,4,5,6,None],method='manual',breaks='0,2,4',excludeoutofrange=True,excl=False,newvarname='Grade / band')
        self.assertEqual(r['status'],'ok',r.get('error'))
        out=r['outputs']['addtodata']
        self.assertEqual(out['row_ids'],['2','5','8','11','14','17','20','23','26'])
        self.assertEqual(out['values'],[None,0,0,0,1,1,None,None,None])
        self.assertEqual(out['title'],'Grade / band');self.assertEqual(out['measure_type'],'ordinal')
        rows=r['tables']['freqTable']['rows']
        self.assertEqual([r['n'] for r in rows],[3,2,1,3])
        self.assertAlmostEqual(sum(r['percent'] for r in rows),1)
        self.assertIsNone(rows[-1]['cumPercent'])
        self.assertIn('cut(x, breaks = c(0x',r['texts']['rcode'])

    def test_invalid_boundaries_constant_seeded_large_jenks_and_invalid_bins(self):
        for kwargs in [dict(method='manual',breaks='1,,2'),dict(method='manual',breaks='nan,2'),dict(method='manual',breaks='2',excludeoutofrange=True),dict(nbins=2.5),dict(method='manual',breaks='0,1e-15,10',excludeoutofrange=True)]:
            self.assertEqual(run('pycategorize',[0,1,2,3],**kwargs)['status'],'input_error',kwargs)
        self.assertEqual(run('pycategorize',[1,1,1])['status'],'input_error')
        self.assertEqual(run('pycategorize',[0,0,0,1],method='median')['status'],'input_error')
        with self.assertRaisesRegex(cpj_runtime.InputError,'not yet implemented'):fisher_jenks(np.arange(20001.),4)

    def test_custom_labels_missing_boundary_and_no_mutation_of_input(self):
        r=run('pycategorize',[0,1,2,3,4],method='equal',nbins=2,labels='custom',customlabels='A,A',includelowest=False)
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['outputs']['addtodata']['levels'],['Category 1','Category 2'])
        self.assertIsNone(r['outputs']['addtodata']['values'][0])
        self.assertTrue(any('Custom labels' in n['text'] for n in r['notices']))
