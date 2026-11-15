"""Independent public-runtime tables and saved-state drawing acceptance."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import execute
from cpj_plots import figure,render
from cpjtest import number,run_analysis,text
FIXTURES=json.loads((ROOT/'tests/fixtures/waffle-core.json').read_text())['fixtures']


def request(f,**options):
    a=f['inputs']
    def factor(codes,levels):return dict(kind='factor',codes=[None if c<0 else c for c in codes],levels=levels)
    columns={'Category':factor(a['codes'],a['levels'])}
    opts=dict(groups='Category',rows=f['rows'],flip=f['flip'],**options)
    if a['weights'] is not None:columns['Count']=number(a['weights']);opts['counts']='Count'
    if a['facets'] is not None:
        columns['Panel']=factor(a['facets'],a['facet_levels']);opts['facet']='Panel'
    return dict(analysis='pyjwaffle',columns=columns,options=opts,
        row_ids=[str(i*7+3) for i in range(len(a['codes']))])


class WaffleAdapter(unittest.TestCase):
    def test_all_independent_runtime_configurations(self):
        for f in FIXTURES:
            req=request(f,showCases=True);got=execute(req);ref=f['expected']
            self.assertEqual(got['status'],'ok',(f['id'],got.get('error')))
            self.assertEqual(got['tables']['cohort']['rows'][0]['total'],ref['n_total'])
            rows=got['tables']['allocation']['rows'];cells=[c for p in ref['panels'] for c in p['cells']]
            self.assertEqual([r['tiles'] for r in rows],[c['tiles'] for c in cells])
            self.assertEqual([r['count'] for r in rows],[c['count'] for c in cells])
            self.assertEqual([r['proportion'] for r in rows],[c['proportion'] for c in cells])
            self.assertEqual([r['denominator'] for r in rows],[p['n_total'] for p in ref['panels'] for c in p['cells']])
            self.assertEqual([r['sourceID'] for r in got['tables']['cases']['rows']],
                [req['row_ids'][i] for i in ref['retained_indices']])
            payload=json.loads(got['plots']['wafflePlot']['columns']['payload'][0])
            self.assertEqual([p['geometry'] for p in payload['panels']],
                [p['geometry'] for p in ref['panels']])

    def test_static_rectangles_and_global_colors_without_core_refit(self):
        for f in FIXTURES:
            # Render all 140 configurations, including both extremes of aspect ratio.
            state=execute(request(f,show_legend=True,mytitle='Composition',legendtitle='Categories'))['plots']['wafflePlot']
            with patch('cpj_waffle.waffle_core',side_effect=RuntimeError('no source access')):
                fig=figure(state,width=900,height=600,palette=['#4477AA','#EE6677'],background='#222222',foreground='white')
            for axis,panel in zip(fig.axes,f['expected']['panels']):
                self.assertEqual(len(axis.patches),100)
                self.assertIn('N='+str(panel['n_total']),axis.get_title())
                for rect,tile in zip(axis.patches,panel['geometry']):
                    self.assertEqual((rect.get_x(),rect.get_y()),(tile['xmin'],tile['ymin']))
                    self.assertEqual((rect.get_width(),rect.get_height()),(1,1))
            self.assertEqual([t.get_text() for t in fig.legends[0].texts],
                [c['label'] for c in f['expected']['panels'][0]['cells']])
        self.assertEqual(render(state)['mime'],'image/png')

    def test_off_outputs_subjects_and_bounded_cases(self):
        req=request(FIXTURES[70],subject='ID',showCases=True,showPlot=False,showExplanations=False)
        req['columns']['ID']=text(['a','b','c','d','e','f'])
        got=execute(req);self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertFalse(got['plots']);self.assertNotIn('explanation',got['texts'])
        self.assertEqual([r['subjectID'] for r in got['tables']['cases']['rows']],list('abcdef'))
        n=1001;req=dict(analysis='pyjwaffle',columns={'g':dict(kind='factor',codes=[0]*n,levels=['A'])},options=dict(groups='g',showCases=True))
        got=execute(req);self.assertEqual(len(got['tables']['cases']['rows']),1000)
        self.assertEqual(got['tables']['cohort']['rows'][0]['total'],1001)

    def test_invalid_options_and_saved_corruptions(self):
        for options in (dict(showPlot=1),dict(mytitle='x'*201),dict(color_palette='pastel'),dict(rows=0)):
            req=request(FIXTURES[0]);req['options'].update(options)
            self.assertEqual(execute(req)['status'],'input_error')
        state=execute(request(FIXTURES[0]))['plots']['wafflePlot']
        for kind in ('count','total','tiles','geometry','proportion','rows','mapping','omitted','excess'):
            s=copy.deepcopy(state);p=json.loads(s['columns']['payload'][0]);panel=p['panels'][0]
            if kind=='count':panel['cells'][0]['count']+=1
            if kind=='total':panel['n_total']+=1
            if kind=='tiles':panel['cells'][0]['tiles']-=1
            if kind=='geometry':panel['geometry'][0]['x']+=1
            if kind=='proportion':panel['cells'][0]['proportion']=float('nan')
            if kind=='rows':p['rows']=0
            if kind=='mapping':panel['cells'][1]['label']=panel['cells'][0]['label']
            if kind=='omitted':panel['cells'][0]['omitted_positive']=True
            if kind=='excess':p['panels']*=9
            s['columns']['payload'][0]=json.dumps(p)
            with self.subTest(kind=kind),self.assertRaises(ValueError):figure(s)

    def test_subprocess_payload_and_native_shape(self):
        req=request(FIXTURES[0],showExplanations=True)
        got=run_analysis(req['analysis'],req['columns'],req['options'],row_ids=req['row_ids'])
        self.assertEqual(got['status'],'ok',got.get('error'))
        self.assertIn('explanation',got['texts'])
        self.assertEqual([r['tiles'] for r in got['tables']['allocation']['rows']],[48,32,20])


if __name__=='__main__':unittest.main()
