"""Native pie adapter and serialized geometry rendered without a statistical refit."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import execute
from cpj_plots import figure, render
from cpjtest import number, text, run_analysis
FIXTURES=json.loads((ROOT/'tests/fixtures/pie-core.json').read_text())['fixtures']


def request(f,**options):
    a=f['inputs']
    columns={'Outcome':dict(kind='factor',codes=[None if c<0 else c for c in a['codes']],levels=a['levels'])}
    opts=dict(dep='Outcome',**options)
    if a['weights'] is not None:
        columns['Frequency']=number(a['weights']);opts['counts']='Frequency'
    return dict(analysis='pyjjpiestats',columns=columns,options=opts,
                row_ids=[str(i*7+3) for i in range(len(a['codes']))])


class PieNativeAdapter(unittest.TestCase):
    def test_all_independent_fixtures_through_public_runtime(self):
        for f in FIXTURES:
            req=request(f,showCases=True);got=execute(req);ref=f['expected']
            self.assertEqual(got['status'],'ok',(f['id'],got.get('error')))
            self.assertEqual(got['tables']['cohort']['rows'][0]['total'],ref['n_total'])
            rows=got['tables']['frequencies']['rows']
            self.assertEqual([r['count'] for r in rows],[c['count'] for c in ref['cells']])
            self.assertEqual([r['category'] for r in rows],[c['label'] for c in ref['cells']])
            self.assertEqual([r['sourceID'] for r in got['tables']['cases']['rows']],
                             [req['row_ids'][i] for i in ref['retained_indices']])
            for row,c in zip(rows,ref['cells']):
                self.assertEqual(row['denominator'],ref['n_total'])
                self.assertAlmostEqual(row['proportion'],c['proportion'])
            self.assertNotIn('association',got['tables'])

    def test_wedges_match_independent_geometry_and_preserve_zero_legend(self):
        for f in FIXTURES:
            state=execute(request(f))['plots']['piePlot']
            with patch('cpj_pie.pie_core',side_effect=RuntimeError('no refit')):
                fig=figure(state,width=650,height=450)
            ax=fig.axes[0];expected=[c for c in f['expected']['cells'] if c['count']>0]
            self.assertEqual(len(ax.patches),len(expected))
            self.assertEqual([t.get_text() for t in ax.get_legend().get_texts()],
                             [c['label'] for c in f['expected']['cells']])
            for wedge,c in zip(ax.patches,expected):
                self.assertAlmostEqual(wedge.theta1,90-math.degrees(c['theta_upper']))
                self.assertAlmostEqual(wedge.theta2,90-math.degrees(c['theta_lower']))
            self.assertTrue(all(t.get_text() for t in ax.texts))
            self.assertEqual(len(ax.texts),len(expected))
        self.assertEqual(render(state)['mime'],'image/png')

    def test_labels_digits_off_switches_and_true_missing_subjects(self):
        for label in ('percentage','counts','both'):
            got=execute(request(FIXTURES[0],label=label,digitsperc=2))
            annotations=got['plots']['piePlot']['columns']['annotation']
            self.assertEqual(annotations[0],{'percentage':'48.00%','counts':'12','both':'12\n(48.00%)'}[label])
        req=request(FIXTURES[6],subject='ID',showCases=True)
        req['columns']['ID']=text(['001',None,'01','1'])
        got=execute(req);self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertEqual([r['subjectID'] for r in got['tables']['cases']['rows']],['001','01','1'])
        got=execute(request(FIXTURES[0],showPlot=False,showCases=False))
        self.assertFalse(got['plots']);self.assertNotIn('cases',got['tables'])

    def test_unsupported_options_and_invalid_inputs_are_refused(self):
        for options in (dict(group='Group'),dict(typestatistics='bayes'),dict(ratio='1,2',customRatios=True,resultssubtitle=True),
                        dict(showPlot=1),dict(label='bogus'),dict(digitsperc=True),dict(digitsperc=3)):
            self.assertEqual(execute(request(FIXTURES[0],**options))['status'],'input_error',options)
        req=request(FIXTURES[0],subject='ID');req['columns']['ID']=text(['a','b','c'])
        self.assertEqual(execute(req)['status'],'input_error')

    def test_saved_geometry_corruptions_are_refused(self):
        state=execute(request(FIXTURES[0]))['plots']['piePlot']
        for kind in ('count','denominator','order','gap','nonfinite','labels'):
            s=copy.deepcopy(state);c=s['columns']
            if kind=='count':c['count'][0]+=1
            if kind=='denominator':c['total']=[999]*3
            if kind=='order':c['lower'].reverse();c['upper'].reverse()
            if kind=='gap':c['lower'][0]+=.01
            if kind=='nonfinite':c['lower'][0]=float('nan')
            if kind=='labels':c['category'][1]=c['category'][0]
            with self.subTest(kind=kind),self.assertRaises(ValueError):figure(s)

    def test_actual_subprocess_returns_descriptive_native_payload(self):
        req=request(FIXTURES[0],label='both',showCases=True)
        got=run_analysis(req['analysis'],req['columns'],req['options'],row_ids=req['row_ids'])
        self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertEqual(got['plots']['piePlot']['columns']['annotation'],['12\n(48%)','8\n(32%)','5\n(20%)'])


if __name__=='__main__':unittest.main()
