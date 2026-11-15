"""Native survival presentation against frozen R outputs and saved-state geometry."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'inst/python'))
from cpj_runtime import execute
from cpj_plots import figure,render
from cpjtest import number,factor,text,run_analysis
FIXTURES=json.loads((ROOT/'tests/fixtures/kaplan-meier-core.json').read_text())['fixtures']


def request(f,**options):
    inp=f['inputs']
    return dict(analysis='pysinglearm',columns=dict(Time=number(inp['time']),
        Status=factor([None if v is None else ['Censored','Event'][v] for v in inp['event']],
                      ['Censored','Event'])),
        row_ids=[str(7*i+3) for i in range(len(inp['time']))],
        options=dict(elapsedtime='Time',outcome='Status',outcomeLevel='Event',censorLevel='Censored',
            cutp=','.join(str(v) for v in f['queries']),ciWidth=f['confidence']*100,
            timefix=f['timefix'],**options))


class SingleArmAdapter(unittest.TestCase):
    def close(self,a,b):
        if b is None:self.assertIsNone(a)
        else:self.assertAlmostEqual(a,b,delta=2e-12*max(1,abs(b)))

    def test_all_frozen_R_configurations_native_tables(self):
        for f in FIXTURES:
            req=request(f,person_time=True,showSteps=True,showCases=True)
            g=execute(req);e=f['expected']
            self.assertEqual(g['status'],'ok',(f['id'],g.get('error')))
            cohort=g['tables']['cohort']['rows'][0]
            for a,b in [('source','n_source'),('complete','n_complete'),('excluded','excluded_missing'),
                        ('events','events'),('censored','censored'),('normalized','timefix_changed_rows')]:
                self.assertEqual(cohort[a],e[b])
            for m,ref in zip(g['tables']['medians']['rows'],[e['median'],e['reverse']['median']]):
                for key in ('estimate','lower','upper'):self.close(m[key],ref[key])
            rate=g['tables']['personTime']['rows'][0]
            for a,b in [('exposure','person_time'),('estimate','estimate'),('lower','lower'),('upper','upper')]:
                self.close(rate[a],e['rate'][b])
            for rows,refs in [(g['tables']['steps']['rows'],e['curve']),
                              (g['tables']['selectedTimes']['rows'],e['selected'])]:
                self.assertEqual(len(rows),len(refs))
                for row,ref in zip(rows,refs):
                    for key in ('time','events','censored','survival','lower','upper'):self.close(row[key],ref[key])
                    self.assertEqual(row['risk'],ref['n_risk'])
            cases=g['tables']['cases']['rows']
            self.assertEqual([r['sourceID'] for r in cases],[req['row_ids'][i] for i in e['retained_indices']])
            self.assertEqual([r['effectiveTime'] for r in cases],e['effective_times'])
            self.assertFalse(g['plots'])

    def test_frozen_step_coordinates_confidence_intervals_and_censor_ticks(self):
        for f in FIXTURES:
            g=execute(request(f,sc=True,ci95=True,censored=True));state=g['plots']['survivalPlot']
            with patch('cpj_kaplan_meier.kaplan_meier_core',side_effect=RuntimeError('no refit')):
                fig=figure(state,palette=['#4477AA'],background='#222222',foreground='white')
            from matplotlib.collections import PolyCollection,PathCollection
            ax=fig.axes[0];e=f['expected'];p=e['curve'];scale=e['max_time'] or 1
            xs=[0]+[r['time']/scale for r in p];ys=[1]+[r['survival'] for r in p]
            if p[-1]['time']<e['max_time']:xs.append(1);ys.append(ys[-1])
            np.testing.assert_allclose(ax.lines[0].get_xdata(),xs,rtol=2e-12)
            np.testing.assert_allclose(ax.lines[0].get_ydata(),ys,rtol=2e-12)
            self.assertEqual(ax.lines[0].get_drawstyle(),'steps-post')
            rects=[r for r in ax.collections if isinstance(r,PolyCollection)]
            expected=[]
            for i,r in enumerate(p):
                end=p[i+1]['time'] if i+1<len(p) else e['max_time']
                if r['lower'] is not None and end>r['time']:
                    expected.append([(r['time']/scale,r['lower']),(end/scale,r['lower']),
                                     (end/scale,r['upper']),(r['time']/scale,r['upper'])])
            self.assertEqual(sum(len(c.get_paths()) for c in rects),len(expected))
            for path,vertices in zip([v for c in rects for v in c.get_paths()],expected):
                np.testing.assert_allclose(path.vertices[:4],vertices,rtol=2e-12,atol=1e-15)
            marks=[r for r in p if r['censored']>0]
            scatters=[r for r in ax.collections if isinstance(r,PathCollection)]
            self.assertEqual(len(scatters),int(bool(marks)))
            if marks:np.testing.assert_allclose(scatters[0].get_offsets(),
                [[r['time']/scale,r['survival']] for r in marks],rtol=2e-12)
        self.assertEqual(render(state)['mime'],'image/png')

    def test_explicit_mapping_missingness_and_subject_alignment(self):
        req=request(FIXTURES[0],subject='ID',showCases=True)
        req['columns']['ID']=text(['001','01','a','b','c','d'])
        req['columns']['Status']['levels'].append('Unused')
        g=execute(req);self.assertEqual(g['status'],'ok',g.get('error'))
        self.assertEqual([r['subjectID'] for r in g['tables']['cases']['rows']],['001','01','a','b','c','d'])
        req['columns']['Time']['values'][0]=None
        req['columns']['Status']['codes'][0]=2
        self.assertEqual(execute(req)['status'],'input_error')
        req=request(FIXTURES[0]);req['columns']['Status']['levels']=['NA','Event']
        req['options']['censorLevel']='NA'
        self.assertEqual(execute(req)['status'],'ok')
        req['columns']['Status']['levels'][0]=None
        self.assertEqual(execute(req)['status'],'input_error')
        for change in ({'outcomeLevel':None},{'censorLevel':'Event'},{'cutp':'1,,2'},
                       {'cutp':'nan'},{'cutp':'-1'},{'cutp':'__import__("os")'},
                       {'ciWidth':True},{'sc':1},{'timefix':1}):
            r=request(FIXTURES[0]);r['options'].update(change)
            self.assertEqual(execute(r)['status'],'input_error',change)

    def test_output_bounds_defaults_and_large_time_rendering(self):
        req=request(FIXTURES[0]);g=execute(req)
        for key in ('personTime','steps','cases'):self.assertFalse(g['tables'].get(key,{}).get('rows',[]))
        req['options']['showFollowup']=False
        self.assertEqual(len(execute(req)['tables']['medians']['rows']),1)
        n=5001
        req['columns']=dict(Time=number(range(1,n+1)),Status=factor(['Event','Censored']*(n//2)+['Event']))
        req['options'].update(sc=True,showSteps=True,showCases=True)
        req.pop('row_ids')
        g=execute(req);self.assertEqual(g['status'],'ok',g.get('error'))
        self.assertEqual(g['tables']['cohort']['rows'][0]['complete'],n)
        self.assertFalse(g['plots']);self.assertEqual(len(g['tables']['steps']['rows']),1000)
        self.assertEqual(len(g['tables']['cases']['rows']),1000)
        for times in ([0,0],[1e300,2e300]):
            req['columns']=dict(Time=number(times),Status=factor(['Event','Censored']))
            g=execute(req);self.assertEqual(g['status'],'ok',g.get('error'))
            self.assertEqual(render(g['plots']['survivalPlot'])['mime'],'image/png')

    def test_saved_state_refusals_and_real_subprocess(self):
        req=request(FIXTURES[0],sc=True,ci95=True,censored=True,showExplanations=True)
        g=run_analysis(req['analysis'],req['columns'],req['options'],row_ids=req['row_ids'])
        self.assertEqual(g['status'],'ok',g.get('error'));self.assertIn('explanation',g['texts'])
        state=g['plots']['survivalPlot']
        for key in ('risk','event','survival','ci','order','flag','size'):
            s=copy.deepcopy(state);p=json.loads(s['columns']['payload'][0])
            if key=='risk':p['points'][0]['n_risk']+=1
            if key=='event':p['points'][0]['events']=-1
            if key=='survival':p['points'][0]['survival']=.1
            if key=='ci':p['points'][0]['lower']=2
            if key=='order':p['points'][1]['time']=p['points'][0]['time']
            if key=='flag':p['show_ci']=1
            if key=='size':p['points']*=1000
            s['columns']['payload'][0]=json.dumps(p)
            with self.subTest(key=key),self.assertRaises(ValueError):figure(s)

if __name__=='__main__':unittest.main()
