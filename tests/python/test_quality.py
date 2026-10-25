"""Independent R accounting fixtures and bounded local interactive/plot contracts."""
import json
import shutil
import subprocess
import tempfile
import sys
import unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
import cpj_runtime
from cpj_quality import profile,duplicate_rows,preview
from cpj_plots import figure
from cpjtest import number,factor,text

class Oracles(unittest.TestCase):
    def test_base_R_profiles_and_duplicate_accounting(self):
        cases=json.loads((ROOT/'tests/fixtures/quality-oracles.json').read_text())['cases']
        for i,c in enumerate(cases):
            with self.subTest(i=i):
                r=profile(cpj_runtime._decode(c['columns']),c['threshold'])
                for got,want in zip(r['summaries'],c['summaries']):
                    self.assertEqual(set(got),set(want))
                    for key,value in want.items():
                        if isinstance(value,float):self.assertAlmostEqual(got[key],value,places=13,msg=(i,key))
                        else:self.assertEqual(got[key],value,(i,key))
                for key in ('complete','missingCells'):self.assertEqual(r[key],c[key])
                self.assertEqual(r['rowMissing'].tolist(),c['rowMissing'])
                expected=c['duplicate'];expected['patterns']=[tuple(x) for x in expected['patterns']]
                self.assertEqual(duplicate_rows(r['codes']),expected)

class Integration(unittest.TestCase):
    def run_quality(self,columns,**options):
        return cpj_runtime.execute(dict(analysis='pydataquality',columns=columns,
            options=dict(vars=list(columns),**options),row_ids=[str(3*i+2) for i in range(len(next(iter(columns.values())).get('values',next(iter(columns.values())).get('codes',[]))))]))

    def test_runtime_duplicates_missing_values_and_original_rows(self):
        cols={'sep':text(['a||b','a','a||b',None,None]),'collapse':text(['c','b||c','c',None,None])}
        r=self.run_quality(cols,check_missing=True,check_duplicates=True,row_level_duplicates=True,showInteractive=True,plot_missing_patterns=True,plot_data_types=True)
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual(r['tables']['duplicates']['rows'][0]['excess'],2)
        self.assertEqual(r['tables']['duplicatePatterns']['rows'],[dict(firstRow='2',n=2,excess=1),dict(firstRow='11',n=2,excess=1)])
        self.assertEqual(r['tables']['completeness']['rows'][0]['complete'],3)
        self.assertEqual(r['plots']['previewMap']['columns']['row'][:4],['2','2','5','5'])
        self.assertIn('Display controls only',r['htmls']['explorer'])
        self.assertIn('No formal MCAR',' '.join(r['tables']['rowMissing']['notes']))

    def test_missing_all_empty_flags_and_value_duplicates(self):
        r=self.run_quality({'x':number([None,None,None]),'g':factor(['NA','NA',None],levels=['NA','unused'])},check_duplicates=True)
        self.assertEqual(r['status'],'ok',r.get('error'))
        rows=r['tables']['duplicates']['rows']
        self.assertIsNone(rows[0]['rate']);self.assertEqual(rows[1]['excess'],1)
        self.assertEqual(r['tables']['overview']['rows'][0]['constant'],'No')
        self.assertFalse(r['plots']);self.assertFalse(r['htmls'])
        self.assertEqual(self.run_quality({'x':number([])})['status'],'input_error')
        self.assertEqual(self.run_quality({'x':number([1])},missing_threshold_visual=101)['status'],'input_error')

    def test_threshold_unrounded_and_plot_preview_bounds(self):
        r=profile({'x':np.r_[np.full(251,np.nan),np.arange(2249)]},10)
        self.assertTrue(r['summaries'][0]['aboveThreshold'])
        r=profile({str(i):np.arange(250,dtype=float) for i in range(25)})
        p=preview(r,list(map(str,range(25))))
        self.assertEqual((len(p['row_ids']),len(p['variables'])),(200,20))
        self.assertEqual((p['total_rows'],p['total_variables']),(250,25))
        with self.assertRaises(cpj_runtime.InputError):profile({str(i):np.ones(1) for i in range(201)})

    def test_html_user_strings_are_safe_and_no_network_or_refit_hooks(self):
        module=cpj_runtime._load('pydataquality')
        html=module.html_document(dict(variables=['</script><img src=x onerror=alert(1)>'],row_ids=['<&'],missing=[[1]],total_rows=1,total_variables=1))
        self.assertEqual(html.count('</script>'),1)
        self.assertIn('\\u003c/script\\u003e',html)
        for bad in ('innerHTML','fetch(','XMLHttpRequest','setOption','http://','https://'):
            self.assertNotIn(bad,html)
        self.assertIn("addEventListener('focus'",html)

    def test_local_javascript_display_events(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node is required for the offline JavaScript DOM harness')
        payload=dict(variables=['X','Y'],row_ids=[str(3*i+2) for i in range(22)],
          missing=[[0,1] if i==1 else [0,0] for i in range(22)],total_rows=22,total_variables=2)
        html=cpj_runtime._load('pydataquality').html_document(payload)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'quality.html';path.write_text(html)
            result=subprocess.run([node,str(ROOT/'tools/check-quality-interaction.js'),str(path)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_quality_map_geometry_uses_original_rows_and_rectangular_cells(self):
        s=dict(kind='qualitymap',columns=dict(variable=['A','B','A','B'],row=['2','2','9','9'],state=['Observed','Missing','Missing','Observed']),xlab='Variable',ylab='Original row')
        f=figure(s);a=f.axes[0]
        np.testing.assert_array_equal(a.images[0].get_array(),[[0,1],[1,0]])
        self.assertEqual([t.get_text() for t in a.get_yticklabels()],['2','9']);f.clear()
        for key in s['columns']:s['columns'][key]=s['columns'][key][:-1]
        with self.assertRaisesRegex(ValueError,'rectangular'):figure(s)
