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
        self.assertNotIn('fetch(',html)
        self.assertNotIn('\"inclusion\":',encoded)

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
        self.assertEqual([v['name'] for v in spec['options'][:-3]],list(OPTIONS)+[
            'confidence_level','reject_invalid','show_studies','show_excluded','forest_plot','plot_limit','show_report'])
        self.assertEqual(spec['options'][-3]['name'],'show_explorer')
        self.assertIs(spec['options'][-3]['default'],False)

    def test_inclusion_is_explicit_original_order_and_audited(self):
        from cpj_study_inclusion import prepare
        d=_decode(data());r=calculate(d,OPTIONS)
        state=prepare(d,OPTIONS,r,None)
        self.assertEqual(state['included'],[str(i) for i in range(1,9)])
        definition=json.dumps(dict(version=1,rows=['7','1'],snapshot=state['snapshot']))
        opts=dict(OPTIONS,enable_inclusion=True,inclusionDefinition=definition,
                  show_explorer=True,show_report=True)
        result=run_analysis('pydiagnosticmeta',data(),opts)
        self.assertEqual(result['status'],'ok',result.get('error'))
        rows=result['tables']['studies']['rows']
        self.assertEqual([v['sourceID'] for v in rows],['1','7'])
        self.assertEqual(rows,[r['studies'][0],r['studies'][6]])
        self.assertEqual(result['tables']['inclusion']['rows'][0],dict(eligible=8,included=2,omitted=6,status='Applied to current input'))
        self.assertEqual(result['tables']['cohort']['rows'][0]['retained'],8)
        self.assertEqual(result['plots']['specificityPlot']['columns']['estimate'],[.9,.9])
        self.assertEqual(len(result['tables']['excluded']['rows']),4)

    def test_empty_stale_and_disabled_inclusion_never_fall_back_silently(self):
        from cpj_study_inclusion import prepare
        d=_decode(data());r=calculate(d,OPTIONS);state=prepare(d,OPTIONS,r,None)
        definition=json.dumps(dict(version=1,rows=[],snapshot=state['snapshot']))
        opts=dict(OPTIONS,enable_inclusion=True,inclusionDefinition=definition,show_explorer=True)
        empty=run_analysis('pydiagnosticmeta',data(),opts)
        self.assertFalse(empty['tables']['studies']['rows']);self.assertFalse(empty['plots'])
        self.assertIn('explorer',empty['htmls'])
        changed=data();changed['TP']['values'][0]=81
        stale=run_analysis('pydiagnosticmeta',changed,opts)
        self.assertEqual(stale['tables']['inclusion']['rows'][0]['status'],'Input changed: review and Apply again')
        self.assertFalse(stale['tables']['studies']['rows']);self.assertFalse(stale['plots'])
        self.assertIn('explorer',stale['htmls'])
        disabled=run_analysis('pydiagnosticmeta',changed,dict(opts,enable_inclusion=False,inclusionDefinition='invalid'))
        self.assertEqual(len(disabled['tables']['studies']['rows']),8)
        self.assertNotIn('inclusion',disabled['tables'])

    def test_snapshot_guards_data_ids_roles_and_order_but_not_confidence(self):
        from cpj_study_inclusion import prepare
        d=_decode(data());r=calculate(d,OPTIONS);state=prepare(d,OPTIONS,r,None)
        definition=json.dumps(dict(version=1,rows=['1'],snapshot=state['snapshot']))
        opts=dict(OPTIONS,inclusionDefinition=definition)
        ci=dict(opts,confidence_level=99)
        self.assertTrue(prepare(d,ci,calculate(d,ci),None)['valid'])
        for column,index,value in [('TP',0,81),('TP',9,2),('Study',0,'renamed')]:
            raw=data();raw[column]['values'][index]=value;changed=_decode(raw)
            self.assertFalse(prepare(changed,opts,calculate(changed,opts),None)['valid'])
        ids=[str(i+2) for i in range(12)]
        self.assertFalse(prepare(d,opts,calculate(d,opts,ids),ids)['valid'])
        raw=data();reversed_data={k:dict(v,values=v['values'][::-1]) for k,v in raw.items()};changed=_decode(reversed_data)
        self.assertFalse(prepare(changed,opts,calculate(changed,opts),None)['valid'])

    def test_inclusion_rejects_malformed_definitions_and_noneligible_rows(self):
        from cpj_study_inclusion import prepare
        d=_decode(data());r=calculate(d,OPTIONS);state=prepare(d,OPTIONS,r,None)
        good=dict(version=1,rows=['1'],snapshot=state['snapshot'])
        for value in [None,'x','x'*30001,json.dumps([]),json.dumps(dict(good,version=True)),
                      json.dumps(dict(good,rows=['1','1'])),json.dumps(dict(good,snapshot='bad')),
                      json.dumps(dict(good,rows=[1])),json.dumps(dict(good,extra=1))]:
            with self.assertRaises(InputError):prepare(d,dict(OPTIONS,inclusionDefinition=value),r,None)
        for row in ['9','unknown']:
            self.assertFalse(prepare(d,dict(OPTIONS,inclusionDefinition=json.dumps(dict(good,rows=[row]))),r,None)['valid'])
        with self.assertRaises(InputError):prepare(d,OPTIONS,r,['1']*12)

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
