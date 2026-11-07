import csv,json,sys,unittest
from cpjtest import ROOT,number,text,factor,run_analysis
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import _decode,InputError
from cpj_diagnostic_studies import calculate,wilson

OPTIONS=dict(study='Study',true_positives='TP',false_positives='FP',false_negatives='FN',true_negatives='TN')


def data():
    with (ROOT/'data/python_diagnostic_study_examples.csv').open() as f:
        rows=list(csv.DictReader(f))
    return dict(Study=text([r['Study'] or None for r in rows]),
                **{k:number([float(r[k]) if r[k] else None for r in rows]) for k in ['TP','FP','FN','TN']})


class DiagnosticStudies(unittest.TestCase):
    def test_inspector_preserves_statistics_and_includes_native_counterparts(self):
        ids=[str(2*i+3) for i in range(12)]
        a=run_analysis('pydiagnosticmeta',data(),OPTIONS,row_ids=ids)
        b=run_analysis('pydiagnosticmeta',data(),dict(OPTIONS,show_explorer=True),row_ids=ids)
        self.assertEqual(b['tables'],a['tables'])
        self.assertEqual(b['outputs'],a['outputs'])
        self.assertFalse(a['htmls']);self.assertFalse(a['plots'])
        self.assertIn('Linked study inspector',b['htmls']['explorer'])
        self.assertEqual(set(b['plots']),{'sensitivityPlot','specificityPlot'})
        self.assertEqual(b['plots']['sensitivityPlot']['columns']['estimate'],[.8,.9,0,.8,1,.9,.8,.9])

    def test_inspector_encodes_only_precomputed_values_and_escapes_markup(self):
        import re
        from cpj_study_inspector import render
        r=calculate(_decode(data()),OPTIONS)
        r['studies'][0]['study']='</script><img src=x onerror="alert(1)"> & [label]'
        html=render(r['studies'],r['confidence'])
        encoded=re.search(r'payload=(\{.*?\}),rows=',html,re.S)[1]
        self.assertNotIn('<',encoded);self.assertNotIn('&',encoded)
        self.assertEqual(json.loads(encoded),dict(studies=r['studies'],confidence=95))
        self.assertNotIn('<img',html)
        self.assertNotIn('setOption',html);self.assertNotIn('fetch(',html)

    def test_inspector_bounds_and_all_excluded_outputs(self):
        from cpj_study_inspector import render
        r=calculate(_decode(data()),OPTIONS)
        for rows in [[],r['studies']*26]:
            with self.assertRaises(ValueError):render(rows,95)
        d=data();d['TP']=number([None]*12)
        result=run_analysis('pydiagnosticmeta',d,dict(OPTIONS,show_explorer=True))
        self.assertFalse(result['htmls']);self.assertFalse(result['plots'])

    def test_inspector_option_appends_without_changing_existing_analysis_defaults(self):
        import ast
        source=ROOT/'inst/python/analyses/oncopath/pydiagnosticmeta.py'
        spec=next(ast.literal_eval(n.value) for n in ast.parse(source.read_text()).body
                  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SPEC' for t in n.targets))
        self.assertEqual([v['name'] for v in spec['options'][:-1]],list(OPTIONS)+[
            'confidence_level','reject_invalid','show_studies','show_excluded','forest_plot','plot_limit','show_report'])
        self.assertEqual(spec['options'][-1]['name'],'show_explorer')
        self.assertIs(spec['options'][-1]['default'],False)

    def test_wilson_agrees_with_base_R_score_intervals(self):
        fixtures=json.loads((ROOT/'tests/fixtures/diagnostic-study-wilson.json').read_text())
        self.assertEqual(len(fixtures),100)
        for row in fixtures:
            lo,hi=wilson(row['x'],row['n'],row['level'])
            self.assertAlmostEqual(lo,row['lower'],places=12)
            self.assertAlmostEqual(hi,row['upper'],places=12)

    def test_literal_counts_exclusions_zero_cells_and_identity(self):
        r=calculate(_decode(data()),OPTIONS)
        self.assertEqual((r['input'],len(r['studies']),len(r['excluded']),r['zero']),(12,8,4,3))
        self.assertEqual((r['identity']['missing'],r['identity']['repeatedSubjects']),(1,1))
        self.assertEqual([v['sensitivity'] for v in r['studies']],[.8,.9,0,.8,1,.9,.8,.9])
        self.assertEqual([v['specificity'] for v in r['studies']],[.9,.8,.75,1,0,.8,.9,.9])
        self.assertEqual([v['reason'] for v in r['excluded']],['Missing count','Fractional count','Negative count','No diseased or no non-diseased participants'])
        self.assertEqual(r['studies'][2]['tp'],0)
        self.assertEqual(r['studies'][2]['seLower'],0)
        self.assertGreater(r['studies'][2]['seUpper'],0)

    def test_runtime_sparse_rows_and_forest_payload(self):
        ids=[str(2*i+3) for i in range(12)]
        r=run_analysis('pydiagnosticmeta',data(),dict(OPTIONS,forest_plot=True,plot_limit=5,show_report=True),row_ids=ids)
        self.assertEqual(r['status'],'ok',r.get('error'))
        self.assertEqual([v['sourceID'] for v in r['tables']['studies']['rows']],ids[:8])
        self.assertEqual(r['plots']['sensitivityPlot']['columns']['estimate'],[.8,.9,0,.8,1])
        self.assertEqual(r['plots']['specificityPlot']['columns']['estimate'],[.9,.8,.75,1,0])
        self.assertIn('No continuity correction',r['texts']['summary'])
        self.assertFalse(r['outputs'])

    def test_all_excluded_is_auditable_and_strict_rejection_is_fatal(self):
        d=data();d['TP']=number([None]*12)
        r=run_analysis('pydiagnosticmeta',d,dict(OPTIONS,forest_plot=True))
        self.assertEqual(r['status'],'ok')
        self.assertEqual(r['tables']['cohort']['rows'][0]['retained'],0)
        self.assertEqual(len(r['tables']['excluded']['rows']),12)
        self.assertFalse(r['plots'])
        strict=run_analysis('pydiagnosticmeta',data(),dict(OPTIONS,reject_invalid=True))
        self.assertEqual(strict['status'],'input_error')
        self.assertFalse(strict['tables'])

    def test_roles_storage_dimensions_and_limits(self):
        self.assertIn('Select',calculate({},OPTIONS)['pending'])
        for key,column in [('TP',factor(['1']*12)),('Study',number(range(12)))]:
            d=data();d[key]=column
            with self.assertRaises(InputError):calculate(_decode(d),OPTIONS)
        d=_decode(data());d.metadata['TP']={'classes':['Date']}
        with self.assertRaises(InputError):calculate(d,OPTIONS)
        for changes in [dict(confidence_level=95.),dict(confidence_level=True),dict(confidence_level=100),dict(plot_limit=101),dict(reject_invalid='yes')]:
            with self.assertRaises(InputError):calculate(_decode(data()),dict(OPTIONS,**changes))
        for n in [0,201]:
            d=dict(Study=text(['a']*n),**{k:number([1]*n) for k in ['TP','FP','FN','TN']})
            with self.assertRaises(InputError):calculate(_decode(d),OPTIONS)

    def test_permutation_and_confidence_width_preserve_points(self):
        d=data();a=calculate(_decode(d),OPTIONS)
        reversed_data={k:dict(v,**({'values':v['values'][::-1]})) for k,v in d.items()}
        b=calculate(_decode(reversed_data),dict(OPTIONS,confidence_level=99))
        self.assertEqual([r['sensitivity'] for r in b['studies']],[r['sensitivity'] for r in a['studies']][::-1])
        for old,new in zip(a['studies'],b['studies'][::-1]):
            self.assertLessEqual(new['seLower'],old['seLower']+1e-15)
            self.assertGreaterEqual(new['seUpper'],old['seUpper']-1e-15)

    def test_factor_id_actual_na_literal_na_and_exact_labels(self):
        d=dict(Study=dict(kind='factor',levels=['001','1','NA',None,'unused'],codes=[0,1,2,3]),**{k:number([1]*4) for k in ['TP','FP','FN','TN']})
        r=calculate(_decode(d),OPTIONS)
        self.assertEqual([v['study'] for v in r['studies']],['001','1','NA','Unnamed study'])
        self.assertEqual(r['identity']['missing'],1)

    def test_transport_integer_ceiling_and_infinity(self):
        d=dict(Study=text(['a']),TP=number([2**53]),FP=number([1]),FN=number([1]),TN=number([1]))
        self.assertIn('transport limit',calculate(_decode(d),OPTIONS)['excluded'][0]['reason'])
        d['TP']=number([float('inf')])
        with self.assertRaises(InputError):calculate(_decode(d),OPTIONS)


if __name__=='__main__':unittest.main()
