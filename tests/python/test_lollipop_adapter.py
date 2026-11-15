"""Native output contracts and static geometry, independently referenced to R."""
import copy
import json
import sys
import unittest
from unittest.mock import patch
import numpy as np
from cpjtest import ROOT, number, run_analysis

sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import execute
from cpj_plots import figure

FIXTURES=json.loads((ROOT/'tests/fixtures/lollipop-core.json').read_text())['fixtures']


def request(f,run=None,**opts):
    a=f['inputs'];options=dict(dep='Value',group='Group',showCases=True)
    if run:options.update(aggregation=run['aggregation'],sortBy=run['sorting'],orientation=run['orientation'])
    options.update(baseline=a['baseline'],**opts)
    return dict(analysis='pylollipop',columns=dict(Value=number(a['values']),
        Group=dict(kind='factor',codes=[None if c<0 else c for c in a['codes']],levels=a['levels'])),
        options=options,row_ids=[str(7*i+3) for i in range(len(a['values']))])


class LollipopAdapter(unittest.TestCase):
    def test_all_independent_reference_runs(self):
        for f in FIXTURES:
            for run in f['runs']:
                req=request(f,run,showMean=True)
                r=execute(req);self.assertEqual(r['status'],'ok',(f['id'],r.get('error')))
                e=run['expected'];rows=r['tables']['descriptives']['rows']
                for actual,key in zip(rows,('raw_summary','plotted_summary')):
                    for field,value in e[key].items():
                        if value is None:self.assertIsNone(actual[field])
                        else:self.assertAlmostEqual(actual[field],value,delta=2e-12*max(1,abs(value)))
                p=r['plots']['lollipopPlot']
                self.assertEqual(p['columns']['label'],[c['label'] for c in e['points']])
                self.assertEqual(p['columns']['slot'],[c['slot'] for c in e['points']])
                np.testing.assert_allclose(p['columns']['value'],[c['value'] for c in e['points']],rtol=2e-12)
                self.assertAlmostEqual(p['reference'],e['reference_mean'],delta=2e-12*max(1,abs(e['reference_mean'])))
                cases=r['tables']['cases']['rows']
                self.assertEqual([c['sourceID'] for c in cases],[req['row_ids'][i] for i in e['retained_indices']])
                mapping={i:(j+1,c['value']) for j,c in enumerate(e['points']) for i in c['source_indices']}
                for actual,i in zip(cases,e['retained_indices']):
                    self.assertEqual(actual['point'],mapping[i][0])
                    self.assertAlmostEqual(actual['plotted'],mapping[i][1],delta=2e-12*max(1,abs(mapping[i][1])))

    def test_stems_scatter_axis_and_no_refit_during_rendering(self):
        f=FIXTURES[0]
        for run in f['runs']:
            req=request(f,run,showMean=True,showValues=True)
            state=execute(req)['plots']['lollipopPlot'];e=run['expected']
            with patch('cpj_lollipop_adapter.lollipop_core',side_effect=AssertionError('refit')):
                fig=figure(state)
            ax=fig.axes[0];segments=ax.collections[0].get_segments();offsets=ax.collections[1].get_offsets()
            horizontal=run['orientation']=='horizontal'
            for segment,offset,p in zip(segments,offsets,e['points']):
                expected=[[p['stem_start'],p['slot']],[p['stem_end'],p['slot']]] if horizontal else [[p['slot'],p['stem_start']],[p['slot'],p['stem_end']]]
                np.testing.assert_allclose(segment,expected)
                np.testing.assert_allclose(offset,expected[1])
            labels=ax.get_yticklabels() if horizontal else ax.get_xticklabels()
            self.assertEqual([x.get_text() for x in labels],e['axis_levels'])
            self.assertEqual(len(ax.lines),1)
            fig.clear()

    def test_defaults_and_output_gates_preserve_computation(self):
        req=request(FIXTURES[0]);req['options'].pop('showCases')
        a=execute(req)
        self.assertIsNone(a['plots']['lollipopPlot']['reference'])
        self.assertNotIn('cases',a['tables'])
        req['options'].update(showPlot=False,showPoints=False)
        b=execute(req)
        self.assertFalse(b['plots']);self.assertNotIn('points',b['tables'])
        for name in ('cohort','missing','descriptives','groups'):
            self.assertEqual(a['tables'][name],b['tables'][name])

    def test_resource_disclosure_and_unknown_options(self):
        f=dict(inputs=dict(values=list(range(1002)),codes=[i%2 for i in range(1002)],levels=['A','B'],baseline=0))
        r=execute(request(f,aggregation='none'))
        self.assertEqual(len(r['tables']['points']['rows']),1000)
        self.assertEqual(len(r['tables']['cases']['rows']),1000)
        self.assertEqual(len(r['plots']['lollipopPlot']['columns']['value']),1002)
        self.assertTrue(r['notices'])
        for opts in (dict(showPlot='yes'),dict(useHighlight=True),dict(dep='Group')):
            self.assertEqual(execute(request(FIXTURES[0],**opts))['status'],'input_error')

    def test_corrupted_drawing_payloads_are_rejected(self):
        state=execute(request(FIXTURES[0]))['plots']['lollipopPlot']
        for column,value in [('slot',0),('slot',True),('label',''),('value',None),
                             ('baseline',float('inf')),('orientation','diagonal'),('annotation',123)]:
            changed=copy.deepcopy(state);changed['columns'][column][0]=value
            with self.subTest(column=column),self.assertRaises(ValueError):figure(changed)
        changed=copy.deepcopy(state);changed['columns']['label'][1]=changed['columns']['label'][0]
        with self.assertRaises(ValueError):figure(changed)

    def test_real_subprocess(self):
        req=request(FIXTURES[0],showMean=True)
        result=run_analysis('pylollipop',columns=req['columns'],options=req['options'],row_ids=req['row_ids'])
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['tables'],execute(req)['tables'])


if __name__=='__main__':unittest.main()
