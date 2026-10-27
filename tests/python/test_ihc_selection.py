"""Snapshot-bound source selections, independent row alignment and non-subsetting checks."""
import json
import sys
import unittest
import numpy as np
from cpjtest import ROOT,number,text
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import execute,InputError
from cpj_ihc import prepare,applied_selection

IDS=['2','4','7','9','12','15']
DATA={'a':np.array([0.,10,1,11,np.nan,np.nan]),
      'b':np.array([0.,20,2,22,3,np.nan]),'id':['same','same','other','other','partial','all']}
BASE=dict(markers=['a','b'],subject='id',enableSelection=True)
def prepared(**extra):return prepare(DATA,dict(BASE,**extra),IDS)
def definition(p,rows):return json.dumps(dict(version=1,rows=rows,snapshot=p['snapshot']))
def runtime(options):
    return execute(dict(analysis='pyihcheatmap',row_ids=IDS,
      columns={'a':number(DATA['a']),'b':number(DATA['b']),'id':text(DATA['id'])},options=options))

class Selection(unittest.TestCase):
    def test_original_rows_and_repeated_subjects_remain_distinct(self):
        p=prepared();s=applied_selection(definition(p,['4','12']),p,IDS)
        self.assertEqual(s['values'],[0,1,0,0,1,None])
        self.assertEqual(s['selectedRows'],['4','12'])
        self.assertEqual(s['selected'][0]['subject'],'same')
        self.assertNotIn('2',s['selectedRows'])

    def test_display_options_do_not_invalidate_selection_or_change_statistics(self):
        p=prepared();saved=definition(p,['4','12'])
        complete=prepared(missing='complete',scaling='zscore',clusterRows=True,clusterColumns=True)
        self.assertEqual(p['snapshot'],complete['snapshot'])
        s=applied_selection(saved,complete,IDS)
        self.assertTrue(s['valid']);self.assertEqual(s['unavailable'],['12'])
        self.assertEqual(s['values'],[0,1,0,0,None,None])
        options=dict(BASE,selectionDefinition=saved,missing='complete',scaling='zscore',
                     clusterRows=True,clusterColumns=True,showScatter=True,showDendrograms=True)
        r=runtime(options);empty=runtime(dict(options,selectionDefinition=''))
        self.assertEqual(r['status'],'ok',r.get('error'))
        for key in ('markerSummary','rowOrder','merges','scatterRows','scatterCohort'):
            self.assertEqual(r['tables'][key],empty['tables'][key])
        self.assertEqual(r['plots'],empty['plots'])
        self.assertEqual(r['outputs']['selectionFlag']['values'],[0,1,0,0,None,None])
        self.assertEqual(r['tables']['selectionSummary']['rows'][0]['unavailable'],1)

    def test_data_edits_deletion_insertion_filters_and_input_roles_require_review(self):
        p=prepared();saved=definition(p,['4'])
        changes=[]
        edited={k:v.copy() for k,v in DATA.items()};edited['a'][0]=99
        changes.append((edited,IDS,BASE))
        filtered={k:[v[i] for i in [0,2,4]] for k,v in DATA.items()}
        changes.append((filtered,['2','7','12'],BASE))
        inserted={k:np.insert(v,0,v[0]) if isinstance(v,np.ndarray) else [v[0]]+v for k,v in DATA.items()}
        changes.append((inserted,['1']+IDS,BASE))
        changes.append((DATA,IDS,dict(BASE,subject=None)))
        for data,ids,opts in changes:
            q=prepare(data,opts,ids);s=applied_selection(saved,q,ids)
            self.assertFalse(s['valid']);self.assertEqual(s['values'],[None]*len(ids))
            self.assertEqual(s['selectedRows'],[])
        q=prepare(filtered,BASE,['2','7','12'])
        current=applied_selection(definition(q,['7']),q,['2','7','12'])
        self.assertEqual(current['values'],[0,1,0])
        self.assertEqual(current['selectedRows'],['7'])
        r=runtime(dict(BASE,selectionDefinition=saved.replace(p['snapshot'],'0'*64)))
        self.assertEqual(r['tables']['selectionSummary']['rows'][0]['status'],'Needs review')
        self.assertEqual(r['outputs']['selectionFlag']['values'],[None]*6)

    def test_empty_disabled_and_malformed_definitions(self):
        p=prepared()
        self.assertEqual(applied_selection('',p,IDS)['values'],[0,0,0,0,0,None])
        disabled=runtime(dict(BASE,enableSelection=False,selectionDefinition='bad JSON'))
        self.assertEqual(disabled['status'],'ok')
        self.assertNotIn('selectionSummary',disabled['tables'])
        self.assertEqual(disabled['outputs']['selectionFlag']['values'],[None]*6)
        good=json.loads(definition(p,['4']))
        bad=['["4"]','bad JSON','x'*12001]
        for patch in [dict(version=True),dict(version=2),dict(rows=['4','4']),dict(rows=[4]),
                      dict(rows=[{}]),dict(rows=['']),dict(rows=['x\n']),dict(snapshot='x'),
                      dict(rows=[str(i) for i in range(201)]),dict(extra=1)]:
            bad.append(json.dumps(dict(good,**patch)))
        for value in bad:
            with self.assertRaises(InputError):applied_selection(value,p,IDS)

    def test_selected_values_preserve_raw_units_and_full_cohort_z_scores(self):
        import math
        saved=definition(prepared(),['4','12'])
        options=dict(BASE,selectionDefinition=saved,showSelectionValues=True,scaling='zscore')
        r=runtime(options)
        self.assertEqual(r['status'],'ok',r.get('error'))
        table=r['tables']['selectionValues']
        values={(v['sourceRow'],v['marker']):v for v in table['rows']}
        self.assertEqual(list(values),[('4','a'),('4','b'),('12','a'),('12','b')])
        self.assertEqual(values['4','a']['raw'],10)
        self.assertAlmostEqual(values['4','a']['displayed'],4.5/math.sqrt(101/3))
        self.assertAlmostEqual(values['4','b']['displayed'],10.6/math.sqrt(455.2/4))
        self.assertEqual(values['12','a']['status'],'Missing')
        self.assertIsNone(values['12','a']['raw']);self.assertIsNone(values['12','a']['displayed'])
        self.assertEqual(values['12','b']['raw'],3)
        self.assertEqual([v['position'] for v in table['rows']],[2,2,5,5])
        self.assertIn('full retained heatmap cohort',table['notes'][0])
        baseline=runtime(dict(options,showSelectionValues=False))
        self.assertNotIn('selectionValues',baseline['tables'])
        self.assertEqual(r['plots'],baseline['plots'])
        self.assertEqual(r['outputs'],baseline['outputs'])
        self.assertEqual(r['tables']['markerSummary'],baseline['tables']['markerSummary'])

    def test_selected_values_follow_both_cluster_orders_and_complete_row_exclusions(self):
        saved=definition(prepared(),['9','4','12'])
        options=dict(BASE,selectionDefinition=saved,showSelectionValues=True,missing='complete',
                     clusterRows=True,clusterColumns=True)
        r=runtime(options);self.assertEqual(r['status'],'ok',r.get('error'))
        values=r['tables']['selectionValues']['rows']
        raw={('4','a'):10,('4','b'):20,('9','a'):11,('9','b'):22}
        self.assertEqual({(v['sourceRow'],v['marker']):v['raw'] for v in values},raw)
        self.assertTrue(all(v['displayed']==v['raw'] for v in values))
        positions={v['sourceRow']:v['position'] for v in r['tables']['rowOrder']['rows']}
        self.assertEqual([v['position'] for v in values],sorted(v['position'] for v in values))
        for v in values:self.assertEqual(v['position'],positions[v['sourceRow']])
        cells=r['plots']['heatmap']['columns']
        markers=list(dict.fromkeys(cells['variable']))
        for i in range(0,len(values),2):self.assertEqual([v['marker'] for v in values[i:i+2]],markers)
        self.assertEqual(r['tables']['selectionSummary']['rows'][0]['unavailable'],1)

    def test_selected_values_clear_for_empty_stale_disabled_and_pending_states(self):
        good=definition(prepared(),['4'])
        for extra in [dict(selectionDefinition=''),dict(selectionDefinition=good.replace(prepared()['snapshot'],'0'*64)),
                      dict(enableSelection=False,selectionDefinition=good),dict(markers=[])]:
            r=runtime(dict(BASE,showSelectionValues=True,**extra))
            self.assertEqual(r.get('tables',{}).get('selectionValues',{}).get('rows',[]),[])

    def test_maximum_selected_values_are_complete_and_constant_missing_values_stay_explicit(self):
        from cpj_runtime import Output
        import importlib.util
        spec=importlib.util.spec_from_file_location('ihc_selection_test',ROOT/'inst/python/analyses/descriptives/pyihcheatmap.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        data={f'm {j}':np.arange(200,dtype=float)+j for j in range(20)}
        ids=[str(2*i+1) for i in range(200)]
        options=dict(markers=list(data),enableSelection=True,showSelectionValues=True,interactive=False)
        p=prepare(data,options,ids);options['selectionDefinition']=definition(p,ids)
        out=Output(module.SPEC,ids);module.run(data,options,out)
        values=out.tables['selectionValues']['rows']
        self.assertEqual(len(values),4000)
        self.assertEqual(len({(v['sourceRow'],v['marker']) for v in values}),4000)
        self.assertEqual(values[-1]['raw'],218)
        data={'A+B':np.array([7.,7.,np.nan]),'Grade 2/3':np.array([1.,2.,3.]),
              'ID':['<same>','<same>','other']};ids=['2','4','7']
        options=dict(markers=['A+B','Grade 2/3'],subject='ID',enableSelection=True,
                     showSelectionValues=True,scaling='zscore',interactive=False)
        options['selectionDefinition']=definition(prepare(data,options,ids),['4','7'])
        out=Output(module.SPEC,ids);module.run(data,options,out)
        values=out.tables['selectionValues']['rows']
        self.assertEqual([v['raw'] for v in values],[7,2,None,3])
        self.assertEqual([v['displayed'] for v in values],[0,0,None,1])
        self.assertEqual(values[0]['subject'],'<same>')
